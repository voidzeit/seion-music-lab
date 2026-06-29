"""Does energy move with intent across the idea?

A single loop is intentionally steady, so this score is moderate by design. The
rising filter automation and the start<end energy target give it some shape; a
real intro/build/drop arrangement is what would push it higher.
"""

from __future__ import annotations

from app.schemas import MusicalIdea

FLAT_LOOP_BASE = 0.45
RISING_AUTOMATION_BONUS = 0.13
ENERGY_DELTA_BONUS = 0.05


def compute_tension_curve(idea: MusicalIdea) -> tuple[float, str]:
    score = FLAT_LOOP_BASE
    reasons = ["steady 16-bar loop (base)"]

    if any(a.is_rising for a in idea.automation):
        score += RISING_AUTOMATION_BONUS
        reasons.append("rising filter automation adds timbral tension")

    if idea.energy_target.end > idea.energy_target.start:
        score += ENERGY_DELTA_BONUS
        reasons.append("energy target rises start->end")

    score = round(min(1.0, score), 4)
    note = (
        "; ".join(reasons)
        + ". Add an intro/build/break/drop arrangement to raise this."
    )
    return score, note
