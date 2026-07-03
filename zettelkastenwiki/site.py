"""The publish orchestrator: home page, note pages, nav, search index,
sitemap, robots and optional .htaccess/OG images."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .catalog import (
    Note,
    escape_attr,
    load_catalog,
    markdown_excerpt,
    search_body_text,
    search_record,
)
from .config import SiteConfig, _run
from .jsonld import json_ld_for_note
from .markdown import markdown_to_html
from .shell import page_shell


def publish(config: SiteConfig, output_dir: "str | Path", render_og: "bool | None" = None) -> Path:
    """Build the whole site into ``output_dir`` (wiped first). Returns it."""
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    for subdir, source in config.static_assets.items():
        source = Path(source)
        if source.is_dir():
            shutil.copytree(
                source,
                output_path / subdir,
                ignore=shutil.ignore_patterns("README.md", ".gitkeep"),
            )

    notes = load_catalog(config)

    og_enabled = config.og_images if render_og is None else render_og
    if og_enabled:
        from .og import write_og_images

        write_og_images(output_path, notes, config)

    render_home(output_path, notes, config)
    for note in notes:
        render_note(output_path, note, notes, config)

    write_search_index(output_path, notes, config)
    write_sitemap(output_path, notes, config)
    write_robots(output_path, config)
    if config.emit_htaccess:
        write_htaccess(output_path, config)
    return output_path


# --- home page --------------------------------------------------------------


def render_article_cards(notes_list: list, config: SiteConfig) -> str:
    cards = "".join(
        f'<a class="article-card" href="{escape_attr(n.url_path)}">'
        f"{_run(config.hooks.card_visual, note=n, notes=None, config=config)}"
        f'<strong class="ac-title">{html.escape(n.title)}</strong>'
        f'<p class="ac-excerpt">{html.escape(n.seo_description)}</p>'
        f'<span class="ac-cta">{html.escape(config.strings.read_more)}</span>'
        f"</a>"
        for n in notes_list
    )
    return f'<div class="article-cards">{cards}</div>'


def _home_sections(notes: list, config: SiteConfig) -> str:
    sections = []
    for label, group_notes_list in group_notes(notes, config).items():
        style = "list"
        spec = config.group(group_notes_list[0].group) if group_notes_list else None
        if spec:
            style = spec.home_style
        if style == "hidden":
            continue
        sec_id = html.escape(label.lower().replace(" ", "-"))
        if style == "cards":
            sections.append(
                f'<section id="{sec_id}">'
                f"<h2>{html.escape(label)}</h2>"
                f"{render_article_cards(group_notes_list, config)}"
                f"</section>"
            )
        elif style == "accordion":
            # Native <details>: keyboard/screen-reader accessible, and the
            # excerpt stays in the DOM (crawlable) while collapsed.
            items = "\n".join(
                f'<details class="faq-item">'
                f"<summary>{html.escape(note.title)}</summary>"
                f'<div class="faq-answer"><p>{html.escape(markdown_excerpt(note.body, 220))}</p>'
                f'<p><a href="{note.url_path}">{html.escape(config.strings.details_label)}</a></p></div>'
                f"</details>"
                for note in group_notes_list
            )
            sections.append(f'<section id="{sec_id}"><h2>{html.escape(label)}</h2>{items}</section>')
        else:
            links = "\n".join(
                f'<li><a href="{note.url_path}">{html.escape(note.title)}</a></li>'
                for note in group_notes_list
            )
            sections.append(
                f'<section id="{sec_id}"><h2>{html.escape(label)}</h2><ul>{links}</ul></section>'
            )
    return "".join(sections)


def render_home(output_dir: Path, notes: list, config: SiteConfig) -> None:
    custom = None
    if config.hooks.home_body is not None:
        custom = config.hooks.home_body(notes=notes, config=config)
    body = custom if custom is not None else f"<h1>{html.escape(config.site_name)}</h1>\n" + _home_sections(
        notes, config
    )

    # When the home_extra_jsonld hook is present, its returned list is used
    # EXACTLY (order matters byte-for-byte for parity migrations); otherwise a
    # default WebSite+SearchAction block is emitted.
    main_jsonld = None
    if config.hooks.home_main_jsonld is not None:
        main_jsonld = config.hooks.home_main_jsonld(notes=notes, config=config)
    if config.hooks.home_extra_jsonld is not None:
        extra_jsonld = config.hooks.home_extra_jsonld(notes=notes, config=config) or []
    else:
        extra_jsonld = [
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": config.site_name,
                "url": f"{config.base_url}/",
                "inLanguage": config.language,
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": f"{config.base_url}/?q={{search_term_string}}",
                    },
                    "query-input": "required name=search_term_string",
                },
            }
        ]

    nav = None
    if config.hooks.nav_override is not None:
        nav = config.hooks.nav_override(note=None, notes=notes, config=config)
    if nav is None:
        nav = render_nav(notes, config)

    html_text = page_shell(
        config=config,
        title=config.home_title or config.site_name,
        description=config.home_description or f"{config.site_name} — {len(notes)} pages",
        canonical_url=f"{config.base_url}/",
        body=body,
        nav=nav,
        og_image=config.home_og_image or f"{config.base_url}/og/index.png",
        og_type="website",
        json_ld=main_jsonld
        or {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": config.site_name,
            "url": f"{config.base_url}/",
            "inLanguage": config.language,
        },
        extra_jsonld=extra_jsonld,
    )
    write_text(output_dir / "index.html", html_text)


# --- note pages -------------------------------------------------------------


def _ensure_single_h1(body: str, title: str) -> str:
    """Guarantee exactly one `<h1>` in rendered ``body``: inject one from the
    title when there is none, and demote any extras to `<h2>` (arbitrary
    repo docs often carry several top-level headings)."""
    import html as _html
    import re as _re

    positions = [m.start() for m in _re.finditer(r"<h1\b", body)]
    if not positions:
        return f"<h1>{_html.escape(title)}</h1>\n{body}"
    if len(positions) == 1:
        return body
    # Keep the first; demote the rest (and their closing tags) to <h2>.
    first_end = body.index("</h1>", positions[0]) + len("</h1>")
    head, tail = body[:first_end], body[first_end:]
    tail = tail.replace("<h1>", "<h2>").replace("<h1 ", "<h2 ").replace("</h1>", "</h2>")
    return head + tail


def render_note(output_dir: Path, note: Note, notes: list, config: SiteConfig) -> None:
    body = markdown_to_html(note.body, note, notes, config)
    # Defaults / memory layer (opt-in): guarantee exactly one <h1> per page.
    if config.enforce_single_h1:
        body = _ensure_single_h1(body, note.title)
    elif config.title_from_h1 and "<h1" not in body:
        import html as _html

        body = f"<h1>{_html.escape(note.title)}</h1>\n{body}"
    if config.hooks.note_body_filter is not None:
        body = config.hooks.note_body_filter(body=body, note=note, notes=notes, config=config)
    extras = _run(config.hooks.note_extras, note=note, notes=notes, config=config)
    cta_html = render_cta(note, config)
    related_html = render_related(note, notes, config)

    nav = None
    if config.hooks.nav_override is not None:
        nav = config.hooks.nav_override(note=note, notes=notes, config=config)
    if nav is None:
        spec = config.group(note.group)
        nav = (
            _standalone_nav(note, notes, config)
            if spec and spec.standalone_nav
            else render_nav(notes, config)
        )

    html_text = page_shell(
        config=config,
        title=note.seo_title,
        description=note.seo_description,
        canonical_url=note.canonical_url,
        body=f"{body}{extras}{cta_html}{related_html}",
        nav=nav,
        note=note,
        og_image=note.og_image,
        json_ld=json_ld_for_note(note, config),
        last_updated=str(note.frontmatter.get("last_updated", "")),
    )
    write_text(output_dir / note.group / note.slug / "index.html", html_text)


def _standalone_nav(note: Note, notes: list, config: SiteConfig) -> str:
    """Minimal own-group nav (the lead-gen pattern): this group's pages + home."""
    siblings = [n for n in notes if n.group == note.group]
    links = "\n".join(
        f'<li><a href="{n.url_path}">{html.escape(n.title)}</a></li>' for n in siblings
    )
    spec = config.group(note.group)
    label = spec.nav_label if spec and spec.nav_label else note.group
    return (
        f'<nav class="nav-group" aria-label="{escape_attr(label)}">'
        f"<h2>{html.escape(label)}</h2><ul>{links}"
        f'<li><a href="{config.base_path}/">{html.escape(config.site_name)} →</a></li>'
        f"</ul></nav>"
    )


