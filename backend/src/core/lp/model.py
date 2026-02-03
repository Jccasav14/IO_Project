from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional, Dict, Any

Op = Literal["<=", ">=", "="]
Sense = Literal["max", "min"]

@dataclass
class Constraint:
    # Restriccion lineal: a * x (op) b
    a: List[float]
    op: Op
    b: float

@dataclass
class LPModel:
    # Modelo de Programacion Lineal con variables no negativas (x >= 0)
    name: str
    sense: Sense
    c: List[float]
    constraints: List[Constraint]
    # Para el proyecto asumimos variables no negativas: x >= 0
    nonneg: bool = True

@dataclass
class LPSolution:
    # Contenedor estandar de la solucion retornada por los solvers
    status: str  # "OPTIMAL" | "INFEASIBLE" | "UNBOUNDED"
    x: List[float]
    objective_value: float
    iterations: int
    message: str = ""
    method_used: str = ""
    # (opcional) info adicional para reporte/defensa
    extra: Optional[Dict[str, Any]] = None
