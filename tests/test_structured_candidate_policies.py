# tests/test_structured_candidate_policies.py
# Phase C-6: Representation Class Falsification — test suite
# TDD: tests written before the 3 new policy functions (C_feature_threshold,
# C_majority, C_zero_only). C_genuine is the existing baseline from C-4.

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

def make_record(
    probe_id: str,
    family: str,
    pass_fail: bool,
    deformation_level: int = 0,
) -> dict:
    """Build an obs_record as constructed by apply_estimator."""
    return {
        "probe_id": probe_id,
        "pass_fail": pass_fail,
        "fingerprint_context": {
            "axis": "reachability",
            "probe_family": family,
            "deformation_level": deformation_level,
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
# 1. C_feature_threshold (Rule 2) — binding
# ---------------------------------------------------------------------------

class TestCFeatureThresholdBinding:

    def test_in_lc322_policies(self):
        assert "C_feature_threshold" in LC322_ESTIMATOR_POLICIES

    def test_in_lc45_policies(self):
        assert "C_feature_threshold" in LC45_ESTIMATOR_POLICIES

    def test_is_not_fail_count_policy(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        assert c_ft is not _fail_count_policy

    def test_source_mentions_deformation_level(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        src = inspect.getsource(c_ft)
        assert "deformation_level" in src


# ---------------------------------------------------------------------------
# 2. C_feature_threshold (Rule 2) — decision rule
# ---------------------------------------------------------------------------

class TestCFeatureThresholdRule:

    def test_accept_zero_failures(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [make_record(f"p{i}", FAMILIES[i % 6], True, deformation_level=2) for i in range(10)]
        assert c_ft(0, 10, records) == "ACCEPT"

    def test_accept_failure_rate_below_threshold(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [
            make_record("p1", "reachability_counterfactual", False, deformation_level=2),
            make_record("p2", "reachability_counterfactual", True, deformation_level=2),
            make_record("p3", "reachability_counterfactual", True, deformation_level=2),
            make_record("p4", "reachability_counterfactual", True, deformation_level=2),
        ]
        assert c_ft(1, 4, records) == "ACCEPT"

    def test_reject_failure_rate_above_threshold(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [
            make_record("p1", "reachability_counterfactual", False, deformation_level=2),
            make_record("p2", "reachability_counterfactual", False, deformation_level=2),
            make_record("p3", "reachability_counterfactual", False, deformation_level=2),
            make_record("p4", "reachability_counterfactual", True, deformation_level=2),
        ]
        assert c_ft(3, 4, records) == "REJECT"

    def test_reject_failure_rate_at_threshold(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [
            make_record("p1", "reachability_counterfactual", False, deformation_level=2),
            make_record("p2", "reachability_counterfactual", False, deformation_level=2),
            make_record("p3", "reachability_counterfactual", True, deformation_level=2),
            make_record("p4", "reachability_counterfactual", True, deformation_level=2),
        ]
        assert c_ft(2, 4, records) == "REJECT"

    def test_fallback_when_no_deformed_probes_with_failures(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [
            make_record("p1", "reachability_counterfactual", False, deformation_level=0),
            make_record("p2", "reachability_counterfactual", True, deformation_level=0),
        ]
        assert c_ft(1, 2, records) == "REJECT"

    def test_fallback_when_obs_records_none(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        assert c_ft(0, 10, None) == "ACCEPT"
        assert c_ft(1, 10, None) == "REJECT"

    def test_only_deformed_probes_count_for_rate(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [
            make_record("p1", "reachability_counterfactual", False, deformation_level=0),
            make_record("p2", "reachability_counterfactual", False, deformation_level=0),
            make_record("p3", "reachability_counterfactual", True, deformation_level=2),
            make_record("p4", "reachability_counterfactual", True, deformation_level=2),
        ]
        assert c_ft(2, 4, records) == "ACCEPT"

    def test_can_differ_from_b1(self):
        c_ft = LC322_ESTIMATOR_POLICIES["C_feature_threshold"]
        records = [
            make_record("p1", "reachability_counterfactual", False, deformation_level=2),
            make_record("p2", "reachability_counterfactual", True, deformation_level=2),
            make_record("p3", "reachability_counterfactual", True, deformation_level=2),
            make_record("p4", "reachability_counterfactual", True, deformation_level=2),
        ]
        assert _fail_count_policy(1, 4, records) == "REJECT"
        assert c_ft(1, 4, records) == "ACCEPT"


# ---------------------------------------------------------------------------
# 3. C_majority (Rule 3) — binding
# ---------------------------------------------------------------------------

class TestCMajorityBinding:

    def test_in_lc322_policies(self):
        assert "C_majority" in LC322_ESTIMATOR_POLICIES

    def test_in_lc45_policies(self):
        assert "C_majority" in LC45_ESTIMATOR_POLICIES

    def test_is_not_fail_count_policy(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        assert c_maj is not _fail_count_policy

    def test_is_not_c_genuine(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        c_gen = LC322_ESTIMATOR_POLICIES["C_genuine"]
        assert c_maj is not c_gen


# ---------------------------------------------------------------------------
# 4. C_majority (Rule 3) — decision rule
# ---------------------------------------------------------------------------

class TestCMajorityRule:

    def test_accept_zero_failures(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        records = [make_record(f"p{i}", FAMILIES[i % 6], True) for i in range(10)]
        assert c_maj(0, 10, records) == "ACCEPT"

    def test_accept_unique_mode(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        records = [
            make_record("p1", "reachability_counterfactual", False),
            make_record("p2", "reachability_counterfactual", False),
            make_record("p3", "reachability_counterfactual", False),
            make_record("p4", "order_dependent", False),
            make_record("p5", "order_dependent", False),
            make_record("p6", "magnitude_boundary", False),
        ]
        assert c_maj(6, 6, records) == "ACCEPT"

    def test_accept_unanimous(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        records = [make_record(f"p{i}", "reachability_counterfactual", False) for i in range(5)]
        assert c_maj(5, 5, records) == "ACCEPT"

    def test_reject_two_way_tie(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        records = [
            make_record("p1", "reachability_counterfactual", False),
            make_record("p2", "reachability_counterfactual", False),
            make_record("p3", "order_dependent", False),
            make_record("p4", "order_dependent", False),
        ]
        assert c_maj(4, 4, records) == "REJECT"

    def test_reject_three_way_tie(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        records = [
            make_record("p1", "reachability_counterfactual", False),
            make_record("p2", "order_dependent", False),
            make_record("p3", "magnitude_boundary", False),
        ]
        assert c_maj(3, 3, records) == "REJECT"

    def test_fallback_when_obs_records_none(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        assert c_maj(0, 10, None) == "ACCEPT"
        assert c_maj(1, 10, None) == "REJECT"

    def test_can_differ_from_c_genuine(self):
        c_maj = LC322_ESTIMATOR_POLICIES["C_majority"]
        c_gen = LC322_ESTIMATOR_POLICIES["C_genuine"]
        records = [
            make_record("p1", "reachability_counterfactual", False),
            make_record("p2", "reachability_counterfactual", False),
            make_record("p3", "reachability_counterfactual", False),
            make_record("p4", "order_dependent", False),
            make_record("p5", "order_dependent", False),
        ]
        assert c_gen(5, 5, records) == "REJECT"
        assert c_maj(5, 5, records) == "ACCEPT"


# ---------------------------------------------------------------------------
# 5. C_zero_only (Rule 4) — binding
# ---------------------------------------------------------------------------

class TestCZeroOnlyBinding:

    def test_in_lc322_policies(self):
        assert "C_zero_only" in LC322_ESTIMATOR_POLICIES

    def test_in_lc45_policies(self):
        assert "C_zero_only" in LC45_ESTIMATOR_POLICIES

    def test_is_not_fail_count_policy_object(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        assert c_zo is not _fail_count_policy


# ---------------------------------------------------------------------------
# 6. C_zero_only (Rule 4) — decision rule
# ---------------------------------------------------------------------------

class TestCZeroOnlyRule:

    def test_accept_zero_failures(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        records = [make_record(f"p{i}", FAMILIES[i % 6], True) for i in range(10)]
        assert c_zo(0, 10, records) == "ACCEPT"

    def test_reject_any_failures(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        records = [make_record("p1", "reachability_counterfactual", False)]
        assert c_zo(1, 1, records) == "REJECT"

    def test_fallback_when_obs_records_none(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        assert c_zo(0, 5, None) == "ACCEPT"
        assert c_zo(1, 5, None) == "REJECT"

    def test_behaves_like_b1_on_constructed_inputs(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        for fails in range(6):
            assert c_zo(fails, 10, None) == _fail_count_policy(fails, 10, None)
            assert c_zo(fails, 10, [make_record("p1", FAMILIES[0], fails == 0)]) == _fail_count_policy(fails, 10, None)


# ---------------------------------------------------------------------------
# 7. R4 (C_zero_only) is the negative control — operationally identical to B1
# ---------------------------------------------------------------------------

class TestR4NegativeControl:

    def test_decision_function_source_ignores_obs_records(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        src = inspect.getsource(c_zo)
        assert "obs_records" not in src or "obs_fails" in src

    def test_predicted_verdict_is_does_not_survive(self):
        c_zo = LC322_ESTIMATOR_POLICIES["C_zero_only"]
        b1 = _fail_count_policy
        for fails in (0, 1, 2, 5, 10):
            for total in (1, 5, 10, 30):
                if fails <= total:
                    assert c_zo(fails, total, None) == b1(fails, total, None)


# ---------------------------------------------------------------------------
# 8. Falsification criterion carryforward
# ---------------------------------------------------------------------------

class TestFalsificationCriterion:

    def test_survives_requires_gap_above_delta_at_all_lambdas(self):
        from doctor.collapse_perturbations import classify_survival
        all_pass = [{"gaps": [{"gap": 0.5} for _ in range(9)]}]
        assert classify_survival(all_pass, delta=0.10) == "SURVIVES"

    def test_does_not_survive_when_one_perturbation_collapses(self):
        from doctor.collapse_perturbations import classify_survival
        one_collapse = [{"gaps": [{"gap": 0.5 if i < 8 else 0.0} for i in range(9)]}]
        assert classify_survival(one_collapse, delta=0.10) == "DOES_NOT_SURVIVE"

    def test_partially_survives_when_some_collapse(self):
        from doctor.collapse_perturbations import classify_survival
        perts = []
        perts.append({"gaps": [{"gap": 0.5} for _ in range(9)]})
        perts.append({"gaps": [{"gap": 0.5 if i < 5 else 0.0} for i in range(9)]})
        perts.append({"gaps": [{"gap": 0.5} for _ in range(9)]})
        assert classify_survival(perts, delta=0.10) == "PARTIALLY_SURVIVES"


# ---------------------------------------------------------------------------
# 9. Aggregate-consistency check carryforward
# ---------------------------------------------------------------------------

class TestAggregateConsistencyCarryforward:

    def test_function_still_importable(self):
        from doctor.identity_resolution import check_aggregate_consistency
        assert check_aggregate_consistency is not None
