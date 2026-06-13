"""CSSE Problem Definition — Subset Sum (Decision).

Deterministic boolean problem: given a list of positive integers and a target,
return True if any subset sums to exactly target, False otherwise.

Ground truth: brute-force over all 2^n subsets.
"""

from __future__ import annotations


def oracle(solver_input: dict) -> bool:
    """Brute-force ground truth for subset sum."""
    nums = solver_input["nums"]
    target = solver_input["target"]
    n = len(nums)
    for mask in range(1 << n):
        s = 0
        for i in range(n):
            if mask & (1 << i):
                s += nums[i]
        if s == target:
            return True
    return False


# ── Probe Suite (32 probes) ──────────────────────────────────────────────
# Each probe has: probe_id, probe_family, axis, nums, target
# Probe families group probes by structural property that bugs target.

PROBES = [
    # Family: single_match — target equals exactly one element
    {"probe_id": "p01", "probe_family": "single_match", "axis": "element_access", "nums": [1, 3, 5, 7], "target": 5},
    {"probe_id": "p02", "probe_family": "single_match", "axis": "element_access", "nums": [2, 4, 6, 8], "target": 4},
    {"probe_id": "p03", "probe_family": "single_match", "axis": "element_access", "nums": [10, 20, 30], "target": 30},
    {"probe_id": "p04", "probe_family": "single_match", "axis": "element_access", "nums": [3, 7, 11, 13], "target": 11},

    # Family: pair_match — target requires exactly 2 elements
    {"probe_id": "p05", "probe_family": "pair_match", "axis": "combination_logic", "nums": [1, 2, 3, 4], "target": 5},
    {"probe_id": "p06", "probe_family": "pair_match", "axis": "combination_logic", "nums": [2, 3, 5, 7], "target": 10},
    {"probe_id": "p07", "probe_family": "pair_match", "axis": "combination_logic", "nums": [4, 6, 8, 10], "target": 14},
    {"probe_id": "p08", "probe_family": "pair_match", "axis": "combination_logic", "nums": [1, 5, 9, 13], "target": 14},

    # Family: multi_match — target requires 3+ elements
    {"probe_id": "p09", "probe_family": "multi_match", "axis": "combination_logic", "nums": [1, 2, 3, 4, 5], "target": 10},
    {"probe_id": "p10", "probe_family": "multi_match", "axis": "combination_logic", "nums": [2, 3, 4, 5, 6], "target": 15},
    {"probe_id": "p11", "probe_family": "multi_match", "axis": "combination_logic", "nums": [1, 1, 1, 1, 1], "target": 3},
    {"probe_id": "p12", "probe_family": "multi_match", "axis": "combination_logic", "nums": [3, 3, 3, 3, 3], "target": 9},

    # Family: impossible — no subset sums to target
    {"probe_id": "p13", "probe_family": "impossible", "axis": "termination", "nums": [2, 4, 6, 8], "target": 11},
    {"probe_id": "p14", "probe_family": "impossible", "axis": "termination", "nums": [1, 3, 5, 7], "target": 20},
    {"probe_id": "p15", "probe_family": "impossible", "axis": "termination", "nums": [10, 20, 30], "target": 25},
    {"probe_id": "p16", "probe_family": "impossible", "axis": "termination", "nums": [2, 2, 2, 2], "target": 7},

    # Family: edge_case — empty list, zero target, single element
    {"probe_id": "p17", "probe_family": "edge_case", "axis": "boundary_handling", "nums": [], "target": 0},
    {"probe_id": "p18", "probe_family": "edge_case", "axis": "boundary_handling", "nums": [5], "target": 5},
    {"probe_id": "p19", "probe_family": "edge_case", "axis": "boundary_handling", "nums": [5], "target": 3},
    {"probe_id": "p20", "probe_family": "edge_case", "axis": "boundary_handling", "nums": [1, 2], "target": 0},

    # Family: exact_total — sum of all elements equals target
    {"probe_id": "p21", "probe_family": "exact_total", "axis": "summation_logic", "nums": [1, 2, 3], "target": 6},
    {"probe_id": "p22", "probe_family": "exact_total", "axis": "summation_logic", "nums": [5, 5, 5], "target": 15},
    {"probe_id": "p23", "probe_family": "exact_total", "axis": "summation_logic", "nums": [1, 1, 1, 1], "target": 4},
    {"probe_id": "p24", "probe_family": "exact_total", "axis": "summation_logic", "nums": [10, 20, 30, 40], "target": 100},

    # Family: large_gap — target much larger than any individual element
    {"probe_id": "p25", "probe_family": "large_gap", "axis": "accumulation", "nums": [1, 2, 3, 4, 5, 6, 7, 8], "target": 30},
    {"probe_id": "p26", "probe_family": "large_gap", "axis": "accumulation", "nums": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "target": 7},
    {"probe_id": "p27", "probe_family": "large_gap", "axis": "accumulation", "nums": [2, 2, 2, 2, 2, 2], "target": 10},

    # Family: redundant — duplicate elements in input
    {"probe_id": "p28", "probe_family": "redundant", "axis": "deduplication", "nums": [3, 3, 3, 3], "target": 6},
    {"probe_id": "p29", "probe_family": "redundant", "axis": "deduplication", "nums": [1, 1, 2, 2], "target": 3},
    {"probe_id": "p30", "probe_family": "redundant", "axis": "deduplication", "nums": [5, 5, 5, 5, 5], "target": 15},

    # Additional probes for density
    {"probe_id": "p31", "probe_family": "single_match", "axis": "element_access", "nums": [7, 14, 21, 28], "target": 21},
    {"probe_id": "p32", "probe_family": "impossible", "axis": "termination", "nums": [3, 6, 9, 12], "target": 8},
]

AXIS_SET = sorted(set(p["axis"] for p in PROBES))
FAMILY_SET = sorted(set(p["probe_family"] for p in PROBES))
