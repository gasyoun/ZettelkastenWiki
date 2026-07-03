"""Note model and catalog loader.

Ported from the ORS-FAQ ``wiki_catalog`` with the group taxonomy, base URL,
slug rules and CTA defaults moved into :class:`~zettelkastenwiki.config.SiteConfig`.
The minimal YAML-frontmatter parser (scalars, ``- `` lists, one-level
mappings) is kept as-is — it is deliberately dependency-free.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .config import SiteConfig


@dataclass(frozen=True)
class Note:
    group: str
    path: Path
    rel_path: str
    body: str
    frontmatter: dict
    title: str
    slug: str
    url_path: str
    canonical_url: str
    seo_title: str
    seo_description: str
    og_image: str
    cta_primary: "tuple[str, str] | None"
    cta_secondary: "tuple[str, str] | None"
    aliases: tuple = ()
    section: str = ""
    source_type: str = ""
    teacher: str = ""
    track: str = ""
    indexable: bool = True
    legacy_source: str = ""
    lang: str = ""
    #: Last-commit date (``YYYY-MM-DD``) and author, filled when
    #: ``SiteConfig.git_recency`` is on — the recency signal for memory sites.
    git_date: str = ""
    git_author: str = ""

    @property
    def output_parts(self) -> tuple:
        return (self.group, self.slug)

    @property
    def testimonial(self) -> "tuple[str, str] | None":
        """Optional (author, text) testimonial from frontmatter; both parts
        must be present (no invented attribution)."""
        block = self.frontmatter.get("testimonial")
        if not isinstance(block, dict):
            return None
        author = str(block.get("author", "")).strip()
        text = str(block.get("text", "")).strip()
        return (author, text) if author and text else None


def split_cta(value: str) -> "tuple[str, str] | None":
    if "|" not in value:
        return None
    label, url = value.split("|", 1)
    label, url = label.strip(), url.strip()
    return (label, url) if label and url else None


def parse_frontmatter(text: str) -> tuple:
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}, text

    data: dict = {}
    current_key: str | None = None
    for line in match.group(1).splitlines():
        if current_key is not None and line.startswith("  ") and line.strip():
            child = line[2:]
            container = data[current_key]
            if child.startswith("- "):
                if not isinstance(container, list):
                    container = data[current_key] = []
                container.append(clean_scalar(child[2:]))
                continue
            if ":" in child:
                if not isinstance(container, dict):
                    container = data[current_key] = {}
                ck, cv = child.split(":", 1)
                container[ck.strip()] = clean_scalar(cv.strip())
                continue
        current_key = None
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not raw_value:
            data[key] = []
            current_key = key
        else:
            data[key] = clean_scalar(raw_value)

    return data, text[match.end():]


def clean_scalar(value: str):
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def slugify(value: str, transliteration: dict | None = None) -> str:
    table = transliteration or {}
    chars = [table.get(char, char) for char in value.lower()]
    slug = "".join(chars)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-") or "page"


def note_slug(rel_path: str, frontmatter: dict, config: SiteConfig) -> str:
    configured = str(frontmatter.get("slug", "")).strip()
    if configured:
        return configured
    if rel_path in config.slug_overrides:
        return config.slug_overrides[rel_path]
    return slugify(Path(rel_path).stem, config.transliteration)


def load_catalog(config: SiteConfig) -> list:
    root = Path(config.wiki_root)
    notes: list[Note] = []
    seen_slugs: set[str] = set()
    for spec in config.groups:
        group_dir = root / (spec.source_dir if spec.source_dir else spec.name)
        if not group_dir.exists():
            continue
        globber = group_dir.rglob if spec.recursive else group_dir.glob
        for path in sorted(globber(spec.pattern)):
            if not path.is_file():
                continue
            if any(path.match(pat) or path.name == pat for pat in spec.exclude):
                continue
            text = path.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(text)
            if config.source_filter is not None:
                body = config.source_filter(body)
            # rel_path stays group-scoped so URLs are /group/slug/ regardless
            # of where the source file physically lives.
            rel_path = f"{spec.name}/{path.name}"
            slug = note_slug(rel_path, frontmatter, config)
            if slug in seen_slugs:
                # Two source files collided on a slug (e.g. same stem in a
                # recursive tree) — disambiguate with a numeric suffix so both
                # publish and every URL stays unique.
                base = slug
                i = 2
                while f"{base}-{i}" in seen_slugs:
                    i += 1
                slug = f"{base}-{i}"
            seen_slugs.add(slug)
            # Defaults layer (opt-in): a frontmatter-less doc still gets a real
            # title from its first `# H1` instead of the filename stem. slug,
            # description and aliases already degrade gracefully below.
            fm_title = str(frontmatter.get("title", "")).strip()
            title = fm_title or (config.title_from_h1 and first_h1(body)) or path.stem
            seo_title = str(frontmatter.get("seo_title", "")).strip() or (
                f"{title}{config.seo_title_suffix}"
            )
            seo_description = str(frontmatter.get("seo_description", "")).strip() or truncate_text(
                markdown_excerpt(body), 155
            )
            og_override = str(frontmatter.get("og_image", "")).strip()
            git_date, git_author = _git_recency(path) if config.git_recency else ("", "")
            notes.append(
                Note(
                    group=spec.name,
                    path=path,
                    rel_path=rel_path,
                    body=body,
                    frontmatter=frontmatter,
                    title=title,
                    slug=slug,
                    url_path=f"{config.base_path}/{spec.name}/{slug}/",
                    canonical_url=f"{config.base_url}/{spec.name}/{slug}/",
                    seo_title=seo_title,
                    seo_description=seo_description,
                    og_image=og_override or f"{config.base_url}/og/{spec.name}/{slug}.png",
                    cta_primary=split_cta(str(frontmatter.get("cta_primary", "")))
                    or config.default_cta_primary,
                    cta_secondary=split_cta(str(frontmatter.get("cta_secondary", "")))
                    or config.default_cta_secondary,
                    aliases=tuple(str(v) for v in frontmatter.get("aliases", []) or []),
                    section=str(frontmatter.get("section", "")),
                    source_type=str(frontmatter.get("source_type", "")),
                    teacher=str(frontmatter.get("teacher", "")),
                    track=str(frontmatter.get("track", "")),
                    indexable=bool(frontmatter.get("indexable", True)),
                    legacy_source=str(frontmatter.get("legacy_source", "")),
                    lang=spec.lang or config.language,
                    git_date=git_date,
                    git_author=git_author,
                )
            )
    return notes


def _git_recency(path: Path) -> tuple:
    """(last-commit YYYY-MM-DD, author) for ``path`` via git log; ('','') if
    unavailable (not a repo, uncommitted file, or git missing)."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs%x09%an", "--", path.name],
            cwd=path.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ("", "")
    line = (out.stdout or "").strip()
    if out.returncode != 0 or not line or "\t" not in line:
        return ("", "")
    date, author = line.split("\t", 1)
    return (date.strip(), author.strip())


