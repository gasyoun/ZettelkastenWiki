"""Optional OpenGraph card rendering (``pip install zettelkastenwiki[og]``).

Branded 1200×630 PNGs per note with a content-addressed render cache. If
Pillow is unavailable the whole module degrades to a no-op (pages still emit
their ``og:image`` tags)."""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import SiteConfig

# Bump when the card layout/colours change, to invalidate the render cache.
OG_RENDER_VERSION = 1

try:
    from PIL import Image, ImageDraw, ImageFont

    _PIL_OK = True
except ImportError:  # pragma: no cover - exercised only without Pillow
    _PIL_OK = False

_SYSTEM_FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
)
_SYSTEM_FONTS_BOLD = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)

WIDTH, HEIGHT = 1200, 630
MARGIN = 96
STRIPE_W = 18


@dataclass(frozen=True)
class OgStyle:
    bg: tuple = (255, 255, 255)
    ink: tuple = (31, 41, 51)
    muted: tuple = (91, 100, 114)
    accent: tuple = (15, 118, 110)
    footer: str = ""
    #: Optional font files (a Cyrillic/Unicode-capable TTF pair).
    font_regular: "Path | None" = None
    font_bold: "Path | None" = None


def og_cache_key(title: str, label: str) -> str:
    raw = f"{OG_RENDER_VERSION}\x00{title}\x00{label}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _font(size: int, style: OgStyle, bold: bool = False):
    configured = style.font_bold if bold else style.font_regular
    if configured and Path(configured).exists():
        return ImageFont.truetype(str(configured), size)
    for candidate in _SYSTEM_FONTS_BOLD if bold else _SYSTEM_FONTS:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def _wrap(draw, text: str, font, max_width: int) -> list:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if not current or draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fit_title(draw, title: str, max_width: int, style: OgStyle):
    for size in (74, 64, 56, 48, 42):
        font = _font(size, style, bold=True)
        lines = _wrap(draw, title, font, max_width)
        if len(lines) <= 4:
            return font, lines
    font = _font(42, style, bold=True)
    return font, _wrap(draw, title, font, max_width)[:4]


def render_og_card(path: Path, title: str, label: str, style: "OgStyle | None" = None) -> bool:
    """Render one OG card. Returns True if an image was written."""
    if not _PIL_OK:
        return False
    style = style or OgStyle()

    image = Image.new("RGB", (WIDTH, HEIGHT), style.bg)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, STRIPE_W, HEIGHT), fill=style.accent)

    text_left = MARGIN
    max_width = WIDTH - MARGIN - MARGIN

    label_font = _font(34, style, bold=True)
    draw.text((text_left, MARGIN), label.upper(), font=label_font, fill=style.accent)

    title_font, lines = _fit_title(draw, title, max_width, style)
    ascent, descent = title_font.getmetrics()
    line_height = int((ascent + descent) * 1.18)
    y = (HEIGHT - line_height * len(lines)) // 2
    for line in lines:
        draw.text((text_left, y), line, font=title_font, fill=style.ink)
        y += line_height

    if style.footer:
        footer_font = _font(32, style)
        footer_bbox = draw.textbbox((0, 0), style.footer, font=footer_font)
        draw.text(
            (text_left, HEIGHT - MARGIN - (footer_bbox[3] - footer_bbox[1])),
            style.footer,
            font=footer_font,
            fill=style.muted,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")
    return True


def write_og_images(
    output_dir: Path,
    notes: list,
    config: SiteConfig,
    *,
    style: "OgStyle | None" = None,
    cache_dir: "Path | None" = None,
) -> None:
    """Write per-note OG cards, reusing a content-addressed cache.

    publish() wipes the output dir each build; unchanged cards are copied
    from the cache instead of re-rendered (Pillow rendering dominated build
    time on the 100+-page ORS site)."""
    style = style or OgStyle(footer=config.site_name)
    cache_root = Path(cache_dir) if cache_dir else Path(config.wiki_root).parent / ".og_cache"

    label_for = {spec.name: (spec.nav_label or spec.name) for spec in config.groups}
    cards = [(output_dir / "og" / "index.png", config.site_name, config.site_name)]
    for note in notes:
        if str(note.frontmatter.get("og_image", "")).strip():
            continue  # external override — nothing to generate
        cards.append(
            (
                output_dir / "og" / note.group / f"{note.slug}.png",
                note.title,
                label_for.get(note.group, note.group),
            )
        )

    pil_ok: "bool | None" = None
    for dest, title, label in cards:
        dest.parent.mkdir(parents=True, exist_ok=True)
        cached = cache_root / f"{og_cache_key(title, label)}.png"
        if cached.exists():
            shutil.copyfile(cached, dest)
            pil_ok = True
            continue
        if render_og_card(dest, title, label, style):
            cache_root.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(dest, cached)
            pil_ok = True
        else:
            pil_ok = False
            break  # Pillow unavailable — remaining renders would also no-op

    if pil_ok is False:
        print("Pillow not available — skipped OG image generation (og:image tags still emitted).")
