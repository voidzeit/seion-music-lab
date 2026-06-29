"""Tool: write explanation.md for a project."""

from __future__ import annotations

from pathlib import Path

from app.export.markdown_writer import write_markdown


def write_explanation_file(project_dir: str | Path, text: str) -> Path:
    return write_markdown(Path(project_dir) / "explanation.md", text)
