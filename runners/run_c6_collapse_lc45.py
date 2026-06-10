# runners/run_c6_collapse_lc45.py
# Phase C-6: Representation Class Falsification — LC45 stress-test runner
#
# Re-runs B1 and each of 4 candidate rules on the unperturbed LC45 (aggregate-
# consistency check). Computes per-rule utility gap tables. Reports LC45 per-rule
# survival separately. LC45 result does not override the LC322 verdict on RQ-C6.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.problem_class_config import get_problem_class_config
from doctor.adversarial.transition_gate import write_gated_artifact
from doctor.asymmetric_cost import run_sweep_aggregate
from doctor.identity_resolution import check_aggregate_consistency
from runners.run_midweather_fingerprint_lc322 import (
    apply_estimator,
    compute_ground_truth,
    execute_solvers,
)

POPULATION_ID          = "LC45"
C6_FREEZE_PATH         = ROOT / "PHASE_C6_FREEZE.json"
DATA_PATH              = ROOT / "data" / "midweather_fingerprint_lc45.json"
FINGERPRINT_FREEZE     = ROOT / "MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json"
PROBE_INDEX_PATH       = ROOT / "data" / "midweather_fingerprint_lc45_probe_index.json"
SEVAL_MANIFEST_PATH    = ROOT / "data" / "midweather_fingerprint_lc45_seval_manifest.json"
C4_DATA_PATH           = ROOT / "data" / "c4_decisions_lc45.json"
OUTPUT_PATH            = ROOT / "data" / "c6_collapse_lc45.json"

C6_FREEZE_COMMIT = "6766f4c"
C4_FREEZE_COMMIT = "88d0243"
C4_CLOSURE_COMMIT = "50d33e5"

CANDIDATE_RULES = [
    ("R1_C_genuine", "C_genuine"),
    ("R2_C_feature_threshold", "C_feature_threshold"),
    ("R3_C_majority", "C_majority"),
    ("R4_C_zero_only", "C_zero_only"),
]


def _aggregate(preds: dict[str, str], sorted_ids: list[str], ground_truth: list[str]) -> tuple[int, int]:
    preds_list = [preds[s] for s in sorted_ids]
    WA = sum(1 for d, g in zip(preds_list, ground_truth) if d == "ACCEPT" and g == "REJECT")
    WR = sum(1 for d, g in zip(preds_list, ground_truth) if d == "REJECT" and g == "ACCEPT")
    return WA, WR


def _compute_gap_table(
    b1_WA: int, b1_WR: int, rule_WA: int, rule_WR: int,
    n: int, lambda_sweep: list[float], lambda_A: float,
) -> list[dict]:
    b1_sweep = run_sweep_aggregate(
        wrong_accepts=b1_WA, wrong_rejects=b1_WR, n_solvers=n,
        lambda_sweep=lambda_sweep, lambda_A=lambda_A,
    )
    rule_sweep = run_sweep_aggregate(
        wrong_accepts=rule_WA, wrong_rejects=rule_WR, n_solvers=n,
        lambda_sweep=lambda_sweep, lambda_A=lambda_A,
    )
    gap_table = []
    for b1_e, rule_e in zip(b1_sweep, rule_sweep):
        lam = b1_e["lambda_R"]
        if b1_e["degenerate"] or rule_e["degenerate"]:
            gap_table.append({
                "lambda_R": lam, "gap": None,
                "b1_utility": b1_e["normalized_utility"],
                "rule_utility": rule_e["normalized_utility"],
            })
            continue
        gap = rule_e["normalized_utility"] - b1_e["normalized_utility"]
        gap_table.append({
            "lambda_R": lam, "gap": gap,
            "b1_utility": b1_e["normalized_utility"],
            "rule_utility": rule_e["normalized_utility"],
        })
    return gap_table


def _survives_pert(gaps: list[dict], delta: float) -> bool:
    return all((g.get("gap") is not None) and g["gap"] > delta for g in gaps)


