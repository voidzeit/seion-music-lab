"""Sprint 2: SQLite-backed memory + project catalog."""

from __future__ import annotations

from app.schemas import Feedback
from app.seion.memory import SeionMemory
from app.storage.sqlite_store import SqliteStore


def test_preferences_roundtrip(tmp_path):
    mem = SeionMemory(memory_dir=tmp_path)
    prefs = mem.load_preferences()
    prefs.likes.append("offbeat bass")
    mem.save_preferences(prefs)

    again = SeionMemory(memory_dir=tmp_path).load_preferences()
    assert "offbeat bass" in again.likes


def test_record_feedback_updates_preferences(tmp_path):
    mem = SeionMemory(memory_dir=tmp_path)
    updated = mem.record_feedback(
        Feedback(
            project_id="idea_x",
            rating=7,
            liked=["warm chords"],
            disliked=["busy arp"],
            request="darker",
        )
    )
    assert "warm chords" in updated.likes
    assert "busy arp" in updated.dislikes
    assert updated.current_direction == "darker"

    # The raw feedback row is persisted in SQLite.
    rows = mem.store.list_feedback("idea_x")
    assert len(rows) == 1
    assert rows[0]["rating"] == 7


def test_project_catalog_lineage(tmp_path):
    store = SqliteStore(db_path=tmp_path / "seion.db")
    store.upsert_project(
        {"id": "idea_a", "title": "A", "bpm": 124, "key": "A minor", "version": 1, "overall": 0.76}
    )
    store.upsert_project(
        {
            "id": "idea_a_v2",
            "parent_id": "idea_a",
            "title": "A v2",
            "bpm": 124,
            "key": "A minor",
            "version": 2,
            "overall": 0.78,
            "direction": "darker",
        }
    )

    assert store.get_project("idea_a")["overall"] == 0.76
    children = store.children_of("idea_a")
    assert len(children) == 1
    assert children[0]["id"] == "idea_a_v2"
    assert children[0]["direction"] == "darker"


def test_upsert_is_idempotent(tmp_path):
    store = SqliteStore(db_path=tmp_path / "seion.db")
    for overall in (0.70, 0.75):
        store.upsert_project(
            {"id": "idea_a", "title": "A", "bpm": 124, "key": "A minor", "overall": overall}
        )
    assert len(store.list_projects()) == 1
    assert store.get_project("idea_a")["overall"] == 0.75