def render_cta(note: Note, config: SiteConfig) -> str:
    if not note.cta_primary and not note.cta_secondary:
        return ""
    links = []
    if note.cta_primary:
        label, url = note.cta_primary
        links.append(f'<a href="{escape_attr(url)}">{html.escape(label)}</a>')
    if note.cta_secondary:
        label, url = note.cta_secondary
        links.append(f'<a class="secondary" href="{escape_attr(url)}">{html.escape(label)}</a>')
    return (
        f'\n<section class="cta">\n  <h2>{html.escape(config.strings.cta_heading)}</h2>\n  '
        + "\n  ".join(links)
        + "\n</section>\n"
    )


def render_related(note: Note, notes: list, config: SiteConfig) -> str:
    candidates = [
        item
        for item in notes
        if item.rel_path != note.rel_path
        and (item.section == note.section or (note.track and item.track == note.track))
    ][:6]
    if not candidates:
        return ""
    links = "\n".join(
        f'<li><a href="{item.url_path}">{html.escape(item.title)}</a></li>' for item in candidates
    )
    return (
        f'<section class="related"><h2>{html.escape(config.strings.related_heading)}</h2>'
        f"<ul>{links}</ul></section>"
    )


# --- nav --------------------------------------------------------------------


def group_notes(notes: list, config: SiteConfig) -> dict:
    """Group notes into ordered nav/home sections. Group order follows
    ``config.groups``; the per-note ``group_label`` hook can split one group
    into several labelled sections (the "Courses: {track}" pattern)."""
    buckets: dict[str, list] = {}
    for spec in config.groups:
        for note in notes:
            if note.group != spec.name:
                continue
            label = ""
            if config.hooks.group_label is not None:
                label = config.hooks.group_label(note=note, config=config) or ""
            label = label or spec.nav_label or spec.name
            buckets.setdefault(label, []).append(note)
    return {label: sorted(items, key=lambda n: n.title) for label, items in buckets.items() if items}


