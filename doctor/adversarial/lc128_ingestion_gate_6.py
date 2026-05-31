"""Runner for LC128 ingestion gate (Longest Consecutive Sequence).

Evaluates solver implementations under ordering_invariant perturbations.
Must reject negative control solvers deterministically.
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc128_ingestion_gate import lc128_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc128_oracle(nums: list[int]) -> int:
    """Set-based longest consecutive sequence."""
    if not nums:
        return 0
    num_set = set(nums)
    longest = 0
    for n in num_set:
        if n - 1 not in num_set:
            length = 1
            while n + length in num_set:
                length += 1
            longest = max(longest, length)
    return longest


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_set_based(nums: list[int]) -> int:
    """Standard set-based O(n) approach."""
    if not nums:
        return 0
    num_set = set(nums)
    longest = 0
    for n in num_set:
        if n - 1 not in num_set:
            length = 1
            while n + length in num_set:
                length += 1
            longest = max(longest, length)
    return longest


def solver_sorted_scan(nums: list[int]) -> int:
    """Sort and scan — O(n log n) but functionally equivalent."""
    if not nums:
        return 0
    nums_sorted = sorted(set(nums))
    longest = 1
    current = 1
    for i in range(1, len(nums_sorted)):
        if nums_sorted[i] == nums_sorted[i - 1] + 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def solver_union_find(nums: list[int]) -> int:
    """Union-find based approach. Tracks consecutive runs via DSU."""
    if not nums:
        return 0
    parent: dict[int, int] = {}
    size: dict[int, int] = {}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx == ry:
            return
        if size[rx] < size[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        size[rx] += size[ry]

    num_set = set(nums)
    for n in num_set:
        parent[n] = n
        size[n] = 1
    for n in num_set:
        if n - 1 in num_set:
            union(n, n - 1)
        if n + 1 in num_set:
            union(n, n + 1)

    return max(size.values()) if size else 0


# ---------------------------------------------------------------------------
# Negative controls (must be rejected by the gate)
# ---------------------------------------------------------------------------

def solver_always_zero(nums: list[int]) -> int:
    """Always returns 0. Expect rejection."""
    return 0


def solver_return_len(nums: list[int]) -> int:
    """Returns len(nums) — wrong. Expect rejection."""
    return len(nums)


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"nums": [100, 4, 200, 1, 3, 2], "expected": 4},
    {"nums": [0, 3, 7, 2, 5, 8, 4, 6, 0, 1], "expected": 9},
    {"nums": [1, 2, 0, 1], "expected": 3},
    {"nums": [0], "expected": 1},
    {"nums": [], "expected": 0},
    {"nums": [1, 1, 1], "expected": 1},
    {"nums": [9, 8, 7, 6, 5, 4, 3, 2, 1], "expected": 9},
    {"nums": [10, 20, 30], "expected": 1},
    {"nums": [1, 3, 5, 2, 4], "expected": 5},
    {"nums": [-5, -4, -3, -2, -1, 0, 1], "expected": 7},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[int]], int]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc128_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc128_oracle,
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
    print("LC128 Ingestion Gate — Longest Consecutive Sequence")
    print("=" * 60)

    good_solvers = [solver_set_based, solver_sorted_scan, solver_union_find]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_always_zero, solver_return_len]
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
