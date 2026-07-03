"""ZettelkastenWiki — static knowledge-site generator for Zettelkasten-style
Markdown wikis.

Extracted from the ORS-FAQ generator (samskrtam.ru/faq, ~170-test suite):
wikilink resolution, SEO/OG/JSON-LD, reciprocal hreflang, client-side search,
sitemap, a data-driven quiz engine, render hooks for theming, and a reusable
invariant test harness (:mod:`zettelkastenwiki.testing`).
"""

from .catalog import Note, load_catalog, markdown_excerpt, slugify
from .config import GroupSpec, Hooks, SiteConfig, Strings
from .markdown import markdown_to_html, resolve_wiki_link
from .quiz import QuizCTA, QuizOption, QuizQuestion, QuizResult, QuizSpec, render_quiz
from .site import publish

__version__ = "0.1.2"

__all__ = [
    "GroupSpec",
    "Hooks",
    "Note",
    "QuizCTA",
    "QuizOption",
    "QuizQuestion",
    "QuizResult",
    "QuizSpec",
    "SiteConfig",
    "Strings",
    "__version__",
    "load_catalog",
    "markdown_excerpt",
    "markdown_to_html",
    "publish",
    "render_quiz",
    "resolve_wiki_link",
    "slugify",
]
