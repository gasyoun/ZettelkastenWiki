"""Wave-5 increment: git-recency ranking + backlinks."""

import subprocess

import pytest

from zettelkastenwiki import GroupSpec, SiteConfig, load_catalog, publish


def _git_repo(tmp_path):
    """A tiny real git repo with three notes committed on distinct dates."""
    def git(*args, **kw):
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, **kw)
    git("init", "-q")
    git("config", "user.email", "t@t.test")
    git("config", "user.name", "Tester")
    (tmp_path / "notes").mkdir()

    def commit(name, body, date):
        (tmp_path / "notes" / name).write_text(body, encoding="utf-8")
        git("add", ".")
        env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
               "GIT_AUTHOR_NAME": "Tester", "GIT_AUTHOR_EMAIL": "t@t.test",
               "GIT_COMMITTER_NAME": "Tester", "GIT_COMMITTER_EMAIL": "t@t.test",
               "PATH": __import__("os").environ["PATH"]}
        subprocess.run(["git", "commit", "-q", "-m", name], cwd=tmp_path,
                       check=True, capture_output=True, env=env)

    commit("old.md", "# Old\n\ntext", "2026-01-01T00:00:00")
    commit("mid.md", "# Mid\n\nsee [[old]] here.", "2026-03-01T00:00:00")
    commit("new.md", "# New\n\nlinks [[old]] too.", "2026-06-01T00:00:00")
    return tmp_path


def _config(root, **kw):
    return SiteConfig(
        base_url="https://example.org",
        site_name="Mem",
        wiki_root=root,
        groups=(GroupSpec(name="notes", source_dir="notes", home_style="cards",
                          sort=kw.pop("sort", "title")),),
        **kw,
    )


def test_git_recency_populates_dates(tmp_path):
    notes = load_catalog(_config(_git_repo(tmp_path), git_recency=True))
    dates = {n.slug: n.git_date for n in notes}
    assert dates == {"old": "2026-01-01", "mid": "2026-03-01", "new": "2026-06-01"}
    assert all(n.git_author == "Tester" for n in notes)


def test_recency_sort_newest_first(tmp_path):
    from zettelkastenwiki.site import group_notes

    cfg = _config(_git_repo(tmp_path), git_recency=True, sort="recency")
    grouped = group_notes(load_catalog(cfg), cfg)
    slugs = [n.slug for n in next(iter(grouped.values()))]
    assert slugs == ["new", "mid", "old"]


def test_git_recency_off_by_default(tmp_path):
    notes = load_catalog(_config(_git_repo(tmp_path)))
    assert all(n.git_date == "" for n in notes)


def test_backlinks_rendered(tmp_path):
    cfg = _config(_git_repo(tmp_path), git_recency=True, backlinks=True, sort="recency")
    out = publish(cfg, tmp_path / "site")
    old = (out / "notes" / "old" / "index.html").read_text(encoding="utf-8")
    # old is linked from mid and new → both appear under "Referenced by".
    assert 'class="backlinks"' in old
    assert "Referenced by" in old
    assert "/notes/mid/" in old and "/notes/new/" in old
    # newest-first ordering inside backlinks
    assert old.index("/notes/new/") < old.index("/notes/mid/")
    # a note nobody links to has no backlinks section
    new = (out / "notes" / "new" / "index.html").read_text(encoding="utf-8")
    assert 'class="backlinks"' not in new


def test_git_date_used_as_page_date_badge(tmp_path):
    cfg = _config(_git_repo(tmp_path), git_recency=True)
    out = publish(cfg, tmp_path / "site")
    page = (out / "notes" / "new" / "index.html").read_text(encoding="utf-8")
    assert "2026-06-01" in page  # git date surfaced as the updated badge
