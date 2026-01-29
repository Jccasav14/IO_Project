from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .errors import NetworkModelError
from .model import NetworkModel
from .parsers import model_from_dict
from .shortest_path import dijkstra, reconstruct_path
from .mst import kruskal_mst
from .max_flow import edmonds_karp
from .min_cost_flow import InfeasibleFlow, min_cost_flow_ssap


def _edge_key(u: str, v: str) -> str:
    return f"{u}->{v}"


def solve_network(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Solve a network problem.

    Expected top-level keys:
    - method: one of {"shortest_path", "mst", "max_flow", "min_cost_flow"}
    - model: graph JSON with nodes/edges and optional source/sink/demand/directed
    """
    if not isinstance(problem, dict):
        raise NetworkModelError("Request must be a JSON object")
    method = str(problem.get("method", "")).strip().lower()
    model_dict = problem.get("model") if "model" in problem else problem
    m: NetworkModel = model_from_dict(model_dict)

    if method in ("", "shortest", "shortest_path", "ruta_mas_corta"):
        src = m.source or problem.get("source")
        dst = m.sink or problem.get("target") or problem.get("sink")
        if not src or not dst:
            raise NetworkModelError("Shortest path requires 'source' and 'sink/target'")
        dist, prev = dijkstra(m, str(src), str(dst))
        path_nodes = reconstruct_path(prev, str(src), str(dst))
        # Build path edges
        path_edges: List[str] = []
        for i in range(len(path_nodes) - 1):
            path_edges.append(_edge_key(path_nodes[i], path_nodes[i + 1]))
        return {
            "method": "shortest_path",
            "source": str(src),
            "target": str(dst),
            "distance": None if dist[str(dst)] == float("inf") else dist[str(dst)],
            "path_nodes": path_nodes,
            "highlight": {"nodes": path_nodes, "edges": path_edges},
        }

    if method in ("mst", "arbol_expansion_minima", "minimum_spanning_tree"):
        total, edges = kruskal_mst(m)
        mst_edges = [_edge_key(e.u, e.v) for e in edges] + [_edge_key(e.v, e.u) for e in edges]
        return {
            "method": "mst",
            "total_weight": total,
            "edges": [{"u": e.u, "v": e.v, "weight": e.weight} for e in edges],
            "highlight": {"nodes": list({n for e in edges for n in (e.u, e.v)}), "edges": mst_edges},
        }

    if method in ("max_flow", "flujo_maximo"):
        src = m.source
        dst = m.sink
        if not src or not dst:
            raise NetworkModelError("Max flow requires 'source' and 'sink'")
        value, flows = edmonds_karp(m, src, dst)
        flows_out = [{"u": u, "v": v, "flow": f} for (u, v), f in flows.items()]
        highlight_edges = [_edge_key(u, v) for (u, v), f in flows.items() if f > 1e-12]
        return {
            "method": "max_flow",
            "source": src,
            "sink": dst,
            "max_flow": value,
            "flows": flows_out,
            "highlight": {"nodes": m.nodes, "edges": highlight_edges},
        }

    if method in ("min_cost_flow", "flujo_costo_minimo", "min_cost"):
        src = m.source
        dst = m.sink
        if not src or not dst:
            raise NetworkModelError("Min-cost flow requires 'source' and 'sink'")
        if m.demand <= 0:
            raise NetworkModelError("Min-cost flow requires 'demand' > 0")
        try:
            sent, tot_cost, flows = min_cost_flow_ssap(m, src, dst, m.demand)
        except InfeasibleFlow as exc:
            return {
                "method": "min_cost_flow",
                "source": src,
                "sink": dst,
                "demand": m.demand,
                "sent": 0,
                "total_cost": None,
                "error": str(exc),
            }
        flows_out = [{"u": u, "v": v, "flow": f} for (u, v), f in flows.items()]
        highlight_edges = [_edge_key(u, v) for (u, v), f in flows.items() if f > 1e-12]
        return {
            "method": "min_cost_flow",
            "source": src,
            "sink": dst,
            "demand": m.demand,
            "sent": sent,
            "total_cost": tot_cost,
            "flows": flows_out,
            "highlight": {"nodes": m.nodes, "edges": highlight_edges},
        }

    raise NetworkModelError(f"Unknown method: {method}")
