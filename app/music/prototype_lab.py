"""Original, deterministic 16-bar A/B/C experiments for SEION Project 001.

This is NOT a transcription. No reference audio, copyrighted melody or artist
preset is embedded. The three prototypes share harmony but differ in rhythmic
architecture, voicing, density and phrasing. Output is MIDI, not finished audio.

Usage:
    python -m app.music.prototype_lab --out projects/cumbia-de-los-monjes-rave/versions/v002
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

BPM = 158
BARS = 16
PPQ = 480
MODES = ("groove", "trance_bounce", "hardcore_hybrid")
ROLES = ("kick", "drums", "percussion", "bass", "chords", "arp", "lead")
CHANNELS = {"kick": 9, "drums": 9, "percussion": 9, "bass": 0,
            "chords": 1, "arp": 2, "lead": 3}
# A measured candidate loop from the original reference (not a transcription).
# F# major introduces A# and gives a Dorian colour against C# minor.
HARMONY = (
    {"name": "C#m", "root": 37, "notes": (61, 64, 68)},
    {"name": "B", "root": 35, "notes": (59, 63, 66)},
    {"name": "B", "root": 35, "notes": (59, 63, 66)},
    {"name": "F#", "root": 42, "notes": (54, 58, 61)},
)

@dataclass(frozen=True)
class Event:
    start: float
    duration: float
    pitch: int
    velocity: int
    channel: int

def make_patterns(mode: str, *, seed: int = 1001, bars: int = BARS) -> dict[str, list[Event]]:
    """Create distinct, original MIDI for one sound-design experiment."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if bars < 4 or bars % 4:
        raise ValueError("bars must be a positive multiple of four, at least four")

    rng = random.Random(seed)
    result: dict[str, list[Event]] = {role: [] for role in ROLES}

    def add(role: str, bar: int, beat: float, duration: float, pitch: int,
            velocity: int, variation: int = 0) -> None:
        tick = bar * 4 + beat
        if tick < 0 or tick + duration > bars * 4 + 1e-9:
            raise ValueError("event outside arrangement")
        v = max(1, min(127, velocity + (rng.randint(-variation, variation) if variation else 0)))
        result[role].append(Event(tick, duration, pitch, v, CHANNELS[role]))

    for bar in range(bars):
        chord = HARMONY[bar % len(HARMONY)]
        root = chord["root"]
        pitches = chord["notes"]
        end_phrase = bar % 4 == 3

        # Every mode has a different low-end strategy; none stack three competing basses.
        kick_beats = (0, 1, 2, 3)
        if mode == "hardcore_hybrid" and end_phrase:
            kick_beats += (3.5, 3.75)
        for beat in kick_beats:
            add("kick", bar, beat, 0.19 if mode != "hardcore_hybrid" else 0.24,
                36, 115 if mode == "hardcore_hybrid" else 106, 4)

        for beat in (1, 3):
            add("drums", bar, beat, 0.12, 39, 95 if mode != "groove" else 84, 3)
        if mode == "groove":
            hat_beats = (0.5, 1.5, 2.5, 3.5)
            perc_beats = (0.75, 1.5, 2.75, 3.5)
        elif mode == "trance_bounce":
            hat_beats = tuple(i / 2 for i in range(8))
            perc_beats = (1.75, 3.75)
        else:
            hat_beats = (0.5, 1.5, 2.5, 3.5)
            perc_beats = (2.75,)
        for i, beat in enumerate(hat_beats):
            add("drums", bar, beat, 0.08, 42, 58 + (8 if i % 2 else 0), 6)
        for i, beat in enumerate(perc_beats):
            add("percussion", bar, beat, 0.12, (64, 67, 56)[i % 3], 74, 8)
        if end_phrase:
            add("drums", bar, 3.75, 0.08, 46, 77, 4)

        if mode == "groove":
            bass_beats = (0.75, 1.75, 2.75, 3.5)
            bass_length = 0.38
        elif mode == "trance_bounce":
            bass_beats = (0.5, 1.5, 2.5, 3.5)
            bass_length = 0.28
        else:
            bass_beats = (0.5, 2.5)
            bass_length = 0.55
        for i, beat in enumerate(bass_beats):
            add("bass", bar, beat, bass_length,
                root + (12 if mode == "trance_bounce" and i == 3 else 0), 94, 5)

        if mode == "groove":
            # Stabs leave space for the percussion.
            for beat in (0.0, 2.5):
                for pitch in pitches:
                    add("chords", bar, beat, 0.30, pitch, 64, 4)
        elif mode == "trance_bounce":
            for pitch in pitches:
                add("chords", bar, 0, 3.5, pitch + 12, 76, 3)
        elif bar % 4 in (0, 2):
            for pitch in pitches:
                add("chords", bar, 0, 1.5, pitch + 12, 65, 2)

        if mode == "trance_bounce":
            arp_beats = tuple(i / 2 for i in range(8))
        elif mode == "groove":
            arp_beats = (0.5, 1.5, 3.0) if bar >= 8 else ()
        else:
            arp_beats = (1.0, 2.0, 3.0) if bar >= 4 and bar % 4 != 3 else ()
        for i, beat in enumerate(arp_beats):
            add("arp", bar, beat, 0.20 if mode != "trance_bounce" else 0.34,
                pitches[(i + bar) % 3] + 12, 72, 5)

        # A newly composed four-note gesture, NOT a source-song transcription.
        # First 4 bars are instrumental to make the entrance meaningful.
        if bar >= 4 and bar % 4 in (0, 2):
            motif = (73, 71, 68, 66)
            times = (0.0, 0.75, 2.0, 2.75) if mode == "groove" else (
                (0.0, 0.5, 1.5, 2.5) if mode == "trance_bounce" else (0.0, 1.0, 2.5, 3.0)
            )
            for i, beat in enumerate(times):
                add("lead", bar, beat, 0.35 if mode != "hardcore_hybrid" else 0.18,
                    motif[i] + (12 if mode == "trance_bounce" else 0), 78, 4)

    return result


