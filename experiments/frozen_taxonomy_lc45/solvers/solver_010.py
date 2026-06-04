"""External blind pack solver 010: first window max then greedy.

Wraps lc45_candidates.lc45_first_window_max_then_greedy.
Family: two-phase (max-first then greedy).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_first_window_max_then_greedy


def solve(nums: list[int]) -> int:
    return lc45_first_window_max_then_greedy(nums)
