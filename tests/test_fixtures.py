"""The fixture ideas must parse into MusicalIdea and be scorable."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents import reference_agent
from app.schemas import MusicalIdea, UserRequest
from app.seion import score_idea

FIXTURES = sorted((Path(__file__).parent / "fixtures").glob("idea_*.json"))


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_fixture_parses_and_scores(path):
    idea = MusicalIdea(**json.loads(path.read_text("utf-8")))
    request = UserRequest(
        bpm=idea.bpm,
        key=idea.key,
        bars=idea.bars,
        style_targets=idea.style_targets,
        emotional_targets=idea.emotional_targets,
    )
    score = score_idea(idea, request, reference_agent.build_style_context(idea.style_targets))
    assert 0.0 <= score.overall <= 1.0
