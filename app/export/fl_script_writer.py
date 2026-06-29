"""Write FL Studio Piano Roll scripts (.pyscript) to disk.

These are *consumed by FL Studio*, which reads a local JSON idea and inserts
notes into the Piano Roll. FL never talks to the network — it just reads files
SEION wrote. See docs/fl_integration.md.
"""

from __future__ import annotations

from pathlib import Path

from app.fl_bridge.piano_roll_script_template import IMPORT_IDEA_SCRIPT


def write_piano_roll_import_script(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(IMPORT_IDEA_SCRIPT, encoding="utf-8")
    return path
