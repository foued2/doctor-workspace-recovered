"""Runner for LC191 boundary probe (Number of 1 Bits / popcount).

Evaluates solver implementations against a boundary-value corpus and
verifies negative controls fail deterministically.
"""
from __future__ import annotations

import sys

from doctor.adversarial.lc191_boundary_probe import lc191_boundary_probe


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_bit_count(n: int) -> int:
    """Python 3.8+ int.bit_count()."""
    return n.bit_count()


def solver_bin_count(n: int) -> int:
    """bin(n).count('1') — traditional approach."""
    return bin(n).count("1")


def solver_loop_shift(n: int) -> int:
    """Loop and shift — bit-by-bit popcount."""
    count = 0
    while n:
        count += n & 1
        n >>= 1
    return count


def solver_brian_kernighan(n: int) -> int:
    """Brian Kernighan's algorithm — clears lowest set bit each iteration."""
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("LC191 Boundary Probe — Number of 1 Bits (popcount)")
    print("=" * 60)

    solvers = [solver_bit_count, solver_bin_count, solver_loop_shift, solver_brian_kernighan]
    result = lc191_boundary_probe(solvers, verbose=True)

    print("-" * 60)
    print(f"Overall verdict: {result['overall_verdict']}")
    print(f"Solvers tested: {len(solvers)}")
    print(f"Boundary cases: {len(result['boundary_cases'])}")
    print("=" * 60)

    return 0 if result["overall_verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
