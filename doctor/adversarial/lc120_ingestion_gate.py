"""Runner for LC120 ingestion gate (Triangle). Evaluates solvers under syntax_only."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc120_ingestion_gate import lc120_ingestion_gate


def lc120_oracle(triangle: list[list[int]]) -> int:
    """DP bottom-up in-place on last row."""
    n = len(triangle)
    dp = triangle[-1][:]
    for i in range(n - 2, -1, -1):
        for j in range(len(triangle[i])):
            dp[j] = triangle[i][j] + min(dp[j], dp[j + 1])
    return dp[0]


def solver_dp_bottom_up(triangle: list[list[int]]) -> int:
    """Standard DP bottom-up."""
    n = len(triangle)
    dp = triangle[-1][:]
    for i in range(n - 2, -1, -1):
        for j in range(len(triangle[i])):
            dp[j] = triangle[i][j] + min(dp[j], dp[j + 1])
    return dp[0]


def solver_dp_top_down(triangle: list[list[int]]) -> int:
    """DP top-down with memo."""
    from functools import lru_cache

    @lru_cache(None)
    def dfs(r: int, c: int) -> int:
        if r == len(triangle) - 1:
            return triangle[r][c]
        return triangle[r][c] + min(dfs(r + 1, c), dfs(r + 1, c + 1))

    return dfs(0, 0)


def solver_always_zero(triangle: list[list[int]]) -> int:
    return 0


def solver_first_row(triangle: list[list[int]]) -> int:
    return triangle[0][0] if triangle else 0


REFERENCE_TESTS: list[dict[str, list[list[int]] | int]] = [
    {"triangle": [[2], [3, 4], [6, 5, 7], [4, 1, 8, 3]], "expected": 11},
    {"triangle": [[-10]], "expected": -10},
    {"triangle": [[1], [2, 3]], "expected": 3},
    {"triangle": [[-1], [2, 3], [1, -1, -3]], "expected": -1},
    {"triangle": [[5], [1, 6], [4, 3, 2], [7, 8, 9, 1]], "expected": 14},
]


def run_suite(solvers: list[Callable[[list[list[int]]], int]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc120_ingestion_gate(problem={}, solvers=solvers, oracle=lc120_oracle, reference_tests=REFERENCE_TESTS)
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
    print("LC120 Ingestion Gate — Triangle")
    print("=" * 60)
    good = run_suite([solver_dp_bottom_up, solver_dp_top_down], "Good solvers (should PASS)")
    bad = run_suite([solver_always_zero, solver_first_row], "Negative controls (must FAIL)")
    verdict = good["ingest"] is True and bad["ingest"] is False
    print(f"\n{'='*60}")
    print(f"Good solvers ingested: {good['ingest']}")
    print(f"Bad solvers rejected: {not bad['ingest']} (reason: {bad['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
