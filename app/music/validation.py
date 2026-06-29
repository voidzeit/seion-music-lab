"""Light musical validation. Returns warnings; raises only on hard errors.

Pydantic already enforces MIDI/velocity ranges at construction time, so this
layer focuses on *musical* sanity: overload, missing roles, empty tracks.
"""

from __future__ import annotations

from app.exceptions import ValidationError
from app.music import analysis
from app.schemas import MusicalIdea

# Above this many melodic notes per bar the loop is getting hard to edit.
MAX_NOTES_PER_BAR = 40


def validate_idea(idea: MusicalIdea) -> list[str]:
    """Return a list of human-readable warnings. Raise on structural errors."""
    warnings: list[str] = []

    if not idea.tracks:
        raise ValidationError("Idea has no tracks.")

    if not analysis.has_harmony(idea):
        warnings.append("No harmony/pad track — the loop lacks a chordal centre.")
    if not analysis.has_bass(idea):
        warnings.append("No bass track — the low end is missing.")
    if not analysis.has_rhythm(idea):
        warnings.append("No drum track — the groove is missing.")

    npb = analysis.notes_per_bar(idea)
    if npb > MAX_NOTES_PER_BAR:
        warnings.append(
            f"High note density ({npb:.1f}/bar > {MAX_NOTES_PER_BAR}); consider thinning."
        )

    for track in idea.tracks:
        if track.event_count == 0:
            warnings.append(f"Track '{track.name}' is empty.")

    return warnings
