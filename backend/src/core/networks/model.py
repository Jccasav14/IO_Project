from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Edge:
    u: str
    v: str
    # Capacity for flow problems (optional for others)
    capacity: float = 0.0
    # Cost for min-cost flow (optional)
    cost: float = 0.0
    # Weight for shortest path / MST (optional)
    weight: float = 0.0


@dataclass(frozen=True)
class NetworkModel:
    nodes: List[str]
    edges: List[Edge]
    source: Optional[str] = None
    sink: Optional[str] = None
    demand: float = 0.0
    directed: bool = True

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "NetworkModel":
        nodes = list(map(str, d.get("nodes", [])))
        edges_in = d.get("edges", []) or []
        edges: List[Edge] = []
        for e in edges_in:
            edges.append(
                Edge(
                    u=str(e.get("u")),
                    v=str(e.get("v")),
                    capacity=float(e.get("capacity", 0.0) or 0.0),
                    cost=float(e.get("cost", 0.0) or 0.0),
                    weight=float(e.get("weight", e.get("w", e.get("cost", 0.0))) or 0.0),
                )
            )

        return NetworkModel(
            nodes=nodes,
            edges=edges,
            source=(str(d.get("source")) if d.get("source") is not None else None),
            sink=(
                str(d.get("sink"))
                if d.get("sink") is not None
                else (str(d.get("target")) if d.get("target") is not None else None)
            ),
            demand=float(d.get("demand", 0.0) or 0.0),
            directed=bool(d.get("directed", True)),
        )
