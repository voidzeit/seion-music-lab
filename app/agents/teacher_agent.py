"""Teacher Agent — explain the idea in clear, learnable language (Markdown)."""

from __future__ import annotations

from app.export.markdown_writer import build_explanation_markdown
from app.schemas import MusicalIdea


def explain(
    idea: MusicalIdea,
    *,
    style_context: dict | None = None,
    sound_design: dict[str, list[str]] | None = None,
    critique: list[dict] | None = None,
    warnings: list[str] | None = None,
) -> str:
    return build_explanation_markdown(
        idea,
        style_context=style_context,
        sound_design=sound_design,
        critique=critique,
        warnings=warnings,
    )
