# runners/run_c6_collapse_lc322.py
# Phase C-6: Representation Class Falsification — LC322 runner
#
# Re-runs B1 and each of 4 candidate rules (R1=C_genuine, R2=C_feature_threshold,
# R3=C_majority, R4=C_zero_only) on the unperturbed LC322 (aggregate-consistency
# check), then applies each of the C-5 perturbations (P1, P2a-c, P3a-f) to each
# rule and computes per-rule, per-perturbation utility gap tables. P4 (LC45) is
# handled by the separate run_c6_collapse_lc45.py runner.
#
# Does NOT modify existing data files.
# Does NOT introduce new probes or solver packs.
# Hard-stop on aggregate inconsistency for B1 on unperturbed LC322.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.problem_class_config import get_problem_class_config
from doctor.adversarial.transition_gate import write_gated_artifact
from doctor.asymmetric_cost import run_sweep_aggregate
from doctor.collapse_perturbations import (
    invert_ground_truth,
    knockout_probe_family,
    subsample_solvers,
)
from doctor.identity_resolution import check_aggregate_consistency
from runners.run_midweather_fingerprint_lc322 import (
    apply_estimator,
    compute_ground_truth,
    execute_solvers,
)

POPULATION_ID          = "LC322"
C6_FREEZE_PATH         = ROOT / "PHASE_C6_FREEZE.json"
DATA_PATH              = ROOT / "data" / "midweather_fingerprint_lc322.json"
FINGERPRINT_FREEZE     = ROOT / "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"
PROBE_INDEX_PATH       = ROOT / "data" / "midweather_fingerprint_lc322_probe_index.json"
SEVAL_MANIFEST_PATH    = ROOT / "data" / "midweather_fingerprint_lc322_seval_manifest.json"
OUTPUT_PATH            = ROOT / "data" / "c6_collapse_lc322.json"

C6_FREEZE_COMMIT = "6766f4c"
C5_FREEZE_COMMIT = "98cc8e4"

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


def _run_perturbation_for_all_rules(
    perturbation_id: str,
    sorted_ids: list[str],
    ground_truth: list[str],
    pass_results: dict,
    observed_ids: list[str],
    probe_index: dict,
    b1_policy,
    rule_policies: list[tuple[str, object]],
) -> dict:
    b1_preds = apply_estimator(b1_policy, pass_results, observed_ids, probe_index)
    b1_WA, b1_WR = _aggregate(b1_preds, sorted_ids, ground_truth)
    n = len(sorted_ids)
    rule_results = {}
    for rule_id, rule_policy in rule_policies:
        rule_preds = apply_estimator(rule_policy, pass_results, observed_ids, probe_index)
        rule_WA, rule_WR = _aggregate(rule_preds, sorted_ids, ground_truth)
        rule_results[rule_id] = {
            "aggregate": {"wrong_accepts": rule_WA, "wrong_rejects": rule_WR},
            "b1_aggregate": {"wrong_accepts": b1_WA, "wrong_rejects": b1_WR},
        }
    return {
        "perturbation_id": perturbation_id,
        "n_solvers": n,
        "b1_aggregate": {"wrong_accepts": b1_WA, "wrong_rejects": b1_WR},
        "rule_results": rule_results,
    }


