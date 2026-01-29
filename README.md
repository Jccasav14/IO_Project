# IO_Project

Proyecto de Investigacion Operativa. Incluye un modulo de Programacion Lineal
implementado desde cero (sin librerias de optimizacion) y una interfaz web para
probar modelos. Tambien incluye un CLI y un servidor HTTP local para conectar el
frontend con el solver.

## Que hace el sistema

- Resuelve problemas de Programacion Lineal con:
  - Simplex basico (solo <= y b>=0)
  - Gran M
  - Dos Fases (recomendado)
  - Dual (construye el dual y lo resuelve)
- Muestra resultados, holguras/excesos, precios sombra y tabla final.
- Tiene una pagina principal con informacion del proyecto y una pagina de
  Programacion Lineal para ingresar el modelo.

## Estructura principal

- `linear_programming/src/core/lp/`: implementaciones de los metodos.
- `linear_programming/tests/`: pruebas unitarias.
- `linear_programming/data/templates/`: ejemplo JSON de modelo.
- `linear_programming/run_lp_cli.py`: ejecutable CLI interactivo.
- `linear_programming/lp_api_server.py`: servidor HTTP local (stdlib) para el frontend.
- `frontend/`: app React (Vite).

## Requisitos

- Python 3.10+ (probado con 3.14)
- Node.js 18+ (para el frontend)

## Uso rapido

### 1) CLI interactivo

```powershell
python linear_programming/run_lp_cli.py
```

### 2) Servidor + Frontend

```powershell
Copie el archivo `.env.example` como `.env` y complete su API key:
```

Terminal 1:
```
python linear_programming/lp_api_server.py
```

Terminal 2:
```
cd frontend
npm install
npm run dev
```

### 3) Pruebas

```powershell
python -m pytest linear_programming\tests
```

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

## Notas importantes

- El solver asume x >= 0 para las variables.
- Big M y Dos Fases resuelven modelos con <=, >= y =.
- El modo Dual retorna la solucion del dual; el frontend muestra tambien
  holguras y precios sombra a partir del dual.
- No se usan librerias de optimizacion, SDKs ni APIs externas.
- La IA se usa solo para interpretar el enunciado y redactar informes.
- El PDF debe contener texto (no escaneado). No se usa OCR.
