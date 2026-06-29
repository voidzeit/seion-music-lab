"""Hypnotic chord-tone arpeggio generator (NTO / melodic techno flavour)."""

from __future__ import annotations

from app.music.chords import chord_notes
from app.music.constants import BEATS_PER_BAR
from app.music.notes import midi_to_note_name
from app.schemas import MixerHint, NoteEvent, Track

# A short up-then-down contour over the four chord tones. Repeating a small
# motif like this (rather than a long melody) is what makes an arp feel
# hypnotic. Indices reference the chord's tones low->high.
HYPNOTIC_CONTOUR = [0, 1, 2, 3, 2, 1, 0, 1]


def generate_arp_track(
    progression: list[str],
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    octave: int = 4,
    base_velocity: int = 76,
    step_beats: float = 0.5,
    contour: list[int] | None = None,
) -> Track:
    """Eighth-note arpeggio using only chord tones, repeating a short motif.

    Low density (one motif per bar, chord tones only) keeps it hypnotic and
    easy to edit. A slowly opening filter (see automation) supplies the tension
    rather than adding more notes.
    """
    contour = contour or HYPNOTIC_CONTOUR
    notes: list[NoteEvent] = []
    steps_per_bar = int(beats_per_bar / step_beats)

    for bar in range(bars):
        symbol = progression[bar % len(progression)]
        tones = chord_notes(symbol, root_octave=octave)
        bar_offset = bar * beats_per_bar
        for step in range(steps_per_bar):
            idx = contour[step % len(contour)] % len(tones)
            midi = tones[idx]
            start = bar_offset + step * step_beats
            # Gentle accent on the down-beats to imply a pulse.
            on_beat = abs((step * step_beats) % 1.0) < 1e-6
            velocity = base_velocity + (8 if on_beat else 0)
            velocity = max(40, min(110, velocity))
            notes.append(
                NoteEvent(
                    pitch=midi_to_note_name(midi),
                    midi=midi,
                    start_beat=float(start),
                    duration_beats=step_beats * 0.9,  # slightly detached
                    velocity=velocity,
                )
            )

    return Track(
        id="track_arp",
        name="hypnotic_chord_arp",
        role="arp",
        instrument_hint="Analog pluck, delay + reverb, slowly opening low-pass filter",
        mixer_hint=MixerHint(
            volume_db=-12.0,
            pan=0.15,
            effects=["delay_1_8", "reverb_large", "auto_filter"],
        ),
        notes=notes,
    )
