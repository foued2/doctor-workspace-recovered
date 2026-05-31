"""Runner for LC121 ingestion gate (Best Time to Buy and Sell Stock). syntax_only."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc121_ingestion_gate import lc121_ingestion_gate


def lc121_oracle(prices: list[int]) -> int:
    """One pass: track min price and max profit."""
    min_price = prices[0]
    max_profit = 0
    for p in prices[1:]:
        min_price = min(min_price, p)
        max_profit = max(max_profit, p - min_price)
    return max_profit


def solver_one_pass(prices: list[int]) -> int:
    """Standard one-pass O(n)."""
    min_price = prices[0]
    max_profit = 0
    for p in prices[1:]:
        min_price = min(min_price, p)
        max_profit = max(max_profit, p - min_price)
    return max_profit


def solver_bruteforce(prices: list[int]) -> int:
    """O(n^2) brute force."""
    best = 0
    for i in range(len(prices)):
        for j in range(i + 1, len(prices)):
            best = max(best, prices[j] - prices[i])
    return best


def solver_always_zero(prices: list[int]) -> int:
    return 0


def solver_max_minus_min(prices: list[int]) -> int:
    return max(0, max(prices) - min(prices))


REFERENCE_TESTS: list[dict[str, list[int] | int]] = [
    {"prices": [7, 1, 5, 3, 6, 4], "expected": 5},
    {"prices": [7, 6, 4, 3, 1], "expected": 0},
    {"prices": [1, 2], "expected": 1},
    {"prices": [3, 2, 6, 5, 0, 3], "expected": 4},
    {"prices": [2, 1, 4], "expected": 3},
]


def run_suite(solvers: list[Callable[[list[int]], int]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc121_ingestion_gate(problem={}, solvers=solvers, oracle=lc121_oracle, reference_tests=REFERENCE_TESTS)
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
    print("LC121 Ingestion Gate — Best Time to Buy and Sell Stock")
    print("=" * 60)
    good = run_suite([solver_one_pass, solver_bruteforce], "Good solvers (should PASS)")
    bad = run_suite([solver_always_zero, solver_max_minus_min], "Negative controls (must FAIL)")
    verdict = good["ingest"] is True and bad["ingest"] is False
    print(f"\n{'='*60}")
    print(f"Good solvers ingested: {good['ingest']}")
    print(f"Bad solvers rejected: {not bad['ingest']} (reason: {bad['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
