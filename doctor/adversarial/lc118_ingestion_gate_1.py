"""Runner for LC118 ingestion gate (Pascal's Triangle).

syntax_only perturbation (integer input, no valid reorder).
exact_scalar comparator (positionally ordered rows).
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from doctor.adversarial.lc118_ingestion_gate import lc118_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc118_oracle(num_rows: int) -> list[list[int]]:
    """Generate Pascal's Triangle."""
    result: list[list[int]] = []
    for i in range(num_rows):
        row = [1] * (i + 1)
        for j in range(1, i):
            row[j] = result[i - 1][j - 1] + result[i - 1][j]
        result.append(row)
    return result


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_iterative(num_rows: int) -> list[list[int]]:
    result: list[list[int]] = []
    for i in range(num_rows):
        row = [1] * (i + 1)
        for j in range(1, i):
            row[j] = result[i - 1][j - 1] + result[i - 1][j]
        result.append(row)
    return result


def solver_recursive(num_rows: int) -> list[list[int]]:
    if num_rows == 0:
        return []

    def _build(n: int) -> list[list[int]]:
        if n == 1:
            return [[1]]
        prev = _build(n - 1)
        last_row = prev[-1]
        new_row = [1]
        for i in range(1, len(last_row)):
            new_row.append(last_row[i - 1] + last_row[i])
        new_row.append(1)
        prev.append(new_row)
        return prev

    return _build(num_rows)


def solver_combinatorial(num_rows: int) -> list[list[int]]:
    """Use math.comb for each value."""
    import math
    result: list[list[int]] = []
    for i in range(num_rows):
        row = [math.comb(i, j) for j in range(i + 1)]
        result.append(row)
    return result


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def solver_empty(num_rows: int) -> list[list[int]]:
    """Always returns empty list. Expect rejection."""
    return []


def solver_ones_only(num_rows: int) -> list[list[int]]:
    """Returns rows of all ones — wrong. Expect rejection."""
    return [[1] * (i + 1) for i in range(num_rows)]


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, int | list[list[int]]]] = [
    {"numRows": 1, "expected": [[1]]},
    {"numRows": 2, "expected": [[1], [1, 1]]},
    {"numRows": 3, "expected": [[1], [1, 1], [1, 2, 1]]},
    {"numRows": 5, "expected": [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]},
    {"numRows": 0, "expected": []},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[int], list[list[int]]]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc118_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc118_oracle,
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
    print("LC118 Ingestion Gate — Pascal's Triangle")
    print("=" * 60)

    good_solvers = [solver_iterative, solver_recursive, solver_combinatorial]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_empty, solver_ones_only]
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
