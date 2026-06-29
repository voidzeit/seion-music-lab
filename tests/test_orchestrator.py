"""End-to-end smoke test for the generation pipeline."""

from __future__ import annotations

import json

from app.orchestrator import run_generation
from app.orchestrator.state_machine import GenerationState
from app.schemas import MusicalIdea, UserRequest
from app.storage import ProjectStore

EXPECTED_FILES = [
    "idea.json",
    "seion_score.json",
    "explanation.md",
    "chords.mid",
    "bass.mid",
    "arp.mid",
    "drums.mid",
    "full_loop.mid",
]


def _request() -> UserRequest:
    return UserRequest(
        bpm=124,
        key="A minor",
        bars=16,
        style_targets=["Computer Data", "NTO"],
        emotional_targets=["warm", "melancholic", "hypnotic"],
    )


def test_run_generation_creates_all_files(tmp_path):
    store = ProjectStore(root=tmp_path)
    result = run_generation(_request(), store=store)

    for filename in EXPECTED_FILES:
        assert (result.project_dir / filename).exists(), f"missing {filename}"

    assert 0.0 <= result.score.overall <= 1.0
    assert len(result.idea.tracks) == 4
    assert GenerationState.DONE in result.states


def test_idea_json_roundtrips(tmp_path):
    store = ProjectStore(root=tmp_path)
    result = run_generation(_request(), store=store)

    reloaded = store.load_idea(result.idea.id)
    assert isinstance(reloaded, MusicalIdea)
    assert reloaded.bpm == 124
    assert reloaded.key == "A minor"
    assert reloaded.seion_scores is not None
    assert reloaded.decision_log  # decisions were recorded


def test_seion_score_json_has_components(tmp_path):
    store = ProjectStore(root=tmp_path)
    result = run_generation(_request(), store=store)
    data = json.loads((result.project_dir / "seion_score.json").read_text("utf-8"))
    for component in ("coherence", "style_match", "emotional_clarity", "overall"):
        assert component in data


def test_decision_log_has_required_fields(tmp_path):
    store = ProjectStore(root=tmp_path)
    result = run_generation(_request(), store=store)
    entry = result.idea.decision_log[0]
    for field in ("decision_id", "agent", "type", "decision", "reason"):
        assert getattr(entry, field)
