from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .model import NetworkModel, Edge


@dataclass
class _DSU:
    parent: Dict[str, str]
    rank: Dict[str, int]

    @staticmethod
    def make(nodes: List[str]) -> "_DSU":
        return _DSU(parent={n: n for n in nodes}, rank={n: 0 for n in nodes})

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal_mst(model: NetworkModel) -> Tuple[float, List[Edge]]:
    """Minimum Spanning Tree (Kruskal).

    Treats the graph as **undirected** (even if model.directed True).
    Uses ``edge.weight``.
    """
    dsu = _DSU.make(model.nodes)
    edges = sorted(model.edges, key=lambda e: float(e.weight))
    mst: List[Edge] = []
    total = 0.0
    for e in edges:
        if dsu.union(e.u, e.v):
            mst.append(e)
            total += float(e.weight)
            if len(mst) == max(0, len(model.nodes) - 1):
                break

    # If graph disconnected, mst will be smaller.
    return total, mst
