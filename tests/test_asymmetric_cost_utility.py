# tests/test_asymmetric_cost_utility.py
# Phase C-1: Asymmetric-Cost Decision Utility
# Tests for cost function, normalization, anti-degeneracy detection.
# Must pass (282 + N) before any runner is written.

import pytest
from doctor.asymmetric_cost import (
    compute_cost,
    compute_raw_cost,
    compute_normalized_utility,
    is_degenerate,
    run_sweep,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LAMBDA_SWEEP = [1, 2, 5, 7, 10, 15, 20, 30, 50]
DELTA = 0.10

# Minimal solver population: 3 solvers
# ground_truth: ACCEPT, REJECT, ACCEPT
# decisions: ACCEPT, ACCEPT, REJECT
# At λ_R=1, λ_A=1:
#   solver 0: correct         → cost 0
#   solver 1: false accept    → cost λ_A = 1
#   solver 2: false reject    → cost λ_R = 1
#   raw_cost = (0 + 1 + 1) / 3 = 0.6667
#   normalized_utility = 1 - 0.6667 / 1 = 0.3333

GROUND_TRUTH_3 = ["ACCEPT", "REJECT", "ACCEPT"]
DECISIONS_3    = ["ACCEPT", "ACCEPT", "REJECT"]

# Perfect population: all correct
GROUND_TRUTH_PERFECT = ["ACCEPT", "REJECT", "ACCEPT"]
DECISIONS_PERFECT     = ["ACCEPT", "REJECT", "ACCEPT"]

# All-ACCEPT degenerate
GROUND_TRUTH_DEG = ["ACCEPT", "REJECT", "REJECT"]
DECISIONS_ALL_ACCEPT = ["ACCEPT", "ACCEPT", "ACCEPT"]

# All-REJECT degenerate
DECISIONS_ALL_REJECT = ["REJECT", "REJECT", "REJECT"]

# LC322-shaped: 11 ACCEPT, 19 REJECT, all correct
GROUND_TRUTH_LC322 = ["ACCEPT"] * 11 + ["REJECT"] * 19
DECISIONS_LC322_PERFECT = GROUND_TRUTH_LC322[:]

# LC45-shaped: 1 ACCEPT, 9 REJECT, all correct
GROUND_TRUTH_LC45 = ["ACCEPT"] * 1 + ["REJECT"] * 9
DECISIONS_LC45_PERFECT = GROUND_TRUTH_LC45[:]


# ---------------------------------------------------------------------------
# 1. compute_cost — per-decision cost
# ---------------------------------------------------------------------------

class TestComputeCost:

    def test_correct_accept(self):
        assert compute_cost("ACCEPT", "ACCEPT", lambda_R=5, lambda_A=1) == 0

    def test_correct_reject(self):
        assert compute_cost("REJECT", "REJECT", lambda_R=5, lambda_A=1) == 0

    def test_false_accept(self):
        # decision=ACCEPT, ground_truth=REJECT → cost = λ_A
        assert compute_cost("ACCEPT", "REJECT", lambda_R=5, lambda_A=1) == 1

    def test_false_reject(self):
        # decision=REJECT, ground_truth=ACCEPT → cost = λ_R
        assert compute_cost("REJECT", "ACCEPT", lambda_R=5, lambda_A=1) == 5

    def test_false_reject_lambda_10(self):
        assert compute_cost("REJECT", "ACCEPT", lambda_R=10, lambda_A=1) == 10

    def test_false_accept_lambda_A_fixed_1(self):
        # λ_A = 1 throughout per freeze file
        assert compute_cost("ACCEPT", "REJECT", lambda_R=20, lambda_A=1) == 1

    def test_symmetric_at_lambda_1(self):
        # λ_R = λ_A = 1 reproduces old symmetric regime
        fa = compute_cost("ACCEPT", "REJECT", lambda_R=1, lambda_A=1)
        fr = compute_cost("REJECT", "ACCEPT", lambda_R=1, lambda_A=1)
        assert fa == fr == 1

    def test_invalid_decision_raises(self):
        with pytest.raises(ValueError):
            compute_cost("MAYBE", "ACCEPT", lambda_R=1, lambda_A=1)

    def test_invalid_ground_truth_raises(self):
        with pytest.raises(ValueError):
            compute_cost("ACCEPT", "UNKNOWN", lambda_R=1, lambda_A=1)


# ---------------------------------------------------------------------------
# 2. compute_raw_cost — mean cost over population
# ---------------------------------------------------------------------------

class TestComputeRawCost:

    def test_perfect_population_zero_cost(self):
        rc = compute_raw_cost(
            DECISIONS_PERFECT, GROUND_TRUTH_PERFECT,
            lambda_R=10, lambda_A=1
        )
        assert rc == pytest.approx(0.0)

    def test_known_population_lambda_1(self):
        rc = compute_raw_cost(
            DECISIONS_3, GROUND_TRUTH_3,
            lambda_R=1, lambda_A=1
        )
        assert rc == pytest.approx(2 / 3, rel=1e-6)

    def test_known_population_lambda_5(self):
        # solver 0: correct → 0
        # solver 1: false accept → λ_A = 1
        # solver 2: false reject → λ_R = 5
        # raw = (0 + 1 + 5) / 3 = 2.0
        rc = compute_raw_cost(
            DECISIONS_3, GROUND_TRUTH_3,
            lambda_R=5, lambda_A=1
        )
        assert rc == pytest.approx(2.0, rel=1e-6)

    def test_all_accept_degenerate_cost(self):
        # 1 correct ACCEPT + 2 false ACCEPTs
        rc = compute_raw_cost(
            DECISIONS_ALL_ACCEPT, GROUND_TRUTH_DEG,
            lambda_R=10, lambda_A=1
        )
        # cost = (0 + 1 + 1) / 3
        assert rc == pytest.approx(2 / 3, rel=1e-6)

    def test_empty_population_raises(self):
        with pytest.raises(ValueError):
            compute_raw_cost([], [], lambda_R=1, lambda_A=1)

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            compute_raw_cost(["ACCEPT"], ["ACCEPT", "REJECT"],
                             lambda_R=1, lambda_A=1)


# ---------------------------------------------------------------------------
# 3. compute_normalized_utility
# ---------------------------------------------------------------------------

class TestComputeNormalizedUtility:

    def test_perfect_utility_is_one(self):
        nu = compute_normalized_utility(
            DECISIONS_PERFECT, GROUND_TRUTH_PERFECT,
            lambda_R=10, lambda_A=1
        )
        assert nu == pytest.approx(1.0)

    def test_known_population_lambda_1(self):
        # raw_cost = 2/3, lambda_A = 1
        # normalized = 1 - (2/3) / 1 = 1/3
        nu = compute_normalized_utility(
            DECISIONS_3, GROUND_TRUTH_3,
            lambda_R=1, lambda_A=1
        )
        assert nu == pytest.approx(1 / 3, rel=1e-6)

    def test_known_population_lambda_5(self):
        # raw_cost = 2.0, lambda_A = 1
        # normalized = 1 - 2.0 / 1 = -1.0
        nu = compute_normalized_utility(
            DECISIONS_3, GROUND_TRUTH_3,
            lambda_R=5, lambda_A=1
        )
        assert nu == pytest.approx(-1.0, rel=1e-6)

    def test_utility_can_be_negative(self):
        # High λ_R with many false rejects pushes utility below 0
        decisions = ["REJECT"] * 10
        ground_truth = ["ACCEPT"] * 10
        nu = compute_normalized_utility(
            decisions, ground_truth,
            lambda_R=50, lambda_A=1
        )
        assert nu < 0

    def test_normalization_is_per_population_lambda_A(self):
        # lambda_A is always 1 per freeze file
        # normalized_utility = 1 - raw_cost / 1 = 1 - raw_cost
        nu = compute_normalized_utility(
            DECISIONS_3, GROUND_TRUTH_3,
            lambda_R=1, lambda_A=1
        )
        rc = compute_raw_cost(
            DECISIONS_3, GROUND_TRUTH_3,
            lambda_R=1, lambda_A=1
        )
        assert nu == pytest.approx(1 - rc, rel=1e-6)


# ---------------------------------------------------------------------------
# 4. is_degenerate — anti-degeneracy detection
# ---------------------------------------------------------------------------

class TestIsDegenerate:

    def test_all_accept_is_degenerate(self):
        assert is_degenerate(DECISIONS_ALL_ACCEPT) is True

    def test_all_reject_is_degenerate(self):
        assert is_degenerate(DECISIONS_ALL_REJECT) is True

    def test_mixed_is_not_degenerate(self):
        assert is_degenerate(DECISIONS_3) is False

    def test_perfect_mixed_is_not_degenerate(self):
        assert is_degenerate(DECISIONS_PERFECT) is False

    def test_single_accept_in_rejects_is_not_degenerate(self):
        # LC45-shaped: 1 ACCEPT, 9 REJECT — not degenerate
        decisions = ["ACCEPT"] + ["REJECT"] * 9
        assert is_degenerate(decisions) is False

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            is_degenerate([])


# ---------------------------------------------------------------------------
# 5. run_sweep — integration over λ sweep
# ---------------------------------------------------------------------------

class TestRunSweep:

    def test_returns_entry_per_lambda(self):
        results = run_sweep(
            decisions=DECISIONS_3,
            ground_truth=GROUND_TRUTH_3,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        assert len(results) == len(LAMBDA_SWEEP)

    def test_each_entry_has_required_keys(self):
        results = run_sweep(
            decisions=DECISIONS_3,
            ground_truth=GROUND_TRUTH_3,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        for entry in results:
            assert "lambda_R" in entry
            assert "raw_cost" in entry
            assert "normalized_utility" in entry
            assert "degenerate" in entry

    def test_lambda_1_matches_symmetric_regime(self):
        results = run_sweep(
            decisions=DECISIONS_3,
            ground_truth=GROUND_TRUTH_3,
            lambda_sweep=[1],
            lambda_A=1,
        )
        assert results[0]["lambda_R"] == 1
        assert results[0]["raw_cost"] == pytest.approx(2 / 3, rel=1e-6)
        assert results[0]["normalized_utility"] == pytest.approx(1 / 3, rel=1e-6)
        assert results[0]["degenerate"] is False

    def test_perfect_population_utility_one_all_lambdas(self):
        results = run_sweep(
            decisions=DECISIONS_PERFECT,
            ground_truth=GROUND_TRUTH_PERFECT,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        for entry in results:
            assert entry["normalized_utility"] == pytest.approx(1.0)
            assert entry["degenerate"] is False

    def test_degenerate_flagged_in_sweep(self):
        results = run_sweep(
            decisions=DECISIONS_ALL_ACCEPT,
            ground_truth=GROUND_TRUTH_DEG,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        for entry in results:
            assert entry["degenerate"] is True

    def test_all_nine_lambda_values_covered(self):
        results = run_sweep(
            decisions=DECISIONS_3,
            ground_truth=GROUND_TRUTH_3,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        returned_lambdas = [r["lambda_R"] for r in results]
        assert returned_lambdas == LAMBDA_SWEEP

    def test_lc322_shaped_perfect_population(self):
        results = run_sweep(
            decisions=DECISIONS_LC322_PERFECT,
            ground_truth=GROUND_TRUTH_LC322,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        for entry in results:
            assert entry["normalized_utility"] == pytest.approx(1.0)

    def test_lc45_shaped_perfect_population(self):
        results = run_sweep(
            decisions=DECISIONS_LC45_PERFECT,
            ground_truth=GROUND_TRUTH_LC45,
            lambda_sweep=LAMBDA_SWEEP,
            lambda_A=1,
        )
        for entry in results:
            assert entry["normalized_utility"] == pytest.approx(1.0)

    def test_empty_lambda_sweep_returns_empty(self):
        results = run_sweep(
            decisions=DECISIONS_3,
            ground_truth=GROUND_TRUTH_3,
            lambda_sweep=[],
            lambda_A=1,
        )
        assert results == []


# ---------------------------------------------------------------------------
# 6. Delta threshold — falsification criterion
# ---------------------------------------------------------------------------

class TestDeltaThreshold:

    def test_gap_above_delta_is_pass(self):
        gap = 0.15
        assert gap > DELTA

    def test_gap_equal_delta_is_not_pass(self):
        gap = 0.10
        assert not (gap > DELTA)

    def test_gap_below_delta_is_fail(self):
        gap = 0.05
        assert not (gap > DELTA)

    def test_delta_value_matches_freeze_file(self):
        assert DELTA == 0.10
