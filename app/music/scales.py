"""Scales and keys."""

from __future__ import annotations

from app.exceptions import MusicTheoryError
from app.music.constants import LETTER_PITCH_CLASS

# Interval patterns (semitones from the tonic).
SCALE_STEPS: dict[str, list[int]] = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],          # natural minor
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
}

_MODE_ALIASES = {
    "maj": "major",
    "major": "major",
    "ionian": "major",
    "min": "minor",
    "minor": "minor",
    "m": "minor",
    "aeolian": "minor",
    "natural_minor": "minor",
    "harmonic_minor": "harmonic_minor",
    "dorian": "dorian",
    "phrygian": "phrygian",
}


def parse_key(key: str) -> tuple[int, str]:
    """'A minor' -> (9, 'minor'), 'C major' -> (0, 'major'), 'F# minor' -> (6, 'minor')."""
    parts = key.strip().split()
    if not parts:
        raise MusicTheoryError(f"Empty key: {key!r}")

    root_token = parts[0]
    letter = root_token[0].upper()
    if letter not in LETTER_PITCH_CLASS:
        raise MusicTheoryError(f"Invalid key root: {root_token!r}")
    pc = LETTER_PITCH_CLASS[letter]
    for acc in root_token[1:]:
        if acc == "#":
            pc += 1
        elif acc.lower() == "b":
            pc -= 1
        else:
            raise MusicTheoryError(f"Invalid accidental in key: {root_token!r}")

    mode_token = (parts[1] if len(parts) > 1 else "major").lower()
    mode = _MODE_ALIASES.get(mode_token)
    if mode is None:
        raise MusicTheoryError(f"Unknown mode: {mode_token!r}")
    return pc % 12, mode


def scale_pitch_classes(key: str) -> list[int]:
    """Sorted set of pitch classes (0-11) belonging to the key."""
    root_pc, mode = parse_key(key)
    steps = SCALE_STEPS[mode]
    return sorted({(root_pc + step) % 12 for step in steps})


def is_in_scale(midi: int, key: str) -> bool:
    return midi % 12 in scale_pitch_classes(key)


def degree_in_scale(midi: int, key: str) -> int | None:
    """Return the scale degree (1-based) of a note, or None if non-diatonic."""
    pcs = scale_pitch_classes(key)
    pc = midi % 12
    return pcs.index(pc) + 1 if pc in pcs else None
