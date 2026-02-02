# Módulo de Redes (Networks)

Este módulo implementa, **sin usar librerías de optimización**, los principales
algoritmos de **Redes** vistos en Investigación Operativa, desarrollados
completamente en código por el grupo.

## Algoritmos implementados

- **Ruta más corta** (Dijkstra)
- **Árbol de expansión mínima** (Kruskal)
- **Flujo máximo** (Edmonds–Karp)
- **Flujo de costo mínimo** (Successive Shortest Augmenting Path)

> No se utilizan librerías externas como NetworkX, OR-Tools, PuLP, etc.
> Toda la lógica de los algoritmos está implementada manualmente.

---

## Uso (API – Core)

```python
from src.core.networks import solve_networks

model = {
  "nodes": ["A", "B", "C", "D"],
  "edges": [
    {"u": "A", "v": "B", "w": 2},
    {"u": "A", "v": "C", "w": 5},
    {"u": "B", "v": "C", "w": 1},
    {"u": "B", "v": "D", "w": 4},
    {"u": "C", "v": "D", "w": 1}
  ],
  "source": "A",
  "target": "D",
  "directed": false
}

res = solve_networks(model, method="shortest_path", log=True)
print(res.method_used, res.status, res.path_nodes, res.distance)
```

---

## Selección de método

- `shortest_path`: requiere `source`, `target` y `w`
- `mst`: requiere solo `w`
- `max_flow`: requiere `source`, `sink` y `capacity`
- `min_cost_flow`: requiere `source`, `sink`, `demand`, `capacity` y `cost`

---

## Ejecución (Backend – Servidor HTTP)

```powershell
python backend/network_api_server.py
```

Servidor disponible en:

```
http://127.0.0.1:8001
```

---

## Endpoint principal

POST `/solve/networks`

Body:

```json
{
  "method": "mst",
  "model": { ... }
}
```

---

## Notas finales

- Dijkstra asume pesos no negativos.
- MST se usa para grafos no dirigidos.
- El frontend genera el modelo automáticamente sin que el usuario escriba JSON.


## Endpoints con Gemini (análisis de sensibilidad)

Este backend soporta un endpoint de **análisis de sensibilidad** para Redes usando la misma API key de Gemini del `.env`
(igual que el módulo LP). Variables esperadas en `.env`:

- `GEMINI_API_KEY`
- `GEMINI_MODEL_REPORT` (ej: `gemini-2.5-flash`)

### POST /ai/sensitivity  (alias: /ai/report)

**Body (ejemplo mínimo):**
```json
{
  "method": "shortest_path",
  "context": "Pega aquí el contexto de DISTRIMAX (opcional).",
  "model": {
    "nodes": ["A","B","C"],
    "edges": [{"u":"A","v":"B","w":5}],
    "source": "A",
    "target": "C"
  }
}
```

Respuesta:
```json
{ "analysis": "..." }
```
