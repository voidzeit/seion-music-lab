"""JSON-backed memory for preferences and feedback history.

The MVP persists to plain JSON files under ``data/memory`` (SQLite comes in a
later sprint, as the brief allows).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings
from app.schemas import Feedback
from app.seion.preference_model import PreferenceModel


class SeionMemory:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self.memory_dir = memory_dir or get_settings().memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.prefs_path = self.memory_dir / "user_preferences.json"
        self.feedback_path = self.memory_dir / "feedback_log.jsonl"

    def load_preferences(self) -> PreferenceModel:
        if self.prefs_path.exists():
            data = json.loads(self.prefs_path.read_text(encoding="utf-8"))
            return PreferenceModel(**data)
        return PreferenceModel()

    def save_preferences(self, prefs: PreferenceModel) -> None:
        self.prefs_path.write_text(
            json.dumps(prefs.model_dump(), indent=2), encoding="utf-8"
        )

    def record_feedback(self, feedback: Feedback) -> PreferenceModel:
        with self.feedback_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(feedback.model_dump(mode="json")) + "\n")
        prefs = self.load_preferences().update_from_feedback(feedback)
        self.save_preferences(prefs)
        return prefs
