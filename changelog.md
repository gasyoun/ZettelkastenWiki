# Changelog

## [0.1.0] — 2026-07-03

Initial extraction from the [ORS-FAQ](https://github.com/gasyoun/ORS-FAQ)
generator (`publish.py` 3,074 lines + `wiki_catalog.py`), per
[H077](https://github.com/gasyoun/Uprava/blob/main/handoffs/H077_zettelkastenwiki_phase1_extraction.md).

- Core: configurable-groups catalog, Markdown + `[[wikilink]]` rendering,
  page shell with render hooks, nav, client-side search, sitemap, robots,
  JSON-LD (article/faq/course/webpage + breadcrumbs + WebSite/SearchAction),
  reciprocal hreflang, canonical URLs, optional `.htaccess`.
- i18n: `Strings` table (English defaults, zero brand literals in core),
  pluggable date formatter, per-group `lang`.
- Data-driven quiz engine (`QuizSpec`, router + scored modes) replacing the
  twelve hand-copied ORS quiz templates; restart handlers window-global.
- `zettelkastenwiki.testing` — reusable invariant harness (links resolve,
  unique descriptions ≤160, single `<h1>`, self-canonical, reciprocal
  hreflang, JSON-LD parses, sitemap coverage, search index, OG resolution).
- Optional `[og]` extra: branded 1200×630 OG card PNGs with a
  content-addressed render cache.
- Example site fixture (three home styles, hreflang pair, themed strings,
  hooked quiz) built and smoked in CI; 23-test suite.
- Release workflow via PyPI Trusted Publishing (first publish gates on the
  owner's PyPI publisher setup).
