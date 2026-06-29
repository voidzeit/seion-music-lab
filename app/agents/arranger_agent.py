"""Arranger Agent — structure.

Builds a full intro/build/main/break/drop/outro arrangement when the request has
room for it (Sprint 3), and falls back to a single loop section otherwise. The
orchestrator already speaks in sections, so nothing downstream changes shape.
"""

from __future__ import annotations

from app.music import build_loop_section, build_song_sections
from app.schemas import Section, UserRequest


def arrange(
    request: UserRequest,
    energy_start: float,
    energy_end: float,
    full: bool = True,
) -> list[Section]:
    if full and request.bars >= 8:
        return build_song_sections(request.bars, energy_start, energy_end)
    return build_loop_section(
        bars=request.bars,
        energy_start=energy_start,
        energy_end=energy_end,
    )
