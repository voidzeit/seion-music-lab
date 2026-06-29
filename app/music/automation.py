"""Automation generators. The signature SEION move: tension from timbre."""

from __future__ import annotations

from app.music.constants import BEATS_PER_BAR
from app.schemas import AutomationEvent


def filter_open_automation(
    target_track: str,
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    start_value: float = 0.25,
    end_value: float = 0.72,
) -> AutomationEvent:
    """A slowly opening low-pass filter across the whole loop.

    This is how NTO-style melodic techno builds tension: the notes repeat while
    the timbre evolves. It also gives the otherwise-steady loop a rising shape.
    """
    return AutomationEvent(
        target_track=target_track,
        param="filter_cutoff",
        start_beat=0.0,
        end_beat=float(bars * beats_per_bar),
        start_value=start_value,
        end_value=end_value,
        curve="exp",
        description=(
            "Open the arp's low-pass filter slowly over the full loop so tension "
            "comes from the evolving timbre, not from extra notes."
        ),
    )
