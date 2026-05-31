"""Runner for LC179 ingestion gate (Largest Number). ordering_invariant."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable
from functools import cmp_to_key

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc179_ingestion_gate import lc179_ingestion_gate


def lc179_oracle(nums: list[int]) -> str:
    """Custom comparator sort."""
    strs = [str(x) for x in nums]

    def cmp(a: str, b: str) -> int:
        if a + b > b + a:
            return -1
        if a + b < b + a:
            return 1
        return 0

    strs.sort(key=cmp_to_key(cmp))
    result = "".join(strs)
    return "0" if result[0] == "0" else result


def solver_sort_cmp(nums: list[int]) -> str:
    """Standard custom comparator sort."""
    strs = [str(x) for x in nums]

    def cmp(a: str, b: str) -> int:
        if a + b > b + a:
            return -1
        if a + b < b + a:
            return 1
        return 0

    strs.sort(key=cmp_to_key(cmp))
    result = "".join(strs)
    return "0" if result[0] == "0" else result


def solver_bubble(nums: list[int]) -> str:
    """Bubble sort with custom comparator."""
    strs = [str(x) for x in nums]
    n = len(strs)
    for i in range(n):
        for j in range(0, n - i - 1):
            if strs[j] + strs[j + 1] < strs[j + 1] + strs[j]:
                strs[j], strs[j + 1] = strs[j + 1], strs[j]
    result = "".join(strs)
    return "0" if result[0] == "0" else result


def solver_always_empty(nums: list[int]) -> str:
    return ""


def solver_always_zero(nums: list[int]) -> str:
    return "0"


REFERENCE_TESTS: list[dict[str, list[int] | str]] = [
    {"nums": [10, 2], "expected": "210"},
    {"nums": [3, 30, 34, 5, 9], "expected": "9534330"},
    {"nums": [9, 90, 9], "expected": "9990"},
    {"nums": [1, 10, 2], "expected": "2110"},
    {"nums": [12, 121], "expected": "12121"},
    {"nums": [8308, 830], "expected": "8308830"},
]


def run_suite(solvers: list[Callable[[list[int]], str]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc179_ingestion_gate(problem={}, solvers=solvers, oracle=lc179_oracle, reference_tests=REFERENCE_TESTS)
    ingest = result["ingest"]
    print(f"  ingest: {ingest}")
    print(f"  reason: {result.get('reason', 'N/A')}")
    metrics = result.get("metrics", {})
    if metrics:
        print(f"  oracle_alignment: {metrics.get('oracle_alignment', 'N/A')}")
        print(f"  avg_stability: {metrics.get('avg_perturbation_stability', 'N/A')}")
    return {"ingest": ingest, "reason": result.get("reason", "N/A")}


def main() -> int:
    print("=" * 60)
    print("LC179 Ingestion Gate — Largest Number")
    print("=" * 60)
    good = run_suite([solver_sort_cmp, solver_bubble], "Good solvers (should PASS)")
    bad = run_suite([solver_always_empty, solver_always_zero], "Negative controls (must FAIL)")
    verdict = good["ingest"] is True and bad["ingest"] is False
    print(f"\n{'='*60}")
    print(f"Good solvers ingested: {good['ingest']}")
    print(f"Bad solvers rejected: {not bad['ingest']} (reason: {bad['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
