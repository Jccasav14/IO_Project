from __future__ import annotations
from typing import List, Tuple
from .model import LPModel, Constraint

def _normalize_constraint_for_dual(c: Constraint) -> Constraint:
    # Asegura b>=0 multiplicando por -1 cuando es necesario
    # Igual que en otros módulos: asegura b >= 0
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

def build_dual(primal: LPModel) -> Tuple[LPModel, dict]:
    """
    Construye el dual para el caso del curso: variables del primal x >= 0.

    Manejo de restricciones del primal (para primal MAX; para MIN se invierte):
      - <=  -> y_i >= 0
      - >=  -> y_i <= 0  (representamos y_i = -y'_i, y'_i>=0)
      - =   -> y_i libre (y_i = y_i^+ - y_i^-, ambas >=0)

    Retorna: (dual_model, mapping_info)
    mapping_info permite interpretar las variables duales originales si lo desean.
    """
    # Normaliza restricciones para signos consistentes
    # Normalizar b>=0 para estabilidad
    cons = [_normalize_constraint_for_dual(c) for c in primal.constraints]

    A = [c.a[:] for c in cons]
    b = [c.b for c in cons]
    cvec = primal.c[:]
    m = len(cons)   # restricciones primal => variables duales "originales"
    n = len(cvec)   # variables primal => restricciones dual

    # Dual sense
    # El sentido del dual es el opuesto al del primal
    dual_sense = "min" if primal.sense == "max" else "max"

    # Construcción de variables duales no negativas (expandimos según tipo).
    # Para primal MAX:
    #   <= -> y_i >= 0
    #   >= -> y_i <= 0  (y_i = -y')
    # Para primal MIN (signos invertidos):
    #   <= -> y_i <= 0  (y_i = -y')
    #   >= -> y_i >= 0
    # En ambos casos, "=" -> y_i libre (y_i = y_i^+ - y_i^-).
    var_map = []  # por restricción i: lista de (idx_new, sign)
    new_var_count = 0
    for i, cst in enumerate(cons):
        if cst.op == "<=":
            sign = +1.0 if primal.sense == "max" else -1.0
            var_map.append([(new_var_count, sign)])
            new_var_count += 1
        elif cst.op == ">=":
            sign = -1.0 if primal.sense == "max" else +1.0
            var_map.append([(new_var_count, sign)])
            new_var_count += 1
        else:  # "=" libre
            var_map.append([(new_var_count, +1.0), (new_var_count+1, -1.0)])
            new_var_count += 2

    # Objetivo dual: b^T y (expansión)
    dual_c = [0.0]*new_var_count
    for i in range(m):
        for (k, sign) in var_map[i]:
            dual_c[k] += b[i]*sign

    # Restricciones dual: A^T y >= c (si primal max, x>=0)
    # Restricciones duales: A^T y >= c (primal max) o A^T y <= c (primal min)
    #                      A^T y <= c (si primal min, x>=0)
    dual_constraints: List[Constraint] = []
    for j in range(n):
        # construir coef para cada new dual var
        coeff = [0.0]*new_var_count
        for i in range(m):
            aij = A[i][j]
            for (k, sign) in var_map[i]:
                coeff[k] += aij*sign

        if primal.sense == "max":
            op = ">="
        else:
            op = "<="
        dual_constraints.append(Constraint(a=coeff, op=op, b=cvec[j]))

    dual_model = LPModel(
        name=f"DUAL({primal.name})",
        sense=dual_sense,
        c=dual_c,
        constraints=dual_constraints,
        nonneg=True
    )

    mapping_info = {
        "expanded_dual_vars": new_var_count,
        "per_constraint_map": var_map,
        "note": "y_i libres se representan como y_i = y_i^+ - y_i^- (ambas >=0)."
    }
    return dual_model, mapping_info
