from src.core.networks.solve import solve_network


def test_shortest_path():
    model = {
        "nodes": ["A", "B", "C"],
        "edges": [
            {"u": "A", "v": "B", "weight": 5},
            {"u": "A", "v": "C", "weight": 2},
            {"u": "C", "v": "B", "weight": 1},
        ],
        "source": "A",
        "sink": "B",
        "directed": True,
    }
    out = solve_network({"method": "shortest_path", "model": model})
    assert out["distance"] == 3
    assert out["path_nodes"] == ["A", "C", "B"]


def test_mst():
    model = {
        "nodes": ["A", "B", "C"],
        "edges": [
            {"u": "A", "v": "B", "weight": 2},
            {"u": "B", "v": "C", "weight": 2},
            {"u": "A", "v": "C", "weight": 10},
        ],
        "directed": False,
    }
    out = solve_network({"method": "mst", "model": model})
    assert out["total_weight"] == 4


def test_max_flow():
    model = {
        "nodes": ["s", "a", "t"],
        "edges": [
            {"u": "s", "v": "a", "capacity": 3},
            {"u": "a", "v": "t", "capacity": 2},
            {"u": "s", "v": "t", "capacity": 1},
        ],
        "source": "s",
        "sink": "t",
        "directed": True,
    }
    out = solve_network({"method": "max_flow", "model": model})
    assert out["max_flow"] == 3


def test_min_cost_flow():
    model = {
        "nodes": ["s", "a", "t"],
        "edges": [
            {"u": "s", "v": "a", "capacity": 5, "cost": 1},
            {"u": "a", "v": "t", "capacity": 5, "cost": 2},
        ],
        "source": "s",
        "sink": "t",
        "demand": 4,
        "directed": True,
    }
    out = solve_network({"method": "min_cost_flow", "model": model})
    assert out["sent"] == 4
    assert out["total_cost"] == 12
