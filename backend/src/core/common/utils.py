from __future__ import annotations

def is_close(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps
