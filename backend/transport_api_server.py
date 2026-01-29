import json
import math
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Ensure this folder is in sys.path so ``src`` resolves to ./src
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.transport import solve_transport  # noqa: E402
from src.core.transport.errors import TransportModelError  # noqa: E402


class TransportHandler(BaseHTTPRequestHandler):
    def _sanitize(self, value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        if isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items()}
        return value

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        # CORS (para Vite/localhost)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
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
        # Health check / evitar 501 por visitas al root o favicon
        if self.path in ("/", "/health"):
            return self._send(200, {"ok": True, "service": "transport"})
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        return self._send(404, {"error": "Not Found"})

    def do_POST(self):
        if self.path.rstrip("/") not in ("/solve/transport", "/solve"):
            return self._send(404, {"error": "Not Found"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(raw) if raw else {}
            result = self._sanitize(solve_transport(data))
            return self._send(200, result)
        except TransportModelError as e:
            return self._send(400, {"error": "Bad Request", "message": str(e)})
        except json.JSONDecodeError:
            return self._send(400, {"error": "Bad Request", "message": "Invalid JSON"})
        except Exception as e:
            return self._send(500, {"error": "Internal Server Error", "message": str(e)})


def main():
    host = "127.0.0.1"
    port = 8002
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    print(f"Transport API listening on http://{host}:{port}")
    HTTPServer((host, port), TransportHandler).serve_forever()
    
if __name__ == "__main__":
    main()