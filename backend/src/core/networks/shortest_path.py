from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from .model import NetworkModel


def dijkstra(model: NetworkModel, source: str, target: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Dijkstra for non-negative weights.

    Uses ``edge.weight`` (falls back to cost if caller stored it there).
    """
    adj: Dict[str, List[Tuple[str, float]]] = {n: [] for n in model.nodes}
    for e in model.edges:
        w = float(e.weight)
        adj[e.u].append((e.v, w))
        if not model.directed:
            adj[e.v].append((e.u, w))

    dist = {n: float("inf") for n in model.nodes}
    prev: Dict[str, Optional[str]] = {n: None for n in model.nodes}
    dist[source] = 0.0
    pq: List[Tuple[float, str]] = [(0.0, source)]

    while pq:
        d, u = heapq.heappop(pq)
        if d != dist[u]:
            continue
        if u == target:
            break
        for v, w in adj[u]:
            if w < 0:
                raise ValueError("Dijkstra requires non-negative weights")
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    return dist, prev


def reconstruct_path(prev: Dict[str, Optional[str]], source: str, target: str) -> List[str]:
    if source == target:
        return [source]
    path: List[str] = []
    cur: Optional[str] = target
    while cur is not None:
        path.append(cur)
        if cur == source:
            break
        cur = prev[cur]
    path.reverse()
    if not path or path[0] != source:
        return []
    return path
