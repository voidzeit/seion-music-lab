"""A small style hypergraph: artists -> traits -> techniques -> emotions.

Loaded from ``data/seed/style_graph.seed.json``. For the MVP it powers simple
look-ups (what traits does an artist use?); later it can drive richer reasoning
in the SEION engine.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.seion.edges import Edge
from app.seion.nodes import Node


class StyleGraph:
    def __init__(self, nodes: list[Node], edges: list[Edge]) -> None:
        self.nodes = {n.id: n for n in nodes}
        self.edges = edges

    @classmethod
    def from_seed(cls, path: str | Path) -> StyleGraph:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        nodes = [Node(**n) for n in data.get("nodes", [])]
        edges = [Edge(**e) for e in data.get("edges", [])]
        return cls(nodes, edges)

    def node_by_label(self, label: str) -> Node | None:
        for node in self.nodes.values():
            if node.label.lower() == label.lower():
                return node
        return None

    def neighbors(self, node_id: str, relation: str | None = None) -> list[tuple[Edge, Node]]:
        out: list[tuple[Edge, Node]] = []
        for edge in self.edges:
            if edge.source == node_id and (relation is None or edge.relation == relation):
                target = self.nodes.get(edge.target)
                if target is not None:
                    out.append((edge, target))
        return out

    def traits_for_artist(self, artist_label: str) -> list[str]:
        node = self.node_by_label(artist_label)
        if node is None:
            return []
        return [tgt.label for _, tgt in self.neighbors(node.id, relation="uses")]
