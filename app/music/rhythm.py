"""Rhythm grids and timing helpers (in beats)."""

from __future__ import annotations

from app.music.constants import BEATS_PER_BAR


def downbeats(beats_per_bar: int = BEATS_PER_BAR) -> list[float]:
    """Quarter-note positions: [0, 1, 2, 3] for 4/4."""
    return [float(b) for b in range(beats_per_bar)]


def offbeat_eighths(beats_per_bar: int = BEATS_PER_BAR) -> list[float]:
    """The 'and' of each beat: [0.5, 1.5, 2.5, 3.5] for 4/4."""
    return [b + 0.5 for b in range(beats_per_bar)]


def eighth_grid(beats_per_bar: int = BEATS_PER_BAR) -> list[float]:
    """All eighth-note positions in a bar."""
    return [i * 0.5 for i in range(beats_per_bar * 2)]


def sixteenth_grid(beats_per_bar: int = BEATS_PER_BAR) -> list[float]:
    """All sixteenth-note positions in a bar."""
    return [i * 0.25 for i in range(beats_per_bar * 4)]


def bar_start(bar_index: int, beats_per_bar: int = BEATS_PER_BAR) -> float:
    """Beat position of the start of a (0-indexed) bar."""
    return float(bar_index * beats_per_bar)
