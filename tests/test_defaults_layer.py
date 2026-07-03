"""The opt-in defaults layer for frontmatter-less Markdown (docs-per-repo).

Measured against real MWS reader docs in Wave-3 pilot #4: title_from_h1 +
source_filter + <h1> injection publish frontmatter-less docs with zero
per-file edits and a passing invariant harness.
"""

import re

import pytest

from zettelkastenwiki import GroupSpec, SiteConfig, publish
from zettelkastenwiki import testing
from zettelkastenwiki.catalog import first_h1, load_catalog


def _write(root, group, name, text):
    d = root / group
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")


def _config(root, **kw):
    return SiteConfig(
        base_url="https://example.org",
        site_name="Docs",
        wiki_root=root,
        groups=(GroupSpec(name="docs", nav_label="Docs", jsonld_type="article"),),
        **kw,
    )


def test_first_h1_helper():
    assert first_h1("intro\n# The Title\nbody") == "The Title"
    assert first_h1("## sub only\ntext") == ""
    assert first_h1("no headings here") == ""


def test_bare_core_uses_filename_stem(tmp_path):
    _write(tmp_path, "docs", "DICT_PROFILE.md", "# Dictionary Profile — MWS\n\nA companion.")
    note = load_catalog(_config(tmp_path))[0]
    assert note.title == "DICT_PROFILE"  # bare core: filename stem


def test_title_from_h1_default(tmp_path):
    _write(tmp_path, "docs", "DICT_PROFILE.md", "# Dictionary Profile — MWS\n\nA companion.")
    note = load_catalog(_config(tmp_path, title_from_h1=True))[0]
    assert note.title == "Dictionary Profile — MWS"


def test_source_filter_strips_jekyll(tmp_path):
    _write(tmp_path, "docs", "d.md", "{% raw %}\n# Data Dictionary\n\nTag inventory.{% endraw %}")
    cfg = _config(
        tmp_path,
        title_from_h1=True,
        source_filter=lambda b: re.sub(r"\{%-?\s*(end)?raw\s*-?%\}", "", b),
    )
    note = load_catalog(cfg)[0]
    assert note.title == "Data Dictionary"
    assert "{%" not in note.seo_description


def test_h1_injected_when_body_has_none(tmp_path):
    # A doc that opens mid-prose (no heading) — the page must still get one <h1>.
    _write(tmp_path, "docs", "DOCS_ISSUE.md", "@reviewer please look at the branch.\n\nMore text.")
    cfg = _config(tmp_path, title_from_h1=True)
    out = publish(cfg, tmp_path / "site")
    page = (out / "docs" / "docs-issue" / "index.html").read_text(encoding="utf-8")
    assert page.count("<h1") == 1
    assert "<h1>DOCS_ISSUE</h1>" in page


def test_frontmatterless_docs_publish_with_zero_edits(tmp_path):
    # The pilot-#4 result: a mixed set of real-shaped frontmatter-less docs
    # builds into a valid site (full harness) with no per-file frontmatter.
    _write(tmp_path, "docs", "DICT_PROFILE.md", "# Dictionary Profile — MWS\n\nA reading companion to MW.")
    _write(tmp_path, "docs", "ENTRY_GUIDE.md", "{% raw %}\n# Entry Reading Guide — MWS\n\nHow to read mw.txt.{% endraw %}")
    _write(tmp_path, "docs", "DOCS_ISSUE.md", "@funderburkjim please review the docs-pass branch.\n\nAll content written.")
    cfg = _config(
        tmp_path,
        title_from_h1=True,
        source_filter=lambda b: re.sub(r"\{%-?\s*(end)?raw\s*-?%\}", "", b),
    )
    out = publish(cfg, tmp_path / "site")
    testing.run_all(out, cfg)  # raises if any invariant fails
    titles = {n.slug: n.title for n in load_catalog(cfg)}
    assert titles["dict-profile"] == "Dictionary Profile — MWS"
    assert titles["entry-guide"] == "Entry Reading Guide — MWS"
    assert titles["docs-issue"] == "DOCS_ISSUE"  # no heading, no title → filename


def test_defaults_off_by_default(tmp_path):
    # Parity guard: the flags must not change behavior for existing configs.
    cfg = _config(tmp_path)
    assert cfg.title_from_h1 is False
    assert cfg.source_filter is None
