"""Catalog loading: groups, slugs, frontmatter, SEO fields."""

from zettelkastenwiki import load_catalog, slugify
from zettelkastenwiki.catalog import parse_frontmatter, split_cta, truncate_text


def test_catalog_loads_configured_groups(config):
    notes = load_catalog(config)
    groups = {n.group for n in notes}
    assert groups == {"guides", "faq", "de"}
    assert len(notes) == 5


def test_note_urls_derive_from_config(config):
    notes = load_catalog(config)
    start = next(n for n in notes if n.slug == "getting-started")
    assert start.url_path == "/guides/getting-started/"
    assert start.canonical_url == "https://example.org/guides/getting-started/"


def test_group_language_override(config):
    notes = load_catalog(config)
    de = next(n for n in notes if n.group == "de")
    en = next(n for n in notes if n.group == "guides")
    assert de.lang == "de"
    assert en.lang == "en"


def test_seo_fields_present_and_bounded(config):
    notes = load_catalog(config)
    descriptions = [n.seo_description for n in notes]
    assert all(descriptions)
    assert all(len(d) <= 160 for d in descriptions)
    assert len(set(descriptions)) == len(descriptions), "descriptions must be unique"


def test_slugify_with_transliteration():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("ещё", {"е": "e", "щ": "sch", "ё": "e"}) == "esche"
    assert slugify("!!!") == "page"


def test_parse_frontmatter_lists_and_nested_maps():
    data, body = parse_frontmatter(
        "---\ntitle: T\naliases:\n  - one\n  - two\ntestimonial:\n  author: A\n  text: Nice\n---\nBody"
    )
    assert data["title"] == "T"
    assert data["aliases"] == ["one", "two"]
    assert data["testimonial"] == {"author": "A", "text": "Nice"}
    assert body == "Body"


def test_split_cta_and_truncate():
    assert split_cta("Label|https://x.example/") == ("Label", "https://x.example/")
    assert split_cta("no pipe") is None
    assert truncate_text("short", 10) == "short"
    assert truncate_text("a long sentence that overflows", 15).endswith("…")


def test_parse_frontmatter_after_house_byline():
    """Org-wide byline passes prepend `_Created: …_` above the delimiter;
    frontmatter after such a short prologue still parses (16-09 regression)."""
    text = (
        "_Created: 03-07-2026 · Last updated: 05-09-2026_\n"
        "\n"
        "---\n"
        "title: T\n"
        "alt_de: /de/x/\n"
        "---\n"
        "Body"
    )
    data, body = parse_frontmatter(text)
    assert data["title"] == "T"
    assert data["alt_de"] == "/de/x/"
    assert body == "Body"


def test_prose_before_thematic_break_is_not_frontmatter():
    """Prose followed by a `---` thematic break must never become
    frontmatter — only the house-byline prologue is tolerated."""
    text = (
        "Some opening prose sentence.\n"
        "\n"
        "---\n"
        "not: frontmatter\n"
        "---\n"
        "Body\n"
    )
    data, body = parse_frontmatter(text)
    assert data == {}
    assert body.startswith("Some opening prose sentence.")
