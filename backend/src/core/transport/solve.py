from __future__ import annotations

from typing import Any, Dict, Literal, Tuple

from .errors import TransportModelError
from .parsers import model_from_dict
from .algorithms import (
    balance_problem,
    northwest_corner,
    min_cost_method,
    vogel_approximation,
    optimize_stepping_stone,
    total_cost,
)

Method = Literal["auto", "northwest", "min_cost", "vogel", "optimize", "compare"]


def _pack(name: str, alloc, costs) -> Dict[str, Any]:
    z, has_M = total_cost(alloc, costs)
    return {
        "method": name,
        "total_cost": z,
        "has_M": has_M,
        "allocation": alloc,
    }


def solve_transport(problem: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(problem, dict):
        raise TransportModelError("Request must be a JSON object")

    method: str = str(problem.get("method", "auto")).strip().lower()
    model_dict = problem.get("model") if "model" in problem else problem

    m = model_from_dict(model_dict)
    bal = balance_problem(m.supply, m.demand, m.costs)

    opts = problem.get("options") if isinstance(problem.get("options"), dict) else {}
    compare_all = bool(opts.get("compare_all", method == "compare"))
    do_opt = bool(opts.get("optimize", method in ("auto", "optimize", "compare")))
    max_it = int(opts.get("max_iterations", 10_000))

    # --- 1) Siempre calculamos los 3 iniciales si compare_all ---
    if compare_all:
        alloc_nw = northwest_corner(bal.supply, bal.demand)
        alloc_mc = min_cost_method(bal.supply, bal.demand, bal.costs)
        alloc_vam = vogel_approximation(bal.supply, bal.demand, bal.costs)

        s_nw = _pack("northwest", alloc_nw, bal.costs)
        s_mc = _pack("min_cost", alloc_mc, bal.costs)
        s_vam = _pack("vogel", alloc_vam, bal.costs)

        initials = {
            "northwest": s_nw,
            "min_cost": s_mc,
            "vogel": s_vam,
        }

        # Elegimos como punto de partida para optimizar el mejor (menor costo)
        # Nota: si hay "M" en alguno, igual se compara por z (tu total_cost ya lo maneja)
        best_key = min(initials.keys(), key=lambda k: initials[k]["total_cost"])
        start_alloc = initials[best_key]["allocation"]
        started_from = best_key

        iterations = 0
        final_alloc = start_alloc

        if do_opt:
            final_alloc, iterations = optimize_stepping_stone(
                start_alloc, bal.costs, max_iterations=max_it
            )

        optimal = _pack("optimal", final_alloc, bal.costs)
        optimal["iterations"] = iterations
        optimal["started_from"] = started_from
        optimal["status"] = "OPTIMAL" if do_opt else "FEASIBLE"

        return {
            "status": optimal["status"],
            "compare": True,
            "initials": initials,
            "optimal": optimal,
            "extra": {
                "balanced": {
                    "added_dummy_origin": bal.added_dummy_origin,
                    "added_dummy_destination": bal.added_dummy_destination,
                    "rows": len(bal.supply),
                    "cols": len(bal.demand),
                }
            },
        }

    # --- 2) Modo normal (como lo tenías) ---
    # Inicial factible según método
    if method in ("northwest", "esquina_noroeste", "nw"):
        alloc = northwest_corner(bal.supply, bal.demand)
        used = "northwest"
    elif method in ("min_cost", "costo_minimo", "least_cost"):
        alloc = min_cost_method(bal.supply, bal.demand, bal.costs)
        used = "min_cost"
    else:
        alloc = vogel_approximation(bal.supply, bal.demand, bal.costs)
        used = "vogel"

    iterations = 0
    if do_opt:
        alloc, iterations = optimize_stepping_stone(alloc, bal.costs, max_iterations=max_it)
        used = f"{used}+optimize"

    z, has_M = total_cost(alloc, bal.costs)

    return {
        "status": "OPTIMAL" if do_opt else "FEASIBLE",
        "method_used": used,
        "iterations": iterations,
        "total_cost": z,
        "has_M": has_M,
        "allocation": alloc,
        "extra": {
            "balanced": {
                "added_dummy_origin": bal.added_dummy_origin,
                "added_dummy_destination": bal.added_dummy_destination,
                "rows": len(bal.supply),
                "cols": len(bal.demand),
            }
        },
    }
