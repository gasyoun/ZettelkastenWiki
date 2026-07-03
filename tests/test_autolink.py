"""Bare-token auto-linking (e.g. H### → the handoff note it names)."""

from zettelkastenwiki import GroupSpec, SiteConfig, publish
from zettelkastenwiki.markdown import autolink_target
from zettelkastenwiki.catalog import load_catalog


def _repo(tmp_path):
    d = tmp_path / "handoffs"
    d.mkdir()
    (d / "H103_wave2_migration.md").write_text("# H103 — Wave 2\n\nthe migration.", encoding="utf-8")
    (d / "H108_pilots.md").write_text(
        "# H108 — pilots\n\nWave 2 was H103; also see [H103](H103_wave2_migration.md) "
        "and the code `H103` token in backticks.",
        encoding="utf-8",
    )
    return tmp_path


def _config(tmp_path, **kw):
    return SiteConfig(
        base_url="https://example.org",
        site_name="M",
        wiki_root=tmp_path,
        groups=(GroupSpec(name="handoffs", source_dir="handoffs"),),
        title_from_h1=True,
        **kw,
    )


def test_autolink_target_resolves_by_prefix(tmp_path):
    notes = load_catalog(_config(_repo(tmp_path)))
    t = autolink_target("H103", notes)
    assert t is not None and t.slug == "h103-wave2-migration"
    assert autolink_target("H999", notes) is None


def test_bare_token_linked_in_prose(tmp_path):
    cfg = _config(_repo(tmp_path), autolink_patterns=(r"\bH\d{3}\b",))
    out = publish(cfg, tmp_path / "site")
    page = (out / "handoffs" / "h108-pilots" / "index.html").read_text(encoding="utf-8")
    # The bare "H103" in "Wave 2 was H103;" becomes a link.
    assert '<a href="/handoffs/h103-wave2-migration/">H103</a>' in page


def test_autolink_skips_existing_links_and_code(tmp_path):
    cfg = _config(_repo(tmp_path), autolink_patterns=(r"\bH\d{3}\b",))
    out = publish(cfg, tmp_path / "site")
    page = (out / "handoffs" / "h108-pilots" / "index.html").read_text(encoding="utf-8")
    # No nested anchors, and the H103 inside <code> stays plain.
    assert "<a href=\"/handoffs/h103-wave2-migration/\"><a" not in page
    assert "<code>H103</code>" in page
    # The own-title "# H103 — Wave 2" self-link is fine to skip or keep; ensure
    # no malformed nesting anywhere.
    assert "</a></a>" not in page


def test_off_by_default(tmp_path):
    cfg = _config(_repo(tmp_path))  # no autolink_patterns
    out = publish(cfg, tmp_path / "site")
    page = (out / "handoffs" / "h108-pilots" / "index.html").read_text(encoding="utf-8")
    # "was H103;" stays plain text (only the explicit [H103](...) link exists).
    assert "was H103;" in page or "was H103 ;" in page


def test_autolink_feeds_backlinks(tmp_path):
    cfg = _config(_repo(tmp_path), autolink_patterns=(r"\bH\d{3}\b",), backlinks=True)
    out = publish(cfg, tmp_path / "site")
    h103 = (out / "handoffs" / "h103-wave2-migration" / "index.html").read_text(encoding="utf-8")
    # H108 references H103 (bare token + md link) → appears under Referenced by.
    assert 'class="backlinks"' in h103 and "/handoffs/h108-pilots/" in h103
