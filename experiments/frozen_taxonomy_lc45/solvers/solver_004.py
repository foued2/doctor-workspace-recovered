"""External blind pack solver 004: max landing value greedy.

Wraps lc45_candidates.lc45_max_landing_value.
Family: greedy-max-value.

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_max_landing_value


def solve(nums: list[int]) -> int:
    return lc45_max_landing_value(nums)
