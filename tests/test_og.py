"""OG card rendering (the [og] extra). Skipped without Pillow."""

import dataclasses

import pytest

pytest.importorskip("PIL")

from example_site import CONFIG  # noqa: E402

from zettelkastenwiki import publish  # noqa: E402
from zettelkastenwiki.testing import assert_og_images_resolve  # noqa: E402


def test_og_cards_render_and_resolve(tmp_path):
    config = dataclasses.replace(CONFIG, og_images=True)
    out = publish(config, tmp_path / "site", render_og=True)
    assert (out / "og" / "index.png").exists()
    card = out / "og" / "guides" / "getting-started.png"
    assert card.exists()
    assert card.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert_og_images_resolve(out, config)


def test_og_cache_reused(tmp_path):
    config = dataclasses.replace(CONFIG, og_images=True)
    cache_probe = tmp_path.parent  # cache lives next to the wiki root by default
    out1 = publish(config, tmp_path / "site1", render_og=True)
    first = (out1 / "og" / "index.png").stat().st_size
    out2 = publish(config, tmp_path / "site2", render_og=True)
    second = (out2 / "og" / "index.png").stat().st_size
    assert first == second
    assert cache_probe is not None
