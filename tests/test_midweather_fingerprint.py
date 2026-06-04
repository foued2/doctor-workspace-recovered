"""Relocated protocol tests for the Midweather-Fingerprint-Gate clean-run.

Originally inlined in
``doctor/adversarial/midweather_fingerprint_features.py`` (lines 572-1034).
Moved here so the source module no longer carries its own test surface and
so the freeze can list the test file separately.

All 39 ``test_*`` defs are preserved verbatim. Only the surrounding
``pytest``, helper, and ``Path`` imports have been added.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from doctor.adversarial.midweather_fingerprint_features import (
    ACCEPT_REJECT_SPEC,
    ProtocolViolation,
    assert_identical_observed_probe_ids,
    certified_manifest,
    clean_run_refusal_reasons,
    decide_accept_reject,
    detect_degenerate_target,
    encode_observation_tensor_for_baselines,
    encode_raw_tensor,
    ensure_feature_map_uses_only_o_obs,
    filter_rows,
    fit_estimators,
    full_probe_index_dict,
    minimal_repo_with_freeze,
    run_retrospective_audit,
    sample_probe_index,
    sample_rows,
    structured_features_from_obs,
    validate_axis_provenance,
    validate_baseline_config,
    validate_decision_spec,
    validate_freeze_artifact,
    validate_observation_budget,
    validate_probe_index,
    validate_seval_freeze_tie,
)


# ---------------------------------------------------------------------------
# Test 1: clean-run refuses without S_eval manifest
# ---------------------------------------------------------------------------

def test_clean_run_refuses_without_seval_manifest(tmp_path):
    repo_root, freeze = minimal_repo_with_freeze(tmp_path)
    reasons = clean_run_refusal_reasons(
        seval_manifest=None,
        freeze=freeze,
        repo_root=repo_root,
        decision_spec=ACCEPT_REJECT_SPEC,
        probe_index=full_probe_index_dict(),
        freeze_id="test_fingerprint_freeze",
    )
    assert "MISSING_SEVAL_MANIFEST" in reasons


# ---------------------------------------------------------------------------
# Test 2: clean-run refuses if S_eval not certified clean
# ---------------------------------------------------------------------------

def test_clean_run_refuses_if_seval_not_certified_clean(tmp_path):
    repo_root, freeze = minimal_repo_with_freeze(tmp_path)
    manifest = certified_manifest(clean=False)
    reasons = clean_run_refusal_reasons(
        seval_manifest=manifest,
        freeze=freeze,
        repo_root=repo_root,
        decision_spec=ACCEPT_REJECT_SPEC,
        probe_index=full_probe_index_dict(),
        freeze_id="test_fingerprint_freeze",
    )
    assert "SEVAL_NOT_CERTIFIED_CLEAN" in reasons


# ---------------------------------------------------------------------------
# Test 3: clean-run refuses when K missing
# ---------------------------------------------------------------------------

def test_clean_run_refuses_when_k_missing(tmp_path):
    repo_root, freeze = minimal_repo_with_freeze(tmp_path)
    del freeze["observation_budget"]
    manifest = certified_manifest(clean=True)
    reasons = clean_run_refusal_reasons(
        seval_manifest=manifest,
        freeze=freeze,
        repo_root=repo_root,
        decision_spec=ACCEPT_REJECT_SPEC,
        probe_index=full_probe_index_dict(),
        freeze_id="test_fingerprint_freeze",
    )
    assert "OBSERVATION_BUDGET_MISSING" in reasons


# ---------------------------------------------------------------------------
# Test 4: all-REJECT cannot PASS
# ---------------------------------------------------------------------------

def test_all_reject_cannot_pass():
    table = [
        {"estimator": "B0_prior", "wrong_accepts": 0, "wrong_rejects": 3, "decision_loss": 3.0,
         "accept_rate": 0.0, "satisfies_minimum_accept_rate": False,
         "degenerate_all_reject": True, "degenerate_all_accept": False},
        {"estimator": "C_structured_fingerprint", "wrong_accepts": 0, "wrong_rejects": 3, "decision_loss": 3.0,
         "accept_rate": 0.0, "satisfies_minimum_accept_rate": False,
         "degenerate_all_reject": True, "degenerate_all_accept": False},
    ]
    decision, reason = decide_accept_reject(
        table, ACCEPT_REJECT_SPEC, status="CLEAN",
        target_rates={"s1": 0.0, "s2": 0.1, "s3": 0.2},
    )
    assert decision == "FAIL"
    assert "degenerate" in reason.lower() or "all-reject" in reason.lower()


# ---------------------------------------------------------------------------
# Test 5: all-ACCEPT cannot PASS
# ---------------------------------------------------------------------------

def test_all_accept_cannot_pass():
    table = [
        {"estimator": "B0_prior", "wrong_accepts": 0, "wrong_rejects": 2, "decision_loss": 2.0,
         "accept_rate": 1.0, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False},
        {"estimator": "C_structured_fingerprint", "wrong_accepts": 3, "wrong_rejects": 0, "decision_loss": 3.0,
         "accept_rate": 1.0, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": True},
    ]
    decision, reason = decide_accept_reject(
        table, ACCEPT_REJECT_SPEC, status="CLEAN",
        target_rates={"s1": 0.0, "s2": 0.0, "s3": 0.1},
    )
    assert decision == "FAIL"
    assert "degenerate" in reason.lower() or "all-accept" in reason.lower()


# ---------------------------------------------------------------------------
# Test 6: threshold producing no acceptable solvers marks INCONCLUSIVE
# ---------------------------------------------------------------------------

def test_degenerate_target_no_acceptable_solvers():
    reasons = detect_degenerate_target(
        {"s1": 0.1, "s2": 0.2, "s3": 0.3},
        failure_threshold=0.05,
    )
    assert "DEGENERATE_TARGET_NO_ACCEPTABLE_SOLVERS" in reasons

    reasons = detect_degenerate_target(
        {"s1": 0.0, "s2": 0.0, "s3": 0.0},
        failure_threshold=0.05,
    )
    assert "DEGENERATE_TARGET_NO_REJECTABLE_SOLVERS" in reasons


# ---------------------------------------------------------------------------
# Test 7: S_eval freeze mismatch refuses clean-run
# ---------------------------------------------------------------------------

def test_seval_freeze_mismatch_refuses_clean_run():
    manifest = certified_manifest(clean=True)
    manifest["protocol_freeze_id"] = "different_freeze_id"
    reasons = validate_seval_freeze_tie(manifest, "test_fingerprint_freeze")
    assert "SEVAL_FREEZE_MISMATCH" in reasons


def test_seval_created_before_freeze_refuses():
    manifest = certified_manifest(clean=True)
    manifest["created_after_protocol_freeze"] = False
    reasons = validate_seval_freeze_tie(manifest, "test_fingerprint_freeze")
    assert "SEVAL_CREATED_BEFORE_FREEZE" in reasons


# ---------------------------------------------------------------------------
# Test 8: missing solver hashes refuses or downgrades certification
# ---------------------------------------------------------------------------

def test_missing_solver_hashes_downgrades_certification():
    manifest = certified_manifest(clean=True)
    manifest["solver_files"][0]["sha256"] = ""
    reasons = validate_seval_freeze_tie(manifest, "test_fingerprint_freeze")
    assert "SEVAL_HASHES_MISSING" in reasons


# ---------------------------------------------------------------------------
# Test 9: post_hoc_selection axis source refuses clean-run
# ---------------------------------------------------------------------------

def test_post_hoc_axis_source_refuses():
    probe_index = full_probe_index_dict()
    probe_index["axis_set_source"] = "post_hoc_selection"
    reasons = validate_axis_provenance(probe_index)
    assert "AXIS_SOURCE_CONTAMINATED" in reasons


def test_missing_axis_source_refuses():
    probe_index = full_probe_index_dict()
    del probe_index["axis_set_source"]
    reasons = validate_axis_provenance(probe_index)
    assert "AXIS_SOURCE_CONTAMINATED" in reasons


# ---------------------------------------------------------------------------
# Test 10: missing B6 fitting config refuses clean-run
# ---------------------------------------------------------------------------

def test_missing_b6_config_refuses():
    reasons = validate_baseline_config(None)
    assert "B6_WEAK_BASELINE_CONFIG_MISSING" in reasons

    reasons = validate_baseline_config({"primary_target": "x"})
    assert "B6_WEAK_BASELINE_CONFIG_MISSING" in reasons


def test_b6_config_missing_model_type_refuses():
    reasons = validate_baseline_config({
        "primary_utility": "x",
        "B6_config": {"regularization": "L2"},
    })
    assert "B6_WEAK_BASELINE_CONFIG_MISSING" in reasons


# ---------------------------------------------------------------------------
# Test 11: RMSE improvement alone cannot produce PASS
# ---------------------------------------------------------------------------

def test_rmse_improvement_alone_cannot_produce_pass():
    table = [
        {"estimator": "B0_prior", "wrong_accepts": 1, "wrong_rejects": 0, "decision_loss": 1.0,
         "accept_rate": 0.8, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False,
         "rmse_secondary": 0.4},
        {"estimator": "B1_count", "wrong_accepts": 1, "wrong_rejects": 0, "decision_loss": 1.0,
         "accept_rate": 0.8, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False,
         "rmse_secondary": 0.3},
        {"estimator": "C_structured_fingerprint", "wrong_accepts": 1, "wrong_rejects": 0, "decision_loss": 1.0,
         "accept_rate": 0.8, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False,
         "rmse_secondary": 0.1},
    ]
    decision, reason = decide_accept_reject(
        table, ACCEPT_REJECT_SPEC, status="CLEAN",
        target_rates={"s1": 0.0, "s2": 0.1, "s3": 0.0, "s4": 0.2},
    )
    assert decision == "FAIL"


# ---------------------------------------------------------------------------
# Test 12: PASS requires decision-utility improvement
# ---------------------------------------------------------------------------

def test_pass_requires_decision_utility_improvement():
    table = [
        {"estimator": "B0_prior", "wrong_accepts": 2, "wrong_rejects": 1, "decision_loss": 3.0,
         "accept_rate": 0.5, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False,
         "rmse_secondary": 0.2},
        {"estimator": "B1_count", "wrong_accepts": 1, "wrong_rejects": 1, "decision_loss": 2.0,
         "accept_rate": 0.5, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False,
         "rmse_secondary": 0.2},
        {"estimator": "C_structured_fingerprint", "wrong_accepts": 0, "wrong_rejects": 1, "decision_loss": 1.0,
         "accept_rate": 0.6, "satisfies_minimum_accept_rate": True,
         "degenerate_all_reject": False, "degenerate_all_accept": False,
         "rmse_secondary": 0.5},
    ]
    decision, reason = decide_accept_reject(
        table, ACCEPT_REJECT_SPEC, status="CLEAN",
        target_rates={"s1": 0.0, "s2": 0.1, "s3": 0.2, "s4": 0.0},
    )
    assert decision == "PASS"


# ---------------------------------------------------------------------------
# Test 13: retrospective audit cannot claim clean utility
# ---------------------------------------------------------------------------

def test_retrospective_audit_cannot_claim_clean_utility():
    report = run_retrospective_audit(
        decision_spec=ACCEPT_REJECT_SPEC,
        compute=False,
    )
    assert report["evaluator_utility_claim_allowed"] is False
    assert "contaminated" in report.get("audit_type", "").lower() or "retrospective" in report.get("status", "").lower()
    assert report["decision"] == "INCONCLUSIVE"


# ---------------------------------------------------------------------------
# Test 14: feature maps cannot access D_target
# ---------------------------------------------------------------------------

def test_feature_maps_cannot_access_d_target():
    observed = sample_rows()
    target_row = {
        "solver_id": "s1",
        "probe_id": "p_fp_0099",
        "pass_fail": False,
        "fingerprint_context": {"axis": "other", "deformation_level": 0},
    }
    features_a = structured_features_from_obs(
        observed, ("p_fp_0001", "p_fp_0002"), sample_probe_index()
    )
    features_b = structured_features_from_obs(
        observed, ("p_fp_0001", "p_fp_0002"), sample_probe_index()
    )
    assert features_a == features_b
    observed_with_target = observed + [target_row]
    features_c = structured_features_from_obs(
        filter_rows(observed_with_target, ("p_fp_0001", "p_fp_0002")),
        ("p_fp_0001", "p_fp_0002"),
        sample_probe_index(),
    )
    assert features_a == features_c


# ---------------------------------------------------------------------------
# Test 15: all estimators receive identical O_obs
# ---------------------------------------------------------------------------

def test_all_estimators_receive_identical_obs():
    assert_identical_observed_probe_ids(sample_rows(), ("p_fp_0001", "p_fp_0002"))
    bad_rows = sample_rows()[:-1]
    with pytest.raises(ProtocolViolation, match="identical observed probe IDs"):
        assert_identical_observed_probe_ids(bad_rows, ("p_fp_0001", "p_fp_0002"))


# ---------------------------------------------------------------------------
# Test 16: C cannot use information unavailable to baselines B4/B5/B6
# ---------------------------------------------------------------------------

def test_c_does_not_use_info_unavailable_to_raw_baselines():
    rows = sample_rows()
    observed = filter_rows(rows, ("p_fp_0001", "p_fp_0002"))
    probe_ids = ("p_fp_0001", "p_fp_0002")
    raw_tensor = encode_observation_tensor_for_baselines(observed, probe_ids)
    structured = structured_features_from_obs(observed, probe_ids, sample_probe_index())
    raw_solvers = set(raw_tensor)
    struct_solvers = set(structured)
    assert raw_solvers == struct_solvers, (
        "C and raw baselines operate on different solvers"
    )


# ---------------------------------------------------------------------------
# Test 17: protocol-check refuses without decision_spec
# ---------------------------------------------------------------------------

def test_protocol_check_refuses_without_decision_spec():
    reasons = validate_decision_spec(None)
    assert "DECISION_SPEC_MISSING" in reasons
    reasons = validate_decision_spec({})
    assert "DECISION_SPEC_MISSING" in reasons


# ---------------------------------------------------------------------------
# Test 18: protocol-check refuses without probe index construction rule
# ---------------------------------------------------------------------------

def test_protocol_check_refuses_without_probe_index_construction_rule():
    reasons = validate_probe_index(None)
    assert "PROBE_INDEX_CONSTRUCTION_RULE_MISSING" in reasons
    reasons = validate_probe_index({"probes": []})
    assert "PROBE_INDEX_CONSTRUCTION_RULE_MISSING" in reasons


# ---------------------------------------------------------------------------
# Additional structural tests
# ---------------------------------------------------------------------------

def test_fingerprint_features_deterministic():
    rows = sample_rows()
    observed = filter_rows(rows, ("p_fp_0001", "p_fp_0002"))
    probe_ids = ("p_fp_0001", "p_fp_0002")
    features_a = ensure_feature_map_uses_only_o_obs(
        structured_features_from_obs, observed, probe_ids,
        probe_index=sample_probe_index(),
    )
    features_b = ensure_feature_map_uses_only_o_obs(
        structured_features_from_obs, observed, probe_ids,
        probe_index=sample_probe_index(),
    )
    assert features_a == features_b


def test_validate_decision_spec_accepts_valid():
    reasons = validate_decision_spec(ACCEPT_REJECT_SPEC)
    assert reasons == []


def test_validate_decision_spec_refuses_none():
    reasons = validate_decision_spec(None)
    assert "DECISION_SPEC_MISSING" in reasons


def test_validate_decision_spec_refuses_missing_failure_threshold():
    spec = dict(ACCEPT_REJECT_SPEC)
    del spec["failure_threshold"]
    reasons = validate_decision_spec(spec)
    assert "FAILURE_THRESHOLD_DEGENERATE" in reasons


def test_validate_decision_spec_refuses_unsupported_type():
    spec = dict(ACCEPT_REJECT_SPEC)
    spec["name"] = "RANK_SELECT_TOP_K"
    reasons = validate_decision_spec(spec)
    assert "DECISION_SPEC_MISSING" in reasons


def test_fit_estimators_returns_all_baselines():
    rows = sample_rows()
    observed = filter_rows(rows, ("p_fp_0001", "p_fp_0002"))
    estimators = fit_estimators(observed, ("p_fp_0001", "p_fp_0002"), sample_probe_index())
    expected = {"B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
                "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
                "B6_regularized_raw_tensor", "C_structured_fingerprint"}
    assert expected <= set(estimators)


def test_raw_tensor_includes_fingerprint_metadata():
    rows = sample_rows()
    observed = filter_rows(rows, ("p_fp_0001", "p_fp_0002"))
    tensor = encode_raw_tensor(observed, ("p_fp_0001", "p_fp_0002"))
    for sid, vec in tensor.items():
        assert len(vec) == 6


def test_evaluator_utility_claim_false_when_contaminated():
    report = run_retrospective_audit(
        decision_spec=ACCEPT_REJECT_SPEC,
        compute=False,
    )
    assert report.get("evaluator_utility_claim_allowed") is False


def test_validate_freeze_artifact_refuses_none():
    reasons = validate_freeze_artifact(None, Path("."))
    assert "PROTOCOL_NOT_FROZEN" in reasons


def test_validate_probe_index_refuses_none():
    reasons = validate_probe_index(None)
    assert "PROBE_INDEX_NOT_FROZEN" in reasons
    assert "PROBE_INDEX_CONSTRUCTION_RULE_MISSING" in reasons


def test_validate_observation_budget_refuses_missing():
    reasons = validate_observation_budget(None)
    assert "OBSERVATION_BUDGET_MISSING" in reasons

    reasons = validate_observation_budget({"primary_target": "x"})
    assert "OBSERVATION_BUDGET_MISSING" in reasons


def test_validate_observation_budget_refuses_missing_K():
    reasons = validate_observation_budget({
        "observation_budget": {"unit": "execution"},
    })
    assert "OBSERVATION_BUDGET_MISSING" in reasons


def test_validate_seval_freeze_tie_refuses_missing_commit():
    manifest = certified_manifest(clean=True)
    del manifest["protocol_freeze_commit"]
    reasons = validate_seval_freeze_tie(manifest, "test_fingerprint_freeze")
    assert "SEVAL_FREEZE_MISMATCH" in reasons


def test_validate_seval_self_reported_only():
    manifest = certified_manifest(clean=True)
    manifest["certification_level"] = "SELF_REPORTED"
    reasons = validate_seval_freeze_tie(manifest, "test_fingerprint_freeze")
    assert "SEVAL_SELF_CERTIFIED_ONLY" in reasons


def test_validate_axis_provenance_accepts_clean():
    probe_index = full_probe_index_dict()
    reasons = validate_axis_provenance(probe_index)
    assert reasons == []


def test_validate_axis_provenance_high_risk():
    probe_index = full_probe_index_dict()
    probe_index["axis_set_contamination_risk"] = "HIGH"
    reasons = validate_axis_provenance(probe_index)
    assert "AXIS_SOURCE_CONTAMINATED" in reasons


def test_validate_baseline_config_accepts_valid():
    reasons = validate_baseline_config({
        "B6_config": {
            "model_type": "ridge",
            "regularization": "L2",
            "hyperparameter_selection": "fixed",
            "predeclared": True,
        }
    })
    assert reasons == []


def test_self_reported_qualification_in_findings():
    assert ACCEPT_REJECT_SPEC["failure_threshold"] == 0.05
    assert "minimum_accept_rate" in ACCEPT_REJECT_SPEC
    assert "degenerate_policy_policy" in ACCEPT_REJECT_SPEC
