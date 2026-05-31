"""Runner for LC70 boundary probe (Climbing Stairs).

Evaluates solver implementations against a boundary-value corpus and
verifies negative controls fail deterministically.
"""
from __future__ import annotations

import sys

from doctor.adversarial.lc70_boundary_probe import lc70_boundary_probe


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_iterative_dp(n: int) -> int:
    """Standard iterative DP — O(n), O(1) space."""
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def solver_list_dp(n: int) -> int:
    """DP with array — O(n), O(n) space."""
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def solver_recursive_memo(n: int) -> int:
    """Top-down memoized recursion."""
    memo = {1: 1, 2: 2}

    def _fib(x: int) -> int:
        if x not in memo:
            memo[x] = _fib(x - 1) + _fib(x - 2)
        return memo[x]

    return _fib(n)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("LC70 Boundary Probe — Climbing Stairs")
    print("=" * 60)

    solvers = [solver_iterative_dp, solver_list_dp, solver_recursive_memo]
    result = lc70_boundary_probe(solvers, verbose=True)

    print("-" * 60)
    print(f"Overall verdict: {result['overall_verdict']}")
    print(f"Solvers tested: {len(solvers)}")
    print(f"Boundary cases: {len(result['boundary_cases'])}")
    print("=" * 60)

    return 0 if result["overall_verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
