# runners/run_c7_quotient_lc322.py
# Phase C-7: Response-Equivalence Quotient on `large_amount_stress` — runner
#
# Re-runs B1 and C_genuine on the unperturbed LC322 (full 30-probe set) and
# the family-3 quotient under each of the 5 C-7 conditions (P0, P1, P2a, P2b, P2c).
# Verifies aggregate consistency of B1 against stored (WA, WR) from
# data/midweather_fingerprint_lc322.json. Computes Delta(M_C, M_B1; T_P) and
# the aggregate utility gap per condition per lambda. Applies the C-7
# per-perturbation stability test and determines the RQ-C7 verdict.
#
# Does NOT modify the existing data files.
# Does NOT introduce new probes or solver packs.
# Does NOT introduce new estimators.
# Hard-stop on aggregate inconsistency for B1 (per C-7 freeze).
#
# Pairs with PHASE_C7_SPEC.md (commit 779f9cb) and
# PHASE_C7_FREEZE.json (commit 06bbe40).

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.problem_class_config import get_problem_class_config
from doctor.adversarial.transition_gate import write_gated_artifact
from doctor.adversarial.quotient import (
    apply_rule_to_quotient,
    compute_quotient,
    quotient_size,
)
from doctor.asymmetric_cost import run_sweep_aggregate
from doctor.identity_resolution import check_aggregate_consistency
from runners.run_midweather_fingerprint_lc322 import (
    execute_solvers,
)


POPULATION_ID       = "LC322"
C7_FREEZE_PATH      = ROOT / "PHASE_C7_FREEZE.json"
C7_SPEC_COMMIT      = "779f9cb"
C7_FREEZE_COMMIT    = "06bbe40"
DATA_PATH           = ROOT / "data" / "midweather_fingerprint_lc322.json"
PROBE_INDEX_PATH    = ROOT / "data" / "midweather_fingerprint_lc322_probe_index.json"
SEVAL_MANIFEST_PATH = ROOT / "data" / "midweather_fingerprint_lc322_seval_manifest.json"
OUTPUT_PATH         = ROOT / "data" / "c7_quotient_lc322.json"

FAMILY3_PROBE_IDS = ["p_fp_0011", "p_fp_0012", "p_fp_0013", "p_fp_0014", "p_fp_0015"]


def compute_aggregate(
    preds: dict[str, str],
    sorted_ids: list[str],
    ground_truth: dict[str, str],
) -> tuple[int, int]:
    """Return (WA, WR) for the given predictions vs ground_truth."""
    WA = 0
    WR = 0
    for sid in sorted_ids:
        dec = preds[sid]
        gt = ground_truth[sid]
        if dec == "ACCEPT" and gt == "REJECT":
            WA += 1
        elif dec == "REJECT" and gt == "ACCEPT":
            WR += 1
    return WA, WR


