"""Runner for LC198 ingestion gate (House Robber). syntax_only."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc198_ingestion_gate import lc198_ingestion_gate


def lc198_oracle(nums: list[int]) -> int:
    """DP with two variables."""
    prev2 = prev1 = 0
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1


def solver_dp_two_var(nums: list[int]) -> int:
    """Standard O(1) space DP."""
    prev2 = prev1 = 0
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1


def solver_dp_array(nums: list[int]) -> int:
    """DP with array."""
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    for i in range(2, len(nums)):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    return dp[-1]


def solver_memo(nums: list[int]) -> int:
    """Top-down with memoization."""
    from functools import lru_cache

    @lru_cache(None)
    def dfs(i: int) -> int:
        if i >= len(nums):
            return 0
        return max(dfs(i + 1), nums[i] + dfs(i + 2))

    return dfs(0)


def solver_always_zero(nums: list[int]) -> int:
    return 0


def solver_sum_all(nums: list[int]) -> int:
    return sum(nums)


REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"nums": [1, 2, 3, 1], "expected": 4},
    {"nums": [2, 7, 9, 3, 1], "expected": 12},
    {"nums": [0], "expected": 0},
    {"nums": [1, 1], "expected": 1},
    {"nums": [5, 1, 1, 5], "expected": 10},
    {"nums": [2, 1, 1, 2], "expected": 4},
]


def run_suite(solvers: list[Callable[[list[int]], int]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc198_ingestion_gate(problem={}, solvers=solvers, oracle=lc198_oracle, reference_tests=REFERENCE_TESTS)
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
    print("LC198 Ingestion Gate — House Robber")
    print("=" * 60)
    good = run_suite([solver_dp_two_var, solver_dp_array, solver_memo], "Good solvers (should PASS)")
    bad = run_suite([solver_always_zero, solver_sum_all], "Negative controls (must FAIL)")
    verdict = good["ingest"] is True and bad["ingest"] is False
    print(f"\n{'='*60}")
    print(f"Good solvers ingested: {good['ingest']}")
    print(f"Bad solvers rejected: {not bad['ingest']} (reason: {bad['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
