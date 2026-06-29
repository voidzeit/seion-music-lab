"""Note <-> MIDI conversion.

Convention: MIDI 60 == C4 (middle C), so A4 == 69 == 440 Hz and A3 == 57.
"""

from __future__ import annotations

import re

from app.exceptions import MusicTheoryError
from app.music.constants import LETTER_PITCH_CLASS, NOTE_NAMES_SHARP

_NOTE_RE = re.compile(r"^([A-Ga-g])([#b]*)(-?\d+)$")


def note_name_to_midi(name: str) -> int:
    """'A3' -> 57, 'C4' -> 60, 'Bb2' -> 46."""
    match = _NOTE_RE.match(name.strip())
    if not match:
        raise MusicTheoryError(f"Invalid note name: {name!r}")
    letter, accidentals, octave_str = match.groups()
    pc = LETTER_PITCH_CLASS[letter.upper()]
    for acc in accidentals:
        pc += 1 if acc == "#" else -1
    octave = int(octave_str)
    midi = (octave + 1) * 12 + pc
    if not 0 <= midi <= 127:
        raise MusicTheoryError(f"Note {name!r} is out of MIDI range (0-127): {midi}")
    return midi


def midi_to_note_name(midi: int) -> str:
    """57 -> 'A3', 60 -> 'C4'."""
    if not 0 <= midi <= 127:
        raise MusicTheoryError(f"MIDI note out of range 0-127: {midi}")
    octave = midi // 12 - 1
    pc = midi % 12
    return f"{NOTE_NAMES_SHARP[pc]}{octave}"


def pitch_class(name_or_midi: str | int) -> int:
    """Return the pitch class (0-11) of a note name or MIDI number."""
    if isinstance(name_or_midi, int):
        return name_or_midi % 12
    return note_name_to_midi(name_or_midi) % 12


def transpose(midi: int, semitones: int) -> int:
    result = midi + semitones
    if not 0 <= result <= 127:
        raise MusicTheoryError(f"Transposed note out of range: {result}")
    return result
