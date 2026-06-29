"""Chord construction and chord-symbol parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.exceptions import MusicTheoryError
from app.music.constants import LETTER_PITCH_CLASS, NOTE_NAMES_SHARP

# Quality -> intervals (semitones from root).
CHORD_INTERVALS: dict[str, list[int]] = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "min7b5": [0, 3, 6, 10],
    "dim7": [0, 3, 6, 9],
    "maj6": [0, 4, 7, 9],
    "min6": [0, 3, 7, 9],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "add9": [0, 4, 7, 14],
}

# Chord-symbol suffix -> canonical quality.
_SUFFIX_TO_QUALITY: dict[str, str] = {
    "": "maj",
    "maj": "maj",
    "major": "maj",
    "M": "maj",
    "m": "min",
    "min": "min",
    "minor": "min",
    "-": "min",
    "dim": "dim",
    "o": "dim",
    "aug": "aug",
    "+": "aug",
    "maj7": "maj7",
    "M7": "maj7",
    "min7": "min7",
    "m7": "min7",
    "-7": "min7",
    "7": "dom7",
    "dom7": "dom7",
    "9": "dom7",       # simplified to a dominant 7 for the MVP
    "6": "maj6",
    "maj6": "maj6",
    "m6": "min6",
    "min6": "min6",
    "m7b5": "min7b5",
    "min7b5": "min7b5",
    "dim7": "dim7",
    "o7": "dim7",
    "sus2": "sus2",
    "sus4": "sus4",
    "sus": "sus4",
    "add9": "add9",
}

_CHORD_RE = re.compile(r"^([A-Ga-g])([#b]?)(.*)$")


@dataclass
class Chord:
    """A parsed chord: its symbol, root and interval structure."""

    symbol: str
    root_pc: int
    root_name: str
    quality: str
    intervals: list[int] = field(default_factory=list)

    @property
    def pitch_classes(self) -> list[int]:
        return [(self.root_pc + iv) % 12 for iv in self.intervals]


def parse_chord_symbol(symbol: str) -> Chord:
    """'Am7' -> Chord(root A, min7), 'Fmaj7', 'G6', 'Cmaj7', 'Bbm7b5', ..."""
    match = _CHORD_RE.match(symbol.strip())
    if not match:
        raise MusicTheoryError(f"Invalid chord symbol: {symbol!r}")
    letter, accidental, suffix = match.groups()
    root_pc = LETTER_PITCH_CLASS[letter.upper()]
    if accidental == "#":
        root_pc += 1
    elif accidental == "b":
        root_pc -= 1
    root_pc %= 12

    quality = _SUFFIX_TO_QUALITY.get(suffix)
    if quality is None:
        raise MusicTheoryError(
            f"Unsupported chord quality in symbol {symbol!r} (suffix {suffix!r})"
        )
    return Chord(
        symbol=symbol,
        root_pc=root_pc,
        root_name=NOTE_NAMES_SHARP[root_pc],
        quality=quality,
        intervals=list(CHORD_INTERVALS[quality]),
    )


def chord_notes(symbol: str, root_octave: int = 3) -> list[int]:
    """Root-position MIDI notes of a chord at the given root octave.

    'Am7', root_octave=3 -> [57, 60, 64, 67] (A3, C4, E4, G4).
    """
    chord = parse_chord_symbol(symbol)
    root_midi = (root_octave + 1) * 12 + chord.root_pc
    return [root_midi + iv for iv in chord.intervals]


def chord_root_midi(symbol: str, octave: int) -> int:
    """MIDI number of the chord root at a given octave (e.g. for the bass)."""
    chord = parse_chord_symbol(symbol)
    return (octave + 1) * 12 + chord.root_pc
