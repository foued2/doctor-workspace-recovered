"""External blind pack solver 003: naive greedy.

Wraps lc45_candidates.lc45_naive_greedy.
Family: naive-greedy (known to be suboptimal on non-monotonic cases).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_naive_greedy


def solve(nums: list[int]) -> int:
    return lc45_naive_greedy(nums)
