"""MIDI export using mido.

Timing is stored in beats on the schema; here we convert to ticks (PPQ=480).
Per-track files are written for editing, plus a combined ``full_loop.mid``
(type 1) with a conductor track carrying tempo + time signature.
"""

from __future__ import annotations

from pathlib import Path

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

from app.exceptions import ExportError
from app.music.constants import GM_PROGRAMS, PPQ
from app.schemas import Track

DRUM_CHANNEL = 9  # MIDI channel 10 (0-indexed)


def _time_signature_parts(time_signature: str) -> tuple[int, int]:
    try:
        num, den = time_signature.split("/")
        return int(num), int(den)
    except Exception as exc:  # pragma: no cover - defensive
        raise ExportError(f"Invalid time signature: {time_signature!r}") from exc


def _track_event_tuples(track: Track) -> list[tuple[float, float, int, int]]:
    """Return (start_beat, duration_beats, midi, velocity) for any track type."""
    if track.is_drum or track.drum_events:
        return [(e.start_beat, e.duration_beats, e.midi, e.velocity) for e in track.drum_events]
    return [(n.start_beat, n.duration_beats, n.midi, n.velocity) for n in track.notes]


def _build_midi_track(
    track: Track,
    channel: int,
    ppq: int,
    *,
    tempo_bpm: int | None = None,
    time_signature: str | None = None,
) -> MidiTrack:
    midi_track = MidiTrack()
    midi_track.append(MetaMessage("track_name", name=track.name[:32], time=0))

    if tempo_bpm is not None:
        midi_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(tempo_bpm), time=0))
    if time_signature is not None:
        num, den = _time_signature_parts(time_signature)
        midi_track.append(
            MetaMessage("time_signature", numerator=num, denominator=den, time=0)
        )

    if channel != DRUM_CHANNEL:
        program = GM_PROGRAMS.get(track.role)
        if program is not None:
            midi_track.append(
                Message("program_change", program=program, channel=channel, time=0)
            )

    # Build an absolute-tick timeline, then convert to delta times. Sorting puts
    # note-offs before note-ons at the same tick so repeated pitches don't choke.
    timeline: list[tuple[int, int, int, int]] = []
    for start, duration, midi, velocity in _track_event_tuples(track):
        on_tick = int(round(start * ppq))
        off_tick = int(round((start + duration) * ppq))
        if off_tick <= on_tick:
            off_tick = on_tick + 1
        timeline.append((on_tick, 1, midi, velocity))
        timeline.append((off_tick, 0, midi, 0))
    timeline.sort(key=lambda item: (item[0], item[1]))

    prev_tick = 0
    for tick, is_on, midi, velocity in timeline:
        delta = tick - prev_tick
        prev_tick = tick
        msg = "note_on" if is_on else "note_off"
        midi_track.append(
            Message(msg, note=midi, velocity=velocity, channel=channel, time=delta)
        )

    return midi_track


def write_track_midi(
    path: str | Path,
    track: Track,
    bpm: int,
    time_signature: str = "4/4",
    ppq: int = PPQ,
) -> Path:
    """Write one track to its own .mid file (with tempo/time signature)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    channel = DRUM_CHANNEL if (track.is_drum or track.drum_events) else 0
    mid = MidiFile(ticks_per_beat=ppq)
    mid.tracks.append(
        _build_midi_track(
            track, channel, ppq, tempo_bpm=bpm, time_signature=time_signature
        )
    )
    mid.save(str(path))
    return path


def write_full_loop_midi(
    path: str | Path,
    tracks: list[Track],
    bpm: int,
    time_signature: str = "4/4",
    ppq: int = PPQ,
) -> Path:
    """Write all tracks into one type-1 MIDI file with a conductor track."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mid = MidiFile(ticks_per_beat=ppq)

    conductor = MidiTrack()
    conductor.append(MetaMessage("track_name", name="SEION full_loop", time=0))
    conductor.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))
    num, den = _time_signature_parts(time_signature)
    conductor.append(MetaMessage("time_signature", numerator=num, denominator=den, time=0))
    mid.tracks.append(conductor)

    next_channel = 0
    for track in tracks:
        if track.is_drum or track.drum_events:
            channel = DRUM_CHANNEL
        else:
            channel = next_channel
            next_channel += 1
            if next_channel == DRUM_CHANNEL:  # keep channel 10 for drums
                next_channel += 1
        mid.tracks.append(_build_midi_track(track, channel, ppq))

    mid.save(str(path))
    return path
