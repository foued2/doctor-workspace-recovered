"""Runner for LC152 ingestion gate (Maximum Product Subarray). syntax_only."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc152_ingestion_gate import lc152_ingestion_gate


def lc152_oracle(nums: list[int]) -> int:
    """DP tracking min/max product."""
    best = cur_max = cur_min = nums[0]
    for x in nums[1:]:
        candidates = (cur_max * x, cur_min * x, x)
        cur_max = max(candidates)
        cur_min = min(candidates)
        best = max(best, cur_max)
    return best


def solver_dp(nums: list[int]) -> int:
    """Standard DP with min/max tracking."""
    best = cur_max = cur_min = nums[0]
    for x in nums[1:]:
        candidates = (cur_max * x, cur_min * x, x)
        cur_max = max(candidates)
        cur_min = min(candidates)
        best = max(best, cur_max)
    return best


def solver_bruteforce(nums: list[int]) -> int:
    """O(n^2) brute force."""
    best = nums[0]
    for i in range(len(nums)):
        p = 1
        for j in range(i, len(nums)):
            p *= nums[j]
            best = max(best, p)
    return best


def solver_always_zero(nums: list[int]) -> int:
    return 0


def solver_max_element(nums: list[int]) -> int:
    return max(nums)


REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"nums": [2, 3, -2, 4], "expected": 6},
    {"nums": [-2, 0, -1], "expected": 0},
    {"nums": [-2], "expected": -2},
    {"nums": [2, -5, 3, 1, -4], "expected": 120},
    {"nums": [0, 2], "expected": 2},
    {"nums": [-1, -2, -3], "expected": 6},
]


def run_suite(solvers: list[Callable[[list[int]], int]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc152_ingestion_gate(problem={}, solvers=solvers, oracle=lc152_oracle, reference_tests=REFERENCE_TESTS)
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
    print("LC152 Ingestion Gate — Maximum Product Subarray")
    print("=" * 60)
    good = run_suite([solver_dp, solver_bruteforce], "Good solvers (should PASS)")
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
