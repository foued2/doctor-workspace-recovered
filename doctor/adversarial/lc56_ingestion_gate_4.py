"""Runner for LC56 ingestion gate (Merge Intervals).

set_of_tuples comparator for order-insensitive outer list.
ordering_invariant perturbation on input interval order.
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from doctor.adversarial.lc56_ingestion_gate import lc56_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc56_oracle(intervals: list[list[int]]) -> list[list[int]]:
    """Sort by start, then merge overlapping intervals."""
    if not intervals:
        return []
    sorted_iv = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_iv[0]]
    for s, e in sorted_iv[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_sort_merge(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    sorted_iv = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_iv[0]]
    for s, e in sorted_iv[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


def solver_sort_merge_lambda(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    sorted_iv = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_iv[0]]
    for iv in sorted_iv[1:]:
        if iv[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], iv[1])
        else:
            merged.append(list(iv))
    return merged


def solver_in_place(intervals: list[list[int]]) -> list[list[int]]:
    """Copy-first to avoid mutating shared test data."""
    iv = [list(i) for i in intervals]
    if not iv:
        return []
    iv.sort(key=lambda x: x[0])
    i = 0
    while i < len(iv) - 1:
        if iv[i][1] >= iv[i + 1][0]:
            iv[i][1] = max(iv[i][1], iv[i + 1][1])
            iv.pop(i + 1)
        else:
            i += 1
    return iv


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def solver_no_merge(intervals: list[list[int]]) -> list[list[int]]:
    """Returns sorted input without merging. Expect rejection."""
    return sorted(intervals, key=lambda x: x[0])


def solver_bogus(intervals: list[list[int]]) -> list[list[int]]:
    """Returns hardcoded bogus interval. Expect rejection."""
    return [[-1, -1]]


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[list[int]] | list[list[int]]]] = [
    {"intervals": [[1, 3], [2, 6], [8, 10], [15, 18]], "expected": [[1, 6], [8, 10], [15, 18]]},
    {"intervals": [[1, 4], [4, 5]], "expected": [[1, 5]]},
    {"intervals": [[1, 4], [2, 3]], "expected": [[1, 4]]},
    {"intervals": [[1, 2], [3, 4], [5, 6]], "expected": [[1, 2], [3, 4], [5, 6]]},
    {"intervals": [[6, 8], [1, 9], [2, 4], [4, 7]], "expected": [[1, 9]]},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[list[int]]], list[list[int]]]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc56_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc56_oracle,
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
    print("LC56 Ingestion Gate — Merge Intervals")
    print("=" * 60)

    good_solvers = [solver_sort_merge, solver_sort_merge_lambda, solver_in_place]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_no_merge, solver_bogus]
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
