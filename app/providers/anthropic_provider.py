"""Anthropic (Claude) provider (optional).

Not used by the MVP. Requires ANTHROPIC_API_KEY and the [llm] extra (httpx).
Claude uses a Messages API with the system prompt passed separately.
"""

from __future__ import annotations

import os
from typing import Any

from app.providers.base import LLMProvider, Message
from app.providers.provider_errors import ProviderNotConfigured, ProviderRequestError


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    base_url = "https://api.anthropic.com/v1/messages"
    api_version = "2023-06-01"

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model or "claude-sonnet-4-6")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def supports_tools(self) -> bool:
        return True

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict:
        if not self.is_configured():
            raise ProviderNotConfigured("ANTHROPIC_API_KEY is not set.")
        httpx = self._require_httpx()

        system = "\n\n".join(m.content for m in messages if m.role == "system")
        convo = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        payload: dict = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            "messages": convo,
        }
        if system:
            payload["system"] = system
        if tools:
            # Claude expects {name, description, input_schema}.
            payload["tools"] = [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {"type": "object"}),
                }
                for t in tools
            ]
        try:
            resp = httpx.post(
                self.base_url,
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.api_version,
                    "content-type": "application/json",
                },
                timeout=60,
            )
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            raise ProviderRequestError(str(exc)) from exc
        data = resp.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        tool_calls = [b for b in data.get("content", []) if b.get("type") == "tool_use"]
        return {"content": text, "tool_calls": tool_calls, "raw": data}
