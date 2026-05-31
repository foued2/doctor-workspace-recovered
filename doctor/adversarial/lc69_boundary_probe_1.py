"""Runner for LC69 boundary probe (Sqrt(x)).

Evaluates solver implementations against a boundary-value corpus and
verifies negative controls fail deterministically.
"""
from __future__ import annotations

import math
import sys

from doctor.adversarial.lc69_boundary_probe import lc69_boundary_probe


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_int_sqrt(x: int) -> int:
    """Python 3.8+ math.isqrt — gold standard."""
    return math.isqrt(x)


def solver_binary_search(x: int) -> int:
    """Binary search floor sqrt."""
    if x < 2:
        return x
    lo, hi = 0, x
    while lo <= hi:
        mid = (lo + hi) // 2
        sq = mid * mid
        if sq == x:
            return mid
        if sq < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return hi


def solver_newton(x: int) -> int:
    """Newton's method integer sqrt."""
    if x < 2:
        return x
    r = x
    while r * r > x:
        r = (r + x // r) // 2
    return r


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("LC69 Boundary Probe — Sqrt(x)")
    print("=" * 60)

    solvers = [solver_int_sqrt, solver_binary_search, solver_newton]
    result = lc69_boundary_probe(solvers, verbose=True)

    print("-" * 60)
    print(f"Overall verdict: {result['overall_verdict']}")
    print(f"Solvers tested: {len(solvers)}")
    print(f"Boundary cases: {len(result['boundary_cases'])}")
    print("=" * 60)

    return 0 if result["overall_verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
