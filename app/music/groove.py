"""Groove helpers: swing and gentle, deterministic humanisation.

Humanisation is seeded so generation stays reproducible (important for tests).
"""

from __future__ import annotations

import random


def apply_swing(beat: float, amount: float = 0.0, subdivision: float = 0.5) -> float:
    """Delay off-grid subdivisions to create swing.

    ``amount`` is 0..1 where ~0.6 is a noticeable shuffle. Only positions that
    fall on the 'off' subdivision are nudged later.
    """
    if amount <= 0:
        return beat
    position_in_sub = round(beat / subdivision) % 2
    if position_in_sub == 1:  # the off-subdivision
        return beat + subdivision * amount * 0.5
    return beat


def humanize_velocity(velocity: int, jitter: int, seed: int) -> int:
    """Deterministically nudge a velocity within +/- jitter, clamped to 1-127."""
    if jitter <= 0:
        return velocity
    rng = random.Random(seed)
    value = velocity + rng.randint(-jitter, jitter)
    return max(1, min(127, value))


def humanize_timing(beat: float, jitter_beats: float, seed: int) -> float:
    """Deterministically nudge timing by up to +/- jitter_beats (never below 0)."""
    if jitter_beats <= 0:
        return beat
    rng = random.Random(seed)
    return max(0.0, beat + rng.uniform(-jitter_beats, jitter_beats))
