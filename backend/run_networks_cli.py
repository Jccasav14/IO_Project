import json
from pathlib import Path

from src.core.networks import solve_network


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    print("\n=== Redes (CLI) ===")
    print("Metodos: shortest_path | mst | max_flow | min_cost_flow")
    print("Tip: usa los templates en linear_programming/data/templates/\n")

    while True:
        method = input("Metodo (o 'q' para salir): ").strip()
        if method.lower() in ("q", "quit", "exit"):
            break
        path = input("Ruta JSON del modelo: ").strip()
        try:
            model = _load_json(path)
            req = {"method": method, "model": model}
            out = solve_network(req)
            print("\nResultado:\n" + json.dumps(out, ensure_ascii=False, indent=2) + "\n")
        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    main()
