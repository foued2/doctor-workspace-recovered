"""External blind pack solver 002: farthest landing path.

Wraps lc45_candidates.lc45_farthest_landing_path.
Family: greedy-farthest.

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_farthest_landing_path


def solve(nums: list[int]) -> int:
    return lc45_farthest_landing_path(nums)
