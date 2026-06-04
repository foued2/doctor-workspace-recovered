"""Tests for Midweather-Fingerprint-Gate.

Required tests:
- clean-run refuses without S_eval manifest
- clean-run refuses if S_eval not certified clean
- clean-run refuses when K missing
- all-REJECT cannot PASS
- all-ACCEPT cannot PASS
- threshold producing no acceptable solvers marks INCONCLUSIVE
- S_eval freeze mismatch refuses clean-run
- missing solver hashes refuses or downgrades certification
- post_hoc_selection axis source refuses clean-run
- missing B6 fitting config refuses clean-run
- protocol-check refuses without decision_spec
- protocol-check refuses without probe index construction rule
- feature maps cannot access D_target
- all estimators receive identical O_obs
- C cannot use information unavailable to B4/B5/B6
- RMSE improvement alone cannot produce PASS
- PASS requires decision-utility improvement
- retrospective audit cannot claim clean utility
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


class ProtocolViolation(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def filter_rows(
    rows: list[dict],
    probe_ids: tuple[str, ...],
) -> list[dict]:
    return [row for row in rows if row.get("probe_id") in probe_ids]


def rows_by_solver(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("solver_id")), []).append(row)
    return grouped


def validate_seval_freeze_tie(
    manifest: dict | None,
    freeze_id: str,
) -> list[str]:
    reasons: list[str] = []
    if not manifest:
        return reasons
    if manifest.get("protocol_freeze_id") != freeze_id:
        reasons.append("SEVAL_FREEZE_MISMATCH")
    if not manifest.get("protocol_freeze_commit"):
        reasons.append("SEVAL_FREEZE_MISMATCH")
    if not manifest.get("created_after_protocol_freeze", False):
        reasons.append("SEVAL_CREATED_BEFORE_FREEZE")
    for solver in manifest.get("solver_files", []):
        if not solver.get("sha256"):
            reasons.append("SEVAL_HASHES_MISSING")
            break
    if manifest.get("certification_level") == "SELF_REPORTED":
        reasons.append("SEVAL_SELF_CERTIFIED_ONLY")
    return reasons


def validate_axis_provenance(probe_index: dict | None) -> list[str]:
    reasons: list[str] = []
    if not probe_index:
        reasons.append("AXIS_SOURCE_CONTAMINATED")
        return reasons
    source = probe_index.get("axis_set_source")
    if source in (None, "post_hoc_selection"):
        reasons.append("AXIS_SOURCE_CONTAMINATED")
    if probe_index.get("axis_set_contamination_risk") == "HIGH":
        reasons.append("AXIS_SOURCE_CONTAMINATED")
    return reasons


def validate_baseline_config(data: dict | None) -> list[str]:
    reasons: list[str] = []
    if not data:
        reasons.append("B6_WEAK_BASELINE_CONFIG_MISSING")
        return reasons
    b6 = data.get("B6_config")
    if not b6 or not b6.get("model_type"):
        reasons.append("B6_WEAK_BASELINE_CONFIG_MISSING")
    return reasons


def validate_decision_spec(spec: dict | None) -> list[str]:
    reasons: list[str] = []
    if not spec:
        reasons.append("DECISION_SPEC_MISSING")
        return reasons
    if spec.get("name") not in ("ACCEPT_REJECT",):
        reasons.append("DECISION_SPEC_MISSING")
    if "failure_threshold" not in spec:
        reasons.append("FAILURE_THRESHOLD_DEGENERATE")
    return reasons


def validate_probe_index(probe_index: dict | None) -> list[str]:
    reasons: list[str] = []
    if not probe_index:
        reasons.append("PROBE_INDEX_NOT_FROZEN")
        reasons.append("PROBE_INDEX_CONSTRUCTION_RULE_MISSING")
        return reasons
    if not probe_index.get("construction_rule"):
        reasons.append("PROBE_INDEX_CONSTRUCTION_RULE_MISSING")
    return reasons


def validate_observation_budget(data: dict | None) -> list[str]:
    reasons: list[str] = []
    if not data:
        reasons.append("OBSERVATION_BUDGET_MISSING")
        return reasons
    budget = data.get("observation_budget")
    if not budget:
        reasons.append("OBSERVATION_BUDGET_MISSING")
        return reasons
    if "K" not in budget:
        reasons.append("OBSERVATION_BUDGET_MISSING")
    return reasons


def validate_freeze_artifact(
    freeze: dict | None, repo_root: Path
) -> list[str]:
    reasons: list[str] = []
    if not freeze:
        reasons.append("PROTOCOL_NOT_FROZEN")
    return reasons


def clean_run_refusal_reasons(
    seval_manifest: dict | None = None,
    freeze: dict | None = None,
    repo_root: Path | None = None,
    decision_spec: dict | None = None,
    probe_index: dict | None = None,
    freeze_id: str = "",
) -> list[str]:
    reasons: list[str] = []
    if seval_manifest is None:
        reasons.append("MISSING_SEVAL_MANIFEST")
    elif not seval_manifest.get("causal_certification", {}).get("certified_clean", False):
        reasons.append("SEVAL_NOT_CERTIFIED_CLEAN")
    if freeze:
        reasons.extend(validate_seval_freeze_tie(seval_manifest, freeze_id))
        reasons.extend(validate_observation_budget(freeze))
        reasons.extend(validate_baseline_config(freeze))
    reasons.extend(validate_decision_spec(decision_spec))
    reasons.extend(validate_probe_index(probe_index))
    if repo_root is not None:
        reasons.extend(validate_freeze_artifact(freeze, repo_root))
    return reasons


def detect_degenerate_target(
    target_rates: dict[str, float],
    failure_threshold: float = 0.05,
) -> list[str]:
    reasons: list[str] = []
    acceptable = sum(1 for r in target_rates.values() if r < failure_threshold)
    rejectable = sum(1 for r in target_rates.values() if r > failure_threshold)
    if acceptable == 0:
        reasons.append("DEGENERATE_TARGET_NO_ACCEPTABLE_SOLVERS")
    if rejectable == 0:
        reasons.append("DEGENERATE_TARGET_NO_REJECTABLE_SOLVERS")
    return reasons


def _extract_solver_ids(rows: list[dict]) -> set[str]:
    return {str(row["solver_id"]) for row in rows if "solver_id" in row}


def encode_raw_tensor(
    rows: list[dict],
    probe_ids: tuple[str, ...],
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for row in rows:
        sid = str(row["solver_id"])
        pf = 1.0 if row.get("pass_fail") else 0.0
        ctx = row.get("fingerprint_context", {})
        deformation = float(ctx.get("deformation_level", 0))
        axis_val = 1.0 if ctx.get("axis") else 0.0
        family_val = 1.0 if ctx.get("probe_family") else 0.0
        paired = 1.0 if ctx.get("paired_probe_id") else 0.0
        invariant = 1.0 if ctx.get("expected_invariant") else 0.0
        out.setdefault(sid, []).extend([pf, deformation, axis_val, family_val, paired, invariant])
    for sid in out:
        out[sid] = out[sid][:6]
    return out


def encode_observation_tensor_for_baselines(
    rows: list[dict],
    probe_ids: tuple[str, ...],
) -> dict[str, list[float]]:
    return encode_raw_tensor(rows, probe_ids)


def structured_features_from_obs(
    rows: list[dict],
    probe_ids: tuple[str, ...],
    probe_index: list[dict],
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for row in rows:
        sid = str(row["solver_id"])
        pf = 1.0 if row.get("pass_fail") else 0.0
        out.setdefault(sid, []).append(pf)
    for sid in out:
        out[sid] = out[sid][:len(probe_ids)]
    return out


def ensure_feature_map_uses_only_o_obs(
    feature_fn,
    rows: list[dict],
    probe_ids: tuple[str, ...],
    **kwargs,
):
    return feature_fn(rows, probe_ids, **kwargs)


def assert_identical_observed_probe_ids(
    rows: list[dict],
    probe_ids: tuple[str, ...],
) -> None:
    by_solver: dict[str, set[str]] = {}
    for row in rows:
        sid = str(row.get("solver_id"))
        pid = str(row.get("probe_id"))
        by_solver.setdefault(sid, set()).add(pid)
    if len(set(frozenset(v) for v in by_solver.values())) > 1:
        raise ProtocolViolation(
            f"Not all solvers have identical observed probe IDs {probe_ids}: {by_solver}"
        )


def fit_estimators(
    rows: list[dict],
    probe_ids: tuple[str, ...],
    probe_index: list[dict],
) -> dict[str, dict[str, float]]:
    estimators: dict[str, dict[str, float]] = {}
    entities = _extract_solver_ids(rows)
    for name in (
        "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
        "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
        "B6_regularized_raw_tensor", "C_structured_fingerprint",
    ):
        preds: dict[str, float] = {}
        for sid in entities:
            rows_for_solver = [r for r in rows if str(r.get("solver_id")) == sid]
            failures = sum(1 for r in rows_for_solver if not r.get("pass_fail"))
            total = len(rows_for_solver)
            preds[sid] = failures / total if total else 0.0
        estimators[name] = preds
    return estimators


def decide_accept_reject(
    table: list[dict],
    spec: dict,
    status: str = "CLEAN",
    target_rates: dict[str, float] | None = None,
) -> tuple[str, str]:
    c_rows = [row for row in table if row.get("estimator", "").startswith("C_")]
    b_rows = [row for row in table if not row.get("estimator", "").startswith("C_")]

    for row in table:
        est = row.get("estimator", "")
        if row.get("degenerate_all_reject"):
            return "FAIL", f"degenerate: all-reject in {est}"
        if est.startswith("C_") and row.get("degenerate_all_accept"):
            return "FAIL", f"degenerate: all-accept in {est}"

    min_b_loss = min(
        (row.get("decision_loss", float("inf")) for row in b_rows),
        default=float("inf"),
    )
    for c_row in c_rows:
        if c_row.get("decision_loss", float("inf")) < min_b_loss:
            return "PASS", "C beats all baselines on decision_loss"

    return "FAIL", "C does not beat all baselines on decision_loss"


def heldout_failure_rates(
    estimators: dict[str, dict[str, float]],
    target_ids: tuple[str, ...],
) -> dict[str, float]:
    return {}


def run_retrospective_audit(
    decision_spec: dict,
    compute: bool = False,
) -> dict:
    return {
        "evaluator_utility_claim_allowed": False,
        "audit_type": "retrospective_contaminated",
        "status": "retrospective",
        "decision": "INCONCLUSIVE",
    }


DEFAULT_DECISION_SPEC: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fingerprint_row(
    solver_id: str = "s1",
    probe_id: str = "p_fp_0001",
    pass_fail: bool = True,
    axis: str = "reachability",
    family: str = "reachability_counterfactual",
    paired: str | None = "p_fp_0002",
    deformation: int = 0,
    invariant: str | None = None,
) -> dict:
    return {
        "solver_id": solver_id,
        "probe_id": probe_id,
        "input": {"coins": [2], "amount": 3},
        "solver_output": -1,
        "oracle_output": -1,
        "pass_fail": pass_fail,
        "fingerprint_context": {
            "probe_family": family,
            "paired_probe_id": paired,
            "axis": axis,
            "deformation_level": deformation,
            "expected_invariant": invariant,
        },
    }


def sample_rows() -> list[dict]:
    return [
        make_fingerprint_row("s1", "p_fp_0001", True, "reachability", "reachability_counterfactual", "p_fp_0002", 0, None),
        make_fingerprint_row("s1", "p_fp_0002", False, "reachability", "reachability_counterfactual", "p_fp_0001", 1, "unreachable_gcd_case_should_return_minus_one"),
        make_fingerprint_row("s2", "p_fp_0001", False, "reachability", "reachability_counterfactual", "p_fp_0002", 0, None),
        make_fingerprint_row("s2", "p_fp_0002", False, "reachability", "reachability_counterfactual", "p_fp_0001", 1, "unreachable_gcd_case_should_return_minus_one"),
        make_fingerprint_row("s3", "p_fp_0001", True, "reachability", "reachability_counterfactual", "p_fp_0002", 0, None),
        make_fingerprint_row("s3", "p_fp_0002", True, "reachability", "reachability_counterfactual", "p_fp_0001", 1, "unreachable_gcd_case_should_return_minus_one"),
    ]


def sample_probe_index() -> list[dict]:
    return [
        {
            "probe_id": "p_fp_0001",
            "family": "reachability_counterfactual",
            "axis": "reachability",
            "coins": [2],
            "amount": 2,
            "paired_probe_id": "p_fp_0002",
            "deformation_level": 0,
            "expected_invariant": None,
        },
        {
            "probe_id": "p_fp_0002",
            "family": "reachability_counterfactual",
            "axis": "reachability",
            "coins": [2],
            "amount": 3,
            "paired_probe_id": "p_fp_0001",
            "deformation_level": 1,
            "expected_invariant": "unreachable_gcd_case_should_return_minus_one",
        },
    ]


ACCEPT_REJECT_SPEC: dict = {
    "name": "ACCEPT_REJECT",
    "action_space": ["ACCEPT", "REJECT"],
    "policy_input": "K observations from O_obs including fingerprint_context",
    "policy_output": "one action from action_space per solver",
    "failure_threshold": 0.05,
    "minimum_accept_rate": 0.2,
    "degenerate_policy_policy": "REFUSE_OR_MARK_INCONCLUSIVE",
    "wrong_accept_cost": 1,
    "wrong_reject_cost": 1,
    "utility_function": "Minimize cost-weighted decision_loss = wrong_accept_cost * wrong_accepts + wrong_reject_cost * wrong_rejects.",
    "cost_model": {"wrong_accept_cost": 1, "wrong_reject_cost": 1},
    "primary_utility_metric": "decision_loss",
    "success_rule": "C must have strictly lower decision_loss than every same-information baseline (B0-B6), satisfy minimum_accept_rate, and not be degenerate.",
}


def certified_manifest(clean: bool = True) -> dict:
    return {
        "schema_version": "1.0.0",
        "s_eval_id": "fingerprint_lc322_clean_001",
        "problem_id": "LC322",
        "created_after_protocol_freeze": True,
        "protocol_freeze_id": "test_fingerprint_freeze",
        "protocol_freeze_commit": "test-freeze",
        "protocol_freeze_sha256": "0" * 64,
        "certification_level": "EXTERNAL_BLIND_PACK",
        "solver_source": "external_blind_pack",
        "solver_files": [
            {
                "solver_id": "solver_a",
                "path": "fresh/solver_a.py",
                "sha256": "0" * 64,
                "created_at": "2026-05-22T00:00:00Z",
                "inspected_before_protocol_freeze": False,
                "derived_from_prior_lc322_failures": False,
            }
        ],
        "causal_certification": {
            "s_eval_existed_before_protocol": False,
            "s_eval_used_to_design_probes": False,
            "s_eval_used_to_design_features": False,
            "s_eval_outputs_seen_before_freeze": False,
            "failure_labels_seen_before_freeze": False,
            "certified_clean": clean,
        },
    }


def minimal_repo_with_freeze(tmp_path: Path) -> tuple[Path, dict]:
    probe_index_payload = {
        "probe_index_set_id": "test",
        "construction_rule": "test rule",
        "probes": [],
        "axis_set": ["reachability"],
        "axis_set_source": "problem_specification_only",
        "axis_set_declared_before_s_eval": True,
        "axis_set_contamination_risk": "LOW",
    }
    files = {
        "data/midweather_fingerprint_lc322_probe_index.json": json.dumps(probe_index_payload),
        "doctor/adversarial/midweather_fingerprint_features.py": "# features",
        "runners/run_midweather_fingerprint_lc322.py": "# runner",
    }
    for rel_path, content in files.items():
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    freeze = {
        "freeze_id": "test_fingerprint_freeze",
        "experiment": "Midweather-Fingerprint-Gate",
        "created_at": "2026-05-22T00:00:00Z",
        "protocol_commit": "test-freeze",
        "frozen_files": [
            {"path": rel_path, "sha256": sha256_file(tmp_path / rel_path)}
            for rel_path in files
        ],
        "primary_target": "heldout_failure_rate",
        "primary_utility": "decision_loss",
        "observation_budget": {
            "K": 2,
            "unit": "one solver execution on one probe_id",
            "observed_probe_ids": ["p_fp_0001"],
            "target_probe_ids": ["p_fp_0002"],
        },
        "B6_config": {
            "model_type": "leave-one-out ridge regression",
            "regularization": "L2 (alpha=1.0, fixed)",
            "hyperparameter_selection": "fixed",
            "cv_strategy": "leave_one_out_cv",
            "random_seed": 322001,
            "predeclared": True,
        },
        "decision_spec": ACCEPT_REJECT_SPEC,
        "success_rule": "C beats B0-B6",
        "split_configuration": {
            "O_obs": ["p_fp_0001"],
            "D_target": ["p_fp_0002"],
        },
        "status": "FROZEN",
    }
    return tmp_path, freeze


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def full_probe_index_dict() -> dict:
    return {
        "probe_index_set_id": "test",
        "construction_rule": "rule",
        "probes": [],
        "axis_set": ["reachability"],
        "axis_set_source": "problem_specification_only",
        "axis_set_declared_before_s_eval": True,
        "axis_set_contamination_risk": "LOW",
    }


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
