"""Pytest bootstrap: make `app` importable and isolate the data directory.

We point SEION_DATA_DIR at a throwaway temp folder *before* settings are read so
tests never write into the real ``data/`` tree.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SEION_DATA_DIR", tempfile.mkdtemp(prefix="seion_test_"))

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()
