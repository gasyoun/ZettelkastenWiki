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

| Site | Status |
|---|---|
| [ORS-FAQ](https://github.com/gasyoun/ORS-FAQ) → [samskrtam.ru/faq](https://samskrtam.ru/faq/) | source of the extraction; migrates in Wave 2 behind a golden-diff parity gate |
| [kosha](https://github.com/gasyoun/kosha) | Wave-3 pilot (greenfield) |
| [SanskritLexicography](https://github.com/gasyoun/SanskritLexicography) article site | Wave-3 pilot (consolidation) |
| SamudraManthanam | Wave-3 pilot (same hosting) |
| [MWS](https://github.com/sanskrit-lexicon/MWS) | Wave-3 pilot (docs-per-repo probe) |

## Development

```
pip install -e .[dev]
python -m pytest tests -q
python example/build.py /tmp/example-site
```

MIT. Provenance: extracted 03-07-2026 by Fable 5 (`claude-fable-5`) per
[H077](https://github.com/gasyoun/Uprava/blob/main/handoffs/H077_zettelkastenwiki_phase1_extraction.md).

_Dr. Mārcis Gasūns_
