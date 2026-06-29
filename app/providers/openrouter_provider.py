"""OpenRouter provider (optional) — one endpoint, many models, easy fallbacks.

Not used by the MVP. Requires OPENROUTER_API_KEY and the [llm] extra (httpx).
"""

from __future__ import annotations

import os
from typing import Any

from app.config import get_settings
from app.providers.base import LLMProvider, Message
from app.providers.provider_errors import ProviderNotConfigured, ProviderRequestError


class OpenRouterProvider(LLMProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model or get_settings().default_model)
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def supports_tools(self) -> bool:
        return True

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict:
        if not self.is_configured():
            raise ProviderNotConfigured("OPENROUTER_API_KEY is not set.")
        httpx = self._require_httpx()
        payload: dict = {
            "model": model or self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60,
            )
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            raise ProviderRequestError(str(exc)) from exc
        data = resp.json()
        msg = data["choices"][0]["message"]
        return {"content": msg.get("content", ""), "tool_calls": msg.get("tool_calls", []), "raw": data}
