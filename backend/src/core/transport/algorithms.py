from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any, Union

BIG_M = 1_000_000_000.0


@dataclass
class Balanced:
    supply: List[float]
    demand: List[float]
    costs: List[List[float]]
    added_dummy_origin: bool = False
    added_dummy_destination: bool = False


def balance_problem(supply: List[float], demand: List[float], costs: List[List[float]]) -> Balanced:
    # Defensive copies
    s = list(supply)
    d = list(demand)
    c = [row[:] for row in costs]

    s_sum = sum(s)
    d_sum = sum(d)

    # Float-tolerant comparison
    if round(s_sum, 8) > round(d_sum, 8):
        diff = s_sum - d_sum
        d.append(diff)
        for row in c:
            row.append(0.0)
        return Balanced(s, d, c, added_dummy_destination=True)

    if round(d_sum, 8) > round(s_sum, 8):
        diff = d_sum - s_sum
        s.append(diff)
        c.append([0.0] * len(d))
        return Balanced(s, d, c, added_dummy_origin=True)

    return Balanced(s, d, c)


def total_cost(allocation: List[List[float]], costs: List[List[float]]) -> Tuple[float, bool]:
    z = 0.0
    has_M = False
    for i in range(len(allocation)):
        for j in range(len(allocation[0]) if allocation else 0):
            qty = allocation[i][j]
            if qty > 0:
                cc = costs[i][j]
                if cc >= BIG_M - 1_000:
                    has_M = True
                z += qty * cc
    return z, has_M


def northwest_corner(supply: List[float], demand: List[float]) -> List[List[float]]:
    rows = len(supply)
    cols = len(demand)
    alloc = [[0.0 for _ in range(cols)] for _ in range(rows)]

    s = list(supply)
    d = list(demand)

    i, j = 0, 0
    while i < rows and j < cols:
        qty = min(s[i], d[j])
        alloc[i][j] = qty
        s[i] -= qty
        d[j] -= qty

        if s[i] <= 1e-9 and d[j] <= 1e-9:
            i += 1
            j += 1
        elif s[i] <= 1e-9:
            i += 1
        else:
            j += 1
    return alloc


def min_cost_method(supply: List[float], demand: List[float], costs: List[List[float]]) -> List[List[float]]:
    rows = len(supply)
    cols = len(demand)
    alloc = [[0.0 for _ in range(cols)] for _ in range(rows)]

    s = list(supply)
    d = list(demand)

    cells = [(costs[i][j], i, j) for i in range(rows) for j in range(cols)]
    cells.sort(key=lambda x: x[0])

    for _, i, j in cells:
        if s[i] > 1e-9 and d[j] > 1e-9:
            qty = min(s[i], d[j])
            alloc[i][j] = qty
            s[i] -= qty
            d[j] -= qty
    return alloc


def vogel_approximation(supply: List[float], demand: List[float], costs: List[List[float]]) -> List[List[float]]:
    rows = len(supply)
    cols = len(demand)
    alloc = [[0.0 for _ in range(cols)] for _ in range(rows)]

    s = list(supply)
    d = list(demand)
    r_done = [False] * rows
    c_done = [False] * cols

    allocated_count = 0
    target = rows + cols - 1

    while allocated_count < target:
        if all(r_done) or all(c_done):
            break

        r_pen = []
        for i in range(rows):
            if r_done[i]:
                r_pen.append(-1.0)
                continue
            vals = [costs[i][j] for j in range(cols) if not c_done[j]]
            if len(vals) >= 2:
                vals.sort()
                r_pen.append(vals[1] - vals[0])
            elif len(vals) == 1:
                r_pen.append(vals[0])
            else:
                r_pen.append(-1.0)

        c_pen = []
        for j in range(cols):
            if c_done[j]:
                c_pen.append(-1.0)
                continue
            vals = [costs[i][j] for i in range(rows) if not r_done[i]]
            if len(vals) >= 2:
                vals.sort()
                c_pen.append(vals[1] - vals[0])
            elif len(vals) == 1:
                c_pen.append(vals[0])
            else:
                c_pen.append(-1.0)

        max_r = max(r_pen) if r_pen else -1.0
        max_c = max(c_pen) if c_pen else -1.0
        if max_r == -1.0 and max_c == -1.0:
            break

        target_r, target_c = -1, -1

        if max_r >= max_c:
            target_r = r_pen.index(max_r)
            min_val = float("inf")
            for j in range(cols):
                if not c_done[j] and costs[target_r][j] < min_val:
                    min_val = costs[target_r][j]
                    target_c = j
        else:
            target_c = c_pen.index(max_c)
            min_val = float("inf")
            for i in range(rows):
                if not r_done[i] and costs[i][target_c] < min_val:
                    min_val = costs[i][target_c]
                    target_r = i

        qty = min(s[target_r], d[target_c])
        alloc[target_r][target_c] = qty
        s[target_r] -= qty
        d[target_c] -= qty

        if s[target_r] <= 1e-9:
            r_done[target_r] = True
        if d[target_c] <= 1e-9:
            c_done[target_c] = True
        allocated_count += 1

    # Residual fill (safety)
    for i in range(rows):
        for j in range(cols):
            if s[i] > 1e-9 and d[j] > 1e-9:
                qty = min(s[i], d[j])
                alloc[i][j] += qty
                s[i] -= qty
                d[j] -= qty

    return alloc


