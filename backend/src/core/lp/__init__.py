from __future__ import annotations
from typing import Optional, Union, Literal

from .model import LPModel, LPSolution
from .parsers import model_from_dict
from .simplex_basic import solve_simplex_basic
from .two_phase import solve_two_phase
from .big_m import solve_big_m
from .dual import build_dual

Method = Literal["auto", "simplex", "two_phase", "big_m", "dual"]

def can_use_basic_simplex(model: LPModel) -> bool:
    # Simplex basico solo funciona si todas las restricciones son <= y b>=0
    # Todas <= y b >= 0
    return all(c.op == "<=" and c.b >= 0 for c in model.constraints)

def choose_method(model: LPModel) -> str:
    # Selector automatico: usa simplex si aplica, si no Two-Phase
    # Regla: si todo es <= y b>=0 => simplex; caso contrario => two_phase (robusto)
    return "simplex" if can_use_basic_simplex(model) else "two_phase"

def solve_lp(model_input: Union[dict, LPModel], method: Method = "auto", log: bool = False) -> LPSolution:
    # Normaliza la entrada a LPModel y ejecuta el solver elegido
    model = model_input if isinstance(model_input, LPModel) else model_from_dict(model_input)

    if method == "auto":
        method = choose_method(model)  # type: ignore

    if method == "simplex":
        # Si el usuario fuerza simplex pero no cumple condiciones, devolvemos mensaje claro
        if not can_use_basic_simplex(model):
            # En vez de fallar, resolvemos con two_phase pero lo reportamos
            res = solve_two_phase(model, log=log)
            res.message = "Simplex básico no aplicaba (hay >= o = o RHS<0). Se resolvió con Two-Phase."
            res.method_used = "two_phase"
            return res
        return solve_simplex_basic(model, log=log)

    if method == "two_phase":
        return solve_two_phase(model, log=log)

    if method == "big_m":
        return solve_big_m(model, log=log)

    if method == "dual":
        # Construimos dual y lo resolvemos automáticamente con el selector (o Two-Phase por robustez)
        dual_model, mapping = build_dual(model)
        dual_res = solve_two_phase(dual_model, log=log)
        # En teoría z_primal == z_dual (con signos según max/min); aquí reportamos el dual.
        dual_res.method_used = "dual(two_phase)"
        dual_res.extra = dual_res.extra or {}
        dual_res.extra["dual_mapping"] = mapping
        dual_res.extra["dual_model_name"] = dual_model.name
        return dual_res

    raise ValueError(f"Método no soportado: {method}")
