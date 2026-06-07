# runners/run_c5_collapse_lc3946.py
# Phase LC3946-C5: Collapse Analysis (Distribution Shift) — LC3946 runner
#
# Re-runs B1 and C_genuine on the unperturbed LC3946 (aggregate-consistency
# check), then applies each of the 11 pre-declared perturbations and
# computes per-perturbation (B1_loss, C_genuine_loss, gap) triples. Applies
# the LC3946-C5 falsification criterion.
#
# Per the LC3946-C5 spec (Step 4):
# - Reuses apply_estimator, compute_ground_truth, execute_solvers from
#   runners/run_midweather_fingerprint_lc322.py
# - Reuses _fail_count_policy and _c_genuine_policy from
#   doctor.adversarial.problem_class_config (no duplication)
# - Reuses threshold_shift, solver_subsample, family_knockout, compute_gap,
#   falsification_criterion, aggregate_consistency_check from
#   doctor.adversarial.lc3946_collapse_perturbations
# - Does NOT modify existing data files (writes only data/c5_collapse_lc3946.json)
# - Does NOT introduce new probes or solver packs
# - Hard-stop on aggregate inconsistency on unperturbed LC3946
#
# Cost model: uniform (wrong_accept=1, wrong_reject=1), no lambda sweep.
# Survival threshold: gap > 0 strictly (per Foued's Point 1 decision).

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.lc3946_collapse_perturbations import (
    P1A_THRESHOLD,
    P2A_INDICES,
    P2B_INDICES,
    P2C_INDICES,
    P3_ROTATION_ORDER,
    aggregate_consistency_check,
    compute_gap,
    cross_population_reference,
    family_knockout,
    falsification_criterion,
    solver_subsample,
    threshold_shift,
)
from doctor.adversarial.problem_class_config import get_problem_class_config
from runners.run_midweather_fingerprint_lc322 import (
    apply_estimator,
    compute_ground_truth,
    execute_solvers,
)

POPULATION_ID = "LC3946"
C5_FREEZE_PATH = ROOT / "PHASE_LC3946_C5_FREEZE.json"
LC3946_FREEZE_PATH = ROOT / "MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json"
PROBE_INDEX_PATH = ROOT / "data" / "midweather_fingerprint_lc3946_probe_index.json"
SEVAL_MANIFEST_PATH = ROOT / "data" / "midweather_fingerprint_lc3946_seval_manifest.json"
LC3946_DATA_PATH = ROOT / "data" / "midweather_fingerprint_lc3946.json"
OUTPUT_PATH = ROOT / "data" / "c5_collapse_lc3946.json"


def _compute_wa_wr_loss(
    preds: dict[str, str],
    ground: dict[str, dict],
) -> dict[str, int | float]:
    """Compute (wrong_accepts, wrong_rejects, decision_loss) for one estimator."""
    wa = 0
    wr = 0
    for sid, pred in preds.items():
        truth = ground[sid]["truth_label"]
        if pred == "ACCEPT" and truth == "REJECT":
            wa += 1
        elif pred == "REJECT" and truth == "ACCEPT":
            wr += 1
    return {"wrong_accepts": wa, "wrong_rejects": wr, "decision_loss": float(wa + wr)}


def _run_perturbation(
    perturbation_id: str,
    pass_results: dict[str, dict[str, bool]],
    observed_ids: list[str],
    target_ids: list[str],
    failure_threshold: float,
    config,
    probe_index: dict,
    b1_policy,
    c_genuine_policy,
    extra: dict | None = None,
) -> dict:
    """Run B1 and C_genuine on a (possibly perturbed) population.

    Args:
        perturbation_id: the perturbation label (e.g. "P1b", "P2a", "P3e").
        pass_results: pass_results dict (full or filtered).
        observed_ids: observed probe_ids (full or reduced).
        target_ids: target probe_ids (full or reduced).
        failure_threshold: failure threshold (baseline or shifted).
        config: ProblemClassConfig.
        probe_index: probe_index dict (for fingerprint_context).
        b1_policy: B1 decision policy.
        c_genuine_policy: C_genuine decision policy.
        extra: optional metadata dict (e.g. family_knocked_out, n_probes_removed).

    Returns:
        dict with perturbation_id, n_solvers, n_probes_observed, n_probes_target,
        failure_threshold, b1_aggregate, c_genuine_aggregate, gap, survives.
    """
    ground = threshold_shift(pass_results, target_ids, failure_threshold)

    b1_preds = apply_estimator(b1_policy, pass_results, observed_ids, probe_index)
    cg_preds = apply_estimator(c_genuine_policy, pass_results, observed_ids, probe_index)

    b1_agg = _compute_wa_wr_loss(b1_preds, ground)
    cg_agg = _compute_wa_wr_loss(cg_preds, ground)
    gap = compute_gap(b1_agg["decision_loss"], cg_agg["decision_loss"])

    return {
        "perturbation_id": perturbation_id,
        "n_solvers": len(pass_results),
        "n_probes_observed": len(observed_ids),
        "n_probes_target": len(target_ids),
        "failure_threshold": failure_threshold,
        "b1_aggregate": b1_agg,
        "c_genuine_aggregate": cg_agg,
        "gap": gap,
        "survives": gap > 0,
        **(extra or {}),
    }


