"""Offbeat root-note bass generator (warm melodic house / melodic techno)."""

from __future__ import annotations

from app.music.chords import chord_root_midi
from app.music.constants import BEATS_PER_BAR
from app.music.notes import midi_to_note_name
from app.music.rhythm import offbeat_eighths
from app.schemas import MixerHint, NoteEvent, Track


def generate_bass_track(
    progression: list[str],
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    octave: int = 2,
    base_velocity: int = 98,
    note_length: float = 0.45,
) -> Track:
    """Root notes on the off-beats, sitting between four-on-the-floor kicks.

    One bass note on each 'and' (0.5, 1.5, 2.5, 3.5) playing the current chord
    root in a low register (MIDI ~36-47). This is the classic offbeat pulse that
    drives house and melodic techno without crowding the kick.
    """
    notes: list[NoteEvent] = []
    offbeats = offbeat_eighths(beats_per_bar)
    for bar in range(bars):
        symbol = progression[bar % len(progression)]
        root_midi = chord_root_midi(symbol, octave)
        bar_offset = bar * beats_per_bar
        for i, pos in enumerate(offbeats):
            # Slight accent on the first off-beat of the bar for forward motion.
            velocity = base_velocity + (6 if i == 0 else 0)
            velocity = max(40, min(120, velocity))
            notes.append(
                NoteEvent(
                    pitch=midi_to_note_name(root_midi),
                    midi=root_midi,
                    start_beat=float(bar_offset + pos),
                    duration_beats=note_length,
                    velocity=velocity,
                )
            )

    return Track(
        id="track_bass",
        name="offbeat_root_bass",
        role="bass",
        instrument_hint="Mono synth bass (3xOSC sine/saw), low-pass, light saturation",
        mixer_hint=MixerHint(
            volume_db=-7.0,
            pan=0.0,
            effects=["low_pass", "saturation_light", "sidechain_to_kick"],
        ),
        notes=notes,
    )
