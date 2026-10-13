"""Unit tests for the Ardour connector's pure parts (no Ardour needed)."""

from __future__ import annotations

import base64
import math
import struct
import wave
from pathlib import Path

import pytest
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from seion_ardour.midi_job import BarRange, read_notes, slice_notes, split_role, write_job
from seion_ardour.runner import ArdourError, prepare_session, session_name
from seion_ardour.surge_state import (
    SURGE_XT_CLASS_ID,
    apply_kit,
    build_vstpreset,
    resolve_kit_paths,
)
from seion_ardour.validation import check_wav, note_coverage


def _write_midi(path: Path, events: list[tuple[int, str, int, int]], bpm: float = 156) -> Path:
    """events: (abs_tick, 'on'|'off', note, velocity) at PPQ 480."""
    track = MidiTrack()
    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))
    last = 0
    for tick, kind, note, vel in sorted(events):
        msg = "note_on" if kind == "on" else "note_off"
        track.append(Message(msg, note=note, velocity=vel, channel=9, time=tick - last))
        last = tick
    mid = MidiFile(ticks_per_beat=480)
    mid.tracks.append(track)
    mid.save(str(path))
    return path


def test_read_notes_pairs_on_off_including_velocity_zero(tmp_path):
    path = _write_midi(
        tmp_path / "d.mid",
        [(0, "on", 36, 100), (240, "off", 36, 0), (480, "on", 38, 90), (720, "on", 38, 0)],
    )
    notes, bpm = read_notes(path)
    assert bpm == pytest.approx(156, abs=0.01)
    assert notes == [(0.0, 0.5, 36, 100, 9), (1.0, 0.5, 38, 90, 9)]


def test_bar_range_and_slice_shift_and_clip():
    start, end = BarRange.parse("2-3").beats()
    assert (start, end) == (4.0, 12.0)
    notes = [(3.0, 1.0, 60, 100, 0), (4.0, 1.0, 61, 100, 0), (11.0, 4.0, 62, 100, 0)]
    assert slice_notes(notes, start, end) == [(0.0, 1.0, 61, 100, 0), (7.0, 1.0, 62, 100, 0)]


def test_split_role_moves_kick_out_of_drums():
    tracks = {"drums": [(0.0, 0.2, 36, 120, 9), (0.5, 0.1, 42, 80, 9)], "bass": []}
    out = split_role(tracks, "kick", "drums", {35, 36})
    assert out["kick"] == [(0.0, 0.2, 36, 120, 9)]
    assert out["drums"] == [(0.5, 0.1, 42, 80, 9)]
    assert split_role(tracks, "kick", "missing", {36}) is tracks


def test_write_job_is_lua_table(tmp_path):
    job = write_job(
        tmp_path / "job.lua",
        tracks={"drums": [(0.0, 0.25, 36, 110, 9)]},
        bpm=156,
        length_beats=4,
        export_dir=tmp_path,
        stems=False,
    )
    text = job.read_text(encoding="utf-8")
    assert text.startswith("return {")
    assert '["drums"] = {{0.000000,0.250000,36,110,9}}' in text
    assert "stems = false" in text


def _write_wav(path: Path, samples: list[int]) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return path


def test_check_wav_rejects_silence_and_accepts_tone(tmp_path):
    silent = check_wav(_write_wav(tmp_path / "s.wav", [0] * 4800))
    assert not silent.passed
    tone = [int(8000 * math.sin(2 * math.pi * 440 * i / 48000)) for i in range(4800)]
    report = check_wav(_write_wav(tmp_path / "t.wav", tone))
    assert report.passed
    assert report.duration_seconds == pytest.approx(0.1)
    assert -13 < report.peak_dbfs < -11


def test_note_coverage_counts_half_second_windows():
    # 120 BPM -> 0.5 s per beat: one 1-beat note covers its own window (+ the boundary one)
    assert note_coverage([], 120, 4.0) == 0
    assert note_coverage([(0.0, 1.0, 60, 100, 0)], 120, 4.0) == pytest.approx(2 / 8)


