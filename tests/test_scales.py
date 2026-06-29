"""Tests for note conversion and scale construction."""

from __future__ import annotations

import pytest

from app.exceptions import MusicTheoryError
from app.music.notes import midi_to_note_name, note_name_to_midi
from app.music.scales import is_in_scale, parse_key, scale_pitch_classes

DIATONIC = [0, 2, 4, 5, 7, 9, 11]


@pytest.mark.parametrize(
    "name,midi",
    [("A3", 57), ("C4", 60), ("A4", 69), ("C-1", 0), ("G9", 127)],
)
def test_note_name_to_midi(name, midi):
    assert note_name_to_midi(name) == midi


def test_note_name_roundtrip():
    for midi in range(0, 128):
        assert note_name_to_midi(midi_to_note_name(midi)) == midi


def test_flats_and_sharps():
    assert note_name_to_midi("Bb2") == note_name_to_midi("A#2")
    assert note_name_to_midi("Db4") == 61


def test_invalid_note_raises():
    with pytest.raises(MusicTheoryError):
        note_name_to_midi("H4")


def test_parse_key():
    assert parse_key("A minor") == (9, "minor")
    assert parse_key("C major") == (0, "major")
    assert parse_key("F# minor") == (6, "minor")
    assert parse_key("Bb major") == (10, "major")


def test_a_minor_and_c_major_share_notes():
    assert scale_pitch_classes("A minor") == DIATONIC
    assert scale_pitch_classes("C major") == DIATONIC


def test_is_in_scale():
    assert is_in_scale(note_name_to_midi("C4"), "A minor")  # C is diatonic
    assert not is_in_scale(note_name_to_midi("C#4"), "A minor")  # C# is not
