"""Status-grouped memory-index home."""

import re

from zettelkastenwiki import GroupSpec, SiteConfig, publish


def _repo(tmp_path):
    d = tmp_path / "notes"
    d.mkdir()
    (d / "a.md").write_text("---\nstatus: in-work PR open\n---\n# Alpha\n\ntext", encoding="utf-8")
    (d / "b.md").write_text("---\nstatus: done\n---\n# Beta\n\ntext", encoding="utf-8")
    (d / "c.md").write_text("---\nstatus: done\n---\n# Gamma\n\ntext", encoding="utf-8")
    (d / "d.md").write_text("# Delta\n\nno status", encoding="utf-8")
    return tmp_path


def _config(tmp_path, **kw):
    return SiteConfig(
        base_url="https://example.org",
        site_name="Memory",
        wiki_root=tmp_path,
        groups=(GroupSpec(name="notes", source_dir="notes"),),
        title_from_h1=True,
        **kw,
    )


def test_default_status_home_from_frontmatter(tmp_path):
    cfg = _config(
        _repo(tmp_path),
        status_home=True,
        status_buckets=(("in-work", "In work"), ("done", "Done")),
    )
    out = publish(cfg, tmp_path / "site")
    home = (out / "index.html").read_text(encoding="utf-8")
    assert '<section class="mi-section" id="in-work">' in home
    assert "In work (1)" in home
    assert "Done (2)" in home
    # the frontmatter-less note falls back to its group ("notes")
    assert "Notes (1)" in home
    # summary line lists counts
    assert 'class="status-summary"' in home
    assert "In work: 1" in home and "Done: 2" in home


def test_bucket_order_follows_config(tmp_path):
    cfg = _config(
        _repo(tmp_path),
        status_home=True,
        status_buckets=(("done", "Done"), ("in-work", "In work")),
    )
    out = publish(cfg, tmp_path / "site")
    home = (out / "index.html").read_text(encoding="utf-8")
    assert home.index('id="done"') < home.index('id="in-work"')


def test_custom_status_of_classifier(tmp_path):
    def classify(note, config):
        return "recent" if "Alpha" in note.title else "other"

    cfg = _config(
        _repo(tmp_path),
        status_home=True,
        status_of=classify,
        status_buckets=(("recent", "Recent"),),
    )
    out = publish(cfg, tmp_path / "site")
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "Recent (1)" in home and "Other (3)" in home


def test_status_home_off_by_default(tmp_path):
    out = publish(_config(_repo(tmp_path)), tmp_path / "site")
    home = (out / "index.html").read_text(encoding="utf-8")
    assert '<section class="mi-section"' not in home
    assert 'class="status-summary"' not in home
