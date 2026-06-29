"""A tiny preference model updated from listening feedback.

Tracks liked/disliked musical traits and a free-form 'current direction'. This
is what lets SEION slowly learn the producer's own language over time.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas import Feedback


class PreferenceModel(BaseModel):
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    current_direction: str = "warm melodic house / melodic techno with nostalgic edges"

    def update_from_feedback(self, feedback: Feedback) -> PreferenceModel:
        for item in feedback.liked:
            self._reinforce(item, liked=True)
        for item in feedback.disliked:
            self._reinforce(item, liked=False)
        if feedback.request:
            self.current_direction = feedback.request.strip()
        return self

    def _reinforce(self, item: str, *, liked: bool) -> None:
        item = item.strip().lower()
        if not item:
            return
        keep, drop = (self.likes, self.dislikes) if liked else (self.dislikes, self.likes)
        if item in drop:
            drop.remove(item)
        if item not in keep:
            keep.append(item)
