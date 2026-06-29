"""Does energy move with intent across the idea?

A flat loop is steady by design, so it scores moderately. Two things lift it:
rising filter automation (timbral tension) and — the big one — a real
arrangement whose sections rise and fall (intro -> build -> drop). An idea with
no sections is unaffected by the arrangement terms, so the MVP/test ideas keep
their original scores.
"""

from __future__ import annotations

from app.schemas import MusicalIdea

FLAT_LOOP_BASE = 0.45
RISING_AUTOMATION_BONUS = 0.13
ENERGY_DELTA_BONUS = 0.05
SECTION_RANGE_WEIGHT = 0.30   # scaled by the energy spread across sections
DROP_SHAPE_BONUS = 0.07       # a clear peak above the quiet parts


def _section_terms(idea: MusicalIdea) -> tuple[float, list[str]]:
    sections = idea.sections or []
    energies = [s.energy for s in sections]
    # A single section (the MVP loop) is not an arrangement.
    if len(energies) < 2:
        return 0.0, []

    spread = max(energies) - min(energies)
    bonus = round(SECTION_RANGE_WEIGHT * spread, 4)
    reasons = [f"sections span energy {min(energies):.2f}->{max(energies):.2f}"]

    names = {s.name.lower(): s.energy for s in sections}
    quiet = [names[n] for n in ("intro", "break") if n in names]
    if "drop" in names and quiet and names["drop"] > max(quiet) + 0.1:
        bonus += DROP_SHAPE_BONUS
        reasons.append("a drop clearly peaks above the intro/break")

    return bonus, reasons


def compute_tension_curve(idea: MusicalIdea) -> tuple[float, str]:
    score = FLAT_LOOP_BASE
    reasons = ["steady loop (base)"]

    if any(a.is_rising for a in idea.automation):
        score += RISING_AUTOMATION_BONUS
        reasons.append("rising filter automation adds timbral tension")

    if idea.energy_target.end > idea.energy_target.start:
        score += ENERGY_DELTA_BONUS
        reasons.append("energy target rises start->end")

    section_bonus, section_reasons = _section_terms(idea)
    score += section_bonus
    reasons.extend(section_reasons)

    score = round(min(1.0, score), 4)
    if section_bonus == 0.0:
        reasons.append("add an intro/build/break/drop arrangement to raise this")
    note = "; ".join(reasons) + "."
    return score, note
