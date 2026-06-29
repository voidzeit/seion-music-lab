"""Tool: export a MusicalIdea to per-track MIDI + a combined full_loop.mid."""

from __future__ import annotations

from pathlib import Path

from app.export.midi_writer import write_full_loop_midi, write_track_midi
from app.schemas import MusicalIdea

# Friendly filenames per role; anything else falls back to '<role>.mid'.
ROLE_TO_FILENAME = {
    "harmony": "chords.mid",
    "pad": "chords.mid",
    "bass": "bass.mid",
    "arp": "arp.mid",
    "drums": "drums.mid",
    "melody": "melody.mid",
    "lead": "lead.mid",
}


def export_idea_midi(idea: MusicalIdea, project_dir: str | Path) -> dict[str, str]:
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, str] = {}
    for track in idea.tracks:
        filename = ROLE_TO_FILENAME.get(track.role, f"{track.role}.mid")
        out = write_track_midi(project_dir / filename, track, idea.bpm, idea.time_signature)
        paths[track.role] = str(out)

    full = write_full_loop_midi(
        project_dir / "full_loop.mid", idea.tracks, idea.bpm, idea.time_signature
    )
    paths["full_loop"] = str(full)
    return paths
