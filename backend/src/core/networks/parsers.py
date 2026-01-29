from __future__ import annotations

from typing import Dict, Any

from .errors import NetworkModelError
from .model import NetworkModel


def model_from_dict(d: Dict[str, Any]) -> NetworkModel:
    if not isinstance(d, dict):
        raise NetworkModelError("Model must be a JSON object")
    m = NetworkModel.from_dict(d)
    if not m.nodes:
        raise NetworkModelError("'nodes' is required and must be non-empty")
    node_set = set(m.nodes)
    if len(node_set) != len(m.nodes):
        raise NetworkModelError("'nodes' contains duplicates")
    if not m.edges:
        raise NetworkModelError("'edges' is required and must be non-empty")
    for i, e in enumerate(m.edges):
        if e.u not in node_set or e.v not in node_set:
            raise NetworkModelError(f"Edge {i} references unknown node: {e.u}->{e.v}")
    return m
