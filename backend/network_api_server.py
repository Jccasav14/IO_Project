import json
import math
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import os
import urllib.request
import urllib.error


# =========================
# ENV LOADER (igual que LP)
# =========================
def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# Carga variables desde el .env en la raíz del proyecto
load_env(Path(__file__).resolve().parents[1] / ".env")

# =========================
# HUGGING FACE ROUTER ENV
# =========================
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct")
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"


# =========================
# HF ROUTER HELPERS
# =========================
def _hf_request_json(payload: dict) -> dict:
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN not set")

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        HF_CHAT_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_hf_text(resp: dict) -> str:
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


# =========================
# PATH SETUP
# =========================
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.networks import solve_network  # noqa: E402
from src.core.networks.errors import NetworkModelError  # noqa: E402


# =========================
# HTTP HANDLER
# =========================
class NetHandler(BaseHTTPRequestHandler):

    def _sanitize(self, value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        if isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items()}
        return value

    def _send_json(self, status: int, payload: dict) -> None:
        safe_payload = self._sanitize(payload)
        body = json.dumps(safe_payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path not in (
            "/solve",
            "/solve/networks",
            "/ai/report",
            "/ai/sensitivity",
        ):
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw) if raw else {}
        except Exception as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        # =========================
        # HF ROUTER – ANALISIS REDES
        # =========================
        if self.path in ("/ai/report", "/ai/sensitivity"):
            if not HF_TOKEN:
                self._send_json(500, {"error": "HF_TOKEN not set"})
                return

            method = str(data.get("method", "")).strip()
            model = data.get("model") if isinstance(data.get("model"), dict) else {}
            result = data.get("result") if isinstance(data.get("result"), dict) else {}
            context = data.get("context", "")

            if not context:
                context = (
                    "DISTRIMAX S.A. es una comercializadora nacional en Ecuador que produce, "
                    "almacena y distribuye productos a clientes en distintas ciudades. "
                    "Actualmente enfrenta costos logísticos elevados, retrasos en entregas "
                    "y problemas de inventario debido a decisiones empíricas. "
                    "Se busca mejorar rutas, conectividad, capacidades y cumplimiento de demanda."
                )

            prompt = f"""
Debes generar un ANALISIS DE SENSIBILIDAD aplicado EXCLUSIVAMENTE
al módulo de REDES del problema de DISTRIMAX S.A.

Reglas:
- NO calcules resultados numéricos.
- NO repitas el modelo matemático.
- NO inventes datos exactos.
- Responde en español, claro y operativo.

Analiza cómo cambian las decisiones óptimas cuando varían:
- costos de transporte
- capacidades de arcos o nodos
- demanda de clientes
- disponibilidad de rutas

Formato:
- Entrega 1 bloque por método: Ruta más corta, Árbol de expansión mínima, Flujo máximo, Flujo de costo mínimo.
- Para el método solicitado: 1–2 párrafos.
- Para los demás métodos: 3–5 viñetas.
- Incluye: variables sensibles, qué cambia en la solución, cuellos de botella y recomendación operativa.

Contexto:
{context}

Método solicitado:
{method}

Modelo de red (resumen):
{json.dumps(model, ensure_ascii=False)[:1500]}

Resultado del solver (si existe):
{json.dumps(result, ensure_ascii=False)[:1200]}
""".strip()

            payload = {
                "model": HF_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres experto en Investigación Operativa y Logística. Responde con precisión y sin inventar datos.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 450,
                "temperature": 0.4,
            }

            try:
                resp = _hf_request_json(payload)
                text = _extract_hf_text(resp).strip()
                if not text:
                    self._send_json(502, {"error": "Empty response from Hugging Face Router"})
                    return
                self._send_json(200, {"analysis": text})
                return
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8")
                except Exception:
                    pass
                self._send_json(e.code, {"error": f"HF Router HTTP error {e.code}: {detail}"})
                return
            except Exception as exc:
                self._send_json(502, {"error": f"HF Router request failed: {exc}"})
                return

        # =========================
        # SOLVER DE REDES
        # =========================
        try:
            result = solve_network(data)
            self._send_json(200, {"result": result})
        except NetworkModelError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})


# =========================
# MAIN
# =========================
def main() -> None:
    host = "127.0.0.1"
    port = 8001
    print(f"[networks] Server running on http://{host}:{port}")
    HTTPServer((host, port), NetHandler).serve_forever()


if __name__ == "__main__":
    main()
