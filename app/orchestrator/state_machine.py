"""The generation state machine (for logging + future control flow)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class GenerationState(StrEnum):
    IDLE = "idle"
    PARSE_REQUEST = "parse_request"
    LOAD_STYLE_CONTEXT = "load_style_context"
    PLAN = "plan"
    COMPOSE = "compose"
    VALIDATE = "validate"
    SEION_SCORE = "seion_score"
    CRITIQUE = "critique"
    REVISE = "revise"
    EXPORT = "export"
    SAVE_VERSION = "save_version"
    EXPLAIN = "explain"
    DONE = "done"


# The canonical happy-path order.
PIPELINE_ORDER: list[GenerationState] = [
    GenerationState.PARSE_REQUEST,
    GenerationState.LOAD_STYLE_CONTEXT,
    GenerationState.PLAN,
    GenerationState.COMPOSE,
    GenerationState.VALIDATE,
    GenerationState.SEION_SCORE,
    GenerationState.CRITIQUE,
    GenerationState.REVISE,
    GenerationState.EXPORT,
    GenerationState.SAVE_VERSION,
    GenerationState.EXPLAIN,
    GenerationState.DONE,
]


@dataclass
class StateTracker:
    """Records the states the pipeline passed through (handy for tests/logs)."""

    history: list[GenerationState] = field(default_factory=list)

    def enter(self, state: GenerationState) -> None:
        self.history.append(state)

    def passed_through(self, state: GenerationState) -> bool:
        return state in self.history
