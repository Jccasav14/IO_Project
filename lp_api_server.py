import json
import math
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Ensure "src" resolves to linear_programming/src.
ROOT = Path(__file__).resolve().parent
LP_ROOT = ROOT / "linear_programming"
if str(LP_ROOT) not in sys.path:
    sys.path.insert(0, str(LP_ROOT))

from src.core.lp import solve_lp  # noqa: E402
from src.core.lp.parsers import model_from_dict  # noqa: E402
from src.core.lp.dual import build_dual  # noqa: E402
from src.core.lp.two_phase import solve_two_phase  # noqa: E402


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
        if self.path != "/solve":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw) if raw else {}
        except Exception as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
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
