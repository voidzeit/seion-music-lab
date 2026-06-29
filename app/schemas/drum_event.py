"""A single drum hit event, measured in beats."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DrumEvent(BaseModel):
    """One percussion hit.

    ``instrument`` is a human-readable role ('kick', 'clap', 'closed_hat', ...)
    and ``midi`` is the General MIDI percussion note used on channel 10.
    """

    instrument: str = Field(description="Drum role, e.g. 'kick' or 'closed_hat'.")
    midi: int = Field(ge=0, le=127, description="General MIDI percussion note.")
    start_beat: float = Field(ge=0, description="Start position in beats.")
    duration_beats: float = Field(gt=0, description="Length in beats (short for drums).")
    velocity: int = Field(ge=1, le=127, description="MIDI velocity 1-127.")

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats
