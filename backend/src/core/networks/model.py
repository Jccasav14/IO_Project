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
                    # Prefer explicit weight, then w, then cost (fallback)
                    weight=float(e.get("weight", e.get("w", e.get("cost", 0.0))) or 0.0),
                )
            )

        # Robust boolean parsing for "directed"
        directed_val = d.get("directed", True)
        if isinstance(directed_val, bool):
            directed = directed_val
        else:
            directed = str(directed_val).strip().lower() in (
                "1",
                "true",
                "yes",
                "y",
                "si",
                "sí",
            )

        # Accept either "sink" or "target" (UI often sends "target")
        sink = (
            str(d.get("sink"))
            if d.get("sink") is not None
            else (str(d.get("target")) if d.get("target") is not None else None)
        )

        source = str(d.get("source")) if d.get("source") is not None else None

        return NetworkModel(
            nodes=nodes,
            edges=edges,
            source=source,
            sink=sink,
            demand=float(d.get("demand", 0.0) or 0.0),
            directed=directed,
        )
