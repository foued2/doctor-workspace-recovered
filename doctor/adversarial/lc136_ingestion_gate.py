"""Runner for LC136 ingestion gate (Single Number).

Evaluates solver implementations under ordering_invariant perturbations.
Must reject negative control solvers deterministically.
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from doctor.adversarial.lc136_ingestion_gate import lc136_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc136_oracle(nums: list[int]) -> int:
    """XOR reduce — canonical Single Number solution."""
    result = 0
    for n in nums:
        result ^= n
    return result


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_xor_reduce(nums: list[int]) -> int:
    """Standard XOR reduce."""
    result = 0
    for n in nums:
        result ^= n
    return result


def solver_reduce_lambda(nums: list[int]) -> int:
    """XOR via functools.reduce."""
    from functools import reduce
    return reduce(lambda a, b: a ^ b, nums)


def solver_xor_sorted(nums: list[int]) -> int:
    """Sort first, then XOR (order-insensitive), same result."""
    result = 0
    for n in sorted(nums):
        result ^= n
    return result


# ---------------------------------------------------------------------------
# Negative controls (must be rejected by the gate)
# ---------------------------------------------------------------------------

def solver_always_zero(nums: list[int]) -> int:
    """Trivially wrong — always returns 0. Expect false_consensus rejection."""
    return 0


def solver_sum_mod(nums: list[int]) -> int:
    """Returns sum % 2 — wrong approach. Expect false_consensus or instability."""
    return sum(nums) % 2


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"nums": [2, 2, 1], "expected": 1},
    {"nums": [4, 1, 2, 1, 2], "expected": 4},
    {"nums": [1], "expected": 1},
    {"nums": [0, 0, 3], "expected": 3},
    {"nums": [100, 50, 100, 50, 7], "expected": 7},
    {"nums": [-5, 10, -5, 3, 10], "expected": 3},
    {"nums": [1, 2, 3, 4, 5, 4, 3, 2, 1], "expected": 5},
    {"nums": [42], "expected": 42},
    {"nums": [7, 3, 5, 3, 7], "expected": 5},
    {"nums": [0, 1, 0, 1, 99], "expected": 99},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[int]], int]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc136_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc136_oracle,
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
    print("LC136 Ingestion Gate — Single Number")
    print("=" * 60)

    # Good solvers — should ingest
    good_solvers = [solver_xor_reduce, solver_reduce_lambda, solver_xor_sorted]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    # Bad solvers — must be rejected
    bad_solvers = [solver_always_zero, solver_sum_mod]
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
