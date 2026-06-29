"""The SEION score for a musical idea."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Weights for the overall score. Kept here so the scorer and docs stay in sync.
SEION_WEIGHTS: dict[str, float] = {
    "coherence": 0.25,
    "style_match": 0.20,
    "emotional_clarity": 0.20,
    "tension_curve": 0.15,
    "editability": 0.10,
    "novelty": 0.10,
}


class SeionScore(BaseModel):
    """Deterministic musical evaluation, each component in [0, 1]."""

    coherence: float = Field(ge=0.0, le=1.0)
    style_match: float = Field(ge=0.0, le=1.0)
    emotional_clarity: float = Field(ge=0.0, le=1.0)
    tension_curve: float = Field(ge=0.0, le=1.0)
    editability: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)

    # Short human-readable note per component, used by the teacher agent.
    details: dict[str, str] = Field(default_factory=dict)

    @staticmethod
    def compute_overall(components: dict[str, float]) -> float:
        """Weighted sum of the six components, rounded to 4 dp."""
        total = sum(SEION_WEIGHTS[name] * components[name] for name in SEION_WEIGHTS)
        return round(total, 4)
