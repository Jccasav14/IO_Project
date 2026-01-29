from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

from .model import LPModel, LPSolution, Constraint
from .simplex import simplex_max, extract_basic_solution, pivot, EPS
from .errors import UnboundedError

@dataclass
class TwoPhaseBuild:
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

def build_phase1_tableau(model: LPModel) -> TwoPhaseBuild:
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

    T = [[0.0]*width for _ in range(m+1)]
    basis = [-1]*m
    artificial_cols: List[int] = []

    s_i = e_i = a_i = 0
    for i, cst in enumerate(constraints, start=1):
        for j in range(n):
            T[i][j] = cst.a[j]
        T[i][rhs] = cst.b

        if cst.op == "<=":
            col_s = slack_start + s_i
            T[i][col_s] = 1.0
            basis[i-1] = col_s
            s_i += 1
        elif cst.op == ">=":
            col_e = surplus_start + e_i
            T[i][col_e] = -1.0
            e_i += 1
            col_a = artificial_start + a_i
            T[i][col_a] = 1.0
            basis[i-1] = col_a
            artificial_cols.append(col_a)
            a_i += 1
        elif cst.op == "=":
            col_a = artificial_start + a_i
            T[i][col_a] = 1.0
            basis[i-1] = col_a
            artificial_cols.append(col_a)
            a_i += 1

    var_names = (
        [f"x{j+1}" for j in range(n)]
        + [f"s{k+1}" for k in range(slack)]
        + [f"e{k+1}" for k in range(surplus)]
        + [f"a{k+1}" for k in range(artificial)]
    )

    # Fase I: max(-sum a) => c_artificial = -1 => fila0 = -c => +1
    for col_a in artificial_cols:
        T[0][col_a] = 1.0

    # Canónica: si una artificial está básica, eliminarla de la fila 0
    for row_idx, bcol in enumerate(basis, start=1):
        if bcol in artificial_cols:
            factor = T[0][bcol]
            if abs(factor) > EPS:
                T[0] = [T[0][j] - factor*T[row_idx][j] for j in range(width)]

    return TwoPhaseBuild(T=T, basis=basis, n_original=n, artificial_cols=artificial_cols, var_names=var_names)

def _remove_columns(T: List[List[float]], remove_cols: List[int]) -> List[List[float]]:
    keep = [j for j in range(len(T[0])) if j not in set(remove_cols)]
    return [[row[j] for j in keep] for row in T]

def _map_basis_after_removal(basis: List[int], remove_cols: List[int]) -> List[int]:
    remove_cols = sorted(remove_cols)
    remove_set = set(remove_cols)
    def new_index(old: int) -> int:
        shift = 0
        for c in remove_cols:
            if c < old:
                shift += 1
        return old - shift
    nb = []
    for b in basis:
        if b in remove_set:
            nb.append(-1)
        else:
            nb.append(new_index(b))
    return nb


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

def _rebuild_phase2_objective(T: List[List[float]], basis: List[int], c: List[float], sense: str) -> None:
    c_vec = c[:]
    if sense == "min":
        c_vec = [-v for v in c_vec]

    width = len(T[0])
    n_original = len(c_vec)

    # fila 0 = -c
    T[0] = [0.0]*width
    for j in range(n_original):
        T[0][j] = -c_vec[j]

    # hacer canónica respecto a la base
    for i, bcol in enumerate(basis, start=1):
        if 0 <= bcol < n_original:
            cost = -T[0][bcol]  # c_k
            if abs(cost) > EPS:
                T[0] = [T[0][j] + cost*T[i][j] for j in range(width)]

def _pivot_out_artificial_zeros(T: List[List[float]], basis: List[int], n_original: int) -> None:
    # Si quedó una columna removida como básica (-1 en basis) con RHS 0, intentamos pivotear
    # buscando una columna no básica con coef !=0 en esa fila para formar base.
    # Esto es raro en ejercicios típicos, pero lo soportamos.
    for i, bcol in enumerate(basis, start=1):
        if bcol != -1:
            continue
        if abs(T[i][-1]) > 1e-7:
            # si RHS no es 0, no deberíamos estar aquí
            continue
        # buscar columna candidata
        for j in range(len(T[0]) - 1):
            # evitar columnas de variables originales? no; podemos usar cualquiera salvo RHS
            if abs(T[i][j]) > 1e-9:
                pivot(T, i, j)
                basis[i-1] = j
                break

def solve_two_phase(model: LPModel, log: bool=False) -> LPSolution:
    # Fase I
    build = build_phase1_tableau(model)
    T1, b1 = build.T, build.basis

    try:
        T1, b1, it1 = simplex_max(T1, b1, log=log)
    except UnboundedError as e:
        return LPSolution(status="UNBOUNDED", x=[0.0]*build.n_original, objective_value=float("inf"),
                          iterations=0, message=str(e), method_used="two_phase")

    phase1_obj = T1[0][-1]
    if abs(phase1_obj) > 1e-7:
        return LPSolution(status="INFEASIBLE", x=[0.0]*build.n_original, objective_value=float("nan"),
                          iterations=it1, message="INFEASIBLE: Fase I no llegó a 0.", method_used="two_phase")

    # Chequeo artificial básica > 0
    for i, bcol in enumerate(b1, start=1):
        if bcol in build.artificial_cols and T1[i][-1] > 1e-7:
            return LPSolution(status="INFEASIBLE", x=[0.0]*build.n_original, objective_value=float("nan"),
                              iterations=it1, message="INFEASIBLE: artificial básica positiva.", method_used="two_phase")

    # Fase II: eliminar columnas artificiales
    remove_cols = sorted(build.artificial_cols)
    T2 = _remove_columns(T1, remove_cols)
    b2 = _map_basis_after_removal(b1, remove_cols)
    var_names2 = [v for i, v in enumerate(build.var_names) if i not in set(remove_cols)]

    # limpiar posibles -1
    _pivot_out_artificial_zeros(T2, b2, build.n_original)

    _rebuild_phase2_objective(T2, b2, model.c, model.sense)

    try:
        Tfinal, bfinal, it2 = simplex_max(T2, b2, log=log)
    except UnboundedError as e:
        return LPSolution(status="UNBOUNDED", x=[0.0]*build.n_original, objective_value=float("inf"),
                          iterations=it1, message=str(e), method_used="two_phase")

    x = extract_basic_solution(Tfinal, bfinal, build.n_original)
    z = Tfinal[0][-1]
    if model.sense == "min":
        z = -z

    extra = _final_info(Tfinal, bfinal, var_names2)
    return LPSolution(status="OPTIMAL", x=x, objective_value=z, iterations=it1+it2,
                      message="OK", method_used="two_phase", extra=extra)
