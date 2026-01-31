"""Network optimization algorithms (Redes).

This module mirrors the style of ``src.core.lp``: pure-Python implementations,
focused on correctness, clarity, and JSON-friendly outputs.

Public entrypoint:

- ``solve_network(problem: dict) -> dict``
"""

from .solve import solve_network  # noqa: F401
