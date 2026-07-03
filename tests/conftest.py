import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "example"))

from example_site import CONFIG  # noqa: E402

from zettelkastenwiki import publish  # noqa: E402


@pytest.fixture(scope="session")
def config():
    return CONFIG


@pytest.fixture(scope="session")
def site(tmp_path_factory, config):
    out = tmp_path_factory.mktemp("example_site")
    publish(config, out)
    return out
