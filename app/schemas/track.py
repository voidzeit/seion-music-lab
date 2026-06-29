"""A track groups note or drum events under a clear musical role."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.drum_event import DrumEvent
from app.schemas.note_event import NoteEvent

# Valid musical roles. Keeping these explicit helps the SEION scorer reward
# clear role separation and helps the teacher explain each layer.
TRACK_ROLES = {
    "kick",
    "snare_clap",
    "closed_hat",
    "open_hat",
    "percussion",
    "drums",
    "bass",
    "harmony",
    "pad",
    "arp",
    "lead",
    "melody",
    "vocal_chop",
    "texture",
    "fx",
    "automation",
}


class MixerHint(BaseModel):
    """Suggested mixer treatment for a track (advice, not enforced)."""

    volume_db: float = Field(default=-6.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    effects: list[str] = Field(default_factory=list)


class Track(BaseModel):
    """One editable layer of the idea.

    A track holds *either* melodic ``notes`` *or* ``drum_events`` depending on
    its role. ``is_drum`` selects MIDI channel 10 on export.
    """

    id: str
    name: str
    role: str
    instrument_hint: str = Field(default="", description="Suggested FL instrument.")
    mixer_hint: MixerHint = Field(default_factory=MixerHint)
    notes: list[NoteEvent] = Field(default_factory=list)
    drum_events: list[DrumEvent] = Field(default_factory=list)
    is_drum: bool = Field(default=False)

    @property
    def event_count(self) -> int:
        return len(self.notes) + len(self.drum_events)
