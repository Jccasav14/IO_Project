"""Transportation problem solvers (Transporte).

Pure-Python implementation aligned with the project's architecture (see ``src.core.lp`` and
``src.core.networks``).

Public entrypoint:
- ``solve_transport(problem: dict) -> dict``
"""

from .solve import solve_transport  # noqa: F401