def render_nav(notes: list, config: SiteConfig) -> str:
    sections = []
    for label, group_notes_list in group_notes(notes, config).items():
        spec = config.group(group_notes_list[0].group)
        if spec and spec.standalone_nav:
            continue  # standalone groups don't appear in the main tree
        links = "\n".join(
            f'<li><a href="{note.url_path}">{html.escape(note.title)}</a></li>'
            for note in group_notes_list
        )
        sections.append(
            f'<nav class="nav-group" aria-label="{escape_attr(label)}">'
            f"<h2>{html.escape(label)}</h2><ul>{links}</ul></nav>"
        )
    top = _run(config.hooks.nav_top, note=None, notes=notes, config=config)
    return top + "\n".join(sections)


# --- machine outputs --------------------------------------------------------


def write_search_index(output_dir: Path, notes: list, config: "SiteConfig | None" = None) -> None:
    extra = config.extra_search_terms if config else None
    full_text = bool(config and config.full_text_search)
    body_chars = config.body_search_chars if config else 4000
    records = []
    for note in notes:
        if not note.indexable:
            continue
        record = search_record(note)
        if extra is not None:
            record["terms"] = record["terms"] + [t for t in extra(note) if t]
        if full_text:
            # Cleaned body text so a query matches content, not just titles —
            # the recall win for AI-memory sites. Preserves hyphens/slashes so
            # technical terms stay searchable.
            record["text"] = search_body_text(note.body, body_chars)
        records.append(record)
    # Minified: fetched by the client, not read by humans.
    write_text(
        output_dir / "search.json",
        json.dumps(records, ensure_ascii=False, separators=(",", ":")),
    )


def write_sitemap(output_dir: Path, notes: list, config: SiteConfig) -> None:
    urls = [f"{config.base_url}/"]
    urls.extend(note.canonical_url for note in notes if note.indexable)
    body = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in sorted(set(urls)))
    write_text(
        output_dir / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n',
    )


def write_robots(output_dir: Path, config: SiteConfig) -> None:
    write_text(
        output_dir / "robots.txt",
        f"User-agent: *\nAllow: {config.base_path}/\nSitemap: {config.base_url}/sitemap.xml\n",
    )


_HTACCESS = """\
# Static site. RewriteEngine Off keeps a CMS on the same host (e.g. WordPress)
# from intercepting these paths — they are served straight from disk.
RewriteEngine Off

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml \\
    application/javascript application/json application/xml \\
    image/svg+xml application/rss+xml
</IfModule>

<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/html "access plus 1 hour"
  ExpiresByType application/json "access plus 1 day"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
</IfModule>
"""


def write_htaccess(output_dir: Path, config: "SiteConfig | None" = None) -> None:
    content = config.htaccess_content if config and config.htaccess_content is not None else _HTACCESS
    write_text(output_dir / ".htaccess", content)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