def main() -> None:
    c6_freeze = json.loads(C6_FREEZE_PATH.read_text(encoding="utf-8"))
    spec_commit  = c6_freeze["lineage"]["c6_spec_commit"]
    lambda_sweep = c6_freeze["lambda_sweep"]["values"]
    lambda_A     = c6_freeze["lambda_sweep"]["lambda_A_fixed"]
    delta        = c6_freeze["delta"]["value"]

    print(f"[phase-c6] population={POPULATION_ID}")
    print(f"[phase-c6] spec_commit={spec_commit}  freeze_commit={C6_FREEZE_COMMIT}")
    print(f"[phase-c6] c4_freeze_commit={C4_FREEZE_COMMIT}  delta={delta}")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    pgt = data["per_solver_ground_truth"]
    sorted_ids = sorted(pgt.keys())
    ground_truth = [pgt[sid]["truth_label"] for sid in sorted_ids]
    n_full = len(sorted_ids)

    expected_b1 = None
    for e in data["estimator_table"]:
        if e["estimator"] == "B1_count":
            expected_b1 = {
                "wrong_accepts": int(e["wrong_accepts"]),
                "wrong_rejects": int(e["wrong_rejects"]),
            }
            break
    if expected_b1 is None:
        raise KeyError("B1_count not found in data/estimator_table")

    freeze = json.loads(FINGERPRINT_FREEZE.read_text(encoding="utf-8"))
    probe_index = json.loads(PROBE_INDEX_PATH.read_text(encoding="utf-8"))
    seval_manifest = json.loads(SEVAL_MANIFEST_PATH.read_text(encoding="utf-8"))

    config = get_problem_class_config("lc45")
    observed_ids_full = freeze["observation_budget"]["observed_probe_ids"]
    target_ids = freeze["observation_budget"]["target_probe_ids"]
    failure_threshold = freeze["decision_spec"]["failure_threshold"]

    pass_results_full = execute_solvers(seval_manifest, probe_index, config)
    ground = compute_ground_truth(pass_results_full, target_ids, failure_threshold)

    b1_policy = config.estimator_policies["B1_count"]
    rule_policies = [(rule_id, config.estimator_policies[policy_name]) for rule_id, policy_name in CANDIDATE_RULES]

    unperturbed_b1 = apply_estimator(b1_policy, pass_results_full, observed_ids_full, probe_index)
    b1_decisions_sorted = [unperturbed_b1[sid] for sid in sorted_ids]
    check_aggregate_consistency(
        b1_decisions_sorted,
        ground_truth,
        expected_wrong_accepts=expected_b1["wrong_accepts"],
        expected_wrong_rejects=expected_b1["wrong_rejects"],
        estimator_name="B1_count",
        population_id=POPULATION_ID,
    )
    print(f"[phase-c6] unperturbed B1 aggregate-consistent "
          f"(WA={expected_b1['wrong_accepts']}, WR={expected_b1['wrong_rejects']})")

    per_rule = {}
    for rule_id, rule_policy in rule_policies:
        rule_preds = apply_estimator(rule_policy, pass_results_full, observed_ids_full, probe_index)
        r_WA, r_WR = _aggregate(rule_preds, sorted_ids, ground_truth)
        gap_table = _compute_gap_table(
            expected_b1["wrong_accepts"], expected_b1["wrong_rejects"],
            r_WA, r_WR, n_full, lambda_sweep, lambda_A,
        )
        per_rule[rule_id] = {
            "rule_aggregate": {"wrong_accepts": r_WA, "wrong_rejects": r_WR},
            "b1_aggregate": expected_b1,
            "gaps": gap_table,
        }
        print(f"[phase-c6] {rule_id}: ({r_WA}, {r_WR}); "
              f"min_gap={min((g['gap'] for g in gap_table if g['gap'] is not None), default=None)}")

    per_rule_falsification = {}
    for rule_id, _ in CANDIDATE_RULES:
        gaps = per_rule[rule_id]["gaps"]
        surv = _survives_pert(gaps, delta)
        per_rule_falsification[rule_id] = {
            "verdict": "SURVIVES" if surv else "DOES_NOT_SURVIVE",
            "min_gap": min((g["gap"] for g in gaps if g["gap"] is not None), default=None),
            "max_gap": max((g["gap"] for g in gaps if g["gap"] is not None), default=None),
        }
        print(f"[phase-c6] {rule_id} LC45: {per_rule_falsification[rule_id]['verdict']}")

    c4_lc45 = json.loads(open(C4_DATA_PATH, encoding="utf-8").read())
    c4_c_genuine_aggregate = c4_lc45.get("c_genuine_aggregate")
    c4_c_genuine_gap_table = c4_lc45.get("utility_gap_table", [])
    r1_c_genuine_aggregate_here = per_rule["R1_C_genuine"]["rule_aggregate"]
    r1_match = (
        r1_c_genuine_aggregate_here["wrong_accepts"] == c4_c_genuine_aggregate["wrong_accepts"]
        and r1_c_genuine_aggregate_here["wrong_rejects"] == c4_c_genuine_aggregate["wrong_rejects"]
    )
    print(f"[phase-c6] R1 (C_genuine) matches C-4 LC45 aggregate: {r1_match}")

    output = {
        "population": POPULATION_ID,
        "spec_commit": spec_commit,
        "freeze_commit": C6_FREEZE_COMMIT,
        "c4_freeze_commit": C4_FREEZE_COMMIT,
        "c4_closure_commit": C4_CLOSURE_COMMIT,
        "delta": delta,
        "lambda_sweep": lambda_sweep,
        "n_solvers": n_full,
        "unperturbed_b1_aggregate": expected_b1,
        "per_rule": per_rule,
        "per_rule_falsification": per_rule_falsification,
        "c4_cross_check": {
            "r1_c_genuine_aggregate_here": r1_c_genuine_aggregate_here,
            "c4_c_genuine_aggregate": c4_c_genuine_aggregate,
            "aggregate_matches": r1_match,
            "c4_verdict": c4_lc45.get("falsification", {}).get("verdict"),
        },
    }

    write_gated_artifact(OUTPUT_PATH, output, "A14", "ARTIFACT_WRITE", ("C-6",))
    print(f"[phase-c6] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
