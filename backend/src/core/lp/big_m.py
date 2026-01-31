from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .model import LPModel, LPSolution, Constraint
from .simplex import simplex_max, extract_basic_solution, EPS
from .errors import UnboundedError

M_DEFAULT = 1e6

@dataclass
class BigMBuild:
    T: List[List[float]]
    basis: List[int]
    n_original: int
    artificial_cols: List[int]
    var_names: List[str]

def _normalize_constraint(c: Constraint) -> Constraint:
    if c.b >= 0:
        return c
    a = [-v for v in c.a]
    b = -c.b
    op = c.op
    if op == "<=":
        op = ">="
    elif op == ">=":
        op = "<="
    return Constraint(a=a, op=op, b=b)

def build_tableau_big_m(model: LPModel, M: float = M_DEFAULT) -> BigMBuild:
    constraints = [_normalize_constraint(cc) for cc in model.constraints]
    n = len(model.c)
    m = len(constraints)

    slack = sum(1 for c in constraints if c.op == "<=")
    surplus = sum(1 for c in constraints if c.op == ">=")
    artificial = sum(1 for c in constraints if c.op in (">=", "="))

    total_cols = n + slack + surplus + artificial
    rhs = total_cols
    width = total_cols + 1

    slack_start = n
    surplus_start = n + slack
    artificial_start = n + slack + surplus

    T = [[0.0] * width for _ in range(m + 1)]
    basis = [-1] * m
    artificial_cols: List[int] = []

    c_vec = model.c[:]
    if model.sense == "min":
        c_vec = [-v for v in c_vec]

    for j in range(n):
        T[0][j] = -c_vec[j]

    s_i = e_i = a_i = 0
    for i, cst in enumerate(constraints, start=1):
        for j in range(n):
            T[i][j] = cst.a[j]
        T[i][rhs] = cst.b

        if cst.op == "<=":
            col_s = slack_start + s_i
            T[i][col_s] = 1.0
            basis[i - 1] = col_s
            s_i += 1
        elif cst.op == ">=":
            col_e = surplus_start + e_i
            T[i][col_e] = -1.0
            e_i += 1
            col_a = artificial_start + a_i
            T[i][col_a] = 1.0
            basis[i - 1] = col_a
            artificial_cols.append(col_a)
            a_i += 1
        elif cst.op == "=":
            col_a = artificial_start + a_i
            T[i][col_a] = 1.0
            basis[i - 1] = col_a
            artificial_cols.append(col_a)
            a_i += 1

    var_names = (
        [f"x{j+1}" for j in range(n)]
        + [f"s{k+1}" for k in range(slack)]
        + [f"e{k+1}" for k in range(surplus)]
        + [f"a{k+1}" for k in range(artificial)]
    )

    # Penalizacion: artificial tiene costo -M (max) => fila 0 usa -c, por eso +M
    for col_a in artificial_cols:
        T[0][col_a] = M

    # Canonicidad para basicas artificiales
    for row_idx, bcol in enumerate(basis, start=1):
        if bcol in artificial_cols:
            factor = M
            T[0] = [T[0][j] - factor * T[row_idx][j] for j in range(width)]

    return BigMBuild(T=T, basis=basis, n_original=n, artificial_cols=artificial_cols, var_names=var_names)


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

def solve_big_m(model: LPModel, M: float = M_DEFAULT, log: bool=False) -> LPSolution:
    build = build_tableau_big_m(model, M=M)

    try:
        history = []
        Tfinal, bfinal, it = simplex_max(build.T, build.basis, log=log, history=history)
    except UnboundedError as e:
        return LPSolution(status="UNBOUNDED", x=[0.0] * build.n_original, objective_value=float("inf"),
                          iterations=0, message=str(e), method_used="big_m")

    # factibilidad: artificial basica > 0 => infactible
    for i, bcol in enumerate(bfinal, start=1):
        if bcol in build.artificial_cols and Tfinal[i][-1] > 1e-7:
            extra = _final_info(Tfinal, bfinal, build.var_names)
            extra["tableau_history"] = {
                "label": "Big M",
                "var_names": build.var_names,
                "items": history,
            }
            return LPSolution(status="INFEASIBLE", x=[0.0] * build.n_original, objective_value=float("nan"),
                              iterations=it, message="INFEASIBLE: artificial basica positiva.", method_used="big_m",
                              extra=extra)

    x = extract_basic_solution(Tfinal, bfinal, build.n_original)
    z = Tfinal[0][-1]
    if model.sense == "min":
        z = -z

    extra = _final_info(Tfinal, bfinal, build.var_names)
    extra["tableau_history"] = {
        "label": "Big M",
        "var_names": build.var_names,
        "items": history,
    }
    return LPSolution(status="OPTIMAL", x=x, objective_value=z, iterations=it, message="OK",
                      method_used="big_m", extra=extra)
