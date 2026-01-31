from src.core.lp import solve_lp

def test_auto_uses_simplex_for_all_le():
    model = {
        "name": "demo_le",
        "sense": "max",
        "c": [3, 5],
        "constraints": [
            {"a": [1, 0], "op": "<=", "b": 4},
            {"a": [0, 2], "op": "<=", "b": 12},
            {"a": [3, 2], "op": "<=", "b": 18},
        ]
    }
    res = solve_lp(model, method="auto", log=False)
    assert res.status == "OPTIMAL"
    assert res.method_used == "simplex"
    assert abs(res.objective_value - 36) < 1e-6

def test_user_can_choose_two_phase_for_mixed_constraints():
    model = {
        "name": "mixed",
        "sense": "max",
        "c": [1, 1],
        "constraints": [
            {"a": [1, 1], "op": ">=", "b": 2},
            {"a": [1, 0], "op": "=", "b": 1},
        ]
    }
    res = solve_lp(model, method="two_phase", log=False)
    assert res.status in ("OPTIMAL", "INFEASIBLE", "UNBOUNDED")
    assert res.method_used == "two_phase"
