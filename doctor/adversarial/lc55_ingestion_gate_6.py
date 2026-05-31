"""Runner for LC55 ingestion gate (Jump Game).

Evaluates solver implementations under margin_compression_invariant perturbations.
Must reject negative control solvers deterministically.
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc55_ingestion_gate import lc55_ingestion_gate
from solvers.negative_controls import lc55_slack_dependent


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc55_oracle(nums: list[int]) -> bool:
    """Greedy right-to-left: can reach the last index."""
    n = len(nums)
    leftmost_good = n - 1
    for i in range(n - 2, -1, -1):
        if i + nums[i] >= leftmost_good:
            leftmost_good = i
    return leftmost_good == 0


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_greedy_rtl(nums: list[int]) -> bool:
    """Right-to-left greedy — standard O(n)."""
    n = len(nums)
    leftmost_good = n - 1
    for i in range(n - 2, -1, -1):
        if i + nums[i] >= leftmost_good:
            leftmost_good = i
    return leftmost_good == 0


def solver_greedy_ltr(nums: list[int]) -> bool:
    """Left-to-right max-reach — alternative O(n)."""
    max_reach = 0
    for i in range(len(nums)):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + nums[i])
        if max_reach >= len(nums) - 1:
            return True
    return max_reach >= len(nums) - 1


def solver_dp_forward(nums: list[int]) -> bool:
    """Forward DP — O(n^2) but functionally correct."""
    n = len(nums)
    if n <= 1:
        return True
    dp = [False] * n
    dp[0] = True
    for i in range(n):
        if dp[i]:
            for j in range(1, nums[i] + 1):
                if i + j < n:
                    dp[i + j] = True
    return dp[n - 1]


# ---------------------------------------------------------------------------
# Negative controls (must be rejected by the gate)
# ---------------------------------------------------------------------------

def solver_always_true(nums: list[int]) -> bool:
    """Always returns True. Expect rejection."""
    return True


def solver_always_false(nums: list[int]) -> bool:
    """Always returns False. Expect rejection."""
    return False


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[int] | bool]] = [
    {"nums": [2, 3, 1, 1, 4], "expected": True},
    {"nums": [3, 2, 1, 0, 4], "expected": False},
    {"nums": [0], "expected": True},
    {"nums": [0, 1], "expected": False},
    {"nums": [1, 0], "expected": True},
    {"nums": [1, 1, 1, 1], "expected": True},
    {"nums": [5, 0, 0, 0, 0], "expected": True},
    {"nums": [2, 0, 0, 0], "expected": False},
    {"nums": [2, 5, 0, 0, 0, 0], "expected": True},
    {"nums": [1, 2, 0, 1, 0], "expected": True},
    {"nums": [3, 0, 0, 2, 0, 1], "expected": True},
    {"nums": [1, 0, 0, 0, 5], "expected": False},
    {"nums": [10, 0, 0, 0, 0], "expected": True},
    {"nums": [2, 0, 1, 0, 1], "expected": False},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[int]], bool]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc55_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc55_oracle,
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
    print("LC55 Ingestion Gate — Jump Game")
    print("=" * 60)

    good_solvers = [solver_greedy_rtl, solver_greedy_ltr, solver_dp_forward]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    # ``minimum_margin_feasibility`` only retains feasible perturbations, so
    # always-true is accidentally competent on this family. The must-fail lane
    # uses controls that are actually falsified by minimum-margin compression.
    bad_solvers = [solver_always_false, lc55_slack_dependent]
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
