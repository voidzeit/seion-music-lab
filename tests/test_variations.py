"""Sprint 2: directed variations + version lineage."""

from __future__ import annotations

from app.agents import variation_agent
from app.music.variations import apply_variation
from app.orchestrator import run_generation, run_variation
from app.schemas import UserRequest
from app.storage import ProjectStore


def _request() -> UserRequest:
    return UserRequest(
        bpm=124,
        key="A minor",
        bars=16,
        style_targets=["Computer Data", "NTO"],
        emotional_targets=["warm", "melancholic", "hypnotic"],
    )


def _avg_arp_pitch(idea) -> float:
    arp = idea.track_by_role("arp")
    return sum(n.midi for n in arp.notes) / len(arp.notes)


def test_parse_direction_keywords():
    spec = variation_agent.parse_direction("darker, simpler arp")
    assert spec.arp_octave_shift == -1
    assert spec.harmony_thin_top is True
    assert spec.simpler_arp is True
    assert "dark" in spec.add_emotions


def test_darker_lowers_arp_register(tmp_path):
    store = ProjectStore(root=tmp_path)
    parent = run_generation(_request(), store=store).idea

    spec = variation_agent.parse_direction("darker")
    child, changes = apply_variation(parent, spec)

    assert _avg_arp_pitch(child) < _avg_arp_pitch(parent)
    assert changes  # human-readable change notes were produced
    # The parent must be untouched (deep copy).
    assert _avg_arp_pitch(parent) > 0


def test_simpler_arp_reduces_note_count(tmp_path):
    store = ProjectStore(root=tmp_path)
    parent = run_generation(_request(), store=store).idea
    child, _ = apply_variation(parent, variation_agent.parse_direction("simpler arp"))
    assert len(child.track_by_role("arp").notes) < len(parent.track_by_role("arp").notes)


def test_more_drive_adds_bass_notes(tmp_path):
    store = ProjectStore(root=tmp_path)
    parent = run_generation(_request(), store=store).idea
    child, _ = apply_variation(parent, variation_agent.parse_direction("more drive"))
    assert len(child.track_by_role("bass").notes) > len(parent.track_by_role("bass").notes)


def test_run_variation_creates_child_with_lineage(tmp_path):
    store = ProjectStore(root=tmp_path)
    parent_result = run_generation(_request(), store=store)
    parent_id = parent_result.idea.id

    result = run_variation(parent_id, "darker, simpler arp", store=store)

    assert result.child.parent_id == parent_id
    assert result.child.version == 2
    assert result.child.lineage == [parent_id]
    assert result.child.variation_request == "darker, simpler arp"

    for filename in ("idea.json", "seion_score.json", "explanation.md", "full_loop.mid"):
        assert (result.project_dir / filename).exists(), f"missing {filename}"

    assert "overall" in result.deltas
    # A variation decision was logged.
    assert any(e.type == "variation" for e in result.child.decision_log)


def test_variation_reloads_from_store(tmp_path):
    store = ProjectStore(root=tmp_path)
    parent_id = run_generation(_request(), store=store).idea.id
    child_id = run_variation(parent_id, "softer", store=store).child.id

    reloaded = store.load_idea(child_id)
    assert reloaded.parent_id == parent_id
    assert reloaded.seion_scores is not None
