# CLAUDE.md

Guidance for Claude Code sessions in this repository.

## What this is

`zettelkastenwiki` — a PyPI package (dist name `zettelkastenwiki`) housing the
static knowledge-site generator extracted from
[ORS-FAQ](https://github.com/gasyoun/ORS-FAQ) (`ors_faq/publish.py` +
`wiki_catalog.py`). ORS-FAQ is consumer #1 and migrates onto this package in
Wave 2 behind a **golden-diff parity gate** — so treat rendering behavior and
CSS class names as a compatibility surface, not an implementation detail.

Plan of record:
[ROADMAP_ZETTELKASTENWIKI_2026.md](https://github.com/gasyoun/ORS-FAQ/blob/main/docs/ROADMAP_ZETTELKASTENWIKI_2026.md)
(decisions D1–D7 are final — do not re-litigate packaging, scope, naming or
PyPI distribution).

## Layout

- `zettelkastenwiki/config.py` — `SiteConfig` / `GroupSpec` / `Strings` (i18n
  table) / `Hooks` (theme extension points). **No UI literal may live outside
  `Strings`; no brand string may live anywhere in the core.**
- `catalog.py` — `Note` + frontmatter parser + `load_catalog(config)`.
- `markdown.py` — the small Markdown dialect + wikilink resolution.
- `shell.py` — page shell + `BASE_CSS`. Class names are frozen for the
  ORS-FAQ parity gate; additive changes only.
- `site.py` — publish orchestrator, home/note/nav renderers, machine outputs.
- `quiz.py` — data-driven quiz engine (router/scored). Restart handlers must
  stay `window`-global (inline onclick can't see IIFE locals).
- `og.py` — optional Pillow extra.
- `testing.py` — the reusable invariant harness consumers import.
- `example/` — the fixture site CI builds; also the living documentation.

## Rules

- Core stays stdlib-only; anything needing a dependency is an extra.
- Every behavior change lands with a test; run `python -m pytest tests -q`.
- Release: bump `pyproject.toml` + `zettelkastenwiki/__init__.__version__`,
  update `changelog.md`, tag `vX.Y.Z` (annotated) — the release workflow
  publishes via PyPI Trusted Publishing.
- Windows sessions: UTF-8 discipline (`sys.stdout.reconfigure(encoding="utf-8")`
  in scripts, `encoding="utf-8"` on file I/O, no BOM).
