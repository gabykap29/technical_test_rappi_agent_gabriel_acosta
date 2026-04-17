"""FastAPI entrypoint for local and hosted ASGI servers."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rappi_intelligence.api.main import app  # noqa: E402

__all__ = ["app"]