def test_surge_state_swaps_payload_and_keeps_header(tmp_path):
    payload_old = b"sub3" + b"\0" * 20
    header = b"VST3" + struct.pack("<i", 1) + SURGE_XT_CLASS_ID
    blob = build_vstpreset(header, payload_old)
    fxp = b"CcnK" + b"\0" * 24 + b"My Kick".ljust(28, b"\0") + b"\0" * 4 + b"sub3NEWDATA"
    session = tmp_path / "s.ardour"
    session.write_text(
        '<Session><Routes><Route name="kick-1-t1"><Processor type="vst3"><chunk>'
        + base64.b64encode(blob).decode()
        + "</chunk></Processor></Route></Routes></Session>",
        encoding="utf-8",
    )
    patch = tmp_path / "k.fxp"
    patch.write_bytes(fxp)
    assert apply_kit(session, {"patches": {"kick": str(patch)}}) == {"kick": "My Kick"}
    new = base64.b64decode(session.read_text(encoding="utf-8").split("<chunk>")[1].split("</chunk>")[0])
    assert new[:40] == header
    assert new[48:48 + 11] == b"sub3NEWDATA"
    assert new.endswith(b"Comp" + struct.pack("<qq", 48, 11))


def test_session_name_requires_single_state_file(tmp_path):
    with pytest.raises(ArdourError):
        session_name(tmp_path)
    (tmp_path / "Untitled-1.ardour").write_text("<Session/>")
    assert session_name(tmp_path) == "Untitled-1"


def test_prepare_session_refuses_existing_and_escapes(tmp_path, monkeypatch):
    from seion_ardour import runner
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "s.ardour").write_text("<Session/>", encoding="utf-8")
    monkeypatch.setattr(runner, "seed_dir", lambda _name: seed)
    monkeypatch.setenv("SEION_ARDOUR_WORKSPACE", str(workspace))
    target = workspace / "song" / "first"
    prepare_session(target)
    (target / "keep.txt").write_text("do not delete", encoding="utf-8")
    with pytest.raises(ArdourError, match="already exists"):
        prepare_session(target)
    assert (target / "keep.txt").read_text() == "do not delete"
    with pytest.raises(ArdourError, match="inside workspace"):
        prepare_session(tmp_path / "outside")


def test_slice_notes_includes_notes_spanning_boundary():
    notes = [(3.5, 1.5, 60, 90, 0), (11.5, 2.0, 62, 80, 0)]
    assert slice_notes(notes, 4, 12) == [
        (0, 1.0, 60, 90, 0), (7.5, 0.5, 62, 80, 0)
    ]


def test_bar_range_rejects_negative_inverted_and_invalid():
    for value in ("0-2", "10-2", "hi-3", "1-2-3"):
        with pytest.raises(ValueError):
            BarRange.parse(value)


def test_lua_job_rejects_unsafe_path(tmp_path):
    with pytest.raises(ValueError, match="unsafe"):
        write_job(tmp_path / "job.lua", tracks={}, bpm=158, length_beats=4,
                  export_dir=tmp_path / "bad]]path")



def test_resolve_surges_portable_uri_and_legacy_windows_path(tmp_path):
    patches = tmp_path / "patches_factory" / "Plucks"
    patches.mkdir(parents=True)
    patch = patches / "FM Pluck.fxp"
    patch.write_bytes(b"placeholder for path resolution only")
    kit = {"patches": {
        "arp": "surge://patches_factory/Plucks/FM Pluck.fxp",
        "lead": "C:/ProgramData/Surge XT/patches_factory/Plucks/FM Pluck.fxp",
    }, "master_gain_db": -4}
    resolved = resolve_kit_paths(kit, root=tmp_path)
    assert resolved["patches"]["arp"] == str(patch.resolve())
    assert resolved["patches"]["lead"] == str(patch.resolve())
    assert resolved["master_gain_db"] == -4


def test_resolve_surges_fails_closed_for_missing_and_escape(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing patch"):
        resolve_kit_paths({"patches": {"kick": "surge://missing.fxp"}}, root=tmp_path)
    with pytest.raises(ValueError, match="Unsafe"):
        resolve_kit_paths({"patches": {"kick": "surge://../outside.fxp"}}, root=tmp_path)
