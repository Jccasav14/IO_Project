# Módulo de Programación Lineal (LP)

Este módulo implementa, **sin librerías de optimización**, los métodos:

- Simplex básico (solo si todas las restricciones son `<=` y RHS `b>=0`)
- Big M (soporta `<=`, `>=`, `=`)
- Dos Fases / Two-Phase (soporta `<=`, `>=`, `=`) **(recomendado)**
- Dual (construye el dual del primal y lo resuelve con Two-Phase)

## Uso (API)

```python
from src.core.lp import solve_lp

model = {
  "name": "demo",
  "sense": "max",
  "c": [3, 5],
  "constraints": [
    {"a": [1, 0], "op": "<=", "b": 4},
    {"a": [0, 2], "op": "<=", "b": 12},
    {"a": [3, 2], "op": "<=", "b": 18},
  ]
}

res = solve_lp(model, method="auto", log=True)   # auto => simplex si aplica, si no => two_phase
print(res.method_used, res.status, res.x, res.objective_value)
```

### Selección de método

- `method="auto"`:
  - Si todas las restricciones son `<=` y `b>=0` => `simplex`
  - En caso contrario => `two_phase`

- Si el modelo incluye `>=` o `=`:
  - El usuario puede elegir: `two_phase`, `big_m` o `dual`

## Notas
- Se asume `x >= 0` para variables del primal (convención estándar del curso).
- El dual para restricciones `=` genera variables libres, representadas como diferencia de dos no-negativas.
