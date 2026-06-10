# runners/run_c4_decisions_lc322.py
# Phase C-4: Genuine Structured Policy — LC322 runner
#
# Re-runs B1 and C_genuine on the LC322 population with per-solver decision
# logging. Verifies aggregate consistency of B1 against stored (WA, WR) from
# data/midweather_fingerprint_lc322.json. Computes D, A, and utility gap
# between C_genuine and B1. Applies the C-4 falsification criterion.
#
# Does NOT modify the existing data file.
# Does NOT introduce new probes or solver packs.
# Hard-stop on aggregate inconsistency for B1 (per C-4 spec).

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.artifact_schema_validators import (
    validate_c4_decisions,
    validate_c4_freeze,
    validate_fp_freeze,
    validate_fingerprint_result,
    validate_probe_index,
    validate_seval_manifest,
)
from doctor.adversarial.transition_gate import write_gated_artifact
from doctor.adversarial.problem_class_config import get_problem_class_config
from doctor.asymmetric_cost import run_sweep_aggregate
from doctor.identity_resolution import (
    check_aggregate_consistency,
    compute_A,
    compute_D,
    apply_three_case_rule,
)
from runners.run_midweather_fingerprint_lc322 import (
    apply_estimator,
    compute_ground_truth,
    execute_solvers,
)

POPULATION_ID          = "LC322"
C4_FREEZE_PATH         = ROOT / "PHASE_C4_FREEZE.json"
DATA_PATH              = ROOT / "data" / "midweather_fingerprint_lc322.json"
FINGERPRINT_FREEZE     = ROOT / "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"
PROBE_INDEX_PATH       = ROOT / "data" / "midweather_fingerprint_lc322_probe_index.json"
SEVAL_MANIFEST_PATH    = ROOT / "data" / "midweather_fingerprint_lc322_seval_manifest.json"
OUTPUT_PATH            = ROOT / "data" / "c4_decisions_lc322.json"

C4_FREEZE_COMMIT = "88d0243"


def _aggregate_from_preds(preds: dict[str, str], ground_truth: list[str]) -> tuple[int, int]:
    WA = 0
    WR = 0
    for sid, dec in preds.items():
        gt = ground_truth[sorted(ground_truth_and_ids := None) and ""]  # placeholder
    return 0, 0


def _aggregate(preds: dict[str, str], sorted_ids: list[str], ground_truth: list[str]) -> tuple[int, int]:
    WA = sum(1 for sid, d in zip(sorted_ids, [preds[s] for s in sorted_ids])
             if d == "ACCEPT" and ground_truth[sorted_ids.index(sid)] == "REJECT")
    WR = sum(1 for sid, d in zip(sorted_ids, [preds[s] for s in sorted_ids])
             if d == "REJECT" and ground_truth[sorted_ids.index(sid)] == "ACCEPT")
    return WA, WR


