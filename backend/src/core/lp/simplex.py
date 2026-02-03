from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
from .errors import UnboundedError

EPS = 1e-9

def pivot(T: List[List[float]], row: int, col: int) -> None:
    # Pivote Gauss-Jordan para hacer (fila,col) basica y anular su columna
    p = T[row][col]
    if abs(p) < EPS:
        raise ValueError("Pivot ~ 0")

    # Normaliza la fila pivote
    T[row] = [v / p for v in T[row]]

    # Elimina la columna pivote del resto
    for r in range(len(T)):
        if r == row:
            continue
        factor = T[r][col]
        if abs(factor) > EPS:
            T[r] = [T[r][j] - factor * T[row][j] for j in range(len(T[0]))]

def choose_entering(cost_row: List[float]) -> int:
    # Para MAX, elige el costo reducido mas negativo
    # Para MAX en tableau con fila 0: entra el mas negativo (mejora mayor).
    min_val = min(cost_row[:-1])  # excluye RHS
    if min_val >= -EPS:
        return -1
    return cost_row[:-1].index(min_val)

def choose_leaving(T: List[List[float]], col: int) -> int:
    # Prueba de razon minima para mantener factibilidad
    # Razon minima RHS / a_ij (a_ij > 0)
    best = None
    for i in range(1, len(T)):
        a = T[i][col]
        if a > EPS:
            ratio = T[i][-1] / a
            cand = (ratio, i)
            if best is None or cand < best:
                best = cand
    return -1 if best is None else best[1]

def _snapshot(
    T: List[List[float]],
    basis: List[int],
    iteration: int,
    enter: int = -1,
    leave: int = -1,
    leave_var: int = -1,
    pivot: Optional[Dict[str, Any]] = None,
    row_ops: Optional[List[str]] = None,
) -> Dict[str, Any]:
    # Captura de una iteracion para UI/historial
    return {
        "iteration": iteration,
        "tableau": [row[:] for row in T],
        "basis": basis[:],
        "enter": enter,
        "leave": leave,
        "leave_var": leave_var,
        "pivot": pivot,
        "row_ops": row_ops or [],
    }

def simplex_max(
    T: List[List[float]],
    basis: List[int],
    log: bool = False,
    max_iter: int = 10_000,
    history: Optional[List[Dict[str, Any]]] = None,
    record_initial: bool = True,
) -> Tuple[List[List[float]], List[int], int]:
    # Bucle principal de simplex para maximizacion en tableau
    it = 0
    if history is not None and record_initial:
        history.append(_snapshot(T, basis, iteration=0))
    while it < max_iter:
        it += 1
        enter = choose_entering(T[0])
        if enter == -1:
            return T, basis, it - 1  # optimo

        leave = choose_leaving(T, enter)
        if leave == -1:
            raise UnboundedError("UNBOUNDED: columna de entrada sin razon valida.")

        if log:
            print(f"[it={it}] enter={enter}, leave={leave}, pivot={T[leave][enter]}")

        leave_var = basis[leave - 1] if 0 <= (leave - 1) < len(basis) else -1
        pivot_value = T[leave][enter]
        pre_T = [row[:] for row in T]
        row_ops = []
        # Row operations are expressed using 1-based row indexes.
        leave_row_disp = leave + 1
        row_ops.append(f"F{leave_row_disp} = F{leave_row_disp} / ({pivot_value})")
        for r in range(len(pre_T)):
            if r == leave:
                continue
            factor = pre_T[r][enter]
            if abs(factor) < EPS:
                continue
            row_ops.append(f"F{r + 1} = F{r + 1} - ({factor}) * F{leave_row_disp}")
        pivot(T, leave, enter)
        basis[leave - 1] = enter
        if history is not None:
            history.append(
                _snapshot(
                    T,
                    basis,
                    iteration=it,
                    enter=enter,
                    leave=leave,
                    leave_var=leave_var,
                    pivot={
                        "row": leave + 1,
                        "col": enter + 1,
                        "value": pivot_value,
                    },
                    row_ops=row_ops,
                )
            )

    raise RuntimeError("Simplex alcanzo max_iter.")

def extract_basic_solution(T: List[List[float]], basis: List[int], n_original: int) -> List[float]:
    # Lee la solucion desde columnas basicas (solo variables originales)
    x = [0.0] * n_original
    for i, col in enumerate(basis):
        if 0 <= col < n_original:
            x[col] = T[i+1][-1]
    return x
