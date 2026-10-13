"""Seed MIDI files for the one-time Ardour seed session.

Ardour 9's headless Lua (ardour9-lua) can load sessions, edit MIDI region
content and export, but cannot create tracks (it crashes on Windows) nor import
MIDI (``Editor:do_import`` only exists in the GUI). So the GUI imports these
files once, producing one MIDI track + one long MIDI region per role. Every
render then copies that session and rewrites the region notes headlessly.

Each seed file carries the GM program for its role and two velocity-1 sentinel
notes that pin the region length to ``SEED_BARS``; the renderer deletes all
notes and shrinks the region to the song length.
"""

from __future__ import annotations

from pathlib import Path

from mido import Message, MetaMessage, MidiFile, MidiTrack

PPQ = 480
SEED_BARS = 256
DRUM_CHANNEL = 9

# role -> (channel, GM program or None for drums). Mirrors app.music.constants
# on purpose without importing it: connectors only talk to SEION through files.
SEED_ROLES: dict[str, tuple[int, int | None]] = {
    "drums": (DRUM_CHANNEL, None),
    "latin_perc": (DRUM_CHANNEL, None),  # congas / guiro / cowbell live in the GM kit
    "bass": (1, 38),  # Synth Bass 1
    "chords": (0, 88),  # Pad 1 (new age), as in project 001's chords.mid
    "arp": (2, 81),  # Lead 2 (sawtooth)
    "lead": (3, 21),  # Accordion: the cumbia voice
    # Seed v2 only: kick split out of the drum part so it can get its own synth + distortion.
    "kick": (0, None),
}


def write_seed_file(path: Path, role: str, channel: int, program: int | None) -> Path:
    track = MidiTrack()
    track.append(MetaMessage("track_name", name=role, time=0))
    if program is not None:
        track.append(Message("program_change", program=program, channel=channel, time=0))
    last_tick = SEED_BARS * 4 * PPQ
    track.append(Message("note_on", note=60, velocity=1, channel=channel, time=0))
    track.append(Message("note_off", note=60, velocity=0, channel=channel, time=PPQ // 4))
    track.append(
        Message("note_on", note=60, velocity=1, channel=channel, time=last_tick - PPQ // 2)
    )
    track.append(Message("note_off", note=60, velocity=0, channel=channel, time=PPQ // 4))
    mid = MidiFile(ticks_per_beat=PPQ)
    mid.tracks.append(track)
    path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(path))
    return path


def write_seed_files(out_dir: Path) -> list[Path]:
    return [
        write_seed_file(out_dir / f"{role}.mid", role, channel, program)
        for role, (channel, program) in SEED_ROLES.items()
    ]


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[2] / "seed"
    for p in write_seed_files(target):
        print(p)
