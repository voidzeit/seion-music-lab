"""The orchestrator: deterministic pipeline today, LLM-ready by design."""

from app.orchestrator.run import GenerationResult, run_generation
from app.orchestrator.variation_run import VariationResult, run_variation

__all__ = [
    "GenerationResult",
    "run_generation",
    "VariationResult",
    "run_variation",
]
