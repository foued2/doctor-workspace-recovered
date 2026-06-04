"""External blind pack solver 001: BFS with depth cutoff (LC45 SURVIVOR).

Wraps lc45_candidates.lc45_bfs_depth_cutoff.
Passes all oracle cases by construction (paper-confirmed survivor).

Pack source: external_baseline (LC45 candidate corpus).
"""
from __future__ import annotations

from doctor.adversarial.lc45_candidates import lc45_bfs_depth_cutoff


def solve(nums: list[int]) -> int:
    return lc45_bfs_depth_cutoff(nums)