def first_h1(body: str) -> str:
    """The text of the first `# H1` heading, or '' if none."""
    match = re.search(r"^\#\s+(.*\S)\s*$", body, re.MULTILINE)
    return match.group(1).strip() if match else ""


def markdown_excerpt(markdown: str, limit: int = 220) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", markdown, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[\[([^]|]+)\|([^]]+)]]", r"\2", text)
    text = re.sub(r"\[\[([^]]+)]]", r"\1", text)
    text = re.sub(r"[#>*_`-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return truncate_text(text, limit)


def search_body_text(markdown: str, limit: int) -> str:
    """Cleaned body text for the full-text search index. Like
    ``markdown_excerpt`` but preserves intra-word hyphens and slashes, so
    technical terms (``golden-diff``, ``bot-kb-sync``, ``H103``, ``a/b``)
    stay searchable — descriptions use ``markdown_excerpt`` unchanged."""
    text = re.sub(r"^---\n.*?\n---\n", "", markdown, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[\[([^]|]+)\|([^]]+)]]", r"\2", text)
    text = re.sub(r"\[\[([^]]+)]]", r"\1", text)
    text = re.sub(r"[#>*_`]+", " ", text)  # markdown markers, but keep - and /
    text = re.sub(r"\s+", " ", text).strip()
    return truncate_text(text, limit)


def truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def search_terms(note: Note) -> list:
    terms = [note.title, note.section, note.source_type, note.track, note.teacher]
    terms.extend(note.aliases)
    return [term for term in terms if term]


def search_record(note: Note) -> dict:
    return {
        "title": note.title,
        "url": note.url_path,
        "section": note.section,
        "source_type": note.source_type,
        "track": note.track,
        "teacher": note.teacher,
        "aliases": list(note.aliases),
        "terms": search_terms(note),
        "excerpt": markdown_excerpt(note.body),
    }


def escape_attr(value: str) -> str:
    return html.escape(value, quote=True)
