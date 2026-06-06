# tests/test_identity_resolution.py
# Phase C-3a: Per-Solver Identity Resolution — test suite
# TDD: tests written before runners.

import pytest
from doctor.identity_resolution import (
    misclassified_set,
    compute_D,
    compute_A,
    apply_three_case_rule,
    check_aggregate_consistency,
)

LAMBDA_SWEEP = [1, 2, 5, 7, 10, 15, 20, 30, 50]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# 4 solvers: 2 ACCEPT, 2 REJECT
GT_4      = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]

# Identical decisions — no errors
DEC_PERFECT = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]

# C wrong on solver 0 (false reject), B1 correct
DEC_C_WRONG_0  = ["REJECT", "ACCEPT", "REJECT", "REJECT"]
DEC_B1_CORRECT = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]

# C wrong on solver 0, B1 wrong on solver 1 — symmetric swap
DEC_C_WRONG_0_ONLY  = ["REJECT", "ACCEPT", "REJECT", "REJECT"]
DEC_B1_WRONG_1_ONLY = ["ACCEPT", "REJECT", "REJECT", "REJECT"]

# Both wrong on same solver (0)
DEC_BOTH_WRONG_0 = ["REJECT", "ACCEPT", "REJECT", "REJECT"]

# LC322-shaped: 11 ACCEPT, 19 REJECT
GT_LC322 = ["ACCEPT"] * 11 + ["REJECT"] * 19

# LC45-shaped: 1 ACCEPT, 9 REJECT
GT_LC45 = ["ACCEPT"] * 1 + ["REJECT"] * 9


# ---------------------------------------------------------------------------
# 1. misclassified_set
# ---------------------------------------------------------------------------

class TestMisclassifiedSet:

    def test_perfect_decisions_empty_set(self):
        assert misclassified_set(DEC_PERFECT, GT_4) == set()

    def test_one_false_reject(self):
        result = misclassified_set(DEC_C_WRONG_0, GT_4)
        assert result == {0}

    def test_all_wrong(self):
        decisions = ["REJECT", "REJECT", "ACCEPT", "ACCEPT"]
        result = misclassified_set(decisions, GT_4)
        assert result == {0, 1, 2, 3}

    def test_empty_decisions_raises(self):
        with pytest.raises(ValueError):
            misclassified_set([], [])

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            misclassified_set(["ACCEPT"], ["ACCEPT", "REJECT"])

    def test_invalid_decision_raises(self):
        with pytest.raises(ValueError):
            misclassified_set(["MAYBE"], ["ACCEPT"])

    def test_invalid_ground_truth_raises(self):
        with pytest.raises(ValueError):
            misclassified_set(["ACCEPT"], ["UNKNOWN"])


# ---------------------------------------------------------------------------
# 2. compute_D
# ---------------------------------------------------------------------------

class TestComputeD:

    def test_identical_decisions_D_zero(self):
        assert compute_D(DEC_PERFECT, DEC_PERFECT, GT_4) == 0

    def test_both_perfect_D_zero(self):
        assert compute_D(DEC_PERFECT, DEC_PERFECT, GT_4) == 0

    def test_C_wrong_B1_correct_D_one(self):
        # M_C = {0}, M_B1 = {} → symmetric diff = {0} → D = 1
        assert compute_D(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4) == 1

    def test_symmetric_swap_D_two(self):
        # M_C = {0}, M_B1 = {1} → symmetric diff = {0,1} → D = 2
        assert compute_D(DEC_C_WRONG_0_ONLY, DEC_B1_WRONG_1_ONLY, GT_4) == 2

    def test_both_wrong_same_solver_D_zero(self):
        # M_C = {0}, M_B1 = {0} → symmetric diff = {} → D = 0
        assert compute_D(DEC_BOTH_WRONG_0, DEC_BOTH_WRONG_0, GT_4) == 0

    def test_D_is_integer(self):
        result = compute_D(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4)
        assert isinstance(result, int)

    def test_lc322_shaped_identical_D_zero(self):
        decisions = ["ACCEPT"] * 11 + ["REJECT"] * 19
        assert compute_D(decisions, decisions, GT_LC322) == 0

    def test_lc45_shaped_single_survivor(self):
        # C wrong on solver 0 (the one ACCEPT), B1 correct
        dec_c  = ["REJECT"] + ["REJECT"] * 9
        dec_b1 = ["ACCEPT"] + ["REJECT"] * 9
        assert compute_D(dec_c, dec_b1, GT_LC45) == 1


# ---------------------------------------------------------------------------
# 3. compute_A
# ---------------------------------------------------------------------------

