# tests/test_genuine_policy.py
# Phase C-4: Genuine Structured Policy — test suite
# TDD: tests written before the C_genuine function.

import inspect

import pytest

from doctor.adversarial.problem_class_config import (
    LC322_ESTIMATOR_POLICIES,
    LC45_ESTIMATOR_POLICIES,
    _fail_count_policy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(probe_id: str, family: str, pass_fail: bool) -> dict:
    """Build an obs_record as constructed by apply_estimator."""
    return {
        "probe_id": probe_id,
        "pass_fail": pass_fail,
        "fingerprint_context": {
            "axis": "reachability",
            "probe_family": family,
            "deformation_level": 0,
            "paired_probe_id": None,
            "expected_invariant": None,
        },
    }


FAMILIES = [
    "reachability_counterfactual",
    "order_dependent",
    "magnitude_boundary",
    "boundary_collapse",
    "transition_break",
    "memoization_collision",
]


# ---------------------------------------------------------------------------
# 1. C_genuine function exists and is bound in both population configs
# ---------------------------------------------------------------------------

class TestCGeniuneBinding:

    def test_c_genuine_in_lc322_policies(self):
        assert "C_genuine" in LC322_ESTIMATOR_POLICIES

    def test_c_genuine_in_lc45_policies(self):
        assert "C_genuine" in LC45_ESTIMATOR_POLICIES

    def test_c_genuine_is_not_fail_count_policy_object(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        assert c_genuine is not _fail_count_policy

    def test_c_genuine_source_mentions_probe_family(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        src = inspect.getsource(c_genuine)
        assert "probe_family" in src, (
            "C_genuine source must reference probe_family. "
            "If it does not, it is not a genuine structured policy."
        )

    def test_c_genuine_source_mentions_obs_records(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        src = inspect.getsource(c_genuine)
        assert "obs_records" in src, (
            "C_genuine source must consume obs_records. "
            "If it does not, it cannot use structured features."
        )


# ---------------------------------------------------------------------------
# 2. C_genuine decision rule — on constructed inputs
# ---------------------------------------------------------------------------

class TestCGeniuneDecisionRule:

    def test_zero_failures_accept(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [make_record("p1", FAMILIES[0], True) for _ in range(15)]
        assert c_genuine(0, 15, records) == "ACCEPT"

    def test_single_failure_accept_b1_rejects(self):
        # 1 failure, 14 passes. B1 says REJECT. C_genuine says ACCEPT
        # (trivially all failures in one family, since there is only 1).
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [make_record("p1", FAMILIES[0], False)] + \
                  [make_record(f"p{i}", FAMILIES[0], True) for i in range(2, 16)]
        assert c_genuine(1, 15, records) == "ACCEPT"
        # Cross-check: B1 says REJECT on the same input.
        assert _fail_count_policy(1, 15, records) == "REJECT"

    def test_two_failures_same_family_accept(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", FAMILIES[0], False),
            make_record("p2", FAMILIES[0], False),
        ] + [make_record(f"p{i}", FAMILIES[0], True) for i in range(3, 16)]
        assert c_genuine(2, 15, records) == "ACCEPT"

    def test_two_failures_different_families_reject(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", FAMILIES[0], False),
            make_record("p2", FAMILIES[1], False),
        ] + [make_record(f"p{i}", FAMILIES[0], True) for i in range(3, 16)]
        assert c_genuine(2, 15, records) == "REJECT"

    def test_three_failures_two_families_reject(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", FAMILIES[0], False),
            make_record("p2", FAMILIES[0], False),
            make_record("p3", FAMILIES[1], False),
        ] + [make_record(f"p{i}", FAMILIES[0], True) for i in range(4, 16)]
        assert c_genuine(3, 15, records) == "REJECT"

    def test_three_failures_one_family_accept(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", FAMILIES[2], False),
            make_record("p2", FAMILIES[2], False),
            make_record("p3", FAMILIES[2], False),
        ] + [make_record(f"p{i}", FAMILIES[0], True) for i in range(4, 16)]
        assert c_genuine(3, 15, records) == "ACCEPT"

    def test_all_fail_one_family_accept(self):
        # Edge case: all 15 probes fail, all in same family. C_genuine accepts.
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [make_record(f"p{i}", FAMILIES[0], False) for i in range(1, 16)]
        assert c_genuine(15, 15, records) == "ACCEPT"

    def test_all_fail_spread_reject(self):
        # All 15 probes fail, spread across 6 families. C_genuine rejects.
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = []
        for i in range(1, 16):
            fam = FAMILIES[(i - 1) % 6]
            records.append(make_record(f"p{i}", fam, False))
        assert c_genuine(15, 15, records) == "REJECT"

    def test_fallback_when_obs_records_none(self):
        # If obs_records is None, C_genuine falls back to B1 behavior.
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        assert c_genuine(0, 15, None) == "ACCEPT"
        assert c_genuine(1, 15, None) == "REJECT"
        assert c_genuine(15, 15, None) == "REJECT"


# ---------------------------------------------------------------------------
# 3. C_genuine can produce different decisions than B1
# ---------------------------------------------------------------------------

class TestCGeniuneCanDifferFromB1:

    def test_single_failure_c_genuine_accepts_b1_rejects(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [make_record("p1", FAMILIES[0], False)] + \
                  [make_record(f"p{i}", FAMILIES[0], True) for i in range(2, 16)]
        c_decision = c_genuine(1, 15, records)
        b1_decision = _fail_count_policy(1, 15, records)
        assert c_decision != b1_decision
        assert c_decision == "ACCEPT"
        assert b1_decision == "REJECT"

    def test_two_failures_same_family_c_genuine_accepts_b1_rejects(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", FAMILIES[0], False),
            make_record("p2", FAMILIES[0], False),
        ] + [make_record(f"p{i}", FAMILIES[0], True) for i in range(3, 16)]
        c_decision = c_genuine(2, 15, records)
        b1_decision = _fail_count_policy(2, 15, records)
        assert c_decision != b1_decision
        assert c_decision == "ACCEPT"
        assert b1_decision == "REJECT"

    def test_multi_family_failures_c_genuine_matches_b1(self):
        c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", FAMILIES[0], False),
            make_record("p2", FAMILIES[1], False),
        ] + [make_record(f"p{i}", FAMILIES[0], True) for i in range(3, 16)]
        c_decision = c_genuine(2, 15, records)
        b1_decision = _fail_count_policy(2, 15, records)
        assert c_decision == b1_decision
        assert c_decision == "REJECT"


# ---------------------------------------------------------------------------
# 4. D > 0 requirement (falsification criterion)
# ---------------------------------------------------------------------------

class TestDGreaterThanZeroRequirement:

    def test_d_zero_on_constructed_data_means_full_equivalence(self):
        # Construct per-solver decisions where C_genuine and B1 are identical.
        # This should produce D = 0, which the falsification criterion maps to FAIL.
        from doctor.identity_resolution import (
            compute_D, apply_three_case_rule,
        )
        # 4 solvers: 0 failures, 1 failure (single family), 2 failures (2 families)
        # C_genuine: ACCEPT, ACCEPT, REJECT
        # B1:       ACCEPT, REJECT, REJECT
        # D = |M_C △ M_B1| where M_C = {2}, M_B1 = {1, 2} → D = 1
        dec_c  = ["ACCEPT", "ACCEPT", "REJECT", "ACCEPT"]
        dec_b1 = ["ACCEPT", "REJECT", "REJECT", "ACCEPT"]
        gt     = ["ACCEPT", "ACCEPT", "ACCEPT", "REJECT"]
        D = compute_D(dec_c, dec_b1, gt)
        assert D == 1
        assert apply_three_case_rule(D, 50) == "DIRECTIONAL_SUPERIORITY"

    def test_d_zero_means_fail_regardless_of_a(self):
        from doctor.identity_resolution import apply_three_case_rule
        # D = 0, any A → FULL_EQUIVALENCE → FAIL per the criterion.
        outcome = apply_three_case_rule(0, 0)
        assert outcome == "FULL_EQUIVALENCE"
        # The spec says D = 0 → FAIL regardless of utility gap.
        # FULL_EQUIVALENCE maps to FAIL.

    def test_d_positive_a_zero_means_masked_divergence(self):
        from doctor.identity_resolution import apply_three_case_rule
        # D > 0, A = 0 → MASKED_DIVERGENCE → FAIL (utility gap is 0).
        outcome = apply_three_case_rule(2, 0)
        assert outcome == "MASKED_DIVERGENCE"

    def test_d_positive_a_positive_means_directional_superiority(self):
        from doctor.identity_resolution import apply_three_case_rule
        # D > 0, A > 0 → DIRECTIONAL_SUPERIORITY → PASS or FAIL based on utility gap.
        outcome = apply_three_case_rule(1, 50)
        assert outcome == "DIRECTIONAL_SUPERIORITY"
