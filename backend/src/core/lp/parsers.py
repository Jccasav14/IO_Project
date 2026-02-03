from __future__ import annotations
from .model import LPModel, Constraint

def model_from_dict(d: dict) -> LPModel:
    # Construye un LPModel interno desde un diccionario tipo JSON
    constraints = [Constraint(a=c["a"], op=c["op"], b=c["b"]) for c in d["constraints"]]
    return LPModel(
        name=d.get("name", "LP"),
        sense=d["sense"],
        c=d["c"],
        constraints=constraints,
        nonneg=True,
    )
