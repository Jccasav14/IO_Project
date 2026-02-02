import json
import math
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# =========================
# ENV LOADER (igual que NETWORK)
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

load_env(Path(__file__).resolve().parents[1] / ".env")


# =========================
# HUGGING FACE ROUTER ENV
# =========================
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL_REPORT = os.getenv("HF_MODEL_REPORT", "meta-llama/Llama-3.1-8B-Instruct")
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"


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


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.transport import solve_transport
from src.core.transport.errors import TransportModelError


class TransportHandler(BaseHTTPRequestHandler):
    def _sanitize(self, value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        if isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items()}
        return value

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(self._sanitize(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/health"):
            return self._send_json(200, {"ok": True, "service": "transport"})
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        return self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        route = self.path.rstrip("/")

        if route not in ("/solve", "/solve/transport", "/ai/report"):
            return self._send_json(404, {"error": "Not found"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return self._send_json(400, {"error": "Bad Request", "message": "Invalid JSON"})
        except Exception as e:
            return self._send_json(400, {"error": "Bad Request", "message": str(e)})

        # =========================
        # IA: REPORTE DE SENSIBILIDAD (HF)
        # =========================
        if route == "/ai/report":
            try:
                problem_text = data.get("problem_text", "")
                model = data.get("model", {})
                result = data.get("result", {})
                sensitivity = result.get("sensitivity") or data.get("sensitivity") or {}

                prompt = (
                    "Redacta un informe breve (en español) de análisis de sensibilidad para un problema de Transporte. "
                    "No resuelvas el problema desde cero. Usa los resultados ya calculados.\n\n"
                    "Incluye:\n"
                    "1) Costo total mínimo y qué significa.\n"
                    "2) Interpretación de la asignación (qué orígenes abastecen a qué destinos).\n"
                    "3) Potenciales u y v como 'precios sombra' (impacto marginal en el costo si cambia 1 unidad de oferta/demanda).\n"
                    "4) Costos reducidos (oportunidad) en rutas vacías: menciona al menos 3 rutas con mayor costo reducido y explica qué implica.\n"
                    "5) Si hay rutas con costo reducido ~0, explica que puede haber soluciones alternativas.\n"
                    "6) Escenarios: 'qué pasa si baja el costo de una ruta' usando nonbasic_cost_decrease_needed.\n\n"
                    "Usa títulos en negrita y listas claras; tono de estudiante universitario (no demasiado formal).\n\n"
                    f"Contexto del problema:\n{problem_text}\n\n"
                    f"Modelo (JSON):\n{json.dumps(model, ensure_ascii=False)}\n\n"
                    f"Resultados del solver (JSON):\n{json.dumps(result, ensure_ascii=False)}\n\n"
                    f"Sensibilidad (JSON):\n{json.dumps(sensitivity, ensure_ascii=False)}\n"
                )

                payload = {
                    "model": HF_MODEL_REPORT,
                    "messages": [
                        {"role": "system", "content": "Eres un asistente que redacta reportes técnicos claros y prácticos."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.4,
                }

                resp = _hf_request_json(payload)
                text = _extract_hf_text(resp).strip()
                return self._send_json(200, {"report": text})

            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8")
                except Exception:
                    pass
                return self._send_json(e.code, {"error": f"HF Router HTTP error {e.code}: {detail}"})
            except Exception as exc:
                return self._send_json(502, {"error": f"HF Router request failed: {exc}"})

        try:
            result = solve_transport(data)
            return self._send_json(200, result)
        except TransportModelError as e:
            return self._send_json(400, {"error": "Bad Request", "message": str(e)})
        except Exception as e:
            return self._send_json(500, {"error": "Internal Server Error", "message": str(e)})


def main():
    host = "127.0.0.1"
    port = 8002
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    print(f"[transport] Server running on http://{host}:{port}")
    HTTPServer((host, port), TransportHandler).serve_forever()


if __name__ == "__main__":
    main()