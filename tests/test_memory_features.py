"""Wave-5 features: multi-root in-place ingest, single-<h1> enforcement, and
full-text body search — the AI-memory-site building blocks."""

import json

import pytest

from zettelkastenwiki import GroupSpec, SiteConfig, load_catalog, publish
from zettelkastenwiki import testing


def _repo(tmp_path):
    """A tiny repo-shaped tree: root docs + a handoffs/ dir + an archive/."""
    (tmp_path / "GTD.md").write_text("# GTD dashboard\n\nWhat to do next.", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme\n\nSkip me.", encoding="utf-8")
    hd = tmp_path / "handoffs"
    hd.mkdir()
    (hd / "H001_thing.md").write_text("# H001 — first thing\n\nStart line here.", encoding="utf-8")
    (hd / "H002_other.md").write_text("intro prose, no heading\n\nmore text about widgets.", encoding="utf-8")
    arch = hd / "archive"
    arch.mkdir()
    (arch / "H000_old.md").write_text("# H000 — archived\n\nDone long ago.", encoding="utf-8")
    return tmp_path


def _config(root, **kw):
    return SiteConfig(
        base_url="https://example.org/mem",
        site_name="Memory",
        wiki_root=root,
        groups=(
            GroupSpec(name="hub", nav_label="Hub", source_dir=".", pattern="*.md",
                      exclude=("README.md",), home_style="list"),
            GroupSpec(name="handoffs", nav_label="Handoffs", source_dir="handoffs",
                      home_style="cards"),
            GroupSpec(name="archive", nav_label="Archive", source_dir="handoffs/archive"),
        ),
        title_from_h1=True,
        enforce_single_h1=True,
        full_text_search=True,
        **kw,
    )


def test_multi_root_ingest_loads_from_in_place_dirs(tmp_path):
    notes = load_catalog(_config(_repo(tmp_path)))
    by_group = {}
    for n in notes:
        by_group.setdefault(n.group, []).append(n.slug)
    assert "gtd" in by_group["hub"]
    assert "readme" not in by_group.get("hub", []), "exclude ignored"
    assert set(by_group["handoffs"]) == {"h001-thing", "h002-other"}
    assert by_group["archive"] == ["h000-old"]


def test_titles_and_single_h1(tmp_path):
    cfg = _config(_repo(tmp_path))
    out = publish(cfg, tmp_path / "site")
    # H001 has an H1 → real title; H002 has none → filename, injected <h1>.
    h1 = (out / "handoffs" / "h001-thing" / "index.html").read_text(encoding="utf-8")
    assert h1.count("<h1") == 1 and "H001 — first thing" in h1
    h2 = (out / "handoffs" / "h002-other" / "index.html").read_text(encoding="utf-8")
    assert h2.count("<h1") == 1  # injected
    testing.run_all(out, cfg, seo=False)


def test_full_text_search_indexes_body(tmp_path):
    out = publish(_config(_repo(tmp_path)), tmp_path / "site")
    records = json.loads((out / "search.json").read_text(encoding="utf-8"))
    h002 = next(r for r in records if r["url"].endswith("/h002-other/"))
    assert "widgets" in h002["text"], "body text not indexed"
    # And the client filter searches item.text (not just terms).
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "item.text" in home


def test_extra_h1_demoted(tmp_path):
    (tmp_path / "multi.md").write_text("# First\n\ntext\n\n# Second\n\nmore", encoding="utf-8")
    cfg = SiteConfig(
        base_url="https://example.org",
        site_name="M",
        wiki_root=tmp_path,
        groups=(GroupSpec(name="hub", source_dir=".", pattern="multi.md"),),
        enforce_single_h1=True,
    )
    out = publish(cfg, tmp_path / "site")
    page = (out / "hub" / "multi" / "index.html").read_text(encoding="utf-8")
    assert page.count("<h1>") == 1
    assert "<h2>Second</h2>" in page


def test_recursive_dedupes_slug_collisions(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "note.md").write_text("# One", encoding="utf-8")
    sub = tmp_path / "a" / "sub"
    sub.mkdir()
    (sub / "note.md").write_text("# Two", encoding="utf-8")
    cfg = SiteConfig(
        base_url="https://example.org",
        site_name="M",
        wiki_root=tmp_path,
        groups=(GroupSpec(name="a", source_dir="a", recursive=True),),
    )
    slugs = sorted(n.slug for n in load_catalog(cfg))
    assert slugs == ["note", "note-2"], slugs


def test_features_off_by_default():
    cfg = SiteConfig(base_url="https://x.org", site_name="X", wiki_root=".", groups=())
    assert cfg.enforce_single_h1 is False
    assert cfg.full_text_search is False
    assert GroupSpec(name="g").source_dir == ""
