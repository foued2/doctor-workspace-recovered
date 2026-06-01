"""experimental.dynamic.solver_agreement — stub.

Reconstructed from import map. `compute_ground_truth` returns a
2-tuple (expected, trace); `generate_solver_pair` returns a 2-tuple
of solvers or None. Runtime not reconstructed.
"""
from __future__ import annotations

from typing import Any


def compute_ground_truth(
    solver_a: Any,
    solver_b: Any,
    case_input: Any,
) -> tuple:
    return (None, None)


def generate_solver_pair(schema: Any) -> tuple | None:
    return None
