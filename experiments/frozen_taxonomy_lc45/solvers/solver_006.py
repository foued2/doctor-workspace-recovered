"""External blind pack solver 006: reachable boolean confusion.

Wraps lc45_candidates.lc45_reachable_boolean_confusion.
Family: reachability-as-boolean (returns truthiness, not count).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_reachable_boolean_confusion


def solve(nums: list[int]) -> int:
    return lc45_reachable_boolean_confusion(nums)
