"""Verify LC322 ingestion gate baseline + structural comparator tests."""
from __future__ import annotations

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doctor.adversarial.lc322_ingestion_gate import lc322_ingestion_gate
from doctor.adversarial.lc322_candidates import (
    lc322_dp,
    lc322_greedy,
    lc322_smallest_first,
    lc322_memo_collision,
    lc322_lookahead_one,
)
from doctor.adversarial.lc322_ground_truth import lc322_brute_force
from doctor.adversarial.structural_comparator import (
    multiset_of_multisets,
    exact_scalar,
    boolean_exact,
    multiset_of_scalars,
)

FIXED_INPUTS: list[dict[str, int | list[int]]] = [
    {"coins": [1], "amount": 5},
    {"coins": [1, 2, 5], "amount": 11},
    {"coins": [2], "amount": 3},
    {"coins": [1, 3, 4], "amount": 6},
    {"coins": [5], "amount": 11},
    {"coins": [2, 5, 10], "amount": 13},
    {"coins": [1, 5, 10, 25], "amount": 30},
]

SOLVERS = [lc322_dp, lc322_greedy, lc322_smallest_first, lc322_memo_collision, lc322_lookahead_one]
ORACLE = lc322_brute_force

# ── Part 1: LC322 baseline ──────────────────────────────────────────────

print("=== Part 1: LC322 Baseline (7 FIXED_INPUTS) ===")
result = lc322_ingestion_gate(
    problem={},
    solvers=SOLVERS,
    oracle=ORACLE,
    reference_tests=FIXED_INPUTS,
    perturbation_samples=5,
)
print(json.dumps(result, indent=2))
print()

# Expected (from FINDINGS_072):
assert result["ingest"] is False, f"Expected FAIL, got ingest={result['ingest']}"
assert "memorization" in result["reason"], f"Expected memorization in reason, got {result['reason']}"
assert "instability" in result["reason"], f"Expected instability in reason, got {result['reason']}"

m = result["metrics"]
assert abs(m["avg_perturbation_stability"] - 0.7643) < 0.01, f"stability mismatch: {m['avg_perturbation_stability']}"
assert abs(m["perturbation_stability"]["max_drop"] - 0.5714) < 0.01, f"max_drop mismatch: {m['perturbation_stability']['max_drop']}"

print("PASS: LC322 baseline matches FINDINGS_072")
print()

# ── Part 2: Bidirectional comparator tests ──────────────────────────────

print("=== Part 2: Bidirectional comparator tests ===")

# multiset_of_multisets
assert multiset_of_multisets([[1,2,3],[1,2,4]], [[1,2,4],[1,2,3]]) is True, "equal case failed"
assert multiset_of_multisets([[1,2,3]], [[1,2,4]]) is False, "not-equal case failed"
assert multiset_of_multisets([[1,1,2]], [[1,2,1]]) is True, "inner-order-invariant case failed"
print("  multiset_of_multisets: all 3 cases PASS")

# exact_scalar
assert exact_scalar(1, 1) is True, "exact_scalar equal"
assert exact_scalar(1, 2) is False, "exact_scalar not-equal"
assert exact_scalar("a", "a") is True, "exact_scalar str equal"
print("  exact_scalar: all 3 cases PASS")

# boolean_exact
assert boolean_exact(True, True) is True, "boolean_exact True==True"
assert boolean_exact(False, False) is True, "boolean_exact False==False"
assert boolean_exact(True, False) is False, "boolean_exact True!=False"
assert boolean_exact(True, 1) is False, "boolean_exact type guard (True != 1)"
assert boolean_exact(False, 0) is False, "boolean_exact type guard (False != 0)"
print("  boolean_exact: all 5 cases PASS")

# multiset_of_scalars
assert multiset_of_scalars([1, 2, 3], [3, 2, 1]) is True, "multiset_of_scalars equal"
assert multiset_of_scalars([1, 2, 3], [1, 2, 4]) is False, "multiset_of_scalars not-equal"
assert multiset_of_scalars([], []) is True, "multiset_of_scalars both empty"
print("  multiset_of_scalars: all 3 cases PASS")

# ── Part 3: GateTypeError for type mismatch ────────────────────────────

print()
print("=== Part 3: Gate type-guard (C1) ===")
from doctor.adversarial.ingestion_gate import GateTypeError

try:
    lc322_ingestion_gate(
        problem={},
        solvers=[lc322_dp],
        oracle=lambda coins, amount: True,  # bool oracle
        reference_tests=[{"coins": [1], "amount": 5}],
    )
    print("FAIL: expected GateTypeError but gate passed")
    sys.exit(1)
except GateTypeError as e:
    print(f"PASS: GateTypeError raised: {e}")

print()
print("=== ALL TESTS PASS ===")
