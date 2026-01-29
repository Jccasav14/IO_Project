from __future__ import annotations
from typing import List, Tuple
from .errors import UnboundedError

EPS = 1e-9

def pivot(T: List[List[float]], row: int, col: int) -> None:
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
    # Para MAX en tableau con fila 0: entra el más negativo (mejora mayor).
    min_val = min(cost_row[:-1])  # excluye RHS
    if min_val >= -EPS:
        return -1
    return cost_row[:-1].index(min_val)

def choose_leaving(T: List[List[float]], col: int) -> int:
    # Razón mínima RHS / a_ij (a_ij > 0)
    best = None
    for i in range(1, len(T)):
        a = T[i][col]
        if a > EPS:
            ratio = T[i][-1] / a
            cand = (ratio, i)
            if best is None or cand < best:
                best = cand
    return -1 if best is None else best[1]

def simplex_max(T: List[List[float]], basis: List[int], log: bool=False, max_iter: int=10_000) -> Tuple[List[List[float]], List[int], int]:
    it = 0
    while it < max_iter:
        it += 1
        enter = choose_entering(T[0])
        if enter == -1:
            return T, basis, it - 1  # óptimo

        leave = choose_leaving(T, enter)
        if leave == -1:
            raise UnboundedError("UNBOUNDED: columna de entrada sin razón válida.")

        if log:
            print(f"[it={it}] enter={enter}, leave={leave}, pivot={T[leave][enter]}")

        pivot(T, leave, enter)
        basis[leave - 1] = enter

    raise RuntimeError("Simplex alcanzó max_iter.")

def extract_basic_solution(T: List[List[float]], basis: List[int], n_original: int) -> List[float]:
    x = [0.0] * n_original
    for i, col in enumerate(basis):
        if 0 <= col < n_original:
            x[col] = T[i+1][-1]
    return x
