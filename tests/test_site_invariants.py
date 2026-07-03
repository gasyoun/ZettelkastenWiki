"""Build the example site once and run the full reusable invariant harness —
the same checks any consumer gets from ``zettelkastenwiki.testing``."""

from zettelkastenwiki import testing


def test_all_invariants(site, config):
    testing.run_all(site, config)


def test_pages_and_outputs_exist(site):
    assert (site / "index.html").exists()
    assert (site / "guides" / "getting-started" / "index.html").exists()
    assert (site / "de" / "erste-schritte" / "index.html").exists()
    assert (site / "robots.txt").exists()


def test_quiz_attached_via_hook(site):
    page = (site / "faq" / "quiz-demo" / "index.html").read_text(encoding="utf-8")
    assert 'id="quiz-setup"' in page
    assert "window.zkqRestart_setup" in page
    other = (site / "faq" / "what-is-this" / "index.html").read_text(encoding="utf-8")
    assert '<section class="quiz-section"' not in other


def test_hreflang_pair_emitted(site):
    en = (site / "guides" / "getting-started" / "index.html").read_text(encoding="utf-8")
    de = (site / "de" / "erste-schritte" / "index.html").read_text(encoding="utf-8")
    assert 'hreflang="de" href="https://example.org/de/erste-schritte/"' in en
    assert 'hreflang="en" href="https://example.org/guides/getting-started/"' in de
    assert 'hreflang="x-default" href="https://example.org/guides/getting-started/"' in de


def test_home_styles_render(site):
    home = (site / "index.html").read_text(encoding="utf-8")
    assert 'class="article-card"' in home, "cards group"
    assert 'class="faq-item"' in home, "accordion group"
    assert 'class="hero"' in home, "home_body hook"


def test_no_language_leaks_in_core_chrome(site):
    """Core must not inject any non-configured UI literals (i18n guard)."""
    page = (site / "guides" / "writing-notes" / "index.html").read_text(encoding="utf-8")
    assert "Search the example…" in page  # configured string, not a hardcoded one
    assert 'lang="en"' in page
