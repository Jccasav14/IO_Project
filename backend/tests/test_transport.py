from src.core.transport import solve_transport

def test_transport_balanced_vogel_optimize():
    problem = {
        "method": "auto",
        "model": {
            "supply": [20, 30, 25],
            "demand": [10, 10, 15, 40],
            "costs": [
                [8, 6, 10, 9],
                [9, 12, 13, 7],
                [14, 9, 16, 5],
            ],
        },
        "options": {"optimize": True, "max_iterations": 2000},
    }

    out = solve_transport(problem)
    assert out["status"] in ("OPTIMAL", "FEASIBLE")
    assert isinstance(out["allocation"], list)
    assert len(out["allocation"]) == 3
    assert len(out["allocation"][0]) == 4
    assert out["total_cost"] >= 0


def test_transport_supports_M():
    problem = {
        "method": "northwest",
        "model": {
            "supply": [5, 5],
            "demand": [5, 5],
            "costs": [
                ["M", 1],
                [2, 3],
            ],
        },
    }
    out = solve_transport(problem)
    assert "allocation" in out
