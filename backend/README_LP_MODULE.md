# Modulo de Programacion Lineal (LP)

Este modulo implementa, **sin librerias de optimizacion**, los metodos:

- Simplex basico (solo si todas las restricciones son `<=` y RHS `b>=0`)
- Big M (soporta `<=`, `>=`, `=`)
- Dos Fases / Two-Phase (soporta `<=`, `>=`, `=`) **(recomendado)**
- Dual (construye el dual del primal y lo resuelve con Two-Phase)

## Requisitos

- Python 3.10+

## Uso rapido

### Servidor HTTP (para el frontend)

```powershell
python backend/lp_api_server.py
```

Servidor disponible en:

```
http://127.0.0.1:8000
```

### CLI interactivo

```powershell
python backend/run_lp_cli.py
```

## Uso (API - Core)

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

### Seleccion de metodo

- `method="auto"`:
  - Si todas las restricciones son `<=` y `b>=0` => `simplex`
  - En caso contrario => `two_phase`
- Si el modelo incluye `>=` o `=`:
  - Puedes elegir: `two_phase`, `big_m` o `dual`

## Formato del modelo (JSON)

```json
{
  "name": "LP_demo",
  "sense": "max",
  "c": [3, 5],
  "constraints": [
    { "a": [1, 0], "op": "<=", "b": 4 },
    { "a": [0, 2], "op": "<=", "b": 12 },
    { "a": [3, 2], "op": "<=", "b": 18 }
  ]
}
```

Notas:
- Se asume `x >= 0` para todas las variables.
- Si hay `>=` o `=` el solver usa Two-Phase o Big M.

## Salida principal del solver

Campos mas usados en la respuesta:
- `status`: OPTIMAL | INFEASIBLE | UNBOUNDED
- `x`: valores de variables
- `objective_value`: valor de la funcion objetivo
- `iterations`: numero de iteraciones
- `method_used`: metodo aplicado
- `slacks`: holguras/excesos
- `tableau`: tabla final
- `tableau_history`: historial de tablas por iteracion (si aplica)

## Notas importantes

- `log=True` imprime informacion de pivoteo en consola (modo debug).
- El modo `dual` resuelve el dual con Two-Phase y reporta sus resultados.
