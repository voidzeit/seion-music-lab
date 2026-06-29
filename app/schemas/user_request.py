"""Normalised representation of what the user asked for."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    """The intake contract: a parsed, normalised generation request.

    The CLI builds this directly; a future Intake Agent can build it from a
    free-form prompt. Either way, everything downstream consumes this object.
    """

    intent: str = Field(default="generate_loop")
    raw_prompt: str = Field(default="")

    bpm: int = Field(default=124, ge=40, le=300)
    key: str = Field(default="A minor")
    time_signature: str = Field(default="4/4")
    bars: int = Field(default=16, ge=1, le=128)

    style_targets: list[str] = Field(default_factory=list)
    emotional_targets: list[str] = Field(default_factory=list)

    progression: list[str] = Field(
        default_factory=lambda: ["Am7", "Fmaj7", "Cmaj7", "G6"],
        description="Chord symbols, one per bar of the core 4-bar loop.",
    )

    deliverables: list[str] = Field(
        default_factory=lambda: ["idea_json", "midi", "explanation", "seion_score"]
    )
    title: str | None = None
