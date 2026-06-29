"""Tool: generate a four-on-the-floor drum track."""

from __future__ import annotations

from app.music import generate_drum_track
from app.music.constants import BEATS_PER_BAR
from app.schemas import Track


def generate_drum_pattern(bars: int = 16, beats_per_bar: int = BEATS_PER_BAR) -> Track:
    return generate_drum_track(bars, beats_per_bar)
