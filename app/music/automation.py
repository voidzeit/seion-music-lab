"""Automation generators. The signature SEION move: tension from timbre."""

from __future__ import annotations

from app.music.constants import BEATS_PER_BAR
from app.schemas import AutomationEvent, Section


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


def section_filter_automation(
    target_track: str,
    sections: list[Section],
    beats_per_bar: int = BEATS_PER_BAR,
) -> list[AutomationEvent]:
    """One filter ramp per section, tracking that section's energy.

    The cutoff follows the arrangement: low in the intro, climbing through the
    build, dipping in the break, wide open in the drop. This is what makes the
    timbre move *with* the structure instead of one flat sweep.
    """
    events: list[AutomationEvent] = []
    prev_value = sections[0].energy if sections else 0.25
    for sec in sections:
        start_beat = float((sec.start_bar - 1) * beats_per_bar)
        end_beat = float((sec.start_bar - 1 + sec.length_bars) * beats_per_bar)
        # Map energy (0-1) to a musical cutoff range (0.2 closed .. 0.95 open).
        target_value = round(0.2 + 0.75 * sec.energy, 3)
        events.append(
            AutomationEvent(
                target_track=target_track,
                param="filter_cutoff",
                start_beat=start_beat,
                end_beat=end_beat,
                start_value=round(prev_value, 3),
                end_value=target_value,
                curve="exp",
                description=(
                    f"{sec.name}: move the filter toward {target_value:.2f} to match "
                    f"the section's energy ({sec.energy:.2f})."
                ),
            )
        )
        prev_value = target_value
    return events
