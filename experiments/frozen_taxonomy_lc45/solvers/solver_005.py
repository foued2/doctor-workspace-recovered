"""External blind pack solver 005: zero dead-end panic.

Wraps lc45_candidates.lc45_zero_dead_end_panic.
Family: dead-end-avoidance heuristic.

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_zero_dead_end_panic


def solve(nums: list[int]) -> int:
    return lc45_zero_dead_end_panic(nums)
