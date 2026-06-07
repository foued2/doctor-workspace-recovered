"""External blind pack solver 28: Hybrid family.
Pack source: reconstructed_stub (see seval_manifest.json).
Mirrors the LC3946 family layout: 5 DP-survivor, 5 Greedy-by-price,
5 Greedy-by-density, 5 BFS-subset, 5 Recursive, 5 Hybrid.
"""
from __future__ import annotations

from doctor.adversarial.lc3946_candidates import solver_028 as _impl


def solve(solver_input: list) -> int:
    return _impl(solver_input)
