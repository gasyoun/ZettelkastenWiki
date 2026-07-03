---
title: Getting started
slug: getting-started
section: basics
seo_title: Getting started with ZettelkastenWiki
seo_description: Install the package, point it at a folder of Markdown notes, and publish a static knowledge site with search, sitemap and SEO built in.
aliases:
  - quickstart
  - install
last_updated: 2026-07-03
alt_de: /de/erste-schritte/
---

# Getting started

Install the package and point it at a wiki directory:

```
pip install zettelkastenwiki
```

Notes are plain Markdown with YAML frontmatter, organised in **group**
subdirectories. Cross-link them with wikilinks: see [[writing-notes]] for the
syntax, or the [[../faq/what-is-this]] answer for the elevator pitch.

## What you get

- Clean folder URLs per note
- Client-side search over titles and aliases
- A sitemap, robots.txt and JSON-LD out of the box
