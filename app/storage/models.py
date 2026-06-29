"""Lightweight storage-facing records (distinct from the rich domain schemas)."""

from __future__ import annotations

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    """A compact view of a saved project, for listings."""

    id: str
    title: str
    created_at: str
    bpm: int
    key: str
    overall_score: float | None = None
    path: str
