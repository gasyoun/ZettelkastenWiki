# ZettelkastenWiki

_Created: 03-07-2026 · Last updated: 03-07-2026_

Static knowledge-site generator for Zettelkasten-style Markdown wikis:
resolving `[[wikilinks]]`, SEO meta, JSON-LD structured data, reciprocal
hreflang, client-side search, sitemap, a data-driven quiz engine, render
hooks for theming — and a **reusable invariant test harness** so every
consumer site gets link/SEO/hreflang/`<h1>` checks for free.

Extracted from the generator behind
[samskrtam.ru/faq](https://samskrtam.ru/faq/)
([ORS-FAQ](https://github.com/gasyoun/ORS-FAQ), ~170-test suite). Dependency-free
core (Python ≥ 3.10, stdlib only); OG card rendering is an optional extra.

```
pip install zettelkastenwiki        # core
pip install zettelkastenwiki[og]    # + Pillow for OpenGraph card PNGs
```

*(PyPI availability verified 03-07-2026: `zettelkastenwiki` was free — the
fallbacks `zettelkasten-wiki` and `zkwiki` were also free and are not used.
First publish gates on the owner's PyPI Trusted-Publisher setup; see
[release.yml](https://github.com/gasyoun/ZettelkastenWiki/blob/main/.github/workflows/release.yml).)*

## Quick start

```python
from pathlib import Path
from zettelkastenwiki import GroupSpec, SiteConfig, publish

config = SiteConfig(
    base_url="https://example.org/kb",
    site_name="My knowledge base",
    wiki_root=Path("wiki"),
    groups=(
        GroupSpec(name="guides", nav_label="Guides", home_style="cards", jsonld_type="article"),
        GroupSpec(name="faq", nav_label="FAQ", home_style="accordion", jsonld_type="faq"),
    ),
)
publish(config, "out/")
```

Notes are Markdown files with YAML frontmatter in group subdirectories
(`wiki/guides/*.md`, `wiki/faq/*.md`). See
[example/](https://github.com/gasyoun/ZettelkastenWiki/tree/main/example) for a
complete site the CI builds and smokes: three home styles, a per-group
language with a reciprocal hreflang pair, a themed string table and a quiz
attached through a hook.

## What the core gives you

| Concern | Mechanism |
|---|---|
| URLs | folder URLs per note (`/group/slug/`), slug overrides, transliteration table |
| Wikilinks | `[[note]]`, `[[note\|label]]`, `[[../group/note]]` — every link resolves or points home |
| SEO | canonical, meta description, OG/Twitter cards, `seo_title`/`seo_description` frontmatter |
| Structured data | per-group JSON-LD (`article` / `faq` / `course` / `webpage`), breadcrumbs, WebSite+SearchAction |
| i18n | zero hardcoded UI literals — a `Strings` table + pluggable date formatter; per-group `lang` |
| hreflang | reciprocal pairs from `alt_<lang>` frontmatter, x-default on the primary language |
| Search | lazy-loaded client-side index (`search.json`) over titles/aliases/terms |
| Quizzes | one data-driven engine (`QuizSpec`: router or scored mode) instead of copy-pasted script blocks |
| Theming | `Hooks`: head extras, body top/bottom, per-note extras, home body, card visuals, shortcuts, mobile CTA, nav, extra CSS |
| Testing | `zettelkastenwiki.testing.run_all(out, config)` — links resolve, unique descriptions ≤160, single `<h1>`, self-canonical, reciprocal hreflang, JSON-LD parses, sitemap coverage, search index |
| OG cards | optional `[og]` extra — branded 1200×630 PNGs with a content-addressed render cache |

## Design decisions (owner rulings D1–D7, 03-07-2026)

| # | Decision | Ruling |
|---|---|---|
| D1 | Packaging | Standalone package repo; [ORS-FAQ](https://github.com/gasyoun/ORS-FAQ) = consumer #1 (no template copies) |
| D2 | Scope | Core + plugin hooks; quizzes-content/CTA/ladder/trust-bar stay consumer plugins; core is language-neutral |
| D3 | Positioning | Knowledge-site lane; csl-guides stays Docusaurus for structured docs |
| D4 | Pilots | kosha, SanskritLexicography article site, SamudraManthanam, MWS |
| D5 | Repo home & name | `gasyoun/ZettelkastenWiki` |
| D6 | Sequencing | Extraction ran as the top agent track, parallel to other work |
| D7 | Distribution | PyPI from day one (Trusted Publishing, no token secrets) |

Full roadmap:
[ROADMAP_ZETTELKASTENWIKI_2026.md](https://github.com/gasyoun/ORS-FAQ/blob/main/docs/ROADMAP_ZETTELKASTENWIKI_2026.md).

## Consumers

| Site | Angle | Status |
|---|---|---|
| [ORS-FAQ](https://github.com/gasyoun/ORS-FAQ) → [samskrtam.ru/faq](https://samskrtam.ru/faq/) | source of the extraction | ✅ **live** — migrated behind a golden-diff byte-parity gate (`publish.py` 3,074→1,812 lines); 168-test suite green |
| [kosha](https://github.com/gasyoun/kosha) → [gasyoun.github.io/kosha/docs-site](https://gasyoun.github.io/kosha/docs-site/) | greenfield | ✅ **live** — 5 notes + ~50-line config on the existing legacy Pages |
| SamudraManthanam → [samskrtam.ru/corpus-faq](https://samskrtam.ru/corpus-faq/) | same hosting | ✅ **live** — 6 RU notes; second FTP site on the shared deploy path |
| [SanskritLexicography](https://github.com/gasyoun/SanskritLexicography) research site | consolidation | ✅ **merged** ([PR #107](https://github.com/gasyoun/SanskritLexicography/pull/107)) — 10 scattered convention docs → one site, **zero per-file edits** (v0.2.0 defaults layer) |
| [MWS](https://github.com/sanskrit-lexicon/MWS) | docs-per-repo probe | ✅ **probed** → drove the v0.2.0 defaults layer; no upstream PR (org batched-PR cadence) |
| Uprava (private) | AI-memory site | ✅ **v0.3.0 pilot** — 124-note searchable memory (root docs + handoffs + archive) from the live repo via multi-root ingest, full-text body search, git recency, backlinks (107 pages), H### auto-linking (262 prose links) & a status-index home (Hub/In-work/Queued/Done/Archived); built locally, never published |

## Use cases

1. **Product FAQ / support site** — the origin case (ORS-FAQ): notes with
   CTAs, quizzes, testimonials, SEO/JSON-LD, hreflang for a lead-gen funnel.
   Live at [samskrtam.ru/faq](https://samskrtam.ru/faq/).
2. **Project docs / knowledge base** — a repo's own explainer site from a
   `wiki/` of Markdown (kosha, SamudraManthanam): nav + search + sitemap +
   JSON-LD for free from ~50 lines of `SiteConfig`.
3. **Docs-per-repo consolidation** — publish frontmatter-less Markdown already
   sitting in a repo (`docs/`, `research/`, conventions) with **zero editing**
   via the defaults layer (`title_from_h1`, `source_filter`, `<h1>` injection,
   v0.2.0) — proven on SanskritLexicography's scattered convention docs.
4. **AI / agent memory browser** — turn a commit-heavy repo's accumulated
   Markdown memory (handoffs, `.ai_state.md`, `FINDINGS.md`, `ROADMAP*.md`,
   decision logs) into a **searchable, cross-linked, status-ranked site** a
   fresh agent session navigates instead of grepping. Built out in v0.3.0–v0.6.0:
   - **multi-root in-place ingest** — one site from several repo dirs, no copying;
   - **full-text body search** — match content, not just titles (hyphen-safe);
   - **git recency** — last-commit date badge + newest-first ordering;
   - **backlinks** — per-note "Referenced by" from wikilinks, Markdown/URL
     `.md` links, and auto-linked tokens;
   - **`H###` auto-linking** — bare handoff/issue tokens in prose become links;
   - **status-index home** — a GTD-style bucketed landing (in-work / done /
     archived) with counts.

   Proven on a **private 126-note [Uprava](https://github.com/gasyoun/Uprava)
   memory site** (built locally, never published): full-text search over every
   body, 107 pages of backlinks, 262 auto-linked `H###` references.

## Roadmap

Waves 1–3 (extract → migrate ORS-FAQ → pilot four consumers) are done; the
defaults layer (v0.2.0) proved arbitrary docs-per-repo publishing with zero
edits. **Wave 5 shipped (v0.3.0):** multi-root in-place ingest, full-text body
search, single-`<h1>` enforcement, git recency, backlinks, `H###`
auto-linking and a status-grouped index home — all proven on a private
126-note Uprava memory site. **AI-memory building blocks (v0.3.0–v0.6.0):**

- ✅ **Multi-root ingest** (v0.3.0) — one site from *several* source dirs
  (`handoffs/`, `docs/`, root `*.md`) with no copying, via
  `GroupSpec.source_dir`/`recursive`/`pattern`/`exclude`.
- ✅ **Recency & provenance** (v0.4.0) — `git_recency` fills each note's
  last-commit date/author; `GroupSpec.sort="recency"` orders newest-first and
  the date becomes the page badge.
- ✅ **Auto-linking** (v0.5.0) — `autolink_patterns` turns bare tokens like
  `H103` in prose into links to the note they name (tag-aware, feeds the
  backlink graph); resolves relative/URL `.md` links too.
- ✅ **Backlinks** (v0.4.0) — `backlinks` renders a per-note "Referenced by"
  from the reverse link graph (wikilinks + Markdown/URL `.md` links).
- ✅ **Status-grouped memory index home** (v0.6.0) — `status_home` +
  `status_of` + `status_buckets` render the home as a GTD-style bucketed
  index (counts summary + per-status sections, newest-first).
- ✅ **Full-text body search** (v0.3.0) — `full_text_search` indexes cleaned
  bodies (hyphen/slash-preserving) so "have we hit this before?" matches content.
- **CI freshness gate** — a reusable action that rebuilds the memory site on
  every push so it never drifts from the repo (the staleness-guard pattern the
  pilots already use, packaged).

Open questions steering this are in the roadmap doc:
[ROADMAP_ZETTELKASTENWIKI_2026.md](https://github.com/gasyoun/ORS-FAQ/blob/main/docs/ROADMAP_ZETTELKASTENWIKI_2026.md).

## Development

```
pip install -e .[dev]
python -m pytest tests -q
python example/build.py /tmp/example-site
```

MIT. Provenance: extracted 03-07-2026 by Fable 5 (`claude-fable-5`) per
[H077](https://github.com/gasyoun/Uprava/blob/main/handoffs/H077_zettelkastenwiki_phase1_extraction.md).

_Dr. Mārcis Gasūns_
