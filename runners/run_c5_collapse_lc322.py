# runners/run_c5_collapse_lc322.py
# Phase C-5: Collapse Analysis (Distribution Shift) — LC322 runner
#
# Re-runs B1 and C_genuine on the unperturbed LC322 (aggregate-consistency
# check), then applies each of the four pre-declared perturbations and
# computes per-perturbation utility gap tables. Applies the C-5 falsification
# criterion.
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
from doctor.asymmetric_cost import run_sweep_aggregate
from doctor.collapse_perturbations import (
    classify_survival,
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
C5_FREEZE_PATH         = ROOT / "PHASE_C5_FREEZE.json"
DATA_PATH              = ROOT / "data" / "midweather_fingerprint_lc322.json"
FINGERPRINT_FREEZE     = ROOT / "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"
PROBE_INDEX_PATH       = ROOT / "data" / "midweather_fingerprint_lc322_probe_index.json"
SEVAL_MANIFEST_PATH    = ROOT / "data" / "midweather_fingerprint_lc322_seval_manifest.json"
C4_DATA_PATH           = ROOT / "data" / "c4_decisions_lc45.json"  # for P4 reference
OUTPUT_PATH            = ROOT / "data" / "c5_collapse_lc322.json"

C5_FREEZE_COMMIT = "98cc8e4"
C4_FREEZE_COMMIT = "88d0243"


def _aggregate(preds: dict[str, str], sorted_ids: list[str], ground_truth: list[str]) -> tuple[int, int]:
    preds_list = [preds[s] for s in sorted_ids]
    WA = sum(1 for d, g in zip(preds_list, ground_truth) if d == "ACCEPT" and g == "REJECT")
    WR = sum(1 for d, g in zip(preds_list, ground_truth) if d == "REJECT" and g == "ACCEPT")
    return WA, WR


def _compute_gap_table(
    b1_WA: int, b1_WR: int, cg_WA: int, cg_WR: int,
    n: int, lambda_sweep: list[float], lambda_A: float, delta: float,
) -> list[dict]:
    b1_sweep = run_sweep_aggregate(
        wrong_accepts=b1_WA, wrong_rejects=b1_WR, n_solvers=n,
        lambda_sweep=lambda_sweep, lambda_A=lambda_A,
    )
    cg_sweep = run_sweep_aggregate(
        wrong_accepts=cg_WA, wrong_rejects=cg_WR, n_solvers=n,
        lambda_sweep=lambda_sweep, lambda_A=lambda_A,
    )
    gap_table = []
    for b1_e, cg_e in zip(b1_sweep, cg_sweep):
        lam = b1_e["lambda_R"]
        if b1_e["degenerate"] or cg_e["degenerate"]:
            gap_table.append({"lambda_R": lam, "gap": None, "b1_utility": b1_e["normalized_utility"], "c_genuine_utility": cg_e["normalized_utility"]})
            continue
        gap = cg_e["normalized_utility"] - b1_e["normalized_utility"]
        gap_table.append({"lambda_R": lam, "gap": gap, "b1_utility": b1_e["normalized_utility"], "c_genuine_utility": cg_e["normalized_utility"]})
    return gap_table


def _run_perturbation(
    perturbation_id: str,
    sorted_ids: list[str],
    ground_truth: list[str],
    pass_results: dict,
    observed_ids: list[str],
    probe_index: dict,
    config,
    b1_policy,
    c_genuine_policy,
    lambda_sweep: list[float],
    lambda_A: float,
    delta: float,
) -> dict:
    b1_preds = apply_estimator(b1_policy, pass_results, observed_ids, probe_index)
    cg_preds = apply_estimator(c_genuine_policy, pass_results, observed_ids, probe_index)

    ids_in_scope = sorted(set(b1_preds.keys()) & set(ground_truth and range(len(sorted_ids)) and sorted_ids))
    n = len(ids_in_scope)
    b1_WA, b1_WR = _aggregate(b1_preds, ids_in_scope, ground_truth)
    cg_WA, cg_WR = _aggregate(cg_preds, ids_in_scope, ground_truth)

    gap_table = _compute_gap_table(b1_WA, b1_WR, cg_WA, cg_WR, n, lambda_sweep, lambda_A, delta)

    return {
        "perturbation_id": perturbation_id,
        "n_solvers": n,
        "b1_aggregate": {"wrong_accepts": b1_WA, "wrong_rejects": b1_WR},
        "c_genuine_aggregate": {"wrong_accepts": cg_WA, "wrong_rejects": cg_WR},
        "gaps": [{"lambda_R": g["lambda_R"], "gap": g["gap"]} for g in gap_table],
    }


def main() -> None:
    c5_freeze = json.loads(C5_FREEZE_PATH.read_text(encoding="utf-8"))
    spec_commit  = c5_freeze["spec_commit"]
    lambda_sweep = c5_freeze["lambda_sweep"]["values"]
    lambda_A     = c5_freeze["lambda_sweep"]["lambda_A_fixed"]
    delta        = c5_freeze["delta"]["value"]

    print(f"[phase-c5] population={POPULATION_ID}")
    print(f"[phase-c5] spec_commit={spec_commit}  freeze_commit={C5_FREEZE_COMMIT}")
    print(f"[phase-c5] c4_freeze_commit={C4_FREEZE_COMMIT}  delta={delta}")

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

    config = get_problem_class_config("lc322")
    observed_ids_full = freeze["observation_budget"]["observed_probe_ids"]
    target_ids = freeze["observation_budget"]["target_probe_ids"]
    failure_threshold = freeze["decision_spec"]["failure_threshold"]

    pass_results_full = execute_solvers(seval_manifest, probe_index, config)
    ground = compute_ground_truth(pass_results_full, target_ids, failure_threshold)

    b1_policy = config.estimator_policies["B1_count"]
    c_genuine_policy = config.estimator_policies["C_genuine"]

    # ---- Aggregate-consistency check on unperturbed LC322 ----
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
    print(f"[phase-c5] unperturbed B1 aggregate-consistent "
          f"(WA={expected_b1['wrong_accepts']}, WR={expected_b1['wrong_rejects']})")

    perturbations = []

    # ---- P1: ratio shift (11/19 -> 19/11) ----
    print("[phase-c5] P1: ratio shift")
    p1_gt = invert_ground_truth(ground_truth)
    per_solver_full = [{"solver_id": sid, "ground_truth": gt} for sid, gt in zip(sorted_ids, ground_truth)]
    per_solver_p1 = [{"solver_id": sid, "ground_truth": gt} for sid, gt in zip(sorted_ids, p1_gt)]
    p1_result = _run_perturbation(
        "P1", sorted_ids, p1_gt, pass_results_full, observed_ids_full, probe_index,
        config, b1_policy, c_genuine_policy, lambda_sweep, lambda_A, delta,
    )
    perturbations.append(p1_result)
    print(f"  P1: b1=({p1_result['b1_aggregate']['wrong_accepts']},{p1_result['b1_aggregate']['wrong_rejects']}) "
          f"c_genuine=({p1_result['c_genuine_aggregate']['wrong_accepts']},{p1_result['c_genuine_aggregate']['wrong_rejects']})")

    # ---- P2a/b/c: subsamples ----
    p2_subsamples = [
        ("P2a", list(range(20))),
        ("P2b", list(range(10, 30))),
        ("P2c", list(range(10)) + list(range(20, 30))),
    ]
    for pid, indices in p2_subsamples:
        print(f"[phase-c5] {pid}: subsample {len(indices)} solvers")
        sub_ids = [sorted_ids[i] for i in indices]
        sub_gt = [ground_truth[i] for i in indices]
        sub_pass = {sid: pass_results_full[sid] for sid in sub_ids}
        result = _run_perturbation(
            pid, sub_ids, sub_gt, sub_pass, observed_ids_full, probe_index,
            config, b1_policy, c_genuine_policy, lambda_sweep, lambda_A, delta,
        )
        perturbations.append(result)
        print(f"  {pid}: b1=({result['b1_aggregate']['wrong_accepts']},{result['b1_aggregate']['wrong_rejects']}) "
              f"c_genuine=({result['c_genuine_aggregate']['wrong_accepts']},{result['c_genuine_aggregate']['wrong_rejects']})")

    # ---- P3a-f: probe family knockout ----
    families = c5_freeze["perturbations"]["P3_rotation_order"]
    for i, fam in enumerate(families):
        pid = f"P3{chr(ord('a') + i)}"
        print(f"[phase-c5] {pid}: knockout family '{fam}'")
        filtered_pass, removed = knockout_probe_family(pass_results_full, probe_index, fam)
        filtered_observed = [oid for oid in observed_ids_full if oid not in set(removed)]
        result = _run_perturbation(
            pid, sorted_ids, ground_truth, filtered_pass, filtered_observed, probe_index,
            config, b1_policy, c_genuine_policy, lambda_sweep, lambda_A, delta,
        )
        result["family_knocked_out"] = fam
        result["n_probes_removed"] = len(removed)
        perturbations.append(result)
        print(f"  {pid}: removed {len(removed)} probes, "
              f"b1=({result['b1_aggregate']['wrong_accepts']},{result['b1_aggregate']['wrong_rejects']}) "
              f"c_genuine=({result['c_genuine_aggregate']['wrong_accepts']},{result['c_genuine_aggregate']['wrong_rejects']})")

    # ---- P4: LC45 cross-population (already measured in C-4) ----
    c4_lc45 = json.loads(C4_DATA_PATH.read_text(encoding="utf-8").read()) if False else json.loads(open(C4_DATA_PATH, encoding="utf-8").read())
    p4_falsification = c4_lc45.get("falsification", {})
    p4_gap_table = c4_lc45.get("utility_gap_table", [])
    p4_gaps = [{"lambda_R": g["lambda_R"], "gap": g["gap"]} for g in p4_gap_table]
    perturbations.append({
        "perturbation_id": "P4",
        "n_solvers": c4_lc45.get("n_solvers"),
        "b1_aggregate": c4_lc45.get("b1_aggregate"),
        "c_genuine_aggregate": c4_lc45.get("c_genuine_aggregate"),
        "gaps": p4_gaps,
        "source": "C-4 LC45 result (already measured)",
        "c4_verdict": p4_falsification.get("verdict"),
    })
    print(f"[phase-c5] P4: LC45 cross-population from C-4 (verdict={p4_falsification.get('verdict')})")

    # ---- Falsification criterion ----
    overall = classify_survival(perturbations, delta=delta)
    print(f"[phase-c5] overall verdict: {overall}")

    n_survived = sum(
        1 for p in perturbations
        if all((g.get("gap") is not None) and g["gap"] > delta for g in p["gaps"])
    )
    n_total = len(perturbations)
    print(f"[phase-c5] per-perturbation survival: {n_survived}/{n_total}")

    output = {
        "population": POPULATION_ID,
        "spec_commit": spec_commit,
        "freeze_commit": C5_FREEZE_COMMIT,
        "c4_freeze_commit": C4_FREEZE_COMMIT,
        "delta": delta,
        "lambda_sweep": lambda_sweep,
        "perturbations": perturbations,
        "falsification": {
            "verdict": overall,
            "n_survived": n_survived,
            "n_total": n_total,
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"[phase-c5] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
