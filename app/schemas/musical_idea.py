"""The central data contract: a complete, editable musical idea.

Every agent reads and writes this object. It is the single source of truth from
which MIDI, JSON and Markdown are derived.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.automation_event import AutomationEvent
from app.schemas.feedback import Feedback
from app.schemas.seion_score import SeionScore
from app.schemas.track import Track


class EnergyTarget(BaseModel):
    """Where the energy should start and end across the idea (0-1)."""

    start: float = Field(default=0.25, ge=0.0, le=1.0)
    end: float = Field(default=0.65, ge=0.0, le=1.0)


class Section(BaseModel):
    """A region of the arrangement. The MVP uses a single loop section."""

    name: str
    start_bar: int = Field(ge=1)
    length_bars: int = Field(ge=1)
    energy: float = Field(ge=0.0, le=1.0)
    description: str = ""


class DecisionLogEntry(BaseModel):
    """An explainable musical decision. This is what trains the producer's ear."""

    decision_id: str
    agent: str
    type: str = Field(description="e.g. 'harmony', 'bass', 'arp', 'drums'.")
    decision: str
    reason: str
    references: list[str] = Field(default_factory=list)
    expected_effect: str = ""


class MusicalIdea(BaseModel):
    """A full, editable musical idea ready for export to FL Studio."""

    id: str
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    bpm: int = Field(ge=40, le=300)
    key: str
    time_signature: str = "4/4"
    bars: int = Field(ge=1, le=128)

    style_targets: list[str] = Field(default_factory=list)
    emotional_targets: list[str] = Field(default_factory=list)
    energy_target: EnergyTarget = Field(default_factory=EnergyTarget)

    sections: list[Section] = Field(default_factory=list)
    tracks: list[Track] = Field(default_factory=list)
    automation: list[AutomationEvent] = Field(default_factory=list)

    seion_scores: SeionScore | None = None
    decision_log: list[DecisionLogEntry] = Field(default_factory=list)
    export_paths: dict[str, Any] = Field(default_factory=dict)
    user_feedback: list[Feedback] = Field(default_factory=list)

    # --- convenience accessors -------------------------------------------------
    def track_by_role(self, role: str) -> Track | None:
        for track in self.tracks:
            if track.role == role:
                return track
        return None

    def melodic_tracks(self) -> list[Track]:
        return [t for t in self.tracks if not t.is_drum]

    def drum_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.is_drum]
