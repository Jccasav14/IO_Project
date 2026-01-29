from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .errors import TransportModelError
from .model import TransportModel

BIG_M = 1_000_000_000.0


def parse_val(v: Any) -> float:
    """Parse a single value.

    Supports:
    - numbers (int/float)
    - strings like "M" (big penalty) or "10.5"
    """
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().upper()
        if s == "M":
            return float(BIG_M)
        try:
            return float(s)
        except ValueError as e:
            raise TransportModelError(f"Invalid numeric value: {v!r}") from e
    raise TransportModelError(f"Invalid value type: {type(v).__name__}")


def model_from_dict(d: Dict[str, Any]) -> TransportModel:
    if not isinstance(d, dict):
        raise TransportModelError("Model must be an object")

    supply_raw = d.get("supply")
    demand_raw = d.get("demand")
    costs_raw = d.get("costs")

    if supply_raw is None or demand_raw is None or costs_raw is None:
        raise TransportModelError("Model must include supply, demand, and costs")

    if not isinstance(supply_raw, list) or not isinstance(demand_raw, list) or not isinstance(costs_raw, list):
        raise TransportModelError("supply, demand, and costs must be arrays")

    supply = [parse_val(x) for x in supply_raw]
    demand = [parse_val(x) for x in demand_raw]

    costs: List[List[float]] = []
    for row in costs_raw:
        if not isinstance(row, list):
            raise TransportModelError("costs must be a 2D array")
        costs.append([parse_val(x) for x in row])

    if len(costs) != len(supply):
        raise TransportModelError("Rows of costs must match number of origins (len(supply))")
    if any(len(row) != len(demand) for row in costs):
        raise TransportModelError("Columns of costs must match number of destinations (len(demand))")

    return TransportModel(
        supply=supply,
        demand=demand,
        costs=costs,
        name=str(d.get("name", "transport")),
        origins=d.get("origins") if isinstance(d.get("origins"), list) else None,
        destinations=d.get("destinations") if isinstance(d.get("destinations"), list) else None,
    )
