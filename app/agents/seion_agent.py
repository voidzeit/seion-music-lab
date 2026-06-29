"""SEION Agent — evaluate an idea with the deterministic scorer."""

from __future__ import annotations

from app.schemas import MusicalIdea, SeionScore, UserRequest
from app.seion import score_idea


def evaluate(
    idea: MusicalIdea,
    request: UserRequest,
    style_context: dict,
) -> SeionScore:
    return score_idea(idea, request, style_context)
