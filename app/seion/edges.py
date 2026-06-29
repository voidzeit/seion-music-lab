"""Style-graph edges (weighted relations)."""

from __future__ import annotations

from dataclasses import dataclass

RELATIONS = {"uses", "creates", "increases", "reduces", "pairs_with"}


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    weight: float = 0.5
