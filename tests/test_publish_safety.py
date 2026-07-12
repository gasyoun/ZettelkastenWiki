"""Safety checks around output-directory wiping."""

import pytest

from zettelkastenwiki import GroupSpec, SiteConfig, publish


def _config(root):
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "a.md").write_text("# A", encoding="utf-8")
    return SiteConfig(
        base_url="https://example.org",
        site_name="Safe",
        wiki_root=root,
        groups=(GroupSpec(name="notes"),),
    )


def test_publish_refuses_to_wipe_wiki_root(tmp_path):
    wiki = tmp_path / "wiki"
    cfg = _config(wiki)
    with pytest.raises(ValueError, match="refuses to wipe the source tree"):
        publish(cfg, wiki)


def test_publish_refuses_to_wipe_parent_of_wiki_root(tmp_path):
    wiki = tmp_path / "wiki"
    cfg = _config(wiki)
    with pytest.raises(ValueError, match="refuses to wipe the source tree"):
        publish(cfg, tmp_path)


def test_publish_allows_sibling_and_child_build_dirs(tmp_path):
    wiki = tmp_path / "wiki"
    cfg = _config(wiki)
    sibling = publish(cfg, tmp_path / "site")
    child = publish(cfg, tmp_path / "build" / "site")
    assert (sibling / "index.html").exists()
    assert (child / "notes" / "a" / "index.html").exists()
