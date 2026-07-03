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
    #: Transform the rendered note body HTML (e.g. inject a badge after <h1>).
    note_body_filter: Callable[..., str] | None = None
    #: Return a full nav HTML for this note, or None for the default logic.
    nav_override: Callable[..., "str | None"] | None = None
    #: Per-page extra footer fragment (lang-aware); joined with " · ".
    footer_extra: Callable[..., str] | None = None
    #: Override the home page's primary JSON-LD block (None → default
    #: CollectionPage).
    home_main_jsonld: Callable[..., "dict | None"] | None = None
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
    #: Per-language string tables (page lang → Strings); falls back to
    #: ``strings`` for languages not listed.
    strings_by_lang: dict = field(default_factory=dict)
    hooks: Hooks = field(default_factory=Hooks)
    #: rel_path → slug (pin URLs independent of filenames).
    slug_overrides: dict = field(default_factory=dict)
    #: char → ascii replacement table used by slugify (e.g. Cyrillic translit).
    transliteration: dict = field(default_factory=dict)
    #: Appended to a note title when frontmatter has no seo_title.
    seo_title_suffix: str = ""
    default_cta_primary: "tuple[str, str] | None" = None
    default_cta_secondary: "tuple[str, str] | None" = None
    #: ISO "YYYY-MM-DD" → display string (a RU theme supplies its own). May
    #: optionally accept a second ``lang`` argument for per-language formats.
    format_date: Callable = _iso_date
    #: Full stylesheet override; None → the packaged BASE_CSS. Themes that
    #: need exact CSS control (parity migrations) set this.
    css: "str | None" = None
    #: Home-page meta overrides ("" → derived defaults).
    home_title: str = ""
    home_description: str = ""
    home_og_image: str = ""
    #: Custom .htaccess body (None → the packaged default when emit_htaccess).
    htaccess_content: "str | None" = None
    #: Extra search terms per note, appended to the search record.
    extra_search_terms: "Callable | None" = None
    #: OG card options: group → card label (fallback nav_label), plus
    #: "footer" and "home_label" keys for the og module.
    og_group_labels: dict = field(default_factory=dict)
    og_options: dict = field(default_factory=dict)
    #: Home crumb name in BreadcrumbList JSON-LD ("" → site_name).
    breadcrumb_home_name: str = ""
    #: Defaults layer (opt-in): derive a note's title from its first `# H1`
    #: when frontmatter has no `title:` — for publishing frontmatter-less
    #: Markdown (docs-per-repo). slug/description/aliases already degrade to
    #: filename / first-paragraph / empty without any flag.
    title_from_h1: bool = False
    #: Preprocess each note's body right after frontmatter is split, before
    #: title/excerpt derivation (e.g. strip Jekyll `{% raw %}` liquid tags).
    source_filter: "Callable[[str], str] | None" = None
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

    def strings_for(self, lang: str) -> Strings:
        return self.strings_by_lang.get(lang, self.strings)

    def display_date(self, value: str, lang: str) -> str:
        try:
            return self.format_date(value, lang)
        except TypeError:
            return self.format_date(value)
