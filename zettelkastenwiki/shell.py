"""The page shell: HTML head (SEO/OG/hreflang/JSON-LD), chrome (topbar,
search, nav, footer, mobile CTA) and the base stylesheet.

Ported from the ORS-FAQ ``page_shell`` with every literal routed through
:class:`~zettelkastenwiki.config.Strings` and every site-specific fragment
behind a :class:`~zettelkastenwiki.config.Hooks` extension point. CSS class
names are kept identical to the ORS-FAQ generator so consumers can migrate
behind a golden-diff parity gate.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone

from .catalog import Note, escape_attr
from .config import Hooks, SiteConfig, _run
from .jsonld import breadcrumb_jsonld, hreflang_links, json_ld_dumps

# Base stylesheet — layout, nav, search, cards, quiz, accordion, CTA. A plain
# (non-f) string so braces stay single; themes append via hooks.css_extra.
BASE_CSS = """
    :root {
      --ink: #1f2933;
      --muted: #5b6472;
      --line: #d8dee6;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent-2: #7c3aed;
      --warn: #a16207;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      line-height: 1.62;
      color: var(--ink);
      background: var(--bg);
    }
    .topbar {
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 16px 24px;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      max-width: 1240px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }
    .brand a { color: var(--ink); font-weight: 700; text-decoration: none; }
    .brand span { color: var(--muted); font-size: 0.95rem; }
    .nav-toggle {
      display: none;
      background: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 1.2rem;
      cursor: pointer;
      line-height: 1;
      color: var(--ink);
    }
    .mobile-cta { display: none; }
    .layout {
      max-width: 1240px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: calc(100vh - 70px);
    }
    aside {
      padding: 24px 20px;
      border-right: 1px solid var(--line);
      background: var(--panel);
    }
    main {
      padding: 32px min(5vw, 56px);
      background: var(--panel);
    }
    h1, h2, h3 { line-height: 1.25; }
    h1 { margin-top: 0; font-size: clamp(2rem, 4vw, 3rem); }
    h2 { margin-top: 2rem; border-bottom: 1px solid var(--line); padding-bottom: 0.35rem; }
    a { color: var(--accent); }
    .faq-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 0.5rem 0;
      background: #fff;
    }
    .faq-item summary {
      cursor: pointer;
      padding: 0.75rem 1rem;
      font-weight: 600;
      color: var(--ink);
      list-style-position: inside;
    }
    .faq-item[open] summary { border-bottom: 1px solid var(--line); }
    .faq-answer { padding: 0.25rem 1rem 0.75rem; color: var(--muted); }
    blockquote {
      border-left: 4px solid var(--accent);
      margin-left: 0;
      padding: 0.5rem 1rem;
      color: var(--muted);
      background: #eef7f5;
    }
    code {
      background: #eef1f5;
      padding: 0.12rem 0.25rem;
      border-radius: 4px;
    }
    .topbar-search {
      position: relative;
      flex: 1;
      max-width: 480px;
    }
    .topbar-search input {
      width: 100%;
      padding: 8px 14px;
      border: 1px solid var(--line);
      border-radius: 20px;
      font-size: 0.95rem;
      background: var(--bg);
      box-sizing: border-box;
    }
    .topbar-search input:focus {
      outline: none;
      border-color: var(--accent);
    }
    #search-results {
      position: absolute;
      top: calc(100% + 4px);
      left: 0;
      right: 0;
      z-index: 300;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      list-style: none;
      padding: 6px 0;
      margin: 0;
      font-size: 0.95rem;
      box-shadow: 0 4px 16px rgba(0,0,0,.10);
      max-height: 320px;
      overflow-y: auto;
    }
    #search-results:empty { display: none; }
    #search-results li { margin: 0; }
    #search-results li a {
      display: block;
      padding: 8px 14px;
      color: var(--ink);
      text-decoration: none;
    }
    #search-results li a:hover { background: #eef7f5; color: var(--accent); }
    .shortcuts-bar {
      max-width: 1240px;
      margin: 8px auto 0;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding: 0 24px;
    }
    .shortcut {
      font-size: 0.82rem;
      padding: 4px 13px;
      border-radius: 20px;
      background: #eef7f5;
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
      white-space: nowrap;
    }
    .shortcut:hover { background: var(--accent); color: #fff; }
    .nav-group { margin: 24px 0; }
    .nav-group h2 {
      margin: 0 0 8px;
      border: 0;
      font-size: 0.8rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .nav-group ul { list-style: none; margin: 0; padding: 0; }
    .nav-group li { margin: 6px 0; }
    .nav-group a { color: var(--ink); text-decoration: none; font-size: 0.95rem; }
    .nav-group a:hover { color: var(--accent); text-decoration: underline; }
    .cta {
      margin: 36px 0 20px;
      padding: 24px;
      border-radius: 10px;
      background: linear-gradient(135deg, #eef7f5 0%, #ede9fe 100%);
    }
    .cta h2 { margin: 0 0 14px; border: 0; font-size: 1.1rem; }
    .cta a {
      display: inline-block;
      margin: 8px 10px 0 0;
      padding: 10px 14px;
      border-radius: 6px;
      background: var(--accent);
      color: white;
      text-decoration: none;
      font-weight: 600;
    }
    .cta a.secondary { background: var(--accent-2); }
    .start-here {
      display: block;
      margin: 0 0 24px;
      padding: 16px 18px;
      border: 1px solid var(--accent);
      border-left: 5px solid var(--accent);
      border-radius: 8px;
      background: #eef7f5;
      text-decoration: none;
      color: var(--ink);
    }
    .start-here strong { display: block; color: var(--accent); font-size: 1.15rem; margin-bottom: 4px; }
    .start-here span { color: var(--muted); }
    .nav-start { margin: 0 0 16px; }
    .nav-start a {
      display: block;
      padding: 9px 12px;
      background: var(--accent);
      color: #fff;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 600;
    }
    .related { margin-top: 32px; color: var(--muted); }
    .page-meta {
      text-align: right;
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 12px;
    }
    footer {
      margin-top: 48px;
      padding-top: 24px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.9rem;
    }
    .hero {
      background: linear-gradient(135deg, #eef7f5 0%, #ede9fe 100%);
      padding: 48px 40px;
      border-radius: 12px;
      margin-bottom: 40px;
    }
    .hero h1 { margin-bottom: 14px; }
    .hero > p { font-size: 1.1rem; color: var(--muted); max-width: 640px; margin-bottom: 28px; }
    .hero-actions { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    .btn-primary {
      background: var(--accent);
      color: #fff;
      padding: 14px 28px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 700;
      font-size: 1.05rem;
      display: inline-block;
    }
    .btn-primary:hover { background: #0d6660; color: #fff; }
    .btn-secondary {
      color: var(--accent);
      padding: 12px 26px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      border: 2px solid var(--accent);
      font-size: 1.05rem;
      display: inline-block;
    }
    .btn-secondary:hover { background: #eef7f5; }
    .home-intro { color: var(--muted); font-size: 0.95rem; margin-bottom: 32px; }
    .article-cards {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin: 20px 0 32px;
    }
    .article-card {
      display: flex;
      flex-direction: column;
      padding: 20px 18px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel);
      text-decoration: none;
      color: var(--ink);
      transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
    }
    .article-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 4px 14px rgba(0,0,0,0.09);
      border-color: var(--accent);
    }
    .ac-icon { font-size: 1.7rem; margin-bottom: 8px; line-height: 1; }
    .ac-img { width: 100%; height: 120px; object-fit: cover; border-radius: 8px; margin-bottom: 10px; display: block; }
    .ac-title { font-size: 0.97rem; font-weight: 700; margin-bottom: 6px; display: block; }
    .ac-excerpt { font-size: 0.85rem; color: var(--muted); flex: 1; margin: 0 0 14px; line-height: 1.55; }
    .ac-cta { font-size: 0.83rem; color: var(--accent); font-weight: 600; margin-top: auto; }
    .quiz-section {
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 32px;
      margin-bottom: 40px;
    }
    .quiz-section h2 { margin-top: 0; border: none; padding: 0; }
    .quiz-lead { color: var(--muted); margin: -8px 0 20px; }
    .zkq-progress { color: var(--muted); font-size: 0.85rem; margin-bottom: 6px; }
    .zkq-question { margin: 0 0 16px; font-size: 1.15rem; }
    .zkq-options { display: flex; flex-direction: column; gap: 10px; }
    .quiz-opt {
      text-align: left;
      padding: 11px 16px;
      border: 1px solid var(--accent);
      border-radius: 8px;
      background: #fff;
      color: var(--accent);
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
    }
    .quiz-opt:hover { background: #eef7f5; }
    .quiz-opt:disabled { cursor: default; }
    .quiz-opt.correct { border-color: #1f7a68; background: #e7f5f1; color: #13533f; }
    .quiz-opt.wrong { border-color: #c0392b; background: #fdecea; color: #922; }
    .zkq-explain { margin: 0 0 14px; font-size: 0.92rem; line-height: 1.6; color: var(--ink); }
    .zkq-score { font-weight: 700; font-size: 1.05rem; margin: 0 0 14px; color: var(--accent); }
    .quiz-result-title { font-size: 1.15rem; font-weight: 700; margin: 0 0 6px; }
    .quiz-result-why { color: var(--muted); margin: 0 0 6px; }
    .quiz-result-ctas { margin: 14px 0 8px; display: flex; gap: 10px; flex-wrap: wrap; }
    @media (max-width: 860px) {
      .layout { display: block; }
      aside {
        display: none;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      aside.open { display: block; }
      main { padding: 24px 18px 88px; }
      .brand span { display: none; }
      .nav-toggle { display: block; }
      .mobile-cta {
        display: block;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--accent);
        text-align: center;
        padding: 16px;
        z-index: 200;
      }
      .mobile-cta a {
        color: #fff;
        text-decoration: none;
        font-weight: 700;
        font-size: 1.05rem;
      }
      .hero { padding: 28px 18px; border-radius: 8px; margin-bottom: 24px; }
      .hero-actions { flex-direction: column; }
      .btn-primary, .btn-secondary { text-align: center; width: 100%; box-sizing: border-box; }
      .quiz-section { padding: 20px 16px; }
      .quiz-result-ctas { flex-direction: column; }
      .brand { flex-wrap: wrap; }
      .topbar-search { flex: 1 1 100%; max-width: 100%; order: 3; margin-top: 8px; }
      .topbar-search input { border-radius: 8px; }
      .shortcuts-bar { flex-wrap: nowrap; overflow-x: auto; padding: 6px 16px 0; gap: 6px; }
      .article-cards { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    }
"""


def page_shell(
    *,
    config: SiteConfig,
    title: str,
    description: str,
    canonical_url: str,
    body: str,
    nav: str,
    json_ld: dict,
    og_image: str,
    note: Note | None = None,
    last_updated: str = "",
    og_type: str = "article",
    extra_jsonld: "list | None" = None,
) -> str:
    page_lang = note.lang if note else config.language
    strings = config.strings_for(page_lang)
    hooks: Hooks = config.hooks

    json_ld_text = json_ld_dumps(json_ld)
    breadcrumb_script = (
        f'\n  <script type="application/ld+json">{json_ld_dumps(breadcrumb_jsonld(note, config))}</script>'
        if note
        else ""
    )
    extra_scripts = "".join(
        f'\n  <script type="application/ld+json">{json_ld_dumps(block)}</script>'
        for block in (extra_jsonld or [])
    )
    page_class = f"page-{note.group}" if note else "page-home"
    safe_title = html.escape(title)
    safe_description = escape_attr(description)
    safe_canonical = escape_attr(canonical_url)
    safe_og_image = escape_attr(og_image)
    alt_links = hreflang_links(note, safe_canonical, config)

    date_html = ""
    if last_updated:
        date_str = html.escape(config.display_date(last_updated, page_lang))
        date_html = (
            f'<div class="page-meta"><time datetime="{html.escape(last_updated)}">'
            f"{strings.updated_label}: {date_str}</time></div>"
        )

    shortcuts_html = _run(hooks.shortcuts, note=note, notes=None, config=config)
    shortcuts_bar = (
        f'<nav class="shortcuts-bar" aria-label="{escape_attr(strings.shortcuts_aria)}">\n'
        f"      {shortcuts_html}\n"
        "    </nav>"
        if shortcuts_html
        else ""
    )
    head_extra = _run(hooks.head_extra, note=note, notes=None, config=config)
    body_top = _run(hooks.body_top, note=note, notes=None, config=config)
    body_bottom_js = _run(hooks.body_bottom_js, note=note, notes=None, config=config)
    css_extra = _run(hooks.css_extra, note=note, notes=None, config=config)

    mobile_cta_html = ""
    if hooks.mobile_cta is not None:
        pair = hooks.mobile_cta(note=note, config=config)
        if pair:
            # Hook-authored markup is trusted verbatim (same contract as the
            # shortcuts/nav hooks) — the theme escapes what needs escaping.
            cta_label, cta_url = pair
            mobile_cta_html = (
                '<div class="mobile-cta">\n'
                f'    <a href="{cta_url}">{cta_label}</a>\n'
                "  </div>"
            )

    author_meta = (
        f'\n  <meta name="author" content="{html.escape(config.author)}">' if config.author else ""
    )
    footer_bits = [
        f"© {datetime.now(timezone.utc).year} {html.escape(config.org_name or config.site_name)}",
        f'<a href="{config.base_path}/sitemap.xml">{html.escape(strings.sitemap_label)}</a>',
    ]
    if config.footer_extra_html:
        footer_bits.append(config.footer_extra_html)
    footer_dynamic = _run(hooks.footer_extra, note=note, notes=None, config=config)
    if footer_dynamic:
        footer_bits.append(footer_dynamic)
    footer_html = " · ".join(footer_bits)

    return f"""<!DOCTYPE html>
<html lang="{page_lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
  <meta name="description" content="{safe_description}">
  <link rel="canonical" href="{safe_canonical}">
  {alt_links}
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="{html.escape(config.site_name)}">
  <meta property="og:title" content="{escape_attr(title)}">
  <meta property="og:description" content="{safe_description}">
  <meta property="og:url" content="{safe_canonical}">
  <meta property="og:image" content="{safe_og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape_attr(title)}">
  <meta name="twitter:description" content="{safe_description}">
  <meta name="twitter:image" content="{safe_og_image}">{author_meta}
  <script type="application/ld+json">{json_ld_text}</script>{breadcrumb_script}{extra_scripts}{head_extra}
  <style>{config.css if config.css is not None else BASE_CSS}{css_extra}
  </style>
</head>
<body class="{page_class}">
  <header class="topbar">
    <div class="brand">
      <a href="{config.base_path}/">{html.escape(config.site_name)}</a>
      <div class="topbar-search">
        <input id="site-search" type="search" placeholder="{escape_attr(strings.search_placeholder)}" aria-label="{escape_attr(strings.search_aria)}" autocomplete="off">
        <ul id="search-results"></ul>
      </div>
      <button class="nav-toggle" id="nav-toggle" aria-label="{escape_attr(strings.nav_toggle_aria)}" aria-expanded="false">☰</button>
    </div>
    {shortcuts_bar}
  </header>
  <div class="layout">
    <aside id="site-aside">
      {nav}
    </aside>
    <main>
      {body_top}
      {date_html}
      {body}
      <footer>{footer_html}</footer>
    </main>
  </div>
  {mobile_cta_html}
  <script>
    const navToggle = document.getElementById('nav-toggle');
    const siteAside = document.getElementById('site-aside');
    if (navToggle && siteAside) {{
      navToggle.addEventListener('click', () => {{
        const isOpen = siteAside.classList.toggle('open');
        navToggle.setAttribute('aria-expanded', isOpen);
        navToggle.textContent = isOpen ? '✕' : '☰';
      }});
    }}
    const input = document.getElementById('site-search');
    const results = document.getElementById('search-results');
    if (input && results) {{
      // Lazy-load the index: most visitors never search, so keep its weight off
      // the critical path. Fetched once on first focus/keystroke (or immediately
      // for a /faq/?q=… deep link below). The promise is cached so it loads once.
      let indexPromise = null;
      const loadIndex = () => {{
        if (!indexPromise) {{
          indexPromise = fetch('{config.base_path}/search.json')
            .then(response => response.json())
            .catch(() => []);
        }}
        return indexPromise;
      }};
      const runSearch = () => {{
        const q = input.value.trim().toLowerCase();
        results.innerHTML = '';
        if (q.length < 2) return;
        loadIndex().then(index => {{
          if (input.value.trim().toLowerCase() !== q) return;  // stale result
          index
            .filter(item => ((item.terms || []).join(' ') + ' ' + (item.text || '')).toLowerCase().includes(q))
            .slice(0, 8)
            .forEach(item => {{
              const li = document.createElement('li');
              const a = document.createElement('a');
              a.href = item.url;
              a.textContent = item.title;
              li.appendChild(a);
              results.appendChild(li);
            }});
        }});
      }};
      input.addEventListener('input', runSearch);
      input.addEventListener('focus', loadIndex, {{ once: true }});  // warm cache
      // Deep-link support: /faq/?q=… pre-fills and runs the search on load.
      // This is the canonical SearchAction target in the home WebSite JSON-LD,
      // so engines can wire a sitelinks searchbox straight to it.
      const initialQuery = new URLSearchParams(window.location.search).get('q');
      if (initialQuery) {{
        input.value = initialQuery;
        runSearch();
        input.focus();
      }}
    }}
  </script>
  {body_bottom_js}
</body>
</html>
"""
