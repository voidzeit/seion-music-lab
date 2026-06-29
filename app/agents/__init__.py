"""Agents.

For the MVP these are thin, deterministic wrappers around the music/seion/export
layers. They define the contract (inputs/outputs) so an LLM-backed version can be
dropped in later without changing the orchestrator.
"""

from app.agents import (
    arranger_agent,
    composer_agent,
    critic_agent,
    intake_agent,
    reference_agent,
    seion_agent,
    sound_design_agent,
    teacher_agent,
)

__all__ = [
    "arranger_agent",
    "composer_agent",
    "critic_agent",
    "intake_agent",
    "reference_agent",
    "seion_agent",
    "sound_design_agent",
    "teacher_agent",
]
