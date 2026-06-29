"""Arranger Agent — structure. The MVP returns one loop section.

Full intro/build/break/drop arrangement is a later sprint; the interface is
here so the orchestrator already speaks in sections.
"""

from __future__ import annotations

from app.music import build_loop_section
from app.schemas import Section, UserRequest


def arrange(request: UserRequest, energy_start: float, energy_end: float) -> list[Section]:
    return build_loop_section(
        bars=request.bars,
        energy_start=energy_start,
        energy_end=energy_end,
    )
