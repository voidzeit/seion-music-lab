"""Typed exceptions for SEION Music Lab.

Using a small hierarchy keeps error handling explicit and lets the CLI / API
surface meaningful messages instead of raw tracebacks.
"""

from __future__ import annotations


class SeionError(Exception):
    """Base class for all SEION Music Lab errors."""


class ConfigError(SeionError):
    """Raised when configuration / environment is invalid."""


class MusicTheoryError(SeionError):
    """Raised for invalid notes, scales, chords or keys."""


class GenerationError(SeionError):
    """Raised when a generation step cannot produce valid output."""


class ValidationError(SeionError):
    """Raised when a MusicalIdea fails musical validation."""


class ExportError(SeionError):
    """Raised when writing MIDI / JSON / Markdown fails."""


class ProviderError(SeionError):
    """Base class for LLM provider errors (optional, future use)."""


class ProviderNotConfigured(ProviderError):
    """Raised when a provider is used without an API key / base URL."""
