"""Markdown rendering and wikilink resolution."""

from zettelkastenwiki import load_catalog, markdown_to_html, resolve_wiki_link


def _note(notes, slug):
    return next(n for n in notes if n.slug == slug)


def test_wikilinks_resolve_same_group_and_cross_group(config):
    notes = load_catalog(config)
    start = _note(notes, "getting-started")
    url, resolved = resolve_wiki_link("writing-notes", start, notes, config)
    assert url == "/guides/writing-notes/"
    assert resolved is not None and resolved.slug == "writing-notes"
    url, resolved = resolve_wiki_link("../faq/what-is-this", start, notes, config)
    assert url == "/faq/what-is-this/"
    assert resolved is not None


def test_unresolved_wikilink_points_home(config):
    notes = load_catalog(config)
    start = _note(notes, "getting-started")
    url, resolved = resolve_wiki_link("no-such-note", start, notes, config)
    assert url == "/"
    assert resolved is None


def test_markdown_blocks_render(config):
    notes = load_catalog(config)
    start = _note(notes, "getting-started")
    html_text = markdown_to_html(start.body, start, notes, config)
    assert "<h1>" in html_text
    assert "<pre><code>" in html_text
    assert "<ul>" in html_text
    assert '<a href="/guides/writing-notes/">' in html_text


def test_inline_markup(config):
    notes = load_catalog(config)
    note = _note(notes, "writing-notes")
    html_text = markdown_to_html(note.body, note, notes, config)
    assert "<blockquote>" in html_text
    assert "<code>" in html_text
    assert "<strong>group</strong>" in html_text
