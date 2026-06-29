"""Tests for chord construction and voicings."""

from __future__ import annotations

from app.music.chords import chord_notes, parse_chord_symbol
from app.music.notes import midi_to_note_name
from app.music.scales import scale_pitch_classes
from app.music.voicings import warm_voicing

DEFAULT_PROGRESSION = ["Am7", "Fmaj7", "Cmaj7", "G6"]


def test_am7_pitch_classes():
    # A C E G
    assert set(parse_chord_symbol("Am7").pitch_classes) == {9, 0, 4, 7}


def test_fmaj7_pitch_classes():
    # F A C E
    assert set(parse_chord_symbol("Fmaj7").pitch_classes) == {5, 9, 0, 4}


def test_chord_notes_root_position():
    assert chord_notes("Am7", 3) == [57, 60, 64, 67]  # A3 C4 E4 G4
    assert chord_notes("Fmaj7", 3) == [53, 57, 60, 64]
    assert chord_notes("Cmaj7", 3) == [48, 52, 55, 59]
    assert chord_notes("G6", 3) == [55, 59, 62, 64]


def test_am7_note_names():
    names = [midi_to_note_name(m) for m in chord_notes("Am7", 3)]
    assert names == ["A3", "C4", "E4", "G4"]


def test_triad_and_seventh_sizes():
    assert len(parse_chord_symbol("C").intervals) == 3       # triad
    assert len(parse_chord_symbol("Cmaj7").intervals) == 4   # seventh


def test_warm_voicing_in_range():
    for symbol in DEFAULT_PROGRESSION:
        voicing = warm_voicing(symbol, low=48, high=72)
        assert all(48 <= n <= 72 for n in voicing)
        assert len(set(voicing)) == len(voicing)  # no duplicate notes


def test_default_progression_is_diatonic_to_a_minor():
    a_minor = set(scale_pitch_classes("A minor"))
    for symbol in DEFAULT_PROGRESSION:
        assert set(parse_chord_symbol(symbol).pitch_classes).issubset(a_minor)
