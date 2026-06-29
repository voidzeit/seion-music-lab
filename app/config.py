"""Runtime configuration for SEION Music Lab.

Configuration is read from environment variables (optionally loaded from a
``.env`` file). We deliberately avoid ``pydantic-settings`` to keep the core
dependency set tiny; a plain Pydantic model plus ``os.environ`` is enough.

All paths are configurable so nothing is hard-coded to a single machine.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

try:  # python-dotenv is a core dependency, but stay resilient if absent.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional at runtime
    pass


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser().resolve()


class Settings(BaseModel):
    """Resolved settings for the running process."""

    env: str = Field(default_factory=lambda: os.environ.get("SEION_ENV", "dev"))
    log_level: str = Field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    data_dir: Path = Field(default_factory=lambda: _env_path("SEION_DATA_DIR", "./data"))

    # LLM routing (optional, only used once providers are wired up).
    default_provider: str = Field(
        default_factory=lambda: os.environ.get("SEION_DEFAULT_PROVIDER", "openrouter")
    )
    default_model: str = Field(
        default_factory=lambda: os.environ.get(
            "SEION_DEFAULT_MODEL", "anthropic/claude-sonnet-4-6"
        )
    )
    local_model: str = Field(
        default_factory=lambda: os.environ.get("SEION_LOCAL_MODEL", "qwen3.6:27b")
    )

    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def midi_dir(self) -> Path:
        return self.data_dir / "midi"

    @property
    def memory_dir(self) -> Path:
        return self.data_dir / "memory"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def seed_dir(self) -> Path:
        return self.data_dir / "seed"

    @property
    def fl_drop_dir(self) -> Path:
        return self.data_dir / "fl_drop"

    def ensure_dirs(self) -> None:
        """Create the standard data directories if they do not exist."""
        for path in (
            self.projects_dir,
            self.exports_dir,
            self.midi_dir,
            self.memory_dir,
            self.logs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide settings (cached)."""
    return Settings()
