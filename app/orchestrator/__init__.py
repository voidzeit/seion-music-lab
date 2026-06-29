"""The orchestrator: deterministic pipeline today, LLM-ready by design."""

from app.orchestrator.run import GenerationResult, run_generation

__all__ = ["GenerationResult", "run_generation"]
