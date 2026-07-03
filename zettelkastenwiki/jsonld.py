"""Structured data (JSON-LD) and hreflang emission."""

from __future__ import annotations

import json

from .catalog import Note, escape_attr, markdown_excerpt
from .config import SiteConfig


def json_ld_dumps(data: dict) -> str:
    """Serialize JSON-LD for an inline <script>. json.dumps leaves '<'/'>'
    intact, so a value containing '</script>' would terminate the element
    early — escape them to their \\u-form (valid JSON, parsed identically)."""
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def breadcrumb_jsonld(note: Note, config: SiteConfig) -> dict:
    """Two-level BreadcrumbList: site name › note title. Kept to 2 levels —
    without per-group landing pages a group level would just repeat the home
    URL (a duplicate-node trail crawlers may discard)."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": config.site_name, "item": f"{config.base_url}/"},
            {"@type": "ListItem", "position": 2, "name": note.title, "item": note.canonical_url},
        ],
    }


def json_ld_for_note(note: Note, config: SiteConfig) -> dict:
    spec = config.group(note.group)
    kind = spec.jsonld_type if spec else "webpage"
    common = {
        "@context": "https://schema.org",
        "name": note.title,
        "url": note.canonical_url,
        "description": note.seo_description,
        "image": note.og_image,
    }
    if kind == "course":
        course: dict = {
            **common,
            "@type": "Course",
            "inLanguage": note.lang,
            "provider": {
                "@type": "EducationalOrganization",
                "name": config.org_name or config.site_name,
                "url": config.org_url or f"{config.base_url}/",
                "sameAs": list(config.org_same_as),
            },
        }
        if note.testimonial:
            author, text = note.testimonial
            course["review"] = [
                {
                    "@type": "Review",
                    "reviewBody": text,
                    "author": {"@type": "Person", "name": author},
                    "itemReviewed": {"@type": "Course", "name": note.title},
                }
            ]
        return course
    if kind == "article":
        data = {
            **common,
            "@type": "Article",
            "headline": note.title,
            "inLanguage": note.lang,
            "mainEntityOfPage": note.canonical_url,
        }
        if config.author:
            data["author"] = {"@type": "Person", "name": config.author}
        if config.org_name:
            data["publisher"] = {
                "@type": "Organization",
                "name": config.org_name,
                "url": config.org_url or f"{config.base_url}/",
            }
        return data
    if kind == "faq":
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": note.title,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": markdown_excerpt(note.body, 500),
                    },
                }
            ],
        }
    return {**common, "@type": "WebPage"}


def hreflang_links(note: "Note | None", self_canonical: str, config: SiteConfig) -> str:
    """Bidirectional hreflang. Crawlers discard non-reciprocal clusters, so a
    translated note (``alt_<lang>`` frontmatter on BOTH sides) must point at
    its counterpart. x-default = the site's primary-language side."""
    if not note:
        return ""

    def _full(path: str) -> str:
        return path if path.startswith("http") else f"{config.base_url}{path}"

    primary = config.language
    if note.lang != primary:
        alt = str(note.frontmatter.get(f"alt_{primary}", "")).strip()
        if not alt:
            return ""
        primary_url = escape_attr(_full(alt))
        links = [
            f'<link rel="alternate" hreflang="{note.lang}" href="{self_canonical}">',
            f'<link rel="alternate" hreflang="{primary}" href="{primary_url}">',
            f'<link rel="alternate" hreflang="x-default" href="{primary_url}">',
        ]
        return "\n  ".join(links)

    for spec in config.groups:
        other = spec.lang
        if not other or other == primary:
            continue
        alt = str(note.frontmatter.get(f"alt_{other}", "")).strip()
        if not alt:
            continue
        other_url = escape_attr(_full(alt))
        links = [
            f'<link rel="alternate" hreflang="{primary}" href="{self_canonical}">',
            f'<link rel="alternate" hreflang="{other}" href="{other_url}">',
            f'<link rel="alternate" hreflang="x-default" href="{self_canonical}">',
        ]
        return "\n  ".join(links)
    return ""
