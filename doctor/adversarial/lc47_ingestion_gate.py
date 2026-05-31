"""Runner for LC47 ingestion gate (Permutations II).

Input may contain duplicate elements.  multiset_of_multisets comparator
handles output deduplication.  Perturbation generator is duplicate-safe
(no set() collapsing of input elements).
"""
from __future__ import annotations

import itertools
import sys
from collections.abc import Callable

from doctor.adversarial.lc47_ingestion_gate import lc47_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc47_oracle(nums: list[int]) -> list[list[int]]:
    """Unique permutations via itertools.permutations + set dedup."""
    seen: set[tuple[int, ...]] = set()
    result: list[list[int]] = []
    for p in itertools.permutations(nums):
        if p not in seen:
            seen.add(p)
            result.append(list(p))
    return result


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_itertools_unique(nums: list[int]) -> list[list[int]]:
    """itertools.permutations with set dedup — correct but may be slow for large n."""
    seen: set[tuple[int, ...]] = set()
    result: list[list[int]] = []
    for p in itertools.permutations(nums):
        if p not in seen:
            seen.add(p)
            result.append(list(p))
    return result


def solver_backtrack_unique(nums: list[int]) -> list[list[int]]:
    """Backtracking with frequency map — standard unique permutations."""
    result: list[list[int]] = []
    freq: dict[int, int] = {}
    for n in nums:
        freq[n] = freq.get(n, 0) + 1

    def _backtrack(path: list[int]) -> None:
        if len(path) == len(nums):
            result.append(list(path))
            return
        for val in list(freq.keys()):
            if freq[val] > 0:
                freq[val] -= 1
                path.append(val)
                _backtrack(path)
                path.pop()
                freq[val] += 1

    _backtrack([])
    return result


def solver_sorted_adjacent(nums: list[int]) -> list[list[int]]:
    """Backtracking with sorted-array skip-duplicates pattern."""
    nums_sorted = sorted(nums)
    result: list[list[int]] = []
    used = [False] * len(nums_sorted)

    def _backtrack(path: list[int]) -> None:
        if len(path) == len(nums_sorted):
            result.append(list(path))
            return
        for i in range(len(nums_sorted)):
            if used[i]:
                continue
            if i > 0 and nums_sorted[i] == nums_sorted[i - 1] and not used[i - 1]:
                continue
            used[i] = True
            path.append(nums_sorted[i])
            _backtrack(path)
            path.pop()
            used[i] = False

    _backtrack([])
    return result


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def solver_empty(nums: list[int]) -> list[list[int]]:
    """Always returns empty list. Expect rejection."""
    return []


def solver_all_duplicates_removed(nums: list[int]) -> list[list[int]]:
    """Returns permutations of deduped set — loses duplicates, expect rejection."""
    return [list(p) for p in itertools.permutations(list(set(nums)))]


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[int] | list[list[int]]]] = [
    {"nums": [1, 1, 2], "expected": [[1, 1, 2], [1, 2, 1], [2, 1, 1]]},
    {"nums": [1, 2, 3], "expected": [list(p) for p in itertools.permutations([1, 2, 3])]},
    {"nums": [2, 2, 1, 1], "expected": [
        [1, 1, 2, 2], [1, 2, 1, 2], [1, 2, 2, 1],
        [2, 1, 1, 2], [2, 1, 2, 1], [2, 2, 1, 1],
    ]},
    {"nums": [1], "expected": [[1]]},
    {"nums": [1, 1], "expected": [[1, 1]]},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[int]], list[list[int]]]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc47_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc47_oracle,
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
    print("LC47 Ingestion Gate — Permutations II (duplicates)")
    print("=" * 60)

    good_solvers = [solver_itertools_unique, solver_backtrack_unique, solver_sorted_adjacent]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_empty, solver_all_duplicates_removed]
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
