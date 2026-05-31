"""Runner for LC137 ingestion gate (Single Number II).

Evaluates solver implementations under ordering_invariant perturbations.
Must reject negative control solvers deterministically.
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from doctor.adversarial.lc137_ingestion_gate import lc137_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc137_oracle(nums: list[int]) -> int:
    """Bit-counting modulo 3 — canonical Single Number II solution."""
    ones = 0
    twos = 0
    for n in nums:
        ones = (ones ^ n) & ~twos
        twos = (twos ^ n) & ~ones
    return ones


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_bitwise_mod3(nums: list[int]) -> int:
    """Standard bitwise tracking of bits appearing 1x vs 2x."""
    ones = 0
    twos = 0
    for n in nums:
        ones = (ones ^ n) & ~twos
        twos = (twos ^ n) & ~ones
    return ones


def solver_dict_count(nums: list[int]) -> int:
    """Count occurrences via dict, return the one with count=1."""
    from collections import Counter
    for val, count in Counter(nums).items():
        if count == 1:
            return val
    return 0


def solver_sorted_scan(nums: list[int]) -> int:
    """Sort and scan for the element that appears once."""
    nums_sorted = sorted(nums)
    for i in range(0, len(nums_sorted), 3):
        if i + 2 >= len(nums_sorted) or nums_sorted[i] != nums_sorted[i + 2]:
            return nums_sorted[i]
    return 0


# ---------------------------------------------------------------------------
# Negative controls (must be rejected by the gate)
# ---------------------------------------------------------------------------

def solver_always_zero(nums: list[int]) -> int:
    """Always returns 0. Expect false_consensus or instability."""
    return 0


def solver_first_element(nums: list[int]) -> int:
    """Returns nums[0] — nonsensical. Expect rejection."""
    return nums[0] if nums else 0


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"nums": [2, 2, 3, 2], "expected": 3},
    {"nums": [0, 1, 0, 1, 0, 1, 99], "expected": 99},
    {"nums": [5], "expected": 5},
    {"nums": [7, 3, 3, 3], "expected": 7},
    {"nums": [1, 1, 1, 2], "expected": 2},
    {"nums": [-2, -2, -2, 5], "expected": 5},
    {"nums": [30000, 500, 30000, 500, 30000, 500, 42], "expected": 42},
    {"nums": [0, 0, 0, 1], "expected": 1},
    {"nums": [2, 4, 2, 4, 2, 4, 9], "expected": 9},
    {"nums": [1, 2, 2, 2], "expected": 1},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[int]], int]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc137_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc137_oracle,
        reference_tests=REFERENCE_TESTS,
    )
    ingest = result["ingest"]
    reason = result["reason"]
    metrics = result.get("metrics", {})
    print(f"  ingest: {ingest}")
    print(f"  reason: {reason}")
    if metrics:
        os_ = metrics.get("oracle_alignment", "N/A")
        ps_ = metrics.get("avg_perturbation_stability", "N/A")
        print(f"  oracle_alignment: {os_}")
        print(f"  avg_stability: {ps_}")
        per_solver = metrics.get("perturbation_stability", {}).get("per_solver", {})
        for sname, stab in per_solver.items():
            print(f"  {sname}: stability={stab}")
    return {"ingest": ingest, "reason": reason}


def main() -> int:
    print("=" * 60)
    print("LC137 Ingestion Gate — Single Number II")
    print("=" * 60)

    good_solvers = [solver_bitwise_mod3, solver_dict_count, solver_sorted_scan]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_always_zero, solver_first_element]
    bad_result = run_suite(bad_solvers, "Negative controls (must FAIL)")

    print("\n" + "=" * 60)
    verdict = (
        good_result["ingest"] is True and bad_result["ingest"] is False
    )
    print(f"Good solvers ingested: {good_result['ingest']}")
    print(f"Bad solvers rejected: {not bad_result['ingest']} (reason: {bad_result['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print("=" * 60)

    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
