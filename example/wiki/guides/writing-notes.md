---
title: Writing notes
slug: writing-notes
section: basics
seo_title: Writing notes — frontmatter and wikilinks
seo_description: The note format ZettelkastenWiki understands — YAML frontmatter fields, wikilink syntax, and how groups map to sections and URLs.
aliases:
  - frontmatter
  - wikilinks
last_updated: 2026-07-03
---

# Writing notes

Each note is one Markdown file with YAML frontmatter. The **group** comes from
the directory the note lives in; the **slug** comes from frontmatter, a
configured override, or a transliteration of the filename.

Link to a sibling with `[[getting-started]]`, or across groups with
`[[../faq/what-is-this]]`. A pipe sets the label: [[getting-started|the
quickstart]].

> Frontmatter drives the SEO layer: `seo_title`, `seo_description` (unique,
> ≤160 chars — the test harness enforces this), `aliases` for search recall.
