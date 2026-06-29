"""Optional LLM providers.

The MVP never imports these at runtime. They exist so the orchestrator can grow
an LLM path without restructuring. ``get_provider`` constructs one by name.
"""

from __future__ import annotations

from app.providers.base import LLMProvider, Message


def get_provider(name: str, model: str | None = None) -> LLMProvider:
    name = name.lower()
    if name == "openai":
        from app.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(model)
    if name == "anthropic":
        from app.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model)
    if name == "openrouter":
        from app.providers.openrouter_provider import OpenRouterProvider

        return OpenRouterProvider(model)
    if name == "ollama":
        from app.providers.ollama_provider import OllamaProvider

        return OllamaProvider(model)
    raise ValueError(f"Unknown provider: {name!r}")


__all__ = ["LLMProvider", "Message", "get_provider"]