def main() -> None:
    c4_freeze = json.loads(C4_FREEZE_PATH.read_text(encoding="utf-8"))
    validate_c4_freeze(c4_freeze, path=str(C4_FREEZE_PATH))
    spec_commit  = c4_freeze["spec_commit"]
    c1_freeze    = c4_freeze["lineage"]["c1_freeze_commit"]
    lambda_sweep = c4_freeze["lambda_sweep"]["values"]
    lambda_A     = c4_freeze["lambda_sweep"]["lambda_A_fixed"]
    delta        = c4_freeze["delta"]["value"]

    print(f"[phase-c4] population={POPULATION_ID}")
    print(f"[phase-c4] spec_commit={spec_commit}  freeze_commit={C4_FREEZE_COMMIT}")
    print(f"[phase-c4] c1_freeze_commit={c1_freeze}  delta={delta}")
    print(f"[phase-c4] lambda_sweep={lambda_sweep}")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    validate_fingerprint_result(data, path=str(DATA_PATH))
    pgt = data["per_solver_ground_truth"]
    sorted_ids = sorted(pgt.keys())
    ground_truth = [pgt[sid]["truth_label"] for sid in sorted_ids]
    n_solvers = len(sorted_ids)

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

    print(f"[phase-c4] solvers={n_solvers}  "
          f"accept={ground_truth.count('ACCEPT')}  reject={ground_truth.count('REJECT')}")

    freeze = json.loads(FINGERPRINT_FREEZE.read_text(encoding="utf-8"))
    validate_fp_freeze(freeze, path=str(FINGERPRINT_FREEZE))
    probe_index = json.loads(PROBE_INDEX_PATH.read_text(encoding="utf-8"))
    validate_probe_index(probe_index, path=str(PROBE_INDEX_PATH))
    seval_manifest = json.loads(SEVAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    validate_seval_manifest(seval_manifest, path=str(SEVAL_MANIFEST_PATH))

    config = get_problem_class_config("lc322")
    observed_ids = freeze["observation_budget"]["observed_probe_ids"]
    target_ids = freeze["observation_budget"]["target_probe_ids"]
    failure_threshold = freeze["decision_spec"]["failure_threshold"]

    pass_results = execute_solvers(seval_manifest, probe_index, config)
    ground = compute_ground_truth(pass_results, target_ids, failure_threshold)

    b1_policy = config.estimator_policies["B1_count"]
    c_genuine_policy = config.estimator_policies["C_genuine"]

    b1_preds = apply_estimator(b1_policy, pass_results, observed_ids, probe_index)
    c_genuine_preds = apply_estimator(c_genuine_policy, pass_results, observed_ids, probe_index)

    b1_decisions_sorted = [b1_preds[sid] for sid in sorted_ids]
    c_genuine_decisions_sorted = [c_genuine_preds[sid] for sid in sorted_ids]

    check_aggregate_consistency(
        b1_decisions_sorted,
        ground_truth,
        expected_wrong_accepts=expected_b1["wrong_accepts"],
        expected_wrong_rejects=expected_b1["wrong_rejects"],
        estimator_name="B1_count",
        population_id=POPULATION_ID,
    )
    print(f"[phase-c4] B1_count aggregate-consistent "
          f"(WA={expected_b1['wrong_accepts']}, WR={expected_b1['wrong_rejects']})")

    b1_WA, b1_WR = _aggregate(b1_preds, sorted_ids, ground_truth)
    c_genuine_WA, c_genuine_WR = _aggregate(c_genuine_preds, sorted_ids, ground_truth)
    print(f"[phase-c4] C_genuine aggregate: WA={c_genuine_WA}, WR={c_genuine_WR}")

    D = compute_D(c_genuine_decisions_sorted, b1_decisions_sorted, ground_truth)
    A = compute_A(c_genuine_decisions_sorted, b1_decisions_sorted, ground_truth, lambda_sweep, lambda_A)
    three_case = apply_three_case_rule(D, A)
    print(f"[phase-c4] D={D}  A={A}  three_case={three_case}")

    b1_sweep = run_sweep_aggregate(
        wrong_accepts=b1_WA, wrong_rejects=b1_WR, n_solvers=n_solvers,
        lambda_sweep=lambda_sweep, lambda_A=lambda_A,
    )
    c_genuine_sweep = run_sweep_aggregate(
        wrong_accepts=c_genuine_WA, wrong_rejects=c_genuine_WR, n_solvers=n_solvers,
        lambda_sweep=lambda_sweep, lambda_A=lambda_A,
    )

    gap_table = []
    best_gap = None
    best_lambda = None
    verdict = "FAIL"
    for b1_e, cg_e in zip(b1_sweep, c_genuine_sweep):
        lam = b1_e["lambda_R"]
        if b1_e["degenerate"] or cg_e["degenerate"]:
            gap_table.append({
                "lambda_R": lam,
                "b1_utility": b1_e["normalized_utility"],
                "c_genuine_utility": cg_e["normalized_utility"],
                "gap": None,
                "eligible": False,
            })
            continue
        gap = cg_e["normalized_utility"] - b1_e["normalized_utility"]
        eligible = gap > delta
        if eligible:
            verdict = "PASS"
            if best_gap is None or gap > best_gap:
                best_gap = gap
                best_lambda = lam
        gap_table.append({
            "lambda_R": lam,
            "b1_utility": b1_e["normalized_utility"],
            "c_genuine_utility": cg_e["normalized_utility"],
            "gap": gap,
            "eligible": eligible,
        })

    if D == 0:
        verdict = "FAIL"
        verdict_reason = f"D=0: C_genuine is operationally B1 (three_case={three_case})"
    elif D > 0 and verdict == "PASS":
        verdict_reason = f"PASS: utility gap > {delta} at lambda={best_lambda}, D={D} > 0"
    elif D > 0 and verdict == "FAIL":
        verdict_reason = f"FAIL: D>0 but no utility gap > {delta} found (three_case={three_case})"
    else:
        verdict_reason = f"FAIL: D={D}, A={A}, three_case={three_case}"

    print(f"[phase-c4] falsification verdict={verdict}")
    print(f"[phase-c4] reason: {verdict_reason}")

    per_solver_list = []
    for i, sid in enumerate(sorted_ids):
        per_solver_list.append({
            "solver_id": sid,
            "ground_truth": ground_truth[i],
            "b1_decision": b1_preds[sid],
            "c_genuine_decision": c_genuine_preds[sid],
        })

    output = {
        "population": POPULATION_ID,
        "n_solvers": n_solvers,
        "spec_commit": spec_commit,
        "freeze_commit": C4_FREEZE_COMMIT,
        "c1_freeze_commit": c1_freeze,
        "per_solver": per_solver_list,
        "b1_aggregate": {"wrong_accepts": b1_WA, "wrong_rejects": b1_WR},
        "c_genuine_aggregate": {"wrong_accepts": c_genuine_WA, "wrong_rejects": c_genuine_WR},
        "identity": {"D": D, "A": A, "three_case_outcome": three_case},
        "utility_gap_table": gap_table,
        "falsification": {
            "verdict": verdict,
            "best_gap": best_gap,
            "best_lambda": best_lambda,
            "delta": delta,
            "reason": verdict_reason,
        },
    }

    write_gated_artifact(OUTPUT_PATH, output, "A1", "ARTIFACT_WRITE", ("C-4",))
    print(f"[phase-c4] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
