"""Runner for LC53 ingestion gate (Maximum Subarray). Evaluates solvers under syntax_only."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc53_ingestion_gate import lc53_ingestion_gate


def lc53_oracle(nums: list[int]) -> int:
    """Kadane's algorithm."""
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def solver_kadane(nums: list[int]) -> int:
    """Standard Kadane's algorithm."""
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def solver_bruteforce(nums: list[int]) -> int:
    """O(n^2) brute force."""
    n = len(nums)
    best = nums[0]
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            best = max(best, s)
    return best


def solver_dc(nums: list[int]) -> int:
    """Divide and conquer."""
    def _max_cross(arr: list[int], lo: int, mid: int, hi: int) -> int:
        left_sum = arr[mid]
        cur = 0
        for i in range(mid, lo - 1, -1):
            cur += arr[i]
            left_sum = max(left_sum, cur)
        right_sum = arr[mid + 1]
        cur = 0
        for i in range(mid + 1, hi + 1):
            cur += arr[i]
            right_sum = max(right_sum, cur)
        return left_sum + right_sum

    def _max_sub(arr: list[int], lo: int, hi: int) -> int:
        if lo == hi:
            return arr[lo]
        mid = (lo + hi) // 2
        return max(_max_sub(arr, lo, mid), _max_sub(arr, mid + 1, hi), _max_cross(arr, lo, mid, hi))

    if not nums:
        return 0
    return _max_sub(nums, 0, len(nums) - 1)


def solver_always_zero(nums: list[int]) -> int:
    return 0


def solver_max_element(nums: list[int]) -> int:
    return max(nums)


REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4], "expected": 6},
    {"nums": [1], "expected": 1},
    {"nums": [5, 4, -1, 7, 8], "expected": 23},
    {"nums": [-1], "expected": -1},
    {"nums": [-2, -1], "expected": -1},
    {"nums": [1, 2, 3, 4], "expected": 10},
    {"nums": [0, -1, 2, -3, 5, -2, 3], "expected": 6},
]


def run_suite(solvers: list[Callable[[list[int]], int]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc53_ingestion_gate(problem={}, solvers=solvers, oracle=lc53_oracle, reference_tests=REFERENCE_TESTS)
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
    print("LC53 Ingestion Gate — Maximum Subarray")
    print("=" * 60)
    good = run_suite([solver_kadane, solver_bruteforce, solver_dc], "Good solvers (should PASS)")
    bad = run_suite([solver_always_zero, solver_max_element], "Negative controls (must FAIL)")
    verdict = good["ingest"] is True and bad["ingest"] is False
    print(f"\n{'='*60}")
    print(f"Good solvers ingested: {good['ingest']}")
    print(f"Bad solvers rejected: {not bad['ingest']} (reason: {bad['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
