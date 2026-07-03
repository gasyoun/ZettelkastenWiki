"""Reusable site-invariant checks — the ported crown jewel of the ORS-FAQ
test suite. Import these in any consumer's pytest and run them against a
built site:

    from zettelkastenwiki import publish
    from zettelkastenwiki.testing import run_all

    def test_site_invariants(tmp_path):
        out = publish(CONFIG, tmp_path / "site")
        run_all(out, CONFIG)

Each ``assert_*`` raises ``AssertionError`` with a list of offending pages;
``run_all`` runs every applicable invariant.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import SiteConfig

_LINK_RE = re.compile(r'href="([^"]+)"')
_OGIMG_RE = re.compile(r'<meta property="og:image" content="([^"]+)"')
_DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
_CANON_RE = re.compile(r'<link rel="canonical" href="([^"]+)"')
_H1_RE = re.compile(r"<h1\b")
_LDJSON_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
_HREFLANG_RE = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"')


def content_pages(output_dir: "Path | str") -> list:
    out = Path(output_dir)
    return [
        p
        for p in sorted(out.rglob("*.html"))
        if 'http-equiv="refresh"' not in p.read_text(encoding="utf-8")
    ]


def _page_url(output_dir: Path, page: Path, config: SiteConfig) -> str:
    rel = page.relative_to(output_dir).as_posix()
    if rel == "index.html":
        return f"{config.base_url}/"
    if rel.endswith("/index.html"):
        return f"{config.base_url}/{rel[: -len('index.html')]}"
    return f"{config.base_url}/{rel}"


def _normalize(url: str, config: SiteConfig) -> str:
    if url.startswith(config.base_url):
        return config.base_path + url[len(config.base_url):]
    return url


def _to_file(output_dir: Path, url: str, config: SiteConfig) -> Path:
    rel = _normalize(url, config)[len(config.base_path):].lstrip("/")
    rel = rel.split("#", 1)[0].split("?", 1)[0]
    if rel == "":
        return output_dir / "index.html"
    if rel.endswith("/"):
        return output_dir / rel / "index.html"
    return output_dir / rel


def assert_internal_links_resolve(output_dir: "Path | str", config: SiteConfig) -> None:
    """Every internal href/content URL on every page maps to an emitted file."""
    out = Path(output_dir)
    missing = []
    for page in content_pages(out):
        text = page.read_text(encoding="utf-8")
        for url in _LINK_RE.findall(text):
            norm = _normalize(url, config)
            if not (norm == f"{config.base_path}/" or norm.startswith(f"{config.base_path}/")):
                continue
            target = _to_file(out, url, config)
            if not target.exists():
                missing.append(f"{page.relative_to(out)} → {url}")
    assert not missing, f"internal links to missing files: {missing[:20]}"


def assert_og_images_resolve(output_dir: "Path | str", config: SiteConfig) -> None:
    """Every og:image URL maps to an emitted PNG (only meaningful when the
    site renders OG cards — ``config.og_images``)."""
    out = Path(output_dir)
    missing = []
    for page in content_pages(out):
        for url in _OGIMG_RE.findall(page.read_text(encoding="utf-8")):
            norm = _normalize(url, config)
            if not norm.startswith(f"{config.base_path}/"):
                continue  # external override
            if not _to_file(out, url, config).exists():
                missing.append(f"{page.relative_to(out)} → {url}")
    assert not missing, f"og:image URLs without files: {missing[:20]}"


def assert_unique_descriptions(output_dir: "Path | str", max_length: int = 160) -> None:
    """Every page has a non-empty, unique meta description ≤ ``max_length``."""
    seen: dict[str, str] = {}
    problems = []
    for page in content_pages(output_dir):
        text = page.read_text(encoding="utf-8")
        match = _DESC_RE.search(text)
        if not match or not match.group(1).strip():
            problems.append(f"{page}: missing description")
            continue
        desc = match.group(1)
        if len(desc) > max_length:
            problems.append(f"{page}: description over {max_length} chars ({len(desc)})")
        if desc in seen:
            problems.append(f"{page}: duplicate description (also on {seen[desc]})")
        else:
            seen[desc] = str(page)
    assert not problems, f"description problems: {problems[:20]}"


def assert_single_h1(output_dir: "Path | str") -> None:
    problems = []
    for page in content_pages(output_dir):
        count = len(_H1_RE.findall(page.read_text(encoding="utf-8")))
        if count != 1:
            problems.append(f"{page}: {count} <h1> elements")
    assert not problems, f"h1 problems: {problems[:20]}"


def assert_canonical_self(output_dir: "Path | str", config: SiteConfig) -> None:
    """Every page's canonical URL points at the page itself."""
    out = Path(output_dir)
    problems = []
    for page in content_pages(out):
        match = _CANON_RE.search(page.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{page.relative_to(out)}: no canonical")
            continue
        expected = _page_url(out, page, config)
        if match.group(1) != expected:
            problems.append(f"{page.relative_to(out)}: canonical {match.group(1)} != {expected}")
    assert not problems, f"canonical problems: {problems[:20]}"


def assert_reciprocal_hreflang(output_dir: "Path | str", config: SiteConfig) -> None:
    """Every page that declares an alternate points at a page that declares
    one back (crawlers discard non-reciprocal clusters)."""
    out = Path(output_dir)
    problems = []
    for page in content_pages(out):
        own_url = _page_url(out, page, config)
        for lang, href in _HREFLANG_RE.findall(page.read_text(encoding="utf-8")):
            if lang == "x-default" or href == own_url:
                continue
            target = _to_file(out, href, config)
            if not target.exists():
                problems.append(f"{page.relative_to(out)}: hreflang {lang} → missing {href}")
                continue
            back = _HREFLANG_RE.findall(target.read_text(encoding="utf-8"))
            if not any(back_href == own_url for _lang, back_href in back):
                problems.append(f"{page.relative_to(out)}: {href} does not point back")
    assert not problems, f"hreflang problems: {problems[:20]}"


def assert_jsonld_parses(output_dir: "Path | str") -> None:
    problems = []
    for page in content_pages(output_dir):
        for raw in _LDJSON_RE.findall(page.read_text(encoding="utf-8")):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                problems.append(f"{page}: invalid JSON-LD ({exc})")
                continue
            if "@context" not in data or "@type" not in data:
                problems.append(f"{page}: JSON-LD missing @context/@type")
    assert not problems, f"JSON-LD problems: {problems[:20]}"


def assert_sitemap_covers_pages(output_dir: "Path | str", config: SiteConfig) -> None:
    """Every sitemap URL resolves to a page, and the sitemap exists."""
    out = Path(output_dir)
    sitemap = out / "sitemap.xml"
    assert sitemap.exists(), "sitemap.xml missing"
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text(encoding="utf-8"))
    assert urls, "sitemap has no URLs"
    missing = [url for url in urls if not _to_file(out, url, config).exists()]
    assert not missing, f"sitemap URLs without pages: {missing[:20]}"


def assert_search_index(output_dir: "Path | str") -> None:
    index = Path(output_dir) / "search.json"
    assert index.exists(), "search.json missing"
    records = json.loads(index.read_text(encoding="utf-8"))
    assert isinstance(records, list)
    empty = [r.get("title", "?") for r in records if not r.get("terms")]
    assert not empty, f"search records without terms: {empty[:10]}"


def run_all(output_dir: "Path | str", config: SiteConfig) -> None:
    assert_internal_links_resolve(output_dir, config)
    if config.og_images:
        assert_og_images_resolve(output_dir, config)
    assert_unique_descriptions(output_dir)
    assert_single_h1(output_dir)
    assert_canonical_self(output_dir, config)
    assert_reciprocal_hreflang(output_dir, config)
    assert_jsonld_parses(output_dir)
    assert_sitemap_covers_pages(output_dir, config)
    assert_search_index(output_dir)