def main() -> None:
    print(f"[phase-lc3946-c5] population={POPULATION_ID}")
    print(f"[phase-lc3946-c5] reading freeze: {C5_FREEZE_PATH.name}")

    c5_freeze = json.loads(C5_FREEZE_PATH.read_text(encoding="utf-8"))
    lc3946_freeze = json.loads(LC3946_FREEZE_PATH.read_text(encoding="utf-8"))
    probe_index = json.loads(PROBE_INDEX_PATH.read_text(encoding="utf-8"))
    seval_manifest = json.loads(SEVAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    lc3946_data = json.loads(LC3946_DATA_PATH.read_text(encoding="utf-8"))

    config = get_problem_class_config("lc3946")
    b1_policy = config.estimator_policies["B1_count"]
    c_genuine_policy = config.estimator_policies["C_genuine"]

    observed_ids_full = lc3946_freeze["observation_budget"]["observed_probe_ids"]
    target_ids_full = lc3946_freeze["observation_budget"]["target_probe_ids"]

    # Read expected (WA, WR, loss) from the recorded C-4 result
    expected_b1 = None
    expected_cg = None
    for row in lc3946_data["estimator_table"]:
        if row["estimator"] == "B1_count":
            expected_b1 = (int(row["wrong_accepts"]), int(row["wrong_rejects"]), float(row["decision_loss"]))
        elif row["estimator"] == "C_genuine":
            expected_cg = (int(row["wrong_accepts"]), int(row["wrong_rejects"]), float(row["decision_loss"]))
    if expected_b1 is None or expected_cg is None:
        raise KeyError("B1_count or C_genuine not found in lc3946 estimator_table")

    # Re-execute solvers (avoids depending on a sidecar file)
    pass_results_full = execute_solvers(seval_manifest, probe_index, config)
    ground_full = compute_ground_truth(pass_results_full, target_ids_full, P1A_THRESHOLD)

    # ---- Aggregate-consistency check on unperturbed LC3946 ----
    consistent = aggregate_consistency_check(
        pass_results=pass_results_full,
        target_ids=target_ids_full,
        failure_threshold=P1A_THRESHOLD,
        expected_b1_wa_wr_loss=expected_b1,
        expected_c_genuine_wa_wr_loss=expected_cg,
        probe_index=probe_index,
    )
    if not consistent:
        raise RuntimeError(
            f"[phase-lc3946-c5] STOP: aggregate consistency check failed. "
            f"Expected B1={expected_b1}, C_genuine={expected_cg}. "
            f"Re-run on unperturbed LC3946 does not reproduce stored aggregates. "
            f"Surface discrepancy for review per protocol Hard Stop #1."
        )
    print(f"[phase-lc3946-c5] unperturbed aggregate-consistent "
          f"(B1={expected_b1}, C_genuine={expected_cg})")

    perturbations: list[dict] = []

    # ---- P1a: baseline reference (no perturbation) ----
    print("[phase-lc3946-c5] P1a: baseline (threshold=0.05, reference only)")
    p1a = _run_perturbation(
        "P1a", pass_results_full, observed_ids_full, target_ids_full, P1A_THRESHOLD,
        config, probe_index, b1_policy, c_genuine_policy,
        extra={"is_baseline_reference": True},
    )
    perturbations.append(p1a)

    # ---- P1b: threshold = 0.10 ----
    print("[phase-lc3946-c5] P1b: threshold=0.10")
    p1b = _run_perturbation(
        "P1b", pass_results_full, observed_ids_full, target_ids_full, 0.10,
        config, probe_index, b1_policy, c_genuine_policy,
        extra={"perturbation_type": "threshold_shift"},
    )
    perturbations.append(p1b)

    # ---- P1c: threshold = 0.20 ----
    print("[phase-lc3946-c5] P1c: threshold=0.20")
    p1c = _run_perturbation(
        "P1c", pass_results_full, observed_ids_full, target_ids_full, 0.20,
        config, probe_index, b1_policy, c_genuine_policy,
        extra={"perturbation_type": "threshold_shift"},
    )
    perturbations.append(p1c)

    # ---- P2: subsamples (3 fixed draws of 25) ----
    sorted_ids = sorted(pass_results_full.keys())
    p2_subsamples = [
        ("P2a", P2A_INDICES),
        ("P2b", P2B_INDICES),
        ("P2c", P2C_INDICES),
    ]
    for pid, indices in p2_subsamples:
        sub_ids = [sorted_ids[i] for i in indices]
        sub_pass = {sid: pass_results_full[sid] for sid in sub_ids}
        print(f"[phase-lc3946-c5] {pid}: subsample {len(sub_ids)} solvers")
        result = _run_perturbation(
            pid, sub_pass, observed_ids_full, target_ids_full, P1A_THRESHOLD,
            config, probe_index, b1_policy, c_genuine_policy,
            extra={"perturbation_type": "subsample", "indices": indices, "n_dropped": 30 - len(sub_ids)},
        )
        perturbations.append(result)

    # ---- P3: probe family knockouts (6 rotations) ----
    for i, fam in enumerate(P3_ROTATION_ORDER):
        pid = f"P3{chr(ord('a') + i)}"
        print(f"[phase-lc3946-c5] {pid}: knockout family '{fam}'")
        obs_reduced, target_reduced = family_knockout(
            observed_ids_full, target_ids_full, fam, probe_index,
        )
        # Pass_results also need to be filtered to the reduced probe sets,
        # so B1 and C_genuine see the same per-solver per-probe grid.
        pass_reduced = {
            sid: {pid: pf for pid, pf in probes.items() if pid in set(obs_reduced) | set(target_reduced)}
            for sid, probes in pass_results_full.items()
        }
        n_probes_removed_obs = len(observed_ids_full) - len(obs_reduced)
        n_probes_removed_target = len(target_ids_full) - len(target_reduced)
        result = _run_perturbation(
            pid, pass_reduced, obs_reduced, target_reduced, P1A_THRESHOLD,
            config, probe_index, b1_policy, c_genuine_policy,
            extra={
                "perturbation_type": "family_knockout",
                "family_knocked_out": fam,
                "n_probes_removed_observed": n_probes_removed_obs,
                "n_probes_removed_target": n_probes_removed_target,
            },
        )
        perturbations.append(result)

    # ---- P4: cross-population anchor (LC322 C-4 result, read-only) ----
    p4_anchor = cross_population_reference()
    p4_record = {
        "perturbation_id": "P4",
        "perturbation_type": "cross_population_anchor",
        "lc322_c4_gap": p4_anchor["lc322_c4_gap"],
        "lc322_c4_signal_family": p4_anchor["lc322_c4_signal_family"],
        "lc322_c5_verdict": p4_anchor["lc322_c5_verdict"],
        "lc3946_perturbation_applied": p4_anchor["lc3946_perturbation_applied"],
        "source": "data/midweather_fingerprint_lc322.json + phase-c5-results tag (d1435a3)",
    }
    perturbations.append(p4_record)
    print(f"[phase-lc3946-c5] P4: cross-population anchor (LC322 C-4 gap={p4_anchor['lc322_c4_gap']})")

    # ---- Falsification criterion ----
    # Per-perturbation gaps for the 11 actual perturbations (P1a is reference)
    p_gaps = {p["perturbation_id"]: p.get("gap", 0.0) for p in perturbations if p["perturbation_id"] != "P4"}
    # Ensure exactly 11 perturbation conditions (P1a + P1b + P1c + P2a + P2b + P2c + P3a..P3f)
    assert len(p_gaps) == 11, f"Expected 11 perturbation conditions, got {len(p_gaps)}"
    overall = falsification_criterion(p_gaps)

    n_survived = sum(1 for pid, gap in p_gaps.items() if gap > 0)
    n_collapse = sum(1 for pid, gap in p_gaps.items() if gap <= 0)
    print(f"[phase-lc3946-c5] falsification verdict: {overall}")
    print(f"[phase-lc3946-c5] per-perturbation: {n_survived} survive, {n_collapse} collapse, total=11")

    # ---- Per-perturbation summary table ----
    print()
    print(f"{'pert':<8} {'n_sol':>5} {'n_obs':>5} {'thr':>5} {'B1_loss':>8} {'CG_loss':>8} {'gap':>6} {'survives':>9}")
    for p in perturbations:
        if p["perturbation_id"] == "P4":
            continue
        print(f"{p['perturbation_id']:<8} {p['n_solvers']:>5} {p['n_probes_observed']:>5} "
              f"{p['failure_threshold']:>5.2f} {p['b1_aggregate']['decision_loss']:>8.1f} "
              f"{p['c_genuine_aggregate']['decision_loss']:>8.1f} {p['gap']:>6.1f} "
              f"{'yes' if p['survives'] else 'NO':>9}")

    output = {
        "population": POPULATION_ID,
        "phase": "LC3946-C5",
        "freeze_path": str(C5_FREEZE_PATH.relative_to(ROOT)),
        "lc3946_freeze_path": str(LC3946_FREEZE_PATH.relative_to(ROOT)),
        "cost_model": "uniform (no lambda sweep)",
        "survival_threshold": "gap > 0 strictly",
        "aggregate_consistency_check": {
            "expected_b1": list(expected_b1),
            "expected_c_genuine": list(expected_cg),
            "result": "consistent",
        },
        "perturbations": perturbations,
        "falsification": {
            "verdict": overall,
            "n_survived": n_survived,
            "n_collapse": n_collapse,
            "n_total": 11,
            "per_perturbation_gaps": {pid: gap for pid, gap in p_gaps.items()},
        },
        "p4_cross_population_anchor": p4_anchor,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print()
    print(f"[phase-lc3946-c5] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