# ----------------------
# Optimization: Stepping-Stone (a.k.a. transportation simplex)
# ----------------------

def _find_closed_path(allocation: List[List[float]], start: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    rows = len(allocation)
    cols = len(allocation[0]) if rows else 0

    # DFS with alternating moves (H/V)
    stack = [(start, [start], None)]  # (curr, path, prev_dir)
    while stack:
        curr, path, prev_dir = stack.pop()
        r, c = curr

        if curr == start and len(path) > 1:
            if len(path) >= 4:
                return path[:-1]

        neighbors: List[Tuple[Tuple[int, int], str]] = []

        if prev_dir != "V":
            # vertical neighbors in same column
            for i in range(rows):
                if i != r and (allocation[i][c] > 1e-9 or (i, c) == start):
                    neighbors.append(((i, c), "V"))

        if prev_dir != "H":
            # horizontal neighbors in same row
            for j in range(cols):
                if j != c and (allocation[r][j] > 1e-9 or (r, j) == start):
                    neighbors.append(((r, j), "H"))

        for n_node, n_dir in neighbors:
            if n_node == start:
                if len(path) >= 3:
                    stack.append((n_node, path + [n_node], n_dir))
            elif n_node not in path:
                stack.append((n_node, path + [n_node], n_dir))

    return None


def optimize_stepping_stone(
    allocation: List[List[float]],
    costs: List[List[float]],
    max_iterations: int = 10_000,
    trace: bool = False,
    trace_limit: int = 200,
) -> Union[Tuple[List[List[float]], int], Tuple[List[List[float]], int, List[Dict[str, Any]]]]:
    rows = len(allocation)
    cols = len(allocation[0]) if rows else 0

    alloc = [row[:] for row in allocation]
    it = 0

    trace_steps: List[Dict[str, Any]] = []

    # helper: costo total actual (sin M aquí; si usas M en total_cost(), úsala en solve.py)
    def _total_cost(a: List[List[float]]) -> float:
        z = 0.0
        for r in range(rows):
            for c in range(cols):
                z += a[r][c] * costs[r][c]
        return z

    while it < max_iterations:
        it += 1

        best_marginal = 0.0
        enter_cell: Optional[Tuple[int, int]] = None
        best_cycle: Optional[List[Tuple[int, int]]] = None

        for i in range(rows):
            for j in range(cols):
                if alloc[i][j] <= 1e-9:  # empty cell
                    cycle = _find_closed_path(alloc, (i, j))
                    if not cycle:
                        continue

                    marginal = 0.0
                    for k, (r, c) in enumerate(cycle):
                        if k % 2 == 0:
                            marginal += costs[r][c]
                        else:
                            marginal -= costs[r][c]

                    # buscamos mejora => marginal negativo (más negativo, mejor)
                    if marginal < best_marginal - 1e-9:
                        best_marginal = marginal
                        enter_cell = (i, j)
                        best_cycle = cycle

        # Si no hay mejora, terminamos: ya es óptimo
        if enter_cell is None or best_cycle is None:
            break

        # Theta = min asignación en posiciones '-' (k impar)
        minus_positions = [(r, c) for k, (r, c) in enumerate(best_cycle) if k % 2 == 1]
        if not minus_positions:
            break

        theta = min(alloc[r][c] for (r, c) in minus_positions)

        # celda que sale: una de las '-' que alcanza el mínimo (queda en 0)
        leaving_cell: Optional[Tuple[int, int]] = None
        for (r, c) in minus_positions:
            if abs(alloc[r][c] - theta) <= 1e-9:
                leaving_cell = (r, c)
                break

        # aplicar ajuste
        for k, (r, c) in enumerate(best_cycle):
            if k % 2 == 0:
                alloc[r][c] += theta
            else:
                alloc[r][c] -= theta
                if alloc[r][c] < 1e-9:
                    alloc[r][c] = 0.0

        # guardar trace (si está activado)
        if trace and len(trace_steps) < trace_limit:
            trace_steps.append({
                "iter": it,
                "enter": [enter_cell[0], enter_cell[1]],
                "delta": float(best_marginal),        # marginal (Δ) - si es negativo, mejora
                "theta": float(theta),
                "cycle": [[r, c] for (r, c) in best_cycle],
                "leaving": [leaving_cell[0], leaving_cell[1]] if leaving_cell else None,
                "total_cost": float(_total_cost(alloc)),
                "allocation": [row[:] for row in alloc],
            })

    if trace:
        return alloc, it, trace_steps
    return alloc, it
