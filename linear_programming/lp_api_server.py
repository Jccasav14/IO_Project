import json
import math
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Ensure "src" resolves to linear_programming/src.
ROOT = Path(__file__).resolve().parent
LP_ROOT = ROOT
if str(LP_ROOT) not in sys.path:
    sys.path.insert(0, str(LP_ROOT))

from src.core.lp import solve_lp  # noqa: E402
from src.core.lp.parsers import model_from_dict  # noqa: E402
from src.core.lp.dual import build_dual  # noqa: E402
from src.core.lp.two_phase import solve_two_phase  # noqa: E402


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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_PARSE = os.getenv("GEMINI_MODEL_PARSE", "gemini-2.5-flash")
GEMINI_MODEL_REPORT = os.getenv("GEMINI_MODEL_REPORT", "gemini-2.5-flash")


def _gemini_request_json(model: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def _extract_gemini_text(resp: dict) -> str:
    for cand in resp.get("candidates", []):
        content = cand.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                return text
    return ""


class LPHandler(BaseHTTPRequestHandler):
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
        if self.path not in ("/solve", "/ai/parse", "/ai/report"):
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw) if raw else {}
        except Exception as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        if self.path == "/ai/parse":
            if not GEMINI_API_KEY:
                self._send_json(500, {"error": "GEMINI_API_KEY not set"})
                return

            filename = data.get("filename", "problem.pdf")
            file_data = data.get("file_data")
            raw_text = data.get("text")

            try:
                if file_data:
                    if "," in file_data:
                        file_data = file_data.split(",", 1)[1]
                    parts = [
                        {"inline_data": {"mime_type": "application/pdf", "data": file_data}},
                        {"text": "Extrae la funcion objetivo y restricciones del problema de programacion lineal."},
                    ]
                elif raw_text:
                    parts = [{"text": raw_text}]
                else:
                    self._send_json(400, {"error": "Missing file_data or text"})
                    return

                schema = {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "sense": {"type": "STRING", "enum": ["max", "min"]},
                        "c": {"type": "ARRAY", "items": {"type": "NUMBER"}},
                        "constraints": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "a": {"type": "ARRAY", "items": {"type": "NUMBER"}},
                                    "op": {"type": "STRING", "enum": ["<=", ">=", "="]},
                                    "b": {"type": "NUMBER"},
                                },
                                "required": ["a", "op", "b"],
                                "propertyOrdering": ["a", "op", "b"],
                            },
                        },
                        "summary": {"type": "STRING"},
                    },
                    "required": ["name", "sense", "c", "constraints", "summary"],
                    "propertyOrdering": ["name", "sense", "c", "constraints", "summary"],
                }

                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": (
                                        "Eres un asistente que extrae modelos de Programacion Lineal. "
                                        "No resuelvas el problema. Devuelve solo JSON valido y agrega "
                                        "un resumen breve del problema en 'summary'."
                                    )
                                }
                            ]
                        },
                        {"parts": parts},
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": schema,
                    },
                }

                resp = _gemini_request_json(GEMINI_MODEL_PARSE, payload)
                text = _extract_gemini_text(resp)
                model_out = json.loads(text) if text else None
                if not model_out:
                    self._send_json(500, {"error": "Empty AI response"})
                    return
                self._send_json(200, {"model": model_out, "summary": model_out.get("summary", "")})
                return
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    detail = exc.read().decode("utf-8")
                except Exception:
                    detail = ""
                self._send_json(500, {"error": f"Gemini HTTP error: {exc}. {detail}"})
                return
            except Exception as exc:
                self._send_json(500, {"error": f"AI parse error: {exc}"})
                return

        if self.path == "/ai/report":
            if not GEMINI_API_KEY:
                self._send_json(500, {"error": "GEMINI_API_KEY not set"})
                return
            try:
                problem_text = data.get("problem_text", "")
                model = data.get("model", {})
                result = data.get("result", {})
                prompt = (
                    "Redacta una respuesta breve y profesional en espanol que presente "
                    "el analisis de sensibilidad con los resultados ya obtenidos. "
                    "No resuelvas el problema. No repitas todo el enunciado. "
                    "Incluye: valor objetivo, variables decision, holguras/excesos, "
                    "precios sombra y una conclusion corta. Usa parrafos y listas claras. "
                    "Usa negritas solo para titulos de seccion y valores numericos clave "
                    "(valor objetivo, valores de variables, holguras/excesos y precios sombra). "
                    "No uses negritas en oraciones completas.\n\n"
                    f"Contexto del problema:\n{problem_text}\n\n"
                    f"Modelo (JSON):\n{json.dumps(model, ensure_ascii=False)}\n\n"
                    f"Resultados:\n{json.dumps(result, ensure_ascii=False)}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                }
                resp = _gemini_request_json(GEMINI_MODEL_REPORT, payload)
                text = _extract_gemini_text(resp)
                self._send_json(200, {"report": text})
                return
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    detail = exc.read().decode("utf-8")
                except Exception:
                    detail = ""
                self._send_json(500, {"error": f"Gemini HTTP error: {exc}. {detail}"})
                return
            except Exception as exc:
                self._send_json(500, {"error": f"AI report error: {exc}"})
                return

        method = data.get("method", "auto")
        model = data.get("model")
        if not model:
            self._send_json(400, {"error": "Missing model"})
            return

        try:
            if method == "dual":
                primal_res = solve_lp(model, method="two_phase", log=False)
            else:
                primal_res = solve_lp(model, method=method, log=False)
        except Exception as exc:
            self._send_json(500, {"error": f"Solver error: {exc}"})
            return

        slacks = None
        if primal_res.status == "OPTIMAL":
            slacks = []
            for cst in model["constraints"]:
                ax = sum(ai * xi for ai, xi in zip(cst["a"], primal_res.x))
                if cst["op"] == "<=":
                    slacks.append(cst["b"] - ax)
                elif cst["op"] == ">=":
                    slacks.append(ax - cst["b"])
                else:
                    slacks.append(0.0)

        dual_info = None
        try:
            primal_model = model_from_dict(model)
            dual_model, mapping = build_dual(primal_model)
            dual_res = solve_two_phase(dual_model, log=False)
            shadow_prices = None
            if dual_res.status == "OPTIMAL":
                shadow_prices = []
                for terms in mapping["per_constraint_map"]:
                    val = 0.0
                    for idx, sign in terms:
                        if idx < len(dual_res.x):
                            val += sign * dual_res.x[idx]
                    shadow_prices.append(val)
            dual_info = {
                "status": dual_res.status,
                "x": dual_res.x,
                "objective_value": dual_res.objective_value,
                "method_used": dual_res.method_used,
                "shadow_prices": shadow_prices,
            }
        except Exception:
            dual_info = None

        tableau = None
        basis = None
        var_names = None
        row0 = None
        basic_vars = None
        nonbasic_vars = None
        if primal_res.extra:
            tableau = primal_res.extra.get("final_tableau")
            basis = primal_res.extra.get("basis")
            var_names = primal_res.extra.get("var_names")
            row0 = primal_res.extra.get("row0")
            basic_vars = primal_res.extra.get("basic_vars")
            nonbasic_vars = primal_res.extra.get("nonbasic_vars")

        payload = {
            "status": primal_res.status,
            "x": primal_res.x,
            "objective_value": primal_res.objective_value,
            "iterations": primal_res.iterations,
            "message": primal_res.message,
            "method_used": primal_res.method_used,
            "slacks": slacks,
            "dual": dual_info,
            "tableau": tableau,
            "basis": basis,
            "var_names": var_names,
            "row0": row0,
            "basic_vars": basic_vars,
            "nonbasic_vars": nonbasic_vars,
        }
        self._send_json(200, payload)


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    httpd = HTTPServer((host, port), LPHandler)
    print(f"LP API server running on http://{host}:{port}")
    print("POST /solve with JSON: { model: {...}, method: 'auto' }")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
