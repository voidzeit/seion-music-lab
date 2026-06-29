"""User listening feedback, stored to train preferences over time."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Feedback(BaseModel):
    """A single round of listening feedback on a generated idea."""

    project_id: str
    rating: int = Field(ge=0, le=10, description="Overall 0-10 rating.")
    liked: list[str] = Field(default_factory=list)
    disliked: list[str] = Field(default_factory=list)
    request: str = Field(default="", description="Free-form 'make it more ...'.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
