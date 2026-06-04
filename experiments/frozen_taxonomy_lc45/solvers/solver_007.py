"""External blind pack solver 007: three-step window DP.

Wraps lc45_candidates.lc45_three_step_window_dp.
Family: windowed-DP (local horizon approximation).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_three_step_window_dp


def solve(nums: list[int]) -> int:
    return lc45_three_step_window_dp(nums)
