"""Write FL Studio Piano Roll scripts (.pyscript) to disk.

These are *consumed by FL Studio*, which reads a local JSON idea and inserts
notes into the Piano Roll. FL never talks to the network — it just reads files
SEION wrote. See docs/fl_integration.md.
"""

from __future__ import annotations

from pathlib import Path

from app.fl_bridge.piano_roll_script_template import (
    HUMANIZE_SCRIPT,
    build_import_script,
)

# Filename -> (role, title). These are the scripts SEION ships into FL.
_BUNDLED_IMPORTS = {
    "SEION Import Idea.pyscript": ("all", "SEION Import Idea.pyscript"),
    "SEION Generate Chords.pyscript": ("harmony", "SEION Generate Chords.pyscript"),
    "SEION Generate Bass.pyscript": ("bass", "SEION Generate Bass.pyscript"),
    "SEION Generate Arp.pyscript": ("arp", "SEION Generate Arp.pyscript"),
}


def write_piano_roll_import_script(path: str | Path, role: str = "all") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_import_script(role), encoding="utf-8")
    return path


def write_all_piano_roll_scripts(dest_dir: str | Path) -> list[Path]:
    """Write every bundled import script + the humanize script into ``dest_dir``."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, (role, title) in _BUNDLED_IMPORTS.items():
        out = dest / filename
        out.write_text(build_import_script(role, title), encoding="utf-8")
        written.append(out)
    humanize = dest / "SEION Humanize.pyscript"
    humanize.write_text(HUMANIZE_SCRIPT, encoding="utf-8")
    written.append(humanize)
    return written
