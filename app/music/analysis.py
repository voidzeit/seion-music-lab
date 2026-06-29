"""Read-only analysis helpers used by the SEION scorer and the critic.

These functions never mutate the idea; they just measure it.
"""

from __future__ import annotations

from app.music.chords import parse_chord_symbol
from app.music.constants import BEATS_PER_BAR
from app.music.scales import scale_pitch_classes
from app.schemas import MusicalIdea, Track


def all_melodic_notes(idea: MusicalIdea) -> list:
    notes = []
    for track in idea.melodic_tracks():
        notes.extend(track.notes)
    return notes


def total_melodic_note_count(idea: MusicalIdea) -> int:
    return len(all_melodic_notes(idea))


def notes_per_bar(idea: MusicalIdea) -> float:
    bars = max(1, idea.bars)
    return total_melodic_note_count(idea) / bars


def in_scale_ratio(idea: MusicalIdea, key: str) -> float:
    """Fraction of melodic notes whose pitch class is diatonic to the key."""
    notes = all_melodic_notes(idea)
    if not notes:
        return 0.0
    pcs = set(scale_pitch_classes(key))
    in_scale = sum(1 for n in notes if n.midi % 12 in pcs)
    return in_scale / len(notes)


def bass_follows_roots_ratio(
    idea: MusicalIdea,
    progression: list[str],
    beats_per_bar: int = BEATS_PER_BAR,
) -> float:
    """Fraction of bass notes that play the root of their bar's chord."""
    bass = idea.track_by_role("bass")
    if bass is None or not bass.notes or not progression:
        return 0.0
    matches = 0
    for note in bass.notes:
        bar = int(note.start_beat // beats_per_bar)
        symbol = progression[bar % len(progression)]
        root_pc = parse_chord_symbol(symbol).root_pc
        if note.midi % 12 == root_pc:
            matches += 1
    return matches / len(bass.notes)


def unique_pitch_classes(track: Track) -> int:
    return len({n.midi % 12 for n in track.notes})


def role_set(idea: MusicalIdea) -> set[str]:
    return {t.role for t in idea.tracks}


def has_harmony(idea: MusicalIdea) -> bool:
    return idea.track_by_role("harmony") is not None or idea.track_by_role("pad") is not None


def has_bass(idea: MusicalIdea) -> bool:
    return idea.track_by_role("bass") is not None


def has_rhythm(idea: MusicalIdea) -> bool:
    return any(t.is_drum and t.drum_events for t in idea.tracks)


def uses_seventh_or_sixth_chords(progression: list[str]) -> bool:
    sevenths = {"maj7", "min7", "dom7", "min7b5", "dim7", "maj6", "min6"}
    try:
        return any(parse_chord_symbol(s).quality in sevenths for s in progression)
    except Exception:
        return False
