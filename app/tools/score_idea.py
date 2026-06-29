"""Tool: score a MusicalIdea with the SEION engine."""

from __future__ import annotations

from app.schemas import MusicalIdea, SeionScore, UserRequest
from app.seion import score_idea as _score_idea


def score_seion_idea(
    idea: MusicalIdea,
    request: UserRequest,
    style_context: dict | None = None,
) -> SeionScore:
    return _score_idea(idea, request, style_context or {})
