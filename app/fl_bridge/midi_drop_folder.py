"""Mirror the latest export into a stable 'drop folder' for FL Studio.

FL-side scripts can read fixed file names (``latest_idea.json``,
``latest_chords.mid`` …) instead of chasing per-project paths.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.config import get_settings


def update_drop_folder(project_dir: str | Path) -> Path:
    """Copy a project's idea.json + MIDI files into ``data/fl_drop`` as latest_*."""
    project_dir = Path(project_dir)
    drop = get_settings().fl_drop_dir
    drop.mkdir(parents=True, exist_ok=True)

    idea = project_dir / "idea.json"
    if idea.exists():
        shutil.copyfile(idea, drop / "latest_idea.json")

    for midi in project_dir.glob("*.mid"):
        shutil.copyfile(midi, drop / f"latest_{midi.name}")

    return drop
