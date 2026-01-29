from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .model import LPModel, LPSolution, Constraint
from .simplex import simplex_max, extract_basic_solution, EPS
from .errors import UnboundedError

@dataclass
class BasicBuild:
    T: List[List[float]]
    basis: List[int]
    n_original: int
    var_names: List[str]

def build_basic_tableau(model: LPModel) -> BasicBuild:
    # Requiere: todas las restricciones <= y b >= 0
    n = len(model.c)
    m = len(model.constraints)

    # slack por restricción
    total_cols = n + m
    rhs = total_cols
    width = total_cols + 1

    T = [[0.0]*width for _ in range(m+1)]
    basis = [-1]*m

    # Convertir a max si es min: max(-c)
    c_vec = model.c[:]
    if model.sense == "min":
        c_vec = [-v for v in c_vec]

    # fila 0 = -c (para max)
    for j in range(n):
        T[0][j] = -c_vec[j]

    # restricciones
    for i, cst in enumerate(model.constraints, start=1):
        for j in range(n):
            T[i][j] = cst.a[j]
        # slack
        slack_col = n + (i-1)
        T[i][slack_col] = 1.0
        basis[i-1] = slack_col
        T[i][rhs] = cst.b

    var_names = [f"x{i+1}" for i in range(n)] + [f"s{i+1}" for i in range(m)]
    return BasicBuild(T=T, basis=basis, n_original=n, var_names=var_names)


def _final_info(T: List[List[float]], basis: List[int], var_names: List[str]) -> dict:
    basic_vars = [var_names[i] if 0 <= i < len(var_names) else "?" for i in basis]
    nonbasic_vars = [var_names[j] for j in range(len(var_names)) if j not in basis]
    return {
        "final_tableau": T,
        "basis": basis,
        "var_names": var_names,
        "basic_vars": basic_vars,
        "nonbasic_vars": nonbasic_vars,
        "row0": T[0][:-1],
    }

def solve_simplex_basic(model: LPModel, log: bool=False) -> LPSolution:
    build = build_basic_tableau(model)
    try:
        Tfinal, bfinal, it = simplex_max(build.T, build.basis, log=log)
    except UnboundedError as e:
        return LPSolution(status="UNBOUNDED", x=[0.0]*build.n_original, objective_value=float("inf"),
                          iterations=0, message=str(e), method_used="simplex")

    x = extract_basic_solution(Tfinal, bfinal, build.n_original)
    z = Tfinal[0][-1]
    if model.sense == "min":
        z = -z
    extra = _final_info(Tfinal, bfinal, build.var_names)
    return LPSolution(status="OPTIMAL", x=x, objective_value=z, iterations=it, message="OK",
                      method_used="simplex", extra=extra)
