"""Turn per-role .mid files into a render job for render_job.lua.

The job is a Lua file (``return { ... }``) so ardour9-lua can ``dofile`` it
without a JSON parser. Notes are expressed in quarter-note beats.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import mido

Note = tuple[float, float, int, int, int]  # start_beats, length_beats, note, velocity, channel


@dataclass(frozen=True)
class BarRange:
    """1-based inclusive bar range, e.g. 65-96 for a 32-bar drop."""

    first: int
    last: int

    @classmethod
    def parse(cls, text: str) -> BarRange:
        a, b = text.split("-")
        return cls(int(a), int(b))

    def beats(self, beats_per_bar: int = 4) -> tuple[float, float]:
        return (self.first - 1) * beats_per_bar, self.last * beats_per_bar


def read_notes(path: Path) -> tuple[list[Note], float | None]:
    """Return all notes in the file plus the first tempo found (BPM)."""
    mid = mido.MidiFile(str(path))
    ppq = mid.ticks_per_beat
    notes: list[Note] = []
    bpm: float | None = None
    for track in mid.tracks:
        tick = 0
        open_notes: dict[tuple[int, int], deque[tuple[int, int]]] = defaultdict(deque)
        for msg in track:
            tick += msg.time
            if msg.type == "set_tempo" and bpm is None:
                bpm = mido.tempo2bpm(msg.tempo)
            elif msg.type == "note_on" and msg.velocity > 0:
                open_notes[(msg.channel, msg.note)].append((tick, msg.velocity))
            elif msg.type in ("note_off", "note_on"):
                queue = open_notes.get((msg.channel, msg.note))
                if queue:
                    start, velocity = queue.popleft()
                    length = max(tick - start, 1)
                    notes.append((start / ppq, length / ppq, msg.note, velocity, msg.channel))
    notes.sort()
    return notes, bpm


def slice_notes(notes: list[Note], start: float, end: float) -> list[Note]:
    """Keep notes starting inside [start, end), shifted to 0 and clipped at end."""
    out = []
    for s, length, note, vel, ch in notes:
        if start <= s < end:
            out.append((s - start, min(length, end - s), note, vel, ch))
    return out


def split_role(
    tracks: dict[str, list[Note]], new_role: str, source: str, pitches: set[int]
) -> dict[str, list[Note]]:
    """Move notes with ``pitches`` from ``source`` into ``new_role`` (e.g. kick out of drums)."""
    if source not in tracks:
        return tracks
    out = dict(tracks)
    out[new_role] = [n for n in tracks[source] if n[2] in pitches]
    out[source] = [n for n in tracks[source] if n[2] not in pitches]
    return out


def _lua_notes(notes: list[Note]) -> str:
    return ",".join(f"{{{s:.6f},{length:.6f},{n},{v},{c}}}" for s, length, n, v, c in notes)


def write_job(
    path: Path,
    *,
    tracks: dict[str, list[Note]],
    bpm: float,
    length_beats: float,
    export_dir: Path,
    stems: bool = True,
    tail_seconds: float = 2.0,
    preroll_beats: float = 4.0,
    gains_db: dict[str, float] | None = None,
    master_gain_db: float = 0.0,
    master_highpass_hz: float = 25.0,
) -> Path:
    """``preroll_beats`` of silence precede the music and are not exported, so
    synth start-up transients (e.g. Surge loading a patch) stay out of the WAV."""
    gains = ",".join(f'["{r}"] = {g:.2f}' for r, g in (gains_db or {}).items())
    lines = [
        "return {",
        f"  bpm = {bpm:.4f},",
        f"  length_beats = {length_beats:.6f},",
        f"  preroll_beats = {preroll_beats:.6f},",
        f"  tail_seconds = {tail_seconds:.3f},",
        f"  export_dir = [[{export_dir}]],",
        f"  stems = {'true' if stems else 'false'},",
        f"  gains_db = {{{gains}}},",
        f"  master_gain_db = {master_gain_db:.2f},",
        f"  master_highpass_hz = {master_highpass_hz:.1f},",
        "  tracks = {",
    ]
    for role, notes in tracks.items():
        lines.append(f'    ["{role}"] = {{{_lua_notes(notes)}}},')
    lines += ["  },", "}", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
