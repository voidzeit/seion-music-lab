"""Resolve FL Studio user directories (from env, with Windows defaults)."""

from __future__ import annotations

import os
from pathlib import Path


def fl_user_data_dir() -> Path | None:
    value = os.environ.get("FL_USER_DATA_DIR")
    if value:
        return Path(value).expanduser()
    default = Path.home() / "Documents" / "Image-Line" / "FL Studio"
    return default if default.exists() else None


def fl_piano_roll_scripts_dir() -> Path | None:
    value = os.environ.get("FL_PIANO_ROLL_SCRIPTS_DIR")
    if value:
        return Path(value).expanduser()
    base = fl_user_data_dir()
    if base is None:
        return None
    return base / "Settings" / "Piano roll scripts"
