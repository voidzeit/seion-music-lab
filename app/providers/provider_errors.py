"""Provider error types (re-exported from app.exceptions for convenience)."""

from __future__ import annotations

from app.exceptions import ProviderError, ProviderNotConfigured


class ProviderRequestError(ProviderError):
    """Raised when an LLM HTTP request fails."""


class ProviderDependencyMissing(ProviderError):
    """Raised when an optional dependency (httpx) is not installed."""


__all__ = [
    "ProviderError",
    "ProviderNotConfigured",
    "ProviderRequestError",
    "ProviderDependencyMissing",
]
