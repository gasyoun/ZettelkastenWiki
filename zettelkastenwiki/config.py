"""Site configuration: groups, i18n strings, render hooks.

Everything site-specific that the ORS-FAQ generator used to hardcode lives
here as data: the group taxonomy (``GroupSpec``), every UI literal
(``Strings``), and the extension points a theme plugs into (``Hooks``).
The core ships English defaults and zero brand strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse


@dataclass(frozen=True)
class GroupSpec:
    """One wiki subdirectory and how it renders.

    home_style: how the group's section on the home page renders —
        "cards" (article cards), "accordion" (<details> Q&A), "list"
        (plain link list) or "hidden" (not on the home page).
    jsonld_type: which schema.org node a note in this group gets —
        "article", "faq", "course" or "webpage".
    lang: per-group language override (e.g. an "en" group on a RU site).
        Empty string → the site language.
    standalone_nav: the group gets a minimal own nav instead of the full
        site tree (the ORS ``en`` lead-gen pattern).
    """

    name: str
    nav_label: str = ""
    home_style: str = "list"
    jsonld_type: str = "webpage"
    lang: str = ""
    standalone_nav: bool = False


@dataclass(frozen=True)
class Strings:
    """Every user-visible UI literal in the core. Defaults are English; a
    theme supplies its own table (RU lives in the ORS-FAQ theme, not here)."""

    search_placeholder: str = "Search…"
    search_aria: str = "Search this site"
    nav_toggle_aria: str = "Menu"
    shortcuts_aria: str = "Quick links"
    updated_label: str = "Updated"
    related_heading: str = "Related pages"
    cta_heading: str = "Next step"
    read_more: str = "Read more →"
    details_label: str = "More →"
    quiz_progress: str = "Question {n} of {total}"
    quiz_restart: str = "↺ Start over"
    quiz_result_intro: str = "Your result:"
    sitemap_label: str = "sitemap"


def _iso_date(date_str: str) -> str:
    return date_str


@dataclass(frozen=True)
class Hooks:
    """Optional render extension points. Every hook returns an HTML string
    ("" to render nothing); ``None`` hooks are skipped.

    All hooks receive keyword arguments ``note`` (the current
    :class:`~zettelkastenwiki.catalog.Note`, or ``None`` on the home page),
    ``notes`` (the full catalog) and ``config`` (the :class:`SiteConfig`) —
    accept ``**kwargs`` for forward compatibility.
    """

    head_extra: Callable[..., str] | None = None
    body_top: Callable[..., str] | None = None
    body_bottom_js: Callable[..., str] | None = None
    #: Rendered between the note body and the CTA (quizzes, testimonials,
    #: "next course" blocks — the ORS plugins live behind this hook).
    note_extras: Callable[..., str] | None = None
    #: Full home-page body override (hero, trust bar, …). None → default
    #: sectioned home built from the group specs.
    home_body: Callable[..., str] | None = None
    home_extra_jsonld: Callable[..., list] | None = None
    #: Visual atop an article card (emoji icon, <img> plate…).
    card_visual: Callable[..., str] | None = None
    shortcuts: Callable[..., str] | None = None
    #: → (label, url) for the fixed mobile CTA bar, or None for no bar.
    mobile_cta: Callable[..., "tuple[str, str] | None"] | None = None
    #: Pinned link(s) above the nav tree (the "🚀 start here" pattern).
    nav_top: Callable[..., str] | None = None
    #: Dynamic nav/section label per note (e.g. "Courses: {track}");
    #: falls back to the group's static nav_label.
    group_label: Callable[..., str] | None = None
    css_extra: Callable[..., str] | None = None


def _run(hook: Callable[..., str] | None, **kwargs) -> str:
    """Run an optional hook, tolerating ones that ignore extra kwargs."""
    if hook is None:
        return ""
    return hook(**kwargs) or ""


@dataclass
class SiteConfig:
    """Everything the generator needs to know about one site."""

    base_url: str
    site_name: str
    wiki_root: Path | str
    groups: tuple[GroupSpec, ...]
    language: str = "en"
    org_name: str = ""
    org_url: str = ""
    author: str = ""
    org_same_as: tuple[str, ...] = ()
    strings: Strings = field(default_factory=Strings)
    hooks: Hooks = field(default_factory=Hooks)
    #: rel_path → slug (pin URLs independent of filenames).
    slug_overrides: dict = field(default_factory=dict)
    #: char → ascii replacement table used by slugify (e.g. Cyrillic translit).
    transliteration: dict = field(default_factory=dict)
    #: Appended to a note title when frontmatter has no seo_title.
    seo_title_suffix: str = ""
    default_cta_primary: "tuple[str, str] | None" = None
    default_cta_secondary: "tuple[str, str] | None" = None
    #: ISO "YYYY-MM-DD" → display string (a RU theme supplies its own).
    format_date: Callable[[str], str] = _iso_date
    #: output subdir name → source directory, copied verbatim into the build.
    static_assets: dict = field(default_factory=dict)
    #: Emit an .htaccess disabling rewrites (WordPress-subfolder hosting).
    emit_htaccess: bool = False
    #: Render OG card PNGs (requires the [og] extra / Pillow).
    og_images: bool = False
    footer_extra_html: str = ""

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.wiki_root = Path(self.wiki_root)

    @property
    def base_path(self) -> str:
        return urlparse(self.base_url).path.rstrip("/")

    def group(self, name: str) -> GroupSpec | None:
        for spec in self.groups:
            if spec.name == name:
                return spec
        return None
