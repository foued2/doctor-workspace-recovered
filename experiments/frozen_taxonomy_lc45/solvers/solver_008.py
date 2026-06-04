"""External blind pack solver 008: frontier off-by-one.

Wraps lc45_candidates.lc45_frontier_off_by_one.
Family: frontier-counting (off-by-one boundary bug).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_frontier_off_by_one


def solve(nums: list[int]) -> int:
    return lc45_frontier_off_by_one(nums)
