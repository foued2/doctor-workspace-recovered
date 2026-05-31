"""Runner for LC46 ingestion gate (Permutations).

Evaluates solvers under multiset_invariant perturbations.
multiset_of_multisets comparator handles structural output.
"""
from __future__ import annotations

import itertools
import sys
from collections.abc import Callable

from doctor.adversarial.lc46_ingestion_gate import lc46_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc46_oracle(nums: list[int]) -> list[list[int]]:
    """All permutations via itertools."""
    return [list(p) for p in itertools.permutations(nums)]


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_itertools(nums: list[int]) -> list[list[int]]:
    return [list(p) for p in itertools.permutations(nums)]


def solver_backtrack(nums: list[int]) -> list[list[int]]:
    """Backtracking permutation generator."""
    result: list[list[int]] = []

    def _backtrack(path: list[int], used: list[bool]) -> None:
        if len(path) == len(nums):
            result.append(list(path))
            return
        for i in range(len(nums)):
            if not used[i]:
                used[i] = True
                path.append(nums[i])
                _backtrack(path, used)
                path.pop()
                used[i] = False

    _backtrack([], [False] * len(nums))
    return result


def solver_recursive_insert(nums: list[int]) -> list[list[int]]:
    """Recursive insertion: build permutations by inserting next element."""
    if not nums:
        return [[]]
    perms = solver_recursive_insert(nums[:-1])
    last = nums[-1]
    result: list[list[int]] = []
    for p in perms:
        for i in range(len(p) + 1):
            result.append(p[:i] + [last] + p[i:])
    return result


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def solver_empty(nums: list[int]) -> list[list[int]]:
    """Always returns empty list. Expect rejection."""
    return []


def solver_first_only(nums: list[int]) -> list[list[int]]:
    """Returns only the original input as a single permutation. Expect rejection."""
    return [list(nums)]


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[int] | list[list[int]]]] = [
    {"nums": [1, 2, 3], "expected": [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]},
    {"nums": [0, 1], "expected": [[0, 1], [1, 0]]},
    {"nums": [1], "expected": [[1]]},
    {"nums": [1, 2, 3, 4], "expected": [list(p) for p in itertools.permutations([1, 2, 3, 4])]},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[int]], list[list[int]]]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc46_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc46_oracle,
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
    print("LC46 Ingestion Gate — Permutations")
    print("=" * 60)

    good_solvers = [solver_itertools, solver_backtrack, solver_recursive_insert]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_empty, solver_first_only]
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
