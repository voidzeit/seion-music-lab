"""Choose an LLM provider/model. Optional — the MVP never calls this.

Kept tiny and lazy so importing it never requires API keys or httpx.
"""

from __future__ import annotations

from app.config import get_settings


def select_model(task: str = "reasoning") -> dict:
    """Return the provider/model the system *would* use for a task.

    Routing intent (per the design):
      - reasoning / critique / teaching -> strong hosted model (OpenAI/Anthropic),
      - fast / local / private          -> Ollama local model,
      - everything via OpenRouter when you want one endpoint + fallbacks.
    """
    settings = get_settings()
    if task in {"fast", "local", "draft", "classify"}:
        return {"provider": "ollama", "model": settings.local_model}
    return {"provider": settings.default_provider, "model": settings.default_model}


def get_provider(name: str):  # pragma: no cover - optional, not used in MVP
    """Lazily construct a provider instance by name (raises if deps/keys absent)."""
    from app import providers

    return providers.get_provider(name)
