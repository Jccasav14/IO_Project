# IO_Project

Proyecto de Investigacion Operativa. Incluye modulos de Programacion Lineal, Redes y Transporte implementados desde cero (sin librerias de optimizacion), mas una interfaz web para probar modelos. Tambien incluye CLI y servidores HTTP locales para conectar el frontend con los solvers.

## Que hace el sistema

- **Programacion Lineal**
  - Simplex basico (solo <= y b>=0)
  - Big M
  - Dos Fases (recomendado)
  - Dual (construye el dual y lo resuelve)
  - Muestra holguras/excesos, precios sombra, tabla final e iteraciones con pivote y operaciones de fila.
- **Redes**
  - Ruta mas corta (Dijkstra)
  - Arbol de expansion minima (Kruskal)
  - Flujo maximo (Edmonds-Karp)
  - Flujo de costo minimo (SSAP)
- **Transporte**
  - Esquina Noroeste, Costo Minimo y Vogel (VAM)
  - Optimizacion con Stepping-Stone

## Estructura principal

- `backend/src/core/lp/`: metodos de Programacion Lineal.
- `backend/src/core/networks/`: algoritmos de Redes.
- `backend/src/core/transport/`: metodos de Transporte.
- `backend/`: CLIs y servidores HTTP locales.
- `frontend/`: app React (Vite).

## Requisitos

- Python 3.10+
- Node.js 18+ (para el frontend)

## Uso rapido

### 1) CLIs interactivos

```powershell
python backend/run_lp_cli.py
python backend/run_networks_cli.py
python backend/run_transport_cli.py
```

### 2) Servidores + Frontend

Si vas a usar IA (parseo de PDF y reporte), copia `.env.example` a `.env` y completa tu API key.

Terminal 1 (LP):
```
python backend/lp_api_server.py
```

Terminal 2 (Redes):
```
python backend/network_api_server.py
```

Terminal 3 (Transporte):
```
python backend/transport_api_server.py
```

Terminal 4 (Frontend):
```
cd frontend
npm install
npm run dev
```

### 3) Pruebas

```powershell
python -m pytest backend\tests
```