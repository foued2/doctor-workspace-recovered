"""Runner for LC57 ingestion gate (Insert Interval).

syntax_only perturbation (input sorted by start, no valid reorder).
exact_scalar comparator (output is positionally ordered).
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from doctor.adversarial.lc57_ingestion_gate import lc57_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc57_oracle(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Insert newInterval into sorted intervals, merge overlapping."""
    result: list[list[int]] = []
    i = 0
    ns, ne = new_interval
    # Add all intervals before newInterval
    while i < len(intervals) and intervals[i][1] < ns:
        result.append(intervals[i])
        i += 1
    # Merge overlapping with newInterval
    while i < len(intervals) and intervals[i][0] <= ne:
        ns = min(ns, intervals[i][0])
        ne = max(ne, intervals[i][1])
        i += 1
    result.append([ns, ne])
    # Add remaining
    while i < len(intervals):
        result.append(intervals[i])
        i += 1
    return result


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_insert_merge(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    i = 0
    ns, ne = new_interval
    while i < len(intervals) and intervals[i][1] < ns:
        result.append(intervals[i])
        i += 1
    while i < len(intervals) and intervals[i][0] <= ne:
        ns = min(ns, intervals[i][0])
        ne = max(ne, intervals[i][1])
        i += 1
    result.append([ns, ne])
    while i < len(intervals):
        result.append(intervals[i])
        i += 1
    return result


def solver_linear_scan(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    ns, ne = new_interval
    left = [iv for iv in intervals if iv[1] < ns]
    right = [iv for iv in intervals if iv[0] > ne]
    merged_ns = ns
    merged_ne = ne
    for iv in intervals:
        if not (iv[1] < ns or iv[0] > ne):
            merged_ns = min(merged_ns, iv[0])
            merged_ne = max(merged_ne, iv[1])
    return left + [[merged_ns, merged_ne]] + right


def solver_append_sort(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Append newInterval, sort, then merge — correct but less efficient."""
    combined = intervals + [new_interval]
    combined.sort(key=lambda x: x[0])
    merged = [combined[0]]
    for s, e in combined[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def solver_empty(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Always returns empty list. Expect rejection."""
    return []


def solver_just_new(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Returns only newInterval — ignores existing intervals. Expect rejection."""
    return [list(new_interval)]


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[list[int]] | list[int]]] = [
    {"intervals": [[1, 3], [6, 9]], "newInterval": [2, 5], "expected": [[1, 5], [6, 9]]},
    {"intervals": [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], "newInterval": [4, 8],
     "expected": [[1, 2], [3, 10], [12, 16]]},
    {"intervals": [], "newInterval": [5, 7], "expected": [[5, 7]]},
    {"intervals": [[1, 5]], "newInterval": [2, 3], "expected": [[1, 5]]},
    {"intervals": [[1, 5]], "newInterval": [6, 8], "expected": [[1, 5], [6, 8]]},
    {"intervals": [[3, 5]], "newInterval": [1, 2], "expected": [[1, 2], [3, 5]]},
    {"intervals": [[1, 2], [3, 4], [5, 6]], "newInterval": [2, 5],
     "expected": [[1, 6]]},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[list[int]], list[int]], list[list[int]]]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc57_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc57_oracle,
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
    print("LC57 Ingestion Gate — Insert Interval")
    print("=" * 60)

    good_solvers = [solver_insert_merge, solver_linear_scan, solver_append_sort]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_empty, solver_just_new]
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