class TestComputeA:

    def test_identical_decisions_A_zero(self):
        assert compute_A(DEC_PERFECT, DEC_PERFECT, GT_4, LAMBDA_SWEEP) == 0

    def test_empty_lambda_sweep_A_zero(self):
        assert compute_A(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4, []) == 0

    def test_C_wrong_B1_correct_A_nonzero(self):
        # solver 0: C=REJECT (false reject, cost=λ_R), B1=ACCEPT (correct, cost=0)
        # max diff = max(λ_R) = 50 at λ=50
        result = compute_A(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4, LAMBDA_SWEEP)
        assert result == 50

    def test_symmetric_swap_A_nonzero(self):
        # solver 0: C wrong (false reject, cost=λ_R), B1 correct (cost=0) → diff = λ_R
        # solver 1: C correct (cost=0), B1 wrong (false reject, cost=λ_R) → diff = λ_R
        # max diff = 50
        result = compute_A(DEC_C_WRONG_0_ONLY, DEC_B1_WRONG_1_ONLY, GT_4, LAMBDA_SWEEP)
        assert result == 50

    def test_both_wrong_same_solver_A_zero(self):
        # both make same error on solver 0 → cost_C = cost_B1 at every λ → diff = 0
        result = compute_A(DEC_BOTH_WRONG_0, DEC_BOTH_WRONG_0, GT_4, LAMBDA_SWEEP)
        assert result == 0

    def test_A_is_integer(self):
        result = compute_A(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4, LAMBDA_SWEEP)
        assert isinstance(result, int)

    def test_lambda_1_only_A_one(self):
        # At λ=1: false reject costs 1, correct costs 0 → diff = 1
        result = compute_A(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4, [1])
        assert result == 1

    def test_lambda_10_only_A_ten(self):
        result = compute_A(DEC_C_WRONG_0, DEC_B1_CORRECT, GT_4, [10])
        assert result == 10


# ---------------------------------------------------------------------------
# 4. apply_three_case_rule
# ---------------------------------------------------------------------------

class TestApplyThreeCaseRule:

    def test_D_zero_full_equivalence(self):
        assert apply_three_case_rule(0, 0) == "FULL_EQUIVALENCE"

    def test_D_zero_A_nonzero_still_full_equivalence(self):
        # D=0 takes priority: same misclassified set means same per-solver costs
        # A>0 with D=0 is logically impossible, but rule is D-first
        assert apply_three_case_rule(0, 5) == "FULL_EQUIVALENCE"

    def test_D_nonzero_A_zero_masked_divergence(self):
        assert apply_three_case_rule(2, 0) == "MASKED_DIVERGENCE"

    def test_D_nonzero_A_nonzero_directional_superiority(self):
        assert apply_three_case_rule(1, 50) == "DIRECTIONAL_SUPERIORITY"

    def test_large_D_large_A_directional_superiority(self):
        assert apply_three_case_rule(30, 50) == "DIRECTIONAL_SUPERIORITY"

    def test_negative_D_raises(self):
        with pytest.raises(ValueError):
            apply_three_case_rule(-1, 0)

    def test_negative_A_raises(self):
        with pytest.raises(ValueError):
            apply_three_case_rule(0, -1)


# ---------------------------------------------------------------------------
# 5. check_aggregate_consistency
# ---------------------------------------------------------------------------

class TestCheckAggregateConsistency:

    def test_consistent_passes(self):
        # solver 0: false reject (WR=1), rest correct
        decisions = ["REJECT", "ACCEPT", "REJECT", "REJECT"]
        # WA=0, WR=1
        check_aggregate_consistency(
            decisions, GT_4,
            expected_wrong_accepts=0,
            expected_wrong_rejects=1,
            estimator_name="B1_count",
            population_id="LC322",
        )

    def test_inconsistent_WA_raises(self):
        decisions = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]  # perfect, WA=0, WR=0
        with pytest.raises(ValueError, match="Aggregate consistency check FAILED"):
            check_aggregate_consistency(
                decisions, GT_4,
                expected_wrong_accepts=1,
                expected_wrong_rejects=0,
                estimator_name="C_structured_fingerprint",
                population_id="LC322",
            )

    def test_inconsistent_WR_raises(self):
        decisions = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]  # perfect
        with pytest.raises(ValueError, match="Aggregate consistency check FAILED"):
            check_aggregate_consistency(
                decisions, GT_4,
                expected_wrong_accepts=0,
                expected_wrong_rejects=1,
                estimator_name="B1_count",
                population_id="LC322",
            )

    def test_error_message_contains_estimator_name(self):
        decisions = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]
        with pytest.raises(ValueError, match="B1_count"):
            check_aggregate_consistency(
                decisions, GT_4,
                expected_wrong_accepts=1,
                expected_wrong_rejects=0,
                estimator_name="B1_count",
                population_id="LC322",
            )

    def test_error_message_contains_population_id(self):
        decisions = ["ACCEPT", "ACCEPT", "REJECT", "REJECT"]
        with pytest.raises(ValueError, match="LC322"):
            check_aggregate_consistency(
                decisions, GT_4,
                expected_wrong_accepts=1,
                expected_wrong_rejects=0,
                estimator_name="B1_count",
                population_id="LC322",
            )

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            check_aggregate_consistency(
                ["ACCEPT"], GT_4,
                expected_wrong_accepts=0,
                expected_wrong_rejects=0,
                estimator_name="B1_count",
                population_id="LC322",
            )

    def test_perfect_decisions_zero_zero_passes(self):
        check_aggregate_consistency(
            DEC_PERFECT, GT_4,
            expected_wrong_accepts=0,
            expected_wrong_rejects=0,
            estimator_name="B0_prior",
            population_id="LC45",
        )
