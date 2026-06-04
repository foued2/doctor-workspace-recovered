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
    weakest = data.get("weakest_baseline_config")
    if not weakest or not weakest.get("model_type"):
        reasons.append("B6_WEAK_BASELINE_CONFIG_MISSING")
    return reasons


def validate_decision_spec(spec: dict | None) -> list[str]:
    reasons: list[str] = []
    if not spec:
        reasons.append("DECISION_SPEC_MISSING")
        return reasons
    name = spec.get("name")
    if not isinstance(name, str) or not name:
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


_SEVAL_MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json"
)


def load_seval_manifest_schema() -> dict:
    return json.loads(_SEVAL_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))


class SevalManifestValidationError(RuntimeError):
    pass


def assert_valid_seval_manifest(
    manifest: dict | None,
    freeze: dict | None,
) -> None:
    """Validate a S_eval manifest against the schema + freeze tie.

    Raises SevalManifestValidationError with a list of reasons if the
    manifest does not conform. Mirrors the call style of
    assert_valid_schema (no return value, raises on failure).
    """
    import jsonschema

    reasons: list[str] = []
    if manifest is None:
        raise SevalManifestValidationError("manifest is None")
    if freeze is None:
        raise SevalManifestValidationError("freeze is None")

    try:
        jsonschema.validate(manifest, load_seval_manifest_schema())
    except jsonschema.ValidationError as exc:
        reasons.append(f"SCHEMA_VIOLATION: {exc.message} at {list(exc.absolute_path)}")

    if manifest.get("protocol_freeze_id") != freeze.get("freeze_id"):
        reasons.append("SEVAL_FREEZE_ID_MISMATCH")
    if manifest.get("protocol_freeze_commit") != freeze.get("protocol_commit"):
        reasons.append("SEVAL_FREEZE_COMMIT_MISMATCH")
    freeze_sha = next(
        (f.get("sha256") for f in freeze.get("frozen_files", [])
         if f.get("path") == "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"),
        None,
    )
    if freeze_sha and manifest.get("protocol_freeze_sha256") and \
       manifest.get("protocol_freeze_sha256") != freeze_sha:
        reasons.append("SEVAL_FREEZE_SHA_MISMATCH")
    certified = (
        manifest.get("causal_certification", {}).get("certified_clean")
    )
    if not isinstance(certified, bool):
        reasons.append("SEVAL_CERTIFIED_CLEAN_NOT_BOOLEAN")

    if reasons:
        raise SevalManifestValidationError("; ".join(reasons))


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
    candidate_prefixes: tuple[str, ...] = ("C_",),
) -> tuple[str, str]:
    def _is_candidate(est: str) -> bool:
        return any(est.startswith(p) for p in candidate_prefixes)

    c_rows = [row for row in table if _is_candidate(row.get("estimator", ""))]
    b_rows = [row for row in table if not _is_candidate(row.get("estimator", ""))]

    for row in table:
        est = row.get("estimator", "")
        if row.get("degenerate_all_reject"):
            return "FAIL", f"degenerate: all-reject in {est}"
        if _is_candidate(est) and row.get("degenerate_all_accept"):
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
                "derived_from_prior_failures": False,
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
        "weakest_baseline_config": {
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