def write_midi(path: Path, tracks: dict[str, list[Event]], *, bpm: int = BPM,
               bars: int = BARS) -> None:
    """Type-1 MIDI with explicit conductor and independent editable tracks."""
    midi = MidiFile(type=1, ticks_per_beat=PPQ)
    conductor = MidiTrack()
    conductor.append(MetaMessage("track_name", name="Conductor", time=0))
    conductor.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))
    conductor.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    conductor.append(MetaMessage("end_of_track", time=bars * 4 * PPQ))
    midi.tracks.append(conductor)
    for role, events in tracks.items():
        lane = MidiTrack()
        lane.append(MetaMessage("track_name", name=role, time=0))
        messages: list[tuple[int, int, Message]] = []
        for n in events:
            if not (0 <= n.pitch <= 127 and 1 <= n.velocity <= 127):
                raise ValueError("invalid MIDI note")
            start = round(n.start * PPQ)
            end = round((n.start + n.duration) * PPQ)
            if end <= start:
                raise ValueError("invalid note duration")
            messages.append((start, 1, Message("note_on", channel=n.channel,
                                               note=n.pitch, velocity=n.velocity)))
            messages.append((end, 0, Message("note_off", channel=n.channel,
                                             note=n.pitch, velocity=0)))
        last = 0
        for tick, priority, msg in sorted(messages, key=lambda item: (item[0], item[1])):
            if tick < last:
                raise ValueError("non-monotonic MIDI")
            lane.append(msg.copy(time=tick - last))
            last = tick
        lane.append(MetaMessage("end_of_track", time=max(0, bars * 4 * PPQ - last)))
        midi.tracks.append(lane)
    path.parent.mkdir(parents=True, exist_ok=True)
    midi.save(path)


def build_experiments(out: Path, *, seed: int = 1001) -> dict:
    """Write three independent versions; refuse to overwrite previous takes."""
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing experiment folder: {out}")
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.0",
        "project_id": "seion-001-cumbia-de-los-monjes",
        "version": "v002",
        "status": "symbolic_prototype_unheard",
        "bpm": BPM,
        "key": "C# minor (Dorian F# major chord tested intentionally)",
        "bars": BARS,
        "duration_seconds": round(BARS * 4 * 60 / BPM, 3),
        "seed": seed,
        "source_audio_included": False,
        "source_melody_transcribed": False,
        "references": "reference/reference_fingerprint.json (candidate harmony only)",
        "quality_gate": "listening_required",
        "experiments": {},
    }
    for mode in MODES:
        tracks = make_patterns(mode, seed=seed)
        folder = out / "prototypes" / mode
        for role, events in tracks.items():
            write_midi(folder / f"{role}.mid", {role: events})
        write_midi(folder / "full.mid", tracks)
        manifest["experiments"][mode] = {
            "midi_folder": f"prototypes/{mode}",
            "midi_files": {role: f"prototypes/{mode}/{role}.mid" for role in ROLES},
            "full_midi": f"prototypes/{mode}/full.mid",
            "note_counts": {role: len(events) for role, events in tracks.items()},
            "sound_design_status": "unassigned",
        }
    (out / "prototype_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New, empty output directory")
    parser.add_argument("--seed", type=int, default=1001)
    args = parser.parse_args(argv)
    manifest = build_experiments(args.out, seed=args.seed)
    print(f"Generated {len(manifest['experiments'])} experiments at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
