"""Chord voicings and the harmony-track generator."""

from __future__ import annotations

from app.music.chords import parse_chord_symbol
from app.music.constants import BEATS_PER_BAR
from app.music.notes import midi_to_note_name
from app.schemas import MixerHint, NoteEvent, Track


def warm_voicing(symbol: str, low: int = 48, high: int = 72) -> list[int]:
    """Root-position voicing placed in a warm register (default C3-C5).

    The root is placed in the lowest octave at or above ``low`` and the chord
    tones are stacked above it. For seventh chords this keeps everything in the
    48-72 band the brief asks for (warm but not muddy).
    """
    chord = parse_chord_symbol(symbol)
    root_midi = low + ((chord.root_pc - low) % 12)
    notes = [root_midi + iv for iv in chord.intervals]

    # Safety: if the stack overshoots the ceiling, drop it an octave when there
    # is room. (Our default seventh chords already fit, this just stays robust.)
    while notes and max(notes) > high and min(notes) - 12 >= low:
        notes = [n - 12 for n in notes]
    return notes


def generate_chord_track(
    progression: list[str],
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    low: int = 48,
    high: int = 72,
    base_velocity: int = 80,
) -> Track:
    """One sustained warm chord per bar, looping the progression across ``bars``.

    Warm seventh-chord voicings, held the full bar, velocity ~70-90.
    """
    notes: list[NoteEvent] = []
    for bar in range(bars):
        symbol = progression[bar % len(progression)]
        voicing = warm_voicing(symbol, low=low, high=high)
        start = bar * beats_per_bar
        # Slight per-bar velocity shape so it breathes without losing clarity.
        velocity = base_velocity + (4 if bar % 2 == 0 else -2)
        velocity = max(40, min(100, velocity))
        for midi in voicing:
            notes.append(
                NoteEvent(
                    pitch=midi_to_note_name(midi),
                    midi=midi,
                    start_beat=float(start),
                    duration_beats=float(beats_per_bar),
                    velocity=velocity,
                )
            )

    return Track(
        id="track_chords",
        name="warm_seventh_chords",
        role="harmony",
        instrument_hint="Warm FLEX pad or electric piano, low-pass, light sidechain",
        mixer_hint=MixerHint(
            volume_db=-10.0,
            pan=0.0,
            effects=["eq_low_cut", "reverb_medium", "sidechain_light"],
        ),
        notes=notes,
    )
