import json
from pathlib import Path

from src.core.transport import solve_transport


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    print("\n=== Transporte (CLI) ===")
    print("Metodos: northwest | min_cost | vogel | optimize | auto")
    print("El JSON del modelo debe incluir: supply, demand, costs (2D)\n")

    while True:
        method = input("Metodo (o 'q' para salir): ").strip()
        if method.lower() in ("q", "quit", "exit"):
            break
        path = input("Ruta JSON del modelo: ").strip()
        optimize = input("¿Optimizar? (y/n, default y): ").strip().lower() not in ("n", "no", "0", "false")

        try:
            model = _load_json(path)
            req = {"method": method, "model": model, "options": {"optimize": optimize}}
            out = solve_transport(req)
            print("\nResultado:\n" + json.dumps(out, ensure_ascii=False, indent=2) + "\n")
        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    main()
