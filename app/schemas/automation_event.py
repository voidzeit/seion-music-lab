"""Parameter automation (e.g. a slowly opening filter)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AutomationEvent(BaseModel):
    """A linear (or shaped) automation ramp on a named parameter.

    For the MVP we describe automation declaratively (it is rendered as advice
    in explanation.md and can later drive Piano Roll / mixer automation in FL).
    """

    target_track: str = Field(description="Name of the track this affects.")
    param: str = Field(description="Parameter name, e.g. 'filter_cutoff'.")
    start_beat: float = Field(ge=0)
    end_beat: float = Field(gt=0)
    start_value: float = Field(ge=0.0, le=1.0, description="Normalised 0-1 value.")
    end_value: float = Field(ge=0.0, le=1.0, description="Normalised 0-1 value.")
    curve: str = Field(default="linear", description="'linear', 'exp', 'log'.")
    description: str = Field(default="", description="Human-readable intent.")

    @property
    def is_rising(self) -> bool:
        return self.end_value > self.start_value
