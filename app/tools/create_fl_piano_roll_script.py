"""Tool: write the FL Studio Piano Roll import script to a path."""

from __future__ import annotations

from pathlib import Path

from app.export.fl_script_writer import write_piano_roll_import_script


def create_fl_piano_roll_script(path: str | Path) -> Path:
    return write_piano_roll_import_script(path)
