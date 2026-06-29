"""Optional sparse melody generator (chord tones).

Not part of the default MVP loop — the brief says identity comes from groove and
harmony first, so a lead is left out until you want one. Exposed here so a future
Composer Agent / variation can add a tasteful, in-key lead on request.
"""

from __future__ import annotations

from app.music.chords import chord_notes
from app.music.constants import BEATS_PER_BAR
from app.music.notes import midi_to_note_name
from app.schemas import MixerHint, NoteEvent, Track

# One sustained chord tone per half bar, picking the 3rd then the 5th — sparse
# and singable rather than busy.
_DEGREE_CYCLE = [1, 2]


def generate_melody_track(
    progression: list[str],
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    octave: int = 5,
    base_velocity: int = 70,
) -> Track:
    notes: list[NoteEvent] = []
    half_bar = beats_per_bar / 2
    for bar in range(bars):
        symbol = progression[bar % len(progression)]
        tones = chord_notes(symbol, root_octave=octave)
        bar_offset = bar * beats_per_bar
        for half in range(2):
            degree = _DEGREE_CYCLE[half % len(_DEGREE_CYCLE)] % len(tones)
            midi = tones[degree]
            notes.append(
                NoteEvent(
                    pitch=midi_to_note_name(midi),
                    midi=midi,
                    start_beat=float(bar_offset + half * half_bar),
                    duration_beats=half_bar * 0.9,
                    velocity=base_velocity,
                )
            )

    return Track(
        id="track_melody",
        name="sparse_chord_tone_lead",
        role="melody",
        instrument_hint="Soft analog lead, mono-ish, gentle reverb",
        mixer_hint=MixerHint(volume_db=-13.0, pan=-0.1, effects=["reverb_medium"]),
        notes=notes,
    )
