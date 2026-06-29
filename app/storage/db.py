"""Storage roots. The MVP persists projects as folders of files under
``data/projects``. A SQLite index is intentionally deferred (see roadmap).
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings


def projects_root() -> Path:
    root = get_settings().projects_dir
    root.mkdir(parents=True, exist_ok=True)
    return root
