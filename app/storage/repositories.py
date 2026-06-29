"""Project persistence: each idea is a folder of files under data/projects/<id>."""

from __future__ import annotations

import json
from pathlib import Path

from app.export.json_writer import write_json
from app.schemas import MusicalIdea
from app.storage.db import projects_root
from app.storage.models import ProjectSummary


class ProjectStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or projects_root()
        self.root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        path = self.root / project_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_idea_json(self, idea: MusicalIdea) -> Path:
        return write_json(self.project_dir(idea.id) / "idea.json", idea)

    def load_idea(self, project_id: str) -> MusicalIdea:
        data = json.loads((self.root / project_id / "idea.json").read_text("utf-8"))
        return MusicalIdea(**data)

    def list_projects(self) -> list[ProjectSummary]:
        summaries: list[ProjectSummary] = []
        for idea_file in sorted(self.root.glob("*/idea.json")):
            try:
                data = json.loads(idea_file.read_text("utf-8"))
            except Exception:
                continue
            score = (data.get("seion_scores") or {}).get("overall")
            summaries.append(
                ProjectSummary(
                    id=data["id"],
                    title=data.get("title", data["id"]),
                    created_at=str(data.get("created_at", "")),
                    bpm=data.get("bpm", 0),
                    key=data.get("key", ""),
                    overall_score=score,
                    path=str(idea_file.parent),
                )
            )
        return summaries
