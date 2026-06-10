"""Artifact schema validators — hard-raises on malformed input.

Covers the 6 critical artifacts that feed into C-4 and FP gates:
  A1: c4_decisions (C-4 gate input)
  A2: midweather_fingerprint result (FP gate input)
  A4: seval_manifest (FP gate input)
  A5: probe_index (FP gate input)
  F1: MIDWEATHER_FINGERPRINT_GATE_FREEZE (FP gate config)
  F2: PHASE_C4_FREEZE (C-4 gate config)

All validators follow the pattern:
  validate_X(data: dict, path: str = "<unknown>") -> None
Hard-raises ArtifactValidationError on missing/malformed fields.
"""
from __future__ import annotations


class ArtifactValidationError(RuntimeError):
    """Raised when an artifact fails schema validation.

    Message format: [path] — <description>
    """

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        super().__init__(f"[{path}] — {message}")


def _require(data: dict, field: str, path: str, *, expected: str = "present") -> object:
    if field not in data:
        raise ArtifactValidationError(path, f"missing required field: {field!r}")
    return data[field]


def _require_str(data: dict, field: str, path: str) -> str:
    val = _require(data, field, path)
    if not isinstance(val, str):
        raise ArtifactValidationError(path, f"invalid type for {field!r}: expected str, got {type(val).__name__}")
    if not val:
        raise ArtifactValidationError(path, f"empty value for required field: {field!r}")
    return val


def _require_int(data: dict, field: str, path: str, *, min_val: int | None = None) -> int:
    val = _require(data, field, path)
    if not isinstance(val, int) or isinstance(val, bool):
        raise ArtifactValidationError(path, f"invalid type for {field!r}: expected int, got {type(val).__name__}")
    if min_val is not None and val < min_val:
        raise ArtifactValidationError(path, f"value for {field!r} must be >= {min_val}, got {val}")
    return val


def _require_float(data: dict, field: str, path: str, *, min_val: float | None = None) -> float:
    val = _require(data, field, path)
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        raise ArtifactValidationError(path, f"invalid type for {field!r}: expected number, got {type(val).__name__}")
    if min_val is not None and val < min_val:
        raise ArtifactValidationError(path, f"value for {field!r} must be >= {min_val}, got {val}")
    return float(val)


def _require_list(data: dict, field: str, path: str, *, non_empty: bool = True) -> list:
    val = _require(data, field, path)
    if not isinstance(val, list):
        raise ArtifactValidationError(path, f"invalid type for {field!r}: expected list, got {type(val).__name__}")
    if non_empty and len(val) == 0:
        raise ArtifactValidationError(path, f"empty list for required field: {field!r}")
    return val


def _require_dict(data: dict, field: str, path: str) -> dict:
    val = _require(data, field, path)
    if not isinstance(val, dict):
        raise ArtifactValidationError(path, f"invalid type for {field!r}: expected dict, got {type(val).__name__}")
    return val


def _require_one_of(data: dict, field: str, path: str, allowed: tuple[str, ...]) -> str:
    val = _require_str(data, field, path)
    if val not in allowed:
        raise ArtifactValidationError(path, f"invalid value for {field!r}: expected {'|'.join(allowed)}, got {val!r}")
    return val


# ── A1: c4_decisions ─────────────────────────────────────────────────


def validate_c4_decisions(data: dict, path: str = "c4_decisions") -> None:
    _require_str(data, "population", path)
    _require_int(data, "n_solvers", path, min_val=1)
    _require_str(data, "spec_commit", path)
    _require_str(data, "freeze_commit", path)
    _require_str(data, "c1_freeze_commit", path)

    per_solver = _require_list(data, "per_solver", path)
    for i, entry in enumerate(per_solver):
        if not isinstance(entry, dict):
            raise ArtifactValidationError(path, f"per_solver[{i}] is not a dict")
        _require_str(entry, "solver_id", f"{path}/per_solver[{i}]")
        _require_one_of(entry, "ground_truth", f"{path}/per_solver[{i}]", ("ACCEPT", "REJECT"))
        _require_one_of(entry, "b1_decision", f"{path}/per_solver[{i}]", ("ACCEPT", "REJECT"))
        _require_one_of(entry, "c_genuine_decision", f"{path}/per_solver[{i}]", ("ACCEPT", "REJECT"))

    gap_table = _require_list(data, "utility_gap_table", path)
    for i, entry in enumerate(gap_table):
        if not isinstance(entry, dict):
            raise ArtifactValidationError(path, f"utility_gap_table[{i}] is not a dict")
        _require_int(entry, "lambda_R", f"{path}/utility_gap_table[{i}]", min_val=1)
        _require_float(entry, "b1_utility", f"{path}/utility_gap_table[{i}]")
        _require_float(entry, "c_genuine_utility", f"{path}/utility_gap_table[{i}]")
        _require_float(entry, "gap", f"{path}/utility_gap_table[{i}]")
        if "eligible" not in entry:
            raise ArtifactValidationError(path, f"utility_gap_table[{i}] missing 'eligible'")

    falsification = _require_dict(data, "falsification", path)
    _require_one_of(falsification, "verdict", f"{path}/falsification", ("PASS", "FAIL"))
    _require_float(falsification, "best_gap", f"{path}/falsification")
    _require_int(falsification, "best_lambda", f"{path}/falsification", min_val=1)
    _require_float(falsification, "delta", f"{path}/falsification", min_val=0.0)
    _require_str(falsification, "reason", f"{path}/falsification")


