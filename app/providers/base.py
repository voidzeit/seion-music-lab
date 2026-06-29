"""Provider interface. The MVP does not call any of these.

A provider turns a list of chat messages (and optional tool schemas) into a
normalised response dict: ``{"content": str, "tool_calls": list, "raw": ...}``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


class LLMProvider(ABC):
    name: str = "base"

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    @abstractmethod
    def is_configured(self) -> bool:
        """True if the provider has the credentials/URL it needs."""

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict:
        """Return a normalised completion dict."""

    def supports_tools(self) -> bool:
        return False

    @staticmethod
    def _require_httpx():
        try:
            import httpx  # noqa: F401

            return httpx
        except ImportError as exc:  # pragma: no cover - optional dependency
            from app.providers.provider_errors import ProviderDependencyMissing

            raise ProviderDependencyMissing(
                "httpx is required for LLM providers. Install with: pip install -e .[llm]"
            ) from exc
