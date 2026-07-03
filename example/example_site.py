"""Example site configuration — the fixture CI builds and smokes.

Demonstrates: three groups with different home styles, a per-group language
(``de``) with a reciprocal hreflang pair, a custom string table, and the
data-driven quiz engine attached through the ``note_extras`` hook.

Build it:

    python example/build.py [output_dir]
"""

from __future__ import annotations

from pathlib import Path

from zettelkastenwiki import (
    GroupSpec,
    Hooks,
    QuizCTA,
    QuizOption,
    QuizQuestion,
    QuizResult,
    QuizSpec,
    SiteConfig,
    Strings,
    render_quiz,
)

WIKI_ROOT = Path(__file__).parent / "wiki"

DEMO_QUIZ = QuizSpec(
    quiz_id="setup",
    heading="Which setup fits you?",
    lead="Two questions — get a starting point.",
    mode="router",
    questions=(
        QuizQuestion(
            key="content",
            prompt="What are you publishing?",
            options=(
                QuizOption(label="A personal note garden", value="garden"),
                QuizOption(label="A product FAQ / support wiki", value="faq"),
                QuizOption(label="Docs for a code project", result="docs"),
            ),
        ),
        QuizQuestion(
            key="size",
            prompt="How many notes?",
            options=(
                QuizOption(label="A handful", value="garden"),
                QuizOption(label="Dozens to hundreds", value="faq"),
            ),
        ),
    ),
    results={
        "garden": QuizResult(
            title="Start with one group",
            why="A single 'notes' group and default settings cover a personal garden.",
            ctas=(QuizCTA(label="Getting started", url="/guides/getting-started/"),),
        ),
        "faq": QuizResult(
            title="Use an accordion FAQ group",
            why="Give support answers their own group with home_style='accordion'.",
            ctas=(
                QuizCTA(label="Getting started", url="/guides/getting-started/"),
                QuizCTA(label="Note format", url="/guides/writing-notes/", secondary=True),
            ),
        ),
        "docs": QuizResult(
            title="Docs-per-repo works too",
            why="Point wiki_root at your repo's docs/ and publish to GitHub Pages.",
            ctas=(QuizCTA(label="Getting started", url="/guides/getting-started/"),),
        ),
    },
)


def _note_extras(*, note, notes, config, **_):
    if note.slug == "quiz-demo":
        return render_quiz(DEMO_QUIZ, config)
    return ""


def _home_body(*, notes, config, **_):
    from zettelkastenwiki.site import _home_sections

    return (
        '<div class="hero"><h1>ZettelkastenWiki example</h1>'
        "<p>A folder of Markdown notes, published as a knowledge site.</p>"
        '<div class="hero-actions">'
        '<a class="btn-primary" href="/guides/getting-started/">Get started →</a>'
        "</div></div>" + _home_sections(notes, config)
    )


CONFIG = SiteConfig(
    base_url="https://example.org",
    site_name="ZettelkastenWiki example",
    org_name="ZettelkastenWiki project",
    author="ZettelkastenWiki maintainers",
    language="en",
    wiki_root=WIKI_ROOT,
    groups=(
        GroupSpec(name="guides", nav_label="Guides", home_style="cards", jsonld_type="article"),
        GroupSpec(name="faq", nav_label="FAQ", home_style="accordion", jsonld_type="faq"),
        GroupSpec(name="de", nav_label="Deutsch", home_style="list", jsonld_type="article", lang="de"),
    ),
    strings=Strings(
        search_placeholder="Search the example…",
        quiz_progress="Question {n} of {total}",
    ),
    hooks=Hooks(note_extras=_note_extras, home_body=_home_body),
    default_cta_primary=("Read the guides", "/guides/getting-started/"),
)
