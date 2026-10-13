"""Functional MIDI tests for the Project 001 16-bar creative prototypes."""
from __future__ import annotations

import json

import mido
import pytest

from app.music.prototype_lab import BARS, BPM, MODES, ROLES, build_experiments, make_patterns


def test_three_modes_have_distinct_low_end_and_arrangement():
    patterns = {mode: make_patterns(mode) for mode in MODES}
    assert all(set(x) == set(ROLES) for x in patterns.values())
    assert len({tuple((n.start, n.pitch) for n in x["bass"]) for x in patterns.values()}) == 3
    assert len(patterns["trance_bounce"]["arp"]) > len(patterns["groove"]["arp"])
    assert len(patterns["hardcore_hybrid"]["bass"]) < len(patterns["groove"]["bass"])


def test_fixed_seed_reproducible_and_event_bounds():
    assert make_patterns("groove", seed=14) == make_patterns("groove", seed=14)
    assert make_patterns("groove", seed=14) != make_patterns("groove", seed=15)
    for mode in MODES:
        for notes in make_patterns(mode).values():
            assert all(0 <= n.start < BARS * 4 for n in notes)
            assert all(n.start + n.duration <= BARS * 4 for n in notes)
            assert all(0 <= n.pitch <= 127 for n in notes)


def test_invalid_mode_and_bars_rejected():
    with pytest.raises(ValueError):
        make_patterns("wrong")
    with pytest.raises(ValueError):
        make_patterns("groove", bars=3)


def test_prototypes_are_valid_multitrack_midi_and_correct_tempo(tmp_path):
    out = tmp_path / "v002"
    manifest = build_experiments(out)
    assert manifest["status"] == "symbolic_prototype_unheard"
    assert manifest["duration_seconds"] == pytest.approx(16 * 4 * 60 / 158, abs=0.001)
    for mode in MODES:
        path = out / manifest["experiments"][mode]["full_midi"]
        mid = mido.MidiFile(path)
        assert mid.type == 1
        assert len(mid.tracks) == 1 + len(ROLES)
        tempo = [msg.tempo for msg in mid.tracks[0] if msg.type == "set_tempo"][0]
        assert mido.tempo2bpm(tempo) == pytest.approx(BPM, abs=0.001)
        assert sum(msg.type == "note_on" and msg.velocity > 0
                   for track in mid.tracks for msg in track) > 100
    assert json.loads((out / "prototype_manifest.json").read_text())["seed"] == 1001


def test_prevent_accidental_overwrite(tmp_path):
    out = tmp_path / "v002"
    build_experiments(out)
    with pytest.raises(FileExistsError):
        build_experiments(out)
