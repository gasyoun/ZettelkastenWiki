# Changelog

## [0.6.0] — 2026-07-03

**Status-grouped memory-index home** (Wave-5; opt-in, default off).

- **`SiteConfig.status_home`** — render the home as a memory index: a counts
  summary line + one section per status bucket, notes newest-first with
  date + group badges (mirrors the GTD / handoff-registry pattern).
- **`SiteConfig.status_of`** — a `note→bucket-key` classifier (accepts
  `(note)` or `(note, config)`); default reads frontmatter `status` (first
  word) else the note's group.
- **`SiteConfig.status_buckets`** — ordered `(key, label)` pairs for section
  order + display names; unlisted buckets append under their key.
- +4 tests (52 total).


## [0.5.0] — 2026-07-03

**Bare-token auto-linking** (Wave-5 memory increment; opt-in, default off).

- **`SiteConfig.autolink_patterns`** — regexes whose bare-token matches in
  prose become links to the note they name (e.g. `(r"\bH\d{3}\b",)` turns
  "H103" into a link to the `h103-…` handoff). A token resolves to a note
  whose slug equals it, starts with `token-`, or whose filename stem starts
  with `token_`; unresolved tokens stay plain. Tag-aware: never links inside
  existing `<a>`/`<code>`. Auto-linked references also feed the backlink
  graph. `markdown.autolink_target()` / `build_autolinker()` are public.
- +5 tests (48 total).


## [0.4.0] — 2026-07-03

**Git recency + backlinks** (Wave-5 memory increments; opt-in, default off).

- **`SiteConfig.git_recency`** — fills each note's `git_date` (YYYY-MM-DD) and
  `git_author` from `git log` at build time. The date becomes the page's
  "updated" badge when frontmatter has no `last_updated`.
- **`GroupSpec.sort="recency"`** — orders a group's nav/home newest-commit
  first (notes without a date sink to the bottom).
- **`SiteConfig.backlinks`** — a "Referenced by" section per note listing the
  notes that reference it (reverse link graph), newest-first. Resolves
  `[[wikilinks]]` AND Markdown-link targets ending in `<name>.md` (relative
  links and full repo/blob URLs alike), so it works on ordinary Markdown
  corpora, not just wikilink ones.
- `Strings.backlinks_heading`. +6 tests (42 total).


## [0.3.0] — 2026-07-03

**AI-memory sites for commit-heavy repos** (Wave 5). All opt-in, default off.

- **Multi-root in-place ingest** — `GroupSpec.source_dir` / `recursive` /
  `pattern` / `exclude`: a group loads `.md` from any dir of an existing repo
  (e.g. `handoffs/`, `.` for the root) instead of a copied `wiki/`, so the
  published memory tracks the repo as it grows. Slug collisions across roots
  are auto-suffixed.
- **Full-text body search** — `SiteConfig.full_text_search` (+ `body_search_chars`)
  indexes cleaned note bodies into `search.json`; the client search now matches
  body content, not just titles/aliases — the recall win for "have we hit this
  before?". A dedicated body cleaner preserves hyphens/slashes so technical
  terms (`golden-diff`, `bot-kb-sync`, `H103`) stay searchable.
- **`enforce_single_h1`** — guarantees exactly one `<h1>` per page (inject from
  title when none, demote extras to `<h2>`) so arbitrary repo docs stay valid.
- **`testing.run_all(out, config, seo=False)`** — skip the public-SEO checks
  (unique ≤160 descriptions) for internal memory sites; structural invariants
  still run. +6 tests (36 total).


## [0.2.0] — 2026-07-03

**Opt-in defaults layer for frontmatter-less Markdown** (Wave-3 pilot #4, MWS
docs-per-repo probe). All flags default off — no change for existing configs.

- `SiteConfig.title_from_h1` — derive a note's title from its first `# H1`
  when frontmatter has no `title:` (slug/description/aliases already degraded
  to filename / first-paragraph / empty without any flag).
- `SiteConfig.source_filter` — preprocess each body after frontmatter split,
  before title/excerpt derivation (e.g. strip Jekyll `{% raw %}` tags).
- `<h1>` injection: a frontmatter-less doc whose body has no heading gets one
  from its title, preserving the single-`<h1>` invariant.
- `catalog.first_h1()` helper. +7 tests (measured against real MWS reader
  docs: 3 frontmatter-less docs publish into a harness-passing site with
  **zero per-file edits**).


## [0.1.2] — 2026-07-03

Byte-parity refinements from the ORS-FAQ Wave-2 migration (H103):

- Shell whitespace matches the source generator (multi-line shortcuts bar and
  mobile-CTA block); search JS comments restored.
- `mobile_cta` hook output is now trusted verbatim (same contract as the
  shortcuts/nav hooks) — the theme owns escaping.

## [0.1.1] — 2026-07-03

Parity-migration extension points (needed by the ORS-FAQ Wave-2 golden-diff
migration; all additive, no behavior change for existing configs):

- `SiteConfig.css` — full stylesheet override; `strings_by_lang` — per-language
  string tables; lang-aware `format_date` (optional second arg);
  `home_title`/`home_description`/`home_og_image`; `htaccess_content`;
  `extra_search_terms`; `og_group_labels` + `og_options` (footer/home_label).
- New hooks: `note_body_filter`, `nav_override`, `footer_extra`,
  `home_main_jsonld`.

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
