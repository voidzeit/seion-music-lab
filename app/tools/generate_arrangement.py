"""Tool: generate arrangement sections (MVP: a single loop section)."""

from __future__ import annotations

from app.music import build_loop_section
from app.schemas import Section


def generate_arrangement(
    bars: int = 16,
    energy_start: float = 0.45,
    energy_end: float = 0.55,
) -> list[Section]:
    return build_loop_section(bars, energy_start, energy_end)
