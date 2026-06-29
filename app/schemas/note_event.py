"""A single pitched note event, measured in beats."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NoteEvent(BaseModel):
    """One note on a melodic/harmonic track.

    Timing is expressed in beats (quarter notes) from the start of the loop so
    it is independent of tempo and PPQ. The MIDI writer converts to ticks.
    """

    pitch: str = Field(description="Note name, e.g. 'A3'.")
    midi: int = Field(ge=0, le=127, description="MIDI note number 0-127.")
    start_beat: float = Field(ge=0, description="Start position in beats.")
    duration_beats: float = Field(gt=0, description="Length in beats.")
    velocity: int = Field(ge=1, le=127, description="MIDI velocity 1-127.")

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats
