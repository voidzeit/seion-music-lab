"""SQLite catalog + memory (Sprint 2).

Replaces the JSON preference/feedback files with a small SQLite database and
adds a project catalog that records version lineage (parent -> child). The idea
*files* (idea.json, MIDI, explanation.md) remain folders under data/projects;
this database is the index and the long-term memory.

Pure stdlib ``sqlite3`` — no extra dependency. All access goes through short
connections so it stays safe across processes and easy to test.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS preferences (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  TEXT NOT NULL,
    rating      INTEGER NOT NULL,
    liked       TEXT NOT NULL DEFAULT '[]',
    disliked    TEXT NOT NULL DEFAULT '[]',
    request     TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    parent_id   TEXT,
    title       TEXT NOT NULL DEFAULT '',
    bpm         INTEGER NOT NULL DEFAULT 0,
    key         TEXT NOT NULL DEFAULT '',
    bars        INTEGER NOT NULL DEFAULT 0,
    version     INTEGER NOT NULL DEFAULT 1,
    overall     REAL,
    direction   TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT ''
);
"""


class SqliteStore:
    """A tiny catalog/memory database."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            memory_dir = get_settings().memory_dir
            memory_dir.mkdir(parents=True, exist_ok=True)
            db_path = memory_dir / "seion.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    # --- preferences -------------------------------------------------------- #
    def get_preferences(self) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM preferences WHERE key = 'model'"
            ).fetchone()
        return json.loads(row["value"]) if row else None

    def save_preferences(self, prefs: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO preferences(key, value) VALUES('model', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (json.dumps(prefs),),
            )

    # --- feedback ----------------------------------------------------------- #
    def add_feedback(self, feedback: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback(project_id, rating, liked, disliked, request, created_at)"
                " VALUES(?, ?, ?, ?, ?, ?)",
                (
                    feedback.get("project_id", ""),
                    int(feedback.get("rating", 0)),
                    json.dumps(feedback.get("liked", [])),
                    json.dumps(feedback.get("disliked", [])),
                    feedback.get("request", ""),
                    str(feedback.get("created_at", "")),
                ),
            )

    def list_feedback(self, project_id: str | None = None) -> list[dict]:
        query = "SELECT * FROM feedback"
        params: tuple = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY id"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "project_id": r["project_id"],
                "rating": r["rating"],
                "liked": json.loads(r["liked"]),
                "disliked": json.loads(r["disliked"]),
                "request": r["request"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # --- project catalog ---------------------------------------------------- #
    def upsert_project(self, project: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO projects"
                "(id, parent_id, title, bpm, key, bars, version, overall, direction, created_at)"
                " VALUES(:id, :parent_id, :title, :bpm, :key, :bars, :version, :overall,"
                " :direction, :created_at)"
                " ON CONFLICT(id) DO UPDATE SET"
                " parent_id=excluded.parent_id, title=excluded.title, bpm=excluded.bpm,"
                " key=excluded.key, bars=excluded.bars, version=excluded.version,"
                " overall=excluded.overall, direction=excluded.direction,"
                " created_at=excluded.created_at",
                {
                    "id": project["id"],
                    "parent_id": project.get("parent_id"),
                    "title": project.get("title", ""),
                    "bpm": int(project.get("bpm", 0)),
                    "key": project.get("key", ""),
                    "bars": int(project.get("bars", 0)),
                    "version": int(project.get("version", 1)),
                    "overall": project.get("overall"),
                    "direction": project.get("direction", ""),
                    "created_at": str(project.get("created_at", "")),
                },
            )

    def get_project(self, project_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_projects(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY created_at, id").fetchall()
        return [dict(r) for r in rows]

    def children_of(self, parent_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM projects WHERE parent_id = ? ORDER BY created_at, id",
                (parent_id,),
            ).fetchall()
        return [dict(r) for r in rows]
