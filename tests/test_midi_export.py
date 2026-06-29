"""Tests for MIDI export."""

from __future__ import annotations

import mido

from app.export.midi_writer import write_full_loop_midi, write_track_midi
from app.music import (
    generate_arp_track,
    generate_bass_track,
    generate_chord_track,
    generate_drum_track,
)

PROG = ["Am7", "Fmaj7", "Cmaj7", "G6"]


def _note_ons(path):
    mid = mido.MidiFile(str(path))
    return [
        msg
        for track in mid.tracks
        for msg in track
        if msg.type == "note_on" and msg.velocity > 0
    ]


def test_chord_track_midi_written(tmp_path):
    track = generate_chord_track(PROG, bars=16)
    path = write_track_midi(tmp_path / "chords.mid", track, bpm=124)
    assert path.exists()

    note_ons = _note_ons(path)
    assert len(note_ons) == 16 * 4  # 4 chord tones per bar, 16 bars
    for msg in note_ons:
        assert 1 <= msg.velocity <= 127
        assert 0 <= msg.note <= 127


def test_bass_and_arp_have_notes(tmp_path):
    bass = write_track_midi(tmp_path / "bass.mid", generate_bass_track(PROG, 16), 124)
    arp = write_track_midi(tmp_path / "arp.mid", generate_arp_track(PROG, 16), 124)
    assert len(_note_ons(bass)) == 16 * 4    # 4 offbeats per bar
    assert len(_note_ons(arp)) == 16 * 8     # 8 eighth-notes per bar


def test_drum_track_on_channel_10(tmp_path):
    path = write_track_midi(tmp_path / "drums.mid", generate_drum_track(16), 124)
    mid = mido.MidiFile(str(path))
    channels = {msg.channel for tr in mid.tracks for msg in tr if msg.type == "note_on"}
    assert channels == {9}  # MIDI channel 10 (0-indexed 9)


def test_full_loop_combines_tracks(tmp_path):
    tracks = [
        generate_chord_track(PROG, 16),
        generate_bass_track(PROG, 16),
        generate_arp_track(PROG, 16),
        generate_drum_track(16),
    ]
    path = write_full_loop_midi(tmp_path / "full_loop.mid", tracks, bpm=124)
    assert path.exists()

    mid = mido.MidiFile(str(path))
    assert len(mid.tracks) == 5  # conductor + 4 instrument tracks
    assert len(_note_ons(path)) > 200
    # tempo is present on the conductor track
    assert any(msg.type == "set_tempo" for msg in mid.tracks[0])
