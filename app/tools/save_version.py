"""Tool: persist idea.json and seion_score.json for a project."""

from __future__ import annotations

from pathlib import Path

from app.export.json_writer import write_json
from app.schemas import MusicalIdea
from app.storage import ProjectStore


def save_project(idea: MusicalIdea, project_dir: str | Path | None = None) -> dict[str, str]:
    """Write idea.json (full) and seion_score.json (just the score)."""
    store = ProjectStore()
    target = Path(project_dir) if project_dir else store.project_dir(idea.id)
    target.mkdir(parents=True, exist_ok=True)

    idea_path = write_json(target / "idea.json", idea)
    paths = {"idea": str(idea_path)}

    if idea.seion_scores is not None:
        score_path = write_json(target / "seion_score.json", idea.seion_scores)
        paths["seion_score"] = str(score_path)

    return paths
