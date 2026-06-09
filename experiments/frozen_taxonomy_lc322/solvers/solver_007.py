"""Wrapper for lc_322_solvers.solve_7 — delegates to GPT-generated solver."""
from __future__ import annotations
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO))

from doctor.solvers.lc322.lc_322_solvers import solve_7 as _solve


def solve(solver_input: list) -> int:
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return _solve(coins, amount)