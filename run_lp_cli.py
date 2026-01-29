import sys
from pathlib import Path

# Ensure "src" resolves to linear_programming/src.
ROOT = Path(__file__).resolve().parent
LP_ROOT = ROOT / "linear_programming"
if str(LP_ROOT) not in sys.path:
    sys.path.insert(0, str(LP_ROOT))

from src.core.lp import solve_lp  # noqa: E402


def prompt_int(label: str, min_value: int | None = None) -> int:
    while True:
        raw = input(label).strip()
        try:
            val = int(raw)
        except ValueError:
            print("Please enter an integer.")
            continue
        if min_value is not None and val < min_value:
            print(f"Please enter a value >= {min_value}.")
            continue
        return val


def prompt_float(label: str) -> float:
    while True:
        raw = input(label).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a number.")


def prompt_choice(label: str, choices: list[str]) -> str:
    choices_lc = [c.lower() for c in choices]
    while True:
        raw = input(label).strip().lower()
        if raw in choices_lc:
            return raw
        print(f"Choose one of: {', '.join(choices)}")


def main() -> None:
    print("LP Interactive CLI")
    name = input("Model name: ").strip() or "LP"
    sense = prompt_choice("Sense (max/min): ", ["max", "min"])

    n = prompt_int("Number of variables: ", min_value=1)
    m = prompt_int("Number of constraints: ", min_value=1)

    c = []
    print("Objective coefficients c:")
    for j in range(n):
        c.append(prompt_float(f"  c[{j+1}]: "))

    constraints = []
    print("Constraints:")
    for i in range(m):
        a = []
        print(f"  Constraint {i+1} coefficients a:")
        for j in range(n):
            a.append(prompt_float(f"    a[{j+1}]: "))
        op = prompt_choice("  Operator (<=, >=, =): ", ["<=", ">=", "="])
        b = prompt_float("  RHS b: ")
        constraints.append({"a": a, "op": op, "b": b})

    method = prompt_choice(
        "Method (auto/simplex/two_phase/big_m/dual): ",
        ["auto", "simplex", "two_phase", "big_m", "dual"],
    )
    log = prompt_choice("Show simplex log? (y/n): ", ["y", "n"]) == "y"

    model = {"name": name, "sense": sense, "c": c, "constraints": constraints}
    res = solve_lp(model, method=method, log=log)

    print("")
    print("Result")
    print(f"  method_used: {res.method_used}")
    print(f"  status: {res.status}")
    print(f"  x: {res.x}")
    print(f"  objective_value: {res.objective_value}")
    if res.message:
        print(f"  message: {res.message}")


if __name__ == "__main__":
    main()