def main() -> None:
    freeze = json.loads(C7_FREEZE_PATH.read_text(encoding="utf-8"))
    spec_commit  = freeze["spec_commit"]
    lambda_sweep = freeze["lambda_sweep"]["values"]
    lambda_A     = freeze["lambda_sweep"]["lambda_A_fixed"]
    delta        = freeze["delta"]["value"]

    print(f"[phase-c7] population={POPULATION_ID}")
    print(f"[phase-c7] spec_commit={spec_commit}  freeze_commit={C7_FREEZE_COMMIT}")
    print(f"[phase-c7] delta={delta}  lambda_sweep={lambda_sweep}")
    print(f"[phase-c7] family-3 probe_ids={FAMILY3_PROBE_IDS}")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    pgt = data["per_solver_ground_truth"]
    sorted_ids = sorted(pgt.keys())
    ground_truth_full = {sid: pgt[sid]["truth_label"] for sid in sorted_ids}
    n_solvers = len(sorted_ids)
    n_accept = sum(1 for v in ground_truth_full.values() if v == "ACCEPT")
    n_reject = n_solvers - n_accept

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

    print(f"[phase-c7] solvers={n_solvers}  accept={n_accept}  reject={n_reject}")
    print(f"[phase-c7] expected B1 (full 30-probe set): WA={expected_b1['wrong_accepts']}, WR={expected_b1['wrong_rejects']}")

    probe_index = json.loads(PROBE_INDEX_PATH.read_text(encoding="utf-8"))
    seval_manifest = json.loads(SEVAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    config = get_problem_class_config("lc322")

    print(f"[phase-c7] running solvers on full 30-probe set...")
    pass_results = execute_solvers(seval_manifest, probe_index, config)

    b1_policy = config.estimator_policies["B1_count"]
    c_genuine_policy = config.estimator_policies["C_genuine"]

    all_probe_ids = [p["probe_id"] for p in probe_index["probes"]]
    b1_preds_full = apply_rule_to_quotient(
        b1_policy,
        compute_quotient(all_probe_ids, pass_results, sorted_ids),
        pass_results,
        sorted_ids,
    )
    b1_decisions_sorted_full = [b1_preds_full[sid] for sid in sorted_ids]
    ground_truth_sorted_full = [ground_truth_full[sid] for sid in sorted_ids]

    check_aggregate_consistency(
        b1_decisions_sorted_full,
        ground_truth_sorted_full,
        expected_wrong_accepts=expected_b1["wrong_accepts"],
        expected_wrong_rejects=expected_b1["wrong_rejects"],
        estimator_name="B1_count",
        population_id=POPULATION_ID,
    )
    print(f"[phase-c7] B1_count aggregate-consistent on full 30-probe set")

    conditions_spec = freeze["perturbation_battery"]
    condition_names = ["P0_unperturbed", "P1_accept_reject_ratio_shift",
                       "P2a_solver_subsample_first_20",
                       "P2b_solver_subsample_last_20",
                       "P2c_solver_subsample_first10_last10"]

    per_condition_results = []

    for cname in condition_names:
        cdef = conditions_spec[cname]
        indices = cdef.get("indices_zero_indexed")
        if indices is None:
            sub_sorted_ids = sorted_ids
            quotient_solver_ids = sorted_ids
        else:
            sub_sorted_ids = [sorted_ids[i] for i in indices]
            quotient_solver_ids = sub_sorted_ids

        sub_ground_truth = {sid: ground_truth_full[sid] for sid in sub_sorted_ids}

        if cname == "P1_accept_reject_ratio_shift":
            for sid in sub_sorted_ids:
                gt = sub_ground_truth[sid]
                sub_ground_truth[sid] = "REJECT" if gt == "ACCEPT" else "ACCEPT"

        quotient = compute_quotient(
            FAMILY3_PROBE_IDS,
            pass_results,
            solver_ids=quotient_solver_ids,
        )
        n_quotient = quotient_size(quotient)
        print(f"[phase-c7] {cname}: |S|={len(sub_sorted_ids)}, |T_P|={n_quotient}")

        b1_preds = apply_rule_to_quotient(b1_policy, quotient, pass_results, sub_sorted_ids)
        c_genuine_preds = apply_rule_to_quotient(c_genuine_policy, quotient, pass_results, sub_sorted_ids)

        b1_WA, b1_WR = compute_aggregate(b1_preds, sub_sorted_ids, sub_ground_truth)
        c_genuine_WA, c_genuine_WR = compute_aggregate(c_genuine_preds, sub_sorted_ids, sub_ground_truth)

        D = sum(1 for sid in sub_sorted_ids if b1_preds[sid] != c_genuine_preds[sid])

        b1_sweep = run_sweep_aggregate(
            wrong_accepts=b1_WA, wrong_rejects=b1_WR, n_solvers=len(sub_sorted_ids),
            lambda_sweep=lambda_sweep, lambda_A=lambda_A,
        )
        c_genuine_sweep = run_sweep_aggregate(
            wrong_accepts=c_genuine_WA, wrong_rejects=c_genuine_WR, n_solvers=len(sub_sorted_ids),
            lambda_sweep=lambda_sweep, lambda_A=lambda_A,
        )

        gap_table = []
        any_collapse = False
        degenerate_at_any_lambda = False
        for b1_e, cg_e in zip(b1_sweep, c_genuine_sweep):
            lam = b1_e["lambda_R"]
            if b1_e["degenerate"] or cg_e["degenerate"]:
                degenerate_at_any_lambda = True
                any_collapse = True
                gap_table.append({
                    "lambda_R": lam,
                    "b1_utility": b1_e["normalized_utility"],
                    "c_genuine_utility": cg_e["normalized_utility"],
                    "gap": None,
                    "eligible": False,
                    "degenerate": True,
                })
                continue
            gap = cg_e["normalized_utility"] - b1_e["normalized_utility"]
            eligible = (D > 0) and (gap > delta)
            if D <= 0 or gap <= delta:
                any_collapse = True
            gap_table.append({
                "lambda_R": lam,
                "b1_utility": b1_e["normalized_utility"],
                "c_genuine_utility": cg_e["normalized_utility"],
                "gap": gap,
                "eligible": eligible,
                "degenerate": False,
            })

        verdict = "COLLAPSE" if any_collapse else "STABLE"
        print(f"[phase-c7]   D={D}  b1 (WA={b1_WA}, WR={b1_WR})  "
              f"c_genuine (WA={c_genuine_WA}, WR={c_genuine_WR})  "
              f"verdict={verdict}")

        per_solver_list = []
        for sid in sub_sorted_ids:
            per_solver_list.append({
                "solver_id": sid,
                "ground_truth": sub_ground_truth[sid],
                "b1_decision": b1_preds[sid],
                "c_genuine_decision": c_genuine_preds[sid],
            })

        per_condition_results.append({
            "condition_id": cname,
            "n_solvers": len(sub_sorted_ids),
            "n_quotient": n_quotient,
            "solver_ids": sub_sorted_ids,
            "quotient": [
                {
                    "member_probes": c["member_probes"],
                    "representative_probe_id": c["representative_probe_id"],
                    "probe_family": c["probe_family"],
                }
                for c in quotient
            ],
            "b1_aggregate": {"wrong_accepts": b1_WA, "wrong_rejects": b1_WR},
            "c_genuine_aggregate": {"wrong_accepts": c_genuine_WA, "wrong_rejects": c_genuine_WR},
            "D": D,
            "gap_table": gap_table,
            "verdict": verdict,
            "degenerate_at_any_lambda": degenerate_at_any_lambda,
            "per_solver": per_solver_list,
        })

    p0_verdict = per_condition_results[0]["verdict"]
    other_verdicts = [r["verdict"] for r in per_condition_results[1:]]
    if p0_verdict == "COLLAPSE":
        rq_c7_verdict = "NEGATIVE"
    elif all(v == "STABLE" for v in other_verdicts):
        rq_c7_verdict = "POSITIVE"
    else:
        rq_c7_verdict = "MIXED"

    print(f"[phase-c7] RQ-C7 verdict: {rq_c7_verdict}")
    print(f"[phase-c7] per-condition: P0={p0_verdict}, "
          f"others={','.join(other_verdicts)}")

    output = {
        "population": POPULATION_ID,
        "n_solvers": n_solvers,
        "spec_commit": spec_commit,
        "freeze_commit": C7_FREEZE_COMMIT,
        "family3_probe_ids": FAMILY3_PROBE_IDS,
        "b1_aggregate_full": {
            "wrong_accepts": expected_b1["wrong_accepts"],
            "wrong_rejects": expected_b1["wrong_rejects"],
        },
        "per_condition": per_condition_results,
        "rq_c7_verdict": rq_c7_verdict,
        "falsification": {
            "verdict": rq_c7_verdict,
            "delta": delta,
            "p0_verdict": p0_verdict,
            "other_verdicts": other_verdicts,
            "epistemological_constraint": "A POSITIVE C-7 result does not establish that the signal is solver-internal. The H1/H2 ambiguity is not resolved by this phase.",
        },
    }

    write_gated_artifact(OUTPUT_PATH, output, "A15", "ARTIFACT_WRITE", ("C-7",))
    print(f"[phase-c7] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
