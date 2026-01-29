from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class TransportModel:
    supply: List[float]
    demand: List[float]
    costs: List[List[float]]
    name: str = "transport"

    # Optional labels for UI/reporting
    origins: Optional[List[str]] = None
    destinations: Optional[List[str]] = None


@dataclass
class TransportSolution:
    status: str  # "OPTIMAL" | "FEASIBLE" | "ERROR"
    allocation: List[List[float]]
    total_cost: float
    has_M: bool
    method_used: str
    iterations: int = 0
    message: str = ""
    extra: Optional[Dict[str, Any]] = None
