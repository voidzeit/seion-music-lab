"""Tool: generate a harmony (chord) track."""

from __future__ import annotations

from app.music import generate_chord_track
from app.music.constants import BEATS_PER_BAR, DEFAULT_PROGRESSION
from app.schemas import Track


def generate_chord_progression(
    progression: list[str] | None = None,
    bars: int = 16,
    beats_per_bar: int = BEATS_PER_BAR,
) -> Track:
    return generate_chord_track(progression or DEFAULT_PROGRESSION, bars, beats_per_bar)
