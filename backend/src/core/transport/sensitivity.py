from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

EPS = 1e-9


def _basic_cells(allocation: List[List[float]]) -> List[Tuple[int, int]]:
    basics: List[Tuple[int, int]] = []
    for i, row in enumerate(allocation):
        for j, x in enumerate(row):
            if x > EPS:
                basics.append((i, j))
    return basics


def compute_potentials(
    costs: List[List[float]],
    allocation: List[List[float]],
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Potenciales (u, v) estilo MODI: en celdas básicas se cumple c_ij = u_i + v_j.
    Fijamos u[0]=0 por componente conectada del grafo básico.
    """
    rows = len(allocation)
    cols = len(allocation[0]) if rows else 0

    u: List[Optional[float]] = [None] * rows
    v: List[Optional[float]] = [None] * cols

    basics = _basic_cells(allocation)
    if rows == 0 or cols == 0 or not basics:
        return u, v

    row_to_cols: List[List[int]] = [[] for _ in range(rows)]
    col_to_rows: List[List[int]] = [[] for _ in range(cols)]
    for i, j in basics:
        row_to_cols[i].append(j)
        col_to_rows[j].append(i)

    for seed_i in range(rows):
        if not row_to_cols[seed_i]:
            continue
        if u[seed_i] is not None:
            continue

        u[seed_i] = 0.0
        stack: List[Tuple[str, int]] = [("r", seed_i)]

        while stack:
            typ, idx = stack.pop()
            if typ == "r":
                i = idx
                for j in row_to_cols[i]:
                    if v[j] is None and u[i] is not None:
                        v[j] = costs[i][j] - u[i]
                        stack.append(("c", j))
            else:
                j = idx
                for i in col_to_rows[j]:
                    if u[i] is None and v[j] is not None:
                        u[i] = costs[i][j] - v[j]
                        stack.append(("r", i))

    return u, v


def reduced_costs(
    costs: List[List[float]],
    u: List[Optional[float]],
    v: List[Optional[float]],
) -> List[List[Optional[float]]]:
    rows = len(costs)
    cols = len(costs[0]) if rows else 0
    rc: List[List[Optional[float]]] = [[None for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            if u[i] is None or v[j] is None:
                rc[i][j] = None
            else:
                rc[i][j] = float(costs[i][j] - u[i] - v[j])
    return rc


def transport_sensitivity(costs: List[List[float]], allocation: List[List[float]]) -> Dict[str, Any]:
    """
    Sensibilidad para Transporte (MODI):
    - u, v: potenciales (interpretables como “precios sombra”)
    - reduced_costs: c_ij - u_i - v_j en rutas NO básicas
    - nonbasic_cost_decrease_needed: cuánto tendría que bajar el costo para que una ruta vacía sea atractiva
    - alternate_optimal_routes: rutas vacías con rc≈0 (posibles óptimos alternativos)
    """
    u, v = compute_potentials(costs, allocation)
    rc = reduced_costs(costs, u, v)

    rows = len(allocation)
    cols = len(allocation[0]) if rows else 0

    best_neg = None
    for i in range(rows):
        for j in range(cols):
            if allocation[i][j] > EPS:
                continue
            val = rc[i][j]
            if val is None:
                continue
            if val < -1e-7:
                if best_neg is None or val < best_neg["reduced_cost"]:
                    best_neg = {"i": i, "j": j, "reduced_cost": float(val)}

    is_optimal = best_neg is None

    thresholds: List[List[Optional[float]]] = [[None for _ in range(cols)] for _ in range(rows)]
    alt_opt: List[List[bool]] = [[False for _ in range(cols)] for _ in range(rows)]

    for i in range(rows):
        for j in range(cols):
            if allocation[i][j] > EPS:
                continue
            val = rc[i][j]
            if val is None:
                thresholds[i][j] = None
                continue
            if abs(val) <= 1e-7:
                alt_opt[i][j] = True
                thresholds[i][j] = 0.0
            elif val > 0:
                thresholds[i][j] = float(val)   # cuánto debe BAJAR
            else:
                thresholds[i][j] = float(val)   # negativo => ya mejora (no óptimo)

    return {
        "u": u,
        "v": v,
        "reduced_costs": rc,
        "is_optimal_by_reduced_costs": is_optimal,
        "most_negative": best_neg,
        "nonbasic_cost_decrease_needed": thresholds,
        "alternate_optimal_routes": alt_opt,
    }
