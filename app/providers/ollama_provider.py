"""Ollama provider (optional) — local models via the OpenAI-compatible API.

Not used by the MVP. Needs a running Ollama (OLLAMA_BASE_URL) and the [llm]
extra (httpx). No API key required since it is local.
"""

from __future__ import annotations

import os
from typing import Any

from app.config import get_settings
from app.providers.base import LLMProvider, Message
from app.providers.provider_errors import ProviderRequestError


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model or get_settings().local_model)
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    def is_configured(self) -> bool:
        # Local server; assume reachable. complete() surfaces connection errors.
        return True

    def supports_tools(self) -> bool:
        return True

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict:
        httpx = self._require_httpx()
        payload: dict = {
            "model": model or self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
        try:
            resp = httpx.post(f"{self.base_url}/chat/completions", json=payload, timeout=120)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            raise ProviderRequestError(str(exc)) from exc
        data = resp.json()
        msg = data["choices"][0]["message"]
        return {"content": msg.get("content", ""), "tool_calls": msg.get("tool_calls", []), "raw": data}
