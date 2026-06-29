"""Tool: compare two SEION scores (e.g. idea_001 vs idea_002)."""

from __future__ import annotations

from app.schemas import SeionScore
from app.schemas.seion_score import SEION_WEIGHTS


def compare_versions(before: SeionScore, after: SeionScore) -> dict[str, float]:
    """Return per-component deltas (after - before), including 'overall'."""
    deltas = {
        component: round(getattr(after, component) - getattr(before, component), 4)
        for component in SEION_WEIGHTS
    }
    deltas["overall"] = round(after.overall - before.overall, 4)
    return deltas