def _per_rule_gap_table(
    b1_WA: int, b1_WR: int, rule_WA: int, rule_WR: int,
    n: int, lambda_sweep: list[float], lambda_A: float,
) -> list[dict]:
    return _compute_gap_table(b1_WA, b1_WR, rule_WA, rule_WR, n, lambda_sweep, lambda_A)


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
    print(f"[phase-c6] c5_freeze_commit={C5_FREEZE_COMMIT}  delta={delta}")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    pgt = data["per_solver_ground_truth"]
    sorted_ids = sorted(pgt.keys())
    ground_truth = [pgt[sid]["truth_label"] for sid in sorted_ids]

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

    config = get_problem_class_config("lc322")
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

    per_rule_unperturbed = {}
    for rule_id, rule_policy in rule_policies:
        rule_preds = apply_estimator(rule_policy, pass_results_full, observed_ids_full, probe_index)
        r_WA, r_WR = _aggregate(rule_preds, sorted_ids, ground_truth)
        per_rule_unperturbed[rule_id] = {
            "rule_aggregate": {"wrong_accepts": r_WA, "wrong_rejects": r_WR},
            "b1_aggregate": expected_b1,
        }
        print(f"[phase-c6] unperturbed {rule_id}: ({r_WA}, {r_WR})")

    perturbations = []

    print("[phase-c6] P1: ratio shift")
    p1_gt = invert_ground_truth(ground_truth)
    p1_pert = _run_perturbation_for_all_rules(
        "P1", sorted_ids, p1_gt, pass_results_full, observed_ids_full, probe_index,
        b1_policy, rule_policies,
    )
    for rule_id in per_rule_unperturbed:
        rr = p1_pert["rule_results"][rule_id]
        n = p1_pert["n_solvers"]
        gap_table = _per_rule_gap_table(
            p1_pert["b1_aggregate"]["wrong_accepts"],
            p1_pert["b1_aggregate"]["wrong_rejects"],
            rr["aggregate"]["wrong_accepts"],
            rr["aggregate"]["wrong_rejects"],
            n, lambda_sweep, lambda_A,
        )
        p1_pert["rule_results"][rule_id]["gaps"] = gap_table
    perturbations.append(p1_pert)
    print(f"  P1 done")

    p2_subsamples = [
        ("P2a", list(range(20))),
        ("P2b", list(range(10, 30))),
        ("P2c", list(range(10)) + list(range(20, 30))),
    ]
    for pid, indices in p2_subsamples:
        print(f"[phase-c6] {pid}: subsample {len(indices)} solvers")
        sub_ids = [sorted_ids[i] for i in indices]
        sub_gt = [ground_truth[i] for i in indices]
        sub_pass = {sid: pass_results_full[sid] for sid in sub_ids}
        pert = _run_perturbation_for_all_rules(
            pid, sub_ids, sub_gt, sub_pass, observed_ids_full, probe_index,
            b1_policy, rule_policies,
        )
        for rule_id in per_rule_unperturbed:
            rr = pert["rule_results"][rule_id]
            n = pert["n_solvers"]
            gap_table = _per_rule_gap_table(
                pert["b1_aggregate"]["wrong_accepts"],
                pert["b1_aggregate"]["wrong_rejects"],
                rr["aggregate"]["wrong_accepts"],
                rr["aggregate"]["wrong_rejects"],
                n, lambda_sweep, lambda_A,
            )
            pert["rule_results"][rule_id]["gaps"] = gap_table
        perturbations.append(pert)
        print(f"  {pid} done")

    families = c5_freeze = json.loads((ROOT / "PHASE_C5_FREEZE.json").read_text(encoding="utf-8"))
    rotation_order = c5_freeze["perturbations"]["P3_rotation_order"]
    for i, fam in enumerate(rotation_order):
        pid = f"P3{chr(ord('a') + i)}"
        print(f"[phase-c6] {pid}: knockout family '{fam}'")
        filtered_pass, removed = knockout_probe_family(pass_results_full, probe_index, fam)
        filtered_observed = [oid for oid in observed_ids_full if oid not in set(removed)]
        pert = _run_perturbation_for_all_rules(
            pid, sorted_ids, ground_truth, filtered_pass, filtered_observed, probe_index,
            b1_policy, rule_policies,
        )
        pert["family_knocked_out"] = fam
        pert["n_probes_removed"] = len(removed)
        for rule_id in per_rule_unperturbed:
            rr = pert["rule_results"][rule_id]
            n = pert["n_solvers"]
            gap_table = _per_rule_gap_table(
                pert["b1_aggregate"]["wrong_accepts"],
                pert["b1_aggregate"]["wrong_rejects"],
                rr["aggregate"]["wrong_accepts"],
                rr["aggregate"]["wrong_rejects"],
                n, lambda_sweep, lambda_A,
            )
            pert["rule_results"][rule_id]["gaps"] = gap_table
        perturbations.append(pert)
        print(f"  {pid} done")

    per_rule_falsification = {}
    for rule_id, _ in CANDIDATE_RULES:
        n_survived = 0
        per_pert_status = []
        for pert in perturbations:
            gaps = pert["rule_results"][rule_id]["gaps"]
            surv = _survives_pert(gaps, delta)
            per_pert_status.append({
                "perturbation_id": pert["perturbation_id"],
                "n_solvers": pert["n_solvers"],
                "b1_aggregate": pert["b1_aggregate"],
                "rule_aggregate": pert["rule_results"][rule_id]["aggregate"],
                "min_gap": min((g["gap"] for g in gaps if g["gap"] is not None), default=None),
                "max_gap": max((g["gap"] for g in gaps if g["gap"] is not None), default=None),
                "survives": surv,
            })
            if surv:
                n_survived += 1
        n_total = len(perturbations)
        if n_survived == n_total:
            verdict = "SURVIVES"
        elif n_survived == 0:
            verdict = "DOES_NOT_SURVIVE"
        else:
            verdict = "PARTIALLY_SURVIVES"
        per_rule_falsification[rule_id] = {
            "verdict": verdict,
            "n_survived": n_survived,
            "n_total": n_total,
            "per_perturbation": per_pert_status,
        }
        print(f"[phase-c6] {rule_id}: {verdict} ({n_survived}/{n_total})")

    surviving_rules = [
        rule_id for rule_id, _ in CANDIDATE_RULES
        if per_rule_falsification[rule_id]["verdict"] == "SURVIVES"
    ]
    non_surviving_rules = [
        rule_id for rule_id, _ in CANDIDATE_RULES
        if per_rule_falsification[rule_id]["verdict"] != "SURVIVES"
    ]
    if not surviving_rules:
        rq_c6_verdict = "NO"
    elif not non_surviving_rules:
        rq_c6_verdict = "YES"
    else:
        rq_c6_verdict = "MIXED"
    print(f"[phase-c6] RQ-C6 class-level verdict: {rq_c6_verdict}")

    output = {
        "population": POPULATION_ID,
        "spec_commit": spec_commit,
        "freeze_commit": C6_FREEZE_COMMIT,
        "c5_freeze_commit": C5_FREEZE_COMMIT,
        "delta": delta,
        "lambda_sweep": lambda_sweep,
        "unperturbed_b1_aggregate": expected_b1,
        "per_rule_unperturbed": per_rule_unperturbed,
        "perturbations": [
            {
                "perturbation_id": p["perturbation_id"],
                "n_solvers": p["n_solvers"],
                "b1_aggregate": p["b1_aggregate"],
                "rule_results": {
                    rid: {
                        "aggregate": p["rule_results"][rid]["aggregate"],
                        "b1_aggregate": p["rule_results"][rid]["b1_aggregate"],
                        "gaps": p["rule_results"][rid].get("gaps", []),
                    }
                    for rid, _ in CANDIDATE_RULES
                },
                "family_knocked_out": p.get("family_knocked_out"),
                "n_probes_removed": p.get("n_probes_removed"),
            }
            for p in perturbations
        ],
        "per_rule_falsification": per_rule_falsification,
        "rq_c6_verdict": {
            "verdict": rq_c6_verdict,
            "surviving_rules": surviving_rules,
            "non_surviving_rules": non_surviving_rules,
        },
    }

    write_gated_artifact(OUTPUT_PATH, output, "A13", "ARTIFACT_WRITE", ("C-6",))
    print(f"[phase-c6] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
