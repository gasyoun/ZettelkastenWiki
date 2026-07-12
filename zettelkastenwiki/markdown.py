"""Markdown → HTML with ``[[wikilink]]`` resolution.

The deliberately small dialect the ORS-FAQ wiki uses: h1–h3, paragraphs,
unordered/ordered lists, blockquotes, fenced code, inline code, bold,
external links and wikilinks (``[[target]]`` / ``[[target|label]]``,
including ``../group/slug`` cross-group forms).
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from .catalog import Note, escape_attr
from .config import SiteConfig


def markdown_to_html(markdown: str, note: Note, notes: list, config: SiteConfig) -> str:
    lines = markdown.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    ordered_items: list[str] = []
    quote: list[str] = []
    in_code = False
    code_lines: list[str] = []
    autolink = build_autolinker(notes, config)

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{render_inline(' '.join(paragraph), note, notes, config, autolink)}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()
        if ordered_items:
            blocks.append("<ol>" + "".join(f"<li>{item}</li>" for item in ordered_items) + "</ol>")
            ordered_items.clear()

    def flush_quote() -> None:
        if quote:
            blocks.append(f"<blockquote>{' '.join(quote)}</blockquote>")
            quote.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_quote()
            if in_code:
                blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            flush_list()
            flush_quote()
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            flush_quote()
            level = len(heading.group(1))
            blocks.append(
                f"<h{level}>{render_inline(heading.group(2), note, notes, config, autolink)}</h{level}>"
            )
            continue
        if line.startswith(">"):
            flush_paragraph()
            flush_list()
            quote.append(render_inline(line.lstrip("> ").strip(), note, notes, config, autolink))
            continue
        unordered = re.match(r"^\s*-\s+(.*)$", line)
        if unordered:
            flush_paragraph()
            flush_quote()
            list_items.append(render_inline(unordered.group(1), note, notes, config, autolink))
            continue
        ordered = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if ordered:
            flush_paragraph()
            flush_quote()
            ordered_items.append(render_inline(ordered.group(1), note, notes, config, autolink))
            continue
        paragraph.append(line)

    flush_paragraph()
    flush_list()
    flush_quote()
    return "\n".join(blocks)


def render_inline(text: str, note: Note, notes: list, config: SiteConfig, autolink=None) -> str:
    escaped = html.escape(text)

    def wiki_link(match: "re.Match[str]") -> str:
        target = html.unescape(match.group(1)).strip()
        has_label = bool(match.lastindex and match.lastindex >= 2)
        url, resolved = resolve_wiki_link(target, note, notes, config)
        if has_label:
            label = html.unescape(match.group(2)).strip()
        elif resolved is not None:
            label = resolved.title
        else:
            label = pretty_wiki_target(target)
        return f'<a href="{escape_attr(url)}">{html.escape(label)}</a>'

    escaped = re.sub(r"\[\[([^]|\n]+)\|([^]\n]+)]]", wiki_link, escaped)
    escaped = re.sub(r"\[\[([^]\n]+)]]", wiki_link, escaped)
    escaped = re.sub(
        r"\[([^]\n]+)]\((https?://[^)\s]+)\)",
        lambda m: f'<a href="{escape_attr(html.unescape(m.group(2)))}">{m.group(1)}</a>',
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    # Auto-link bare tokens (e.g. H103) last, skipping existing links/code.
    if autolink is not None:
        escaped = autolink(escaped)
    return escaped


def resolve_wiki_link(target: str, current: Note, notes: list, config: SiteConfig) -> tuple:
    """Resolve a wikilink to (url_path, Note | None). Same-group wins, then
    exact group/name, then unique stem; unresolved links point home."""
    key = target.split("#", 1)[0].strip()
    key = key.removesuffix(".md").replace("\\", "/")
    while key.startswith("../"):
        key = key[3:]
    key = key.removeprefix("./").strip("/")

    by_rel = {note.rel_path.removesuffix(".md"): note for note in notes}
    by_stem = {}
    ambiguous_stems = set()
    for item in notes:
        stem = Path(item.rel_path).stem
        if stem in ambiguous_stems:
            continue
        if stem in by_stem:
            ambiguous_stems.add(stem)
            by_stem.pop(stem, None)
            continue
        by_stem[stem] = item
    same_group = by_rel.get(f"{current.group}/{key}")
    if same_group:
        return same_group.url_path, same_group
    if key in by_rel:
        return by_rel[key].url_path, by_rel[key]
    if key in by_stem:
        return by_stem[key].url_path, by_stem[key]
    return f"{config.base_path}/", None


def pretty_wiki_target(target: str) -> str:
    text = target.split("#", 1)[0].strip().removesuffix(".md")
    text = text.replace("\\", "/").rstrip("/").split("/")[-1]
    return text.replace("_", " ")


def autolink_target(token: str, notes: list):
    """Resolve a bare autolink token (e.g. ``H103``) to a Note: slug equals it,
    starts with ``token-``, or filename stem starts with ``token_``. Returns
    the Note or None."""
    key = token.lower()
    for note in notes:
        if note.slug == key:
            return note
    for note in notes:
        stem = Path(note.rel_path).stem.lower()
        if note.slug.startswith(key + "-") or stem.startswith(key + "_") or stem == key:
            return note
    return None


def build_autolinker(notes: list, config):
    """Build a callable that auto-links bare tokens in a rendered-HTML string,
    skipping text inside existing <a>/<code> spans. None if no patterns."""
    if not config.autolink_patterns:
        return None
    combined = re.compile("|".join(f"(?:{p})" for p in config.autolink_patterns))
    _skip = re.compile(r"(<a\b[^>]*>.*?</a>|<code\b[^>]*>.*?</code>|<[^>]+>)", re.DOTALL)
    cache: dict = {}

    def _link(m: "re.Match[str]") -> str:
        token = m.group(0)
        key = token.lower()
        if key not in cache:
            target = autolink_target(token, notes)
            cache[key] = target.url_path if target else None
        url = cache[key]
        return f'<a href="{escape_attr(url)}">{token}</a>' if url else token

    def apply(html_str: str) -> str:
        return "".join(
            part if part[:1] == "<" else combined.sub(_link, part)
            for part in _skip.split(html_str)
        )

    return apply
