from src.core.lp import solve_lp

def test_big_m_runs():
    model = {
        "name": "bigm",
        "sense": "max",
        "c": [2, 1],
        "constraints": [
            {"a": [1, 1], "op": ">=", "b": 4},
            {"a": [1, 0], "op": "<=", "b": 6},
        ]
    }
    res = solve_lp(model, method="big_m", log=False)
    assert res.status in ("OPTIMAL", "INFEASIBLE", "UNBOUNDED")
    assert res.method_used == "big_m"

def test_dual_builder_runs_and_solves():
    model = {
        "name": "dual_demo",
        "sense": "max",
        "c": [3, 2],
        "constraints": [
            {"a": [2, 1], "op": "<=", "b": 8},
            {"a": [1, 2], "op": ">=", "b": 4},
        ]
    }
    res = solve_lp(model, method="dual", log=False)
    assert res.status in ("OPTIMAL", "INFEASIBLE", "UNBOUNDED")
    assert res.method_used.startswith("dual(")
    assert res.extra and "dual_mapping" in res.extra
