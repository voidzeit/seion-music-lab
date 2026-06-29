"""SQLite-backed memory for preferences and feedback history (Sprint 2).

The API is unchanged from the JSON MVP (``load_preferences`` /
``save_preferences`` / ``record_feedback``) so callers don't care that the
backing store is now SQLite. A one-time migration folds any legacy
``user_preferences.json`` / ``feedback_log.jsonl`` into the database.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings
from app.schemas import Feedback
from app.seion.preference_model import PreferenceModel
from app.storage.sqlite_store import SqliteStore


class SeionMemory:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self.memory_dir = memory_dir or get_settings().memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.store = SqliteStore(self.memory_dir / "seion.db")
        self._migrate_legacy_json()

    def load_preferences(self) -> PreferenceModel:
        data = self.store.get_preferences()
        return PreferenceModel(**data) if data else PreferenceModel()

    def save_preferences(self, prefs: PreferenceModel) -> None:
        self.store.save_preferences(prefs.model_dump())

    def record_feedback(self, feedback: Feedback) -> PreferenceModel:
        self.store.add_feedback(feedback.model_dump(mode="json"))
        prefs = self.load_preferences().update_from_feedback(feedback)
        self.save_preferences(prefs)
        return prefs

    # --- legacy migration --------------------------------------------------- #
    def _migrate_legacy_json(self) -> None:
        prefs_path = self.memory_dir / "user_preferences.json"
        if prefs_path.exists() and self.store.get_preferences() is None:
            try:
                self.store.save_preferences(json.loads(prefs_path.read_text("utf-8")))
                prefs_path.rename(prefs_path.with_suffix(".json.migrated"))
            except Exception:  # pragma: no cover - defensive
                pass

        log_path = self.memory_dir / "feedback_log.jsonl"
        if log_path.exists() and not self.store.list_feedback():
            try:
                for line in log_path.read_text("utf-8").splitlines():
                    line = line.strip()
                    if line:
                        self.store.add_feedback(json.loads(line))
                log_path.rename(log_path.with_suffix(".jsonl.migrated"))
            except Exception:  # pragma: no cover - defensive
                pass
