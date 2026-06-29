"""Optional local HTTP API (FastAPI).

The MVP is CLI-first; this module is here so ``POST /generate`` and
``POST /feedback`` exist when you install the ``[server]`` extra. Importing this
module never requires FastAPI — ``create_app`` imports it lazily.

Run with: ``uvicorn app.main:app`` (after ``pip install -e .[server]``).
"""

from __future__ import annotations

from typing import Any


def create_app():  # pragma: no cover - exercised only with the server extra
    from fastapi import FastAPI
    from pydantic import BaseModel

    from app.agents import intake_agent
    from app.config import get_settings
    from app.orchestrator import run_generation
    from app.schemas import Feedback, UserRequest
    from app.tools import log_user_feedback

    api = FastAPI(title="SEION Music Lab", version="0.1.0")

    class GenerateBody(BaseModel):
        prompt: str | None = None
        style: list[str] = []
        emotion: list[str] = []
        key: str = "A minor"
        bpm: int = 124
        bars: int = 16

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/generate")
    def generate(body: GenerateBody) -> dict[str, Any]:
        get_settings().ensure_dirs()
        if body.prompt:
            request = intake_agent.parse_prompt(
                body.prompt, style_targets=body.style, emotional_targets=body.emotion
            )
        else:
            request = UserRequest(
                bpm=body.bpm, key=body.key, bars=body.bars,
                style_targets=body.style, emotional_targets=body.emotion,
            )
        result = run_generation(request)
        return {
            "project_id": result.idea.id,
            "score": result.score.model_dump(),
            "exports": result.idea.export_paths,
        }

    @api.post("/feedback")
    def feedback(fb: Feedback) -> dict[str, Any]:
        prefs = log_user_feedback(fb)
        return {"next_action": "generate_variation", "updated_preferences": prefs.model_dump()}

    return api


# Lazily instantiate so plain `import app.main` works without FastAPI installed.
try:  # pragma: no cover
    app = create_app()
except Exception:  # pragma: no cover - FastAPI not installed; CLI still works
    app = None
