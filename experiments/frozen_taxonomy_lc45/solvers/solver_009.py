"""External blind pack solver 009: uniform formula generalizer.

Wraps lc45_candidates.lc45_uniform_formula_generalizer.
Family: closed-form-uniform (assumes all values equal).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_uniform_formula_generalizer


def solve(nums: list[int]) -> int:
    return lc45_uniform_formula_generalizer(nums)
