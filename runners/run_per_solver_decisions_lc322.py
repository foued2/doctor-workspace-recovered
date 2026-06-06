# runners/run_per_solver_decisions_lc322.py
# Phase C-3a: Per-Solver Decision Persistence — LC322 runner
#
# Re-runs the 8 estimators on the LC322 population with per-solver decision
# logging. Verifies aggregate consistency with stored (WA, WR) from
# data/midweather_fingerprint_lc322.json. Writes per-solver decisions to
# data/midweather_fingerprint_lc322_per_solver.json.
#
# Does NOT modify the existing data file.
# Does NOT add new estimators or probes.
# Hard-stop on aggregate inconsistency (per C-3a spec §8).

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.problem_class_config import get_problem_class_config
from doctor.identity_resolution import check_aggregate_consistency
from runners.run_midweather_fingerprint_lc322 import (
    apply_estimator,
    compute_ground_truth,
    execute_solvers,
)

POPULATION_ID          = "LC322"
C3A_FREEZE_PATH        = ROOT / "PHASE_C3A_FREEZE.json"
DATA_PATH              = ROOT / "data" / "midweather_fingerprint_lc322.json"
FINGERPRINT_FREEZE     = ROOT / "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"
PROBE_INDEX_PATH       = ROOT / "data" / "midweather_fingerprint_lc322_probe_index.json"
SEVAL_MANIFEST_PATH    = ROOT / "data" / "midweather_fingerprint_lc322_seval_manifest.json"
OUTPUT_PATH            = ROOT / "data" / "midweather_fingerprint_lc322_per_solver.json"

C3A_FREEZE_COMMIT = "a6c97bc"


def main() -> None:
    c3a_freeze = json.loads(C3A_FREEZE_PATH.read_text(encoding="utf-8"))
    spec_commit    = c3a_freeze["spec_commit"]
    c1_freeze      = c3a_freeze["cost_function_inherited_from_c1"]["c1_freeze_commit"]
    estimator_list = c3a_freeze["estimators"]

    print(f"[phase-c3a] population={POPULATION_ID}")
    print(f"[phase-c3a] spec_commit={spec_commit}  freeze_commit={C3A_FREEZE_COMMIT}")
    print(f"[phase-c3a] c1_freeze_commit={c1_freeze}")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    pgt = data["per_solver_ground_truth"]
    sorted_ids = sorted(pgt.keys())
    ground_truth = [pgt[sid]["truth_label"] for sid in sorted_ids]
    n_solvers = len(sorted_ids)

    expected = {
        e["estimator"]: {
            "wrong_accepts": int(e["wrong_accepts"]),
            "wrong_rejects": int(e["wrong_rejects"]),
        }
        for e in data["estimator_table"]
    }

    missing = [e for e in estimator_list if e not in expected]
    if missing:
        raise KeyError(f"Estimators in freeze but absent from data: {missing}")

    print(f"[phase-c3a] solvers={n_solvers}  "
          f"accept={ground_truth.count('ACCEPT')}  reject={ground_truth.count('REJECT')}")

    freeze = json.loads(FINGERPRINT_FREEZE.read_text(encoding="utf-8"))
    probe_index = json.loads(PROBE_INDEX_PATH.read_text(encoding="utf-8"))
    seval_manifest = json.loads(SEVAL_MANIFEST_PATH.read_text(encoding="utf-8"))

    config = get_problem_class_config("lc322")
    observed_ids = freeze["observation_budget"]["observed_probe_ids"]
    target_ids = freeze["observation_budget"]["target_probe_ids"]
    failure_threshold = freeze["decision_spec"]["failure_threshold"]

    pass_results = execute_solvers(seval_manifest, probe_index, config)
    ground = compute_ground_truth(pass_results, target_ids, failure_threshold)

    per_solver_decisions: dict[str, dict[str, str]] = {}
    for est in estimator_list:
        policy = config.estimator_policies[est]
        preds = apply_estimator(policy, pass_results, observed_ids, probe_index)

        check_aggregate_consistency(
            [preds[sid] for sid in sorted_ids],
            ground_truth,
            expected_wrong_accepts=expected[est]["wrong_accepts"],
            expected_wrong_rejects=expected[est]["wrong_rejects"],
            estimator_name=est,
            population_id=POPULATION_ID,
        )
        print(f"[phase-c3a]   {est}: consistent "
              f"(WA={expected[est]['wrong_accepts']}, WR={expected[est]['wrong_rejects']})")

        per_solver_decisions[est] = preds

    per_solver_list = []
    for i, sid in enumerate(sorted_ids):
        per_solver_list.append({
            "solver_id": sid,
            "ground_truth": ground_truth[i],
            "decisions": {est: per_solver_decisions[est][sid] for est in estimator_list},
        })

    output = {
        "population": POPULATION_ID,
        "n_solvers": n_solvers,
        "spec_commit": spec_commit,
        "freeze_commit": C3A_FREEZE_COMMIT,
        "c1_freeze_commit": c1_freeze,
        "per_solver": per_solver_list,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"[phase-c3a] written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
