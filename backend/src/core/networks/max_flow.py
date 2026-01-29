from __future__ import annotations

from collections import deque
from typing import Dict, List, Tuple

from .model import NetworkModel


def edmonds_karp(model: NetworkModel, source: str, sink: str) -> Tuple[float, Dict[Tuple[str, str], float]]:
    """Max Flow (Edmonds–Karp).

    Uses ``edge.capacity``. Graph is treated as directed; if ``model.directed`` is False, edges are mirrored.
    """
    # Build capacity dictionary and adjacency for BFS over residual network.
    cap: Dict[Tuple[str, str], float] = {}
    adj: Dict[str, List[str]] = {n: [] for n in model.nodes}

    def add_edge(u: str, v: str, c: float) -> None:
        key = (u, v)
        cap[key] = cap.get(key, 0.0) + c
        if v not in adj[u]:
            adj[u].append(v)
        if u not in adj[v]:
            adj[v].append(u)  # residual back-edge traversal

    for e in model.edges:
        add_edge(e.u, e.v, float(e.capacity))
        if not model.directed:
            add_edge(e.v, e.u, float(e.capacity))

    flow: Dict[Tuple[str, str], float] = {}

    def residual(u: str, v: str) -> float:
        return cap.get((u, v), 0.0) - flow.get((u, v), 0.0)

    max_flow = 0.0
    while True:
        parent: Dict[str, str] = {source: ""}
        q = deque([source])
        while q and sink not in parent:
            u = q.popleft()
            for v in adj[u]:
                if v in parent:
                    continue
                if residual(u, v) > 1e-12:
                    parent[v] = u
                    q.append(v)

        if sink not in parent:
            break

        # Find bottleneck
        bottleneck = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            bottleneck = min(bottleneck, residual(u, v))
            v = u

        # Augment
        v = sink
        while v != source:
            u = parent[v]
            flow[(u, v)] = flow.get((u, v), 0.0) + bottleneck
            flow[(v, u)] = flow.get((v, u), 0.0) - bottleneck
            v = u

        max_flow += bottleneck

    # Return only positive flows on original arcs
    clean: Dict[Tuple[str, str], float] = {k: v for k, v in flow.items() if v > 1e-12}
    return max_flow, clean
