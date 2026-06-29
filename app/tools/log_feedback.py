"""Tool: store listening feedback and update preference weights."""

from __future__ import annotations

from app.schemas import Feedback
from app.seion.memory import SeionMemory
from app.seion.preference_model import PreferenceModel


def log_user_feedback(feedback: Feedback) -> PreferenceModel:
    return SeionMemory().record_feedback(feedback)
