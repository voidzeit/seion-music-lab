"""Tests for the deterministic SEION scorer."""

from __future__ import annotations

from app.agents import reference_agent
from app.music import (
    filter_open_automation,
    generate_arp_track,
    generate_bass_track,
    generate_chord_track,
    generate_drum_track,
)
from app.schemas import MusicalIdea, NoteEvent, UserRequest
from app.seion import score_idea

PROG = ["Am7", "Fmaj7", "Cmaj7", "G6"]


def _request() -> UserRequest:
    return UserRequest(
        bpm=124,
        key="A minor",
        bars=16,
        style_targets=["Computer Data", "NTO"],
        emotional_targets=["warm", "melancholic", "hypnotic"],
    )


def _idea(tracks, automation=None) -> MusicalIdea:
    return MusicalIdea(
        id="test",
        title="test",
        bpm=124,
        key="A minor",
        bars=16,
        style_targets=["Computer Data", "NTO"],
        emotional_targets=["warm", "melancholic", "hypnotic"],
        tracks=tracks,
        automation=automation or [],
    )


def _full_tracks():
    return [
        generate_chord_track(PROG, 16),
        generate_bass_track(PROG, 16),
        generate_arp_track(PROG, 16),
        generate_drum_track(16),
    ]


def _score(tracks, automation=None):
    req = _request()
    ctx = reference_agent.build_style_context(req.style_targets)
    return score_idea(_idea(tracks, automation), req, ctx)


def test_full_idea_scores_reasonably():
    score = _score(_full_tracks(), [filter_open_automation("hypnotic_chord_arp", 16)])
    assert 0.0 <= score.overall <= 1.0
    assert score.overall > 0.6
    assert score.coherence > 0.7
    for component in (
        "coherence", "style_match", "emotional_clarity",
        "tension_curve", "editability", "novelty",
    ):
        assert 0.0 <= getattr(score, component) <= 1.0


def test_missing_bass_penalises_coherence():
    full = _score(_full_tracks())
    no_bass = _score(
        [generate_chord_track(PROG, 16), generate_arp_track(PROG, 16), generate_drum_track(16)]
    )
    assert no_bass.coherence < full.coherence


def test_out_of_scale_notes_penalise_coherence():
    clean = _full_tracks()
    dirty = _full_tracks()
    # Append C#4 (MIDI 61) — not diatonic to A minor — to the harmony track.
    dirty[0].notes.append(
        NoteEvent(pitch="C#4", midi=61, start_beat=0.0, duration_beats=1.0, velocity=80)
    )
    assert _score(dirty).coherence < _score(clean).coherence


def test_too_many_notes_penalise_editability():
    normal = _full_tracks()
    busy = [
        generate_chord_track(PROG, 16),
        generate_bass_track(PROG, 16),
        generate_arp_track(PROG, 16, step_beats=0.125),  # 32 notes/bar — overloaded
        generate_drum_track(16),
    ]
    assert _score(busy).editability < _score(normal).editability


def test_automation_raises_tension_curve():
    without = _score(_full_tracks())
    with_auto = _score(_full_tracks(), [filter_open_automation("hypnotic_chord_arp", 16)])
    assert with_auto.tension_curve > without.tension_curve


def test_overall_matches_weighted_formula():
    score = _score(_full_tracks(), [filter_open_automation("hypnotic_chord_arp", 16)])
    expected = (
        0.25 * score.coherence
        + 0.20 * score.style_match
        + 0.20 * score.emotional_clarity
        + 0.15 * score.tension_curve
        + 0.10 * score.editability
        + 0.10 * score.novelty
    )
    assert abs(score.overall - round(expected, 4)) < 1e-6
