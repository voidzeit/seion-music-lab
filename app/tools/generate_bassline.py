"""Tool: generate a bassline that follows a chord progression."""

from __future__ import annotations

from app.music import generate_bass_track
from app.music.constants import BEATS_PER_BAR, DEFAULT_PROGRESSION
from app.schemas import Track


def generate_bassline(
    progression: list[str] | None = None,
    bars: int = 16,
    beats_per_bar: int = BEATS_PER_BAR,
) -> Track:
    return generate_bass_track(progression or DEFAULT_PROGRESSION, bars, beats_per_bar)
