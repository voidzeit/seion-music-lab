"""Style-graph node types."""

from __future__ import annotations

from dataclasses import dataclass

NODE_TYPES = {"artist", "trait", "technique", "emotion", "genre", "timbre"}


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    label: str
