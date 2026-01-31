from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from .model import NetworkModel


class InfeasibleFlow(Exception):
    pass


def min_cost_flow_ssap(
    model: NetworkModel,
    source: str,
    sink: str,
    demand: float,
) -> Tuple[float, float, Dict[Tuple[str, str], float]]:
    """Minimum-cost flow for a single source->sink demand.

    Successive Shortest Augmenting Path (SSAP) with Johnson potentials.

    - Uses ``edge.capacity`` and ``edge.cost`` (directed).
    - If ``model.directed`` is False, edges are mirrored with same capacity and cost.
    - Returns: (sent_flow, total_cost, flow_dict)
    """

    # Residual network representation
    # cap[(u,v)] and cost[(u,v)] for residual arcs
    cap: Dict[Tuple[str, str], float] = {}
    cost: Dict[Tuple[str, str], float] = {}
    adj: Dict[str, List[str]] = {n: [] for n in model.nodes}

    def add_arc(u: str, v: str, c: float, w: float) -> None:
        if (u, v) not in cap:
            adj[u].append(v)
            adj[v].append(u)  # ensure residual traversal
            cap[(u, v)] = 0.0
            cap[(v, u)] = 0.0
            cost[(u, v)] = 0.0
            cost[(v, u)] = 0.0
        cap[(u, v)] += c
        cost[(u, v)] = w
        cost[(v, u)] = -w

    for e in model.edges:
        add_arc(e.u, e.v, float(e.capacity), float(e.cost))
        if not model.directed:
            add_arc(e.v, e.u, float(e.capacity), float(e.cost))

    flow: Dict[Tuple[str, str], float] = {k: 0.0 for k in cap.keys()}
    potential: Dict[str, float] = {n: 0.0 for n in model.nodes}

    def residual(u: str, v: str) -> float:
        return cap[(u, v)] - flow[(u, v)]

    sent = 0.0
    total_cost = 0.0
    EPS = 1e-12

    while sent + EPS < demand:
        # Dijkstra on reduced costs
        dist: Dict[str, float] = {n: float("inf") for n in model.nodes}
        parent: Dict[str, Optional[str]] = {n: None for n in model.nodes}
        parent_edge: Dict[str, Optional[Tuple[str, str]]] = {n: None for n in model.nodes}
        dist[source] = 0.0
        pq: List[Tuple[float, str]] = [(0.0, source)]

        while pq:
            d, u = heapq.heappop(pq)
            if d != dist[u]:
                continue
            for v in adj[u]:
                if residual(u, v) <= EPS:
                    continue
                rcost = cost[(u, v)] + potential[u] - potential[v]
                nd = d + rcost
                if nd < dist[v] - 1e-15:
                    dist[v] = nd
                    parent[v] = u
                    parent_edge[v] = (u, v)
                    heapq.heappush(pq, (nd, v))

        if parent[sink] is None:
            raise InfeasibleFlow("No augmenting path: demand cannot be satisfied with given capacities")

        # Update potentials
        for n in model.nodes:
            if dist[n] < float("inf"):
                potential[n] += dist[n]

        # Find bottleneck
        add = demand - sent
        v = sink
        while v != source:
            e = parent_edge[v]
            assert e is not None
            u, w = e
            add = min(add, residual(u, w))
            v = parent[v]  # type: ignore

        # Augment and accumulate true costs
        v = sink
        while v != source:
            u = parent[v]
            assert u is not None
            flow[(u, v)] += add
            flow[(v, u)] -= add
            total_cost += add * cost[(u, v)]
            v = u

        sent += add

    clean = {k: v for k, v in flow.items() if v > EPS}
    return sent, total_cost, clean