# ── A2: midweather_fingerprint result ────────────────────────────────


def validate_fingerprint_result(data: dict, path: str = "fingerprint_result") -> None:
    pgt = _require_dict(data, "per_solver_ground_truth", path)
    for sid, entry in pgt.items():
        if not isinstance(entry, dict):
            raise ArtifactValidationError(path, f"per_solver_ground_truth[{sid!r}] is not a dict")
        _require_one_of(entry, "truth_label", f"{path}/per_solver_ground_truth[{sid!r}]", ("ACCEPT", "REJECT"))
        _require_float(entry, "heldout_fail_rate", f"{path}/per_solver_ground_truth[{sid!r}]", min_val=0.0)

    estimator_table = _require_list(data, "estimator_table", path)
    for i, entry in enumerate(estimator_table):
        if not isinstance(entry, dict):
            raise ArtifactValidationError(path, f"estimator_table[{i}] is not a dict")
        _require_str(entry, "estimator", f"{path}/estimator_table[{i}]")
        _require_int(entry, "wrong_accepts", f"{path}/estimator_table[{i}]", min_val=0)
        _require_int(entry, "wrong_rejects", f"{path}/estimator_table[{i}]", min_val=0)
        _require_int(entry, "decision_loss", f"{path}/estimator_table[{i}]", min_val=0)
        if "degenerate_all_accept" not in entry:
            raise ArtifactValidationError(path, f"estimator_table[{i}] missing 'degenerate_all_accept'")
        if "degenerate_all_reject" not in entry:
            raise ArtifactValidationError(path, f"estimator_table[{i}] missing 'degenerate_all_reject'")

    _require_one_of(data, "decision", path, ("PASS", "FAIL"))
    _require_str(data, "decision_reason", path)
    if "guard_statuses" not in data:
        raise ArtifactValidationError(path, "missing required field: 'guard_statuses'")


# ── A4: seval_manifest ──────────────────────────────────────────────


def validate_seval_manifest(data: dict, path: str = "seval_manifest") -> None:
    _require_str(data, "certification_level", path)
    _require_str(data, "protocol_freeze_id", path)
    _require_list(data, "solver_files", path)
    _require_int(data, "n_solvers", path, min_val=1)
    _require_str(data, "pack_source", path)


# ── A5: probe_index ─────────────────────────────────────────────────


def validate_probe_index(data: dict, path: str = "probe_index") -> None:
    _require_list(data, "probes", path)
    for i, probe in enumerate(data["probes"]):
        if not isinstance(probe, dict):
            raise ArtifactValidationError(path, f"probes[{i}] is not a dict")
        _require_str(probe, "probe_id", f"{path}/probes[{i}]")
        _require_str(probe, "family", f"{path}/probes[{i}]")
        _require_str(probe, "axis", f"{path}/probes[{i}]")
        if "coins" not in probe:
            raise ArtifactValidationError(path, f"probes[{i}] missing 'coins'")
        _require_int(probe, "amount", f"{path}/probes[{i}]", min_val=1)

    _require_list(data, "axis_set", path)
    _require_str(data, "probe_index_set_id", path)


# ── F1: MIDWEATHER_FINGERPRINT_GATE_FREEZE ──────────────────────────


def validate_fp_freeze(data: dict, path: str = "fp_freeze") -> None:
    _require_str(data, "freeze_id", path)
    _require_str(data, "experiment", path)
    _require_str(data, "protocol_commit", path)

    decision_spec = _require_dict(data, "decision_spec", path)
    _require_float(decision_spec, "failure_threshold", f"{path}/decision_spec", min_val=0.0)
    _require_float(decision_spec, "minimum_accept_rate", f"{path}/decision_spec", min_val=0.0)

    obs_budget = _require_dict(data, "observation_budget", path)
    _require_int(obs_budget, "K", f"{path}/observation_budget", min_val=1)
    _require_list(obs_budget, "observed_probe_ids", f"{path}/observation_budget")
    _require_list(obs_budget, "target_probe_ids", f"{path}/observation_budget")


# ── F2: PHASE_C4_FREEZE ─────────────────────────────────────────────


def validate_c4_freeze(data: dict, path: str = "c4_freeze") -> None:
    delta = _require_dict(data, "delta", path)
    _require_float(delta, "value", f"{path}/delta", min_val=0.0)

    lambda_sweep = _require_dict(data, "lambda_sweep", path)
    values = _require_list(lambda_sweep, "values", f"{path}/lambda_sweep")
    for i, v in enumerate(values):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ArtifactValidationError(path, f"lambda_sweep.values[{i}] is not an int")
        if v < 1:
            raise ArtifactValidationError(path, f"lambda_sweep.values[{i}] must be >= 1, got {v}")
    _require_int(lambda_sweep, "lambda_A_fixed", f"{path}/lambda_sweep", min_val=1)

    _require_str(data, "spec_commit", path)
