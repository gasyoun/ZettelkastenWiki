"""Build the example site: ``python example/build.py [output_dir]``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from example_site import CONFIG  # noqa: E402

from zettelkastenwiki import publish  # noqa: E402

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "_site"
    publish(CONFIG, out)
    print(f"Example site built at {out}")
