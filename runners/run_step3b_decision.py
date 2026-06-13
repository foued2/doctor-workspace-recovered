"""STEP 3B — Decision Perturbation Test.

Hard invariants (fixed):
  - Solver population: LC756(R2) set only
  - Estimator definitions: C_genuine, B1, B2 only
  - Oracle implementation: LC743 oracle unchanged
  - Canonical test suite baseline: 24-case reference set
  - Sampling split: frozen (seed=42, 3 obs/dir)

Only decision function changes:
  - FAILURE_THRESHOLD: 0.01, 0.05, 0.10, 0.20, 0.50

Output per condition: agreement matrix, gap value, verdict stability indicator.
No narrative synthesis.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
from doctor.solvers.lc756.lc_756_solvers import SOLVER_REGISTRY

N_CASES = len(CANONICAL_TEST_SUITE)
RANDOM_SEED = 42


def check_connected(times, n, k):
    graph = defaultdict(list)
    for u, v, _w in times:
        graph[u].append(v)
    reachable = set()
    queue = deque([k])
    while queue:
        u = queue.popleft()
        if u in reachable:
            continue
        reachable.add(u)
        for v in graph[u]:
            if v not in reachable:
                queue.append(v)
    return len(reachable) == n


def classify_failure(solver_output, oracle_output, times, n, k):
    if solver_output == oracle_output:
        return None
    connected = check_connected(times, n, k)
    if not connected and isinstance(solver_output, (int, float)) and solver_output != -1:
        return "F4"
    if connected and solver_output == -1:
        return "F1"
    if connected and isinstance(solver_output, (int, float)) and isinstance(oracle_output, (int, float)):
        if solver_output > oracle_output:
            return "F2"
    if connected and isinstance(solver_output, (int, float)) and isinstance(oracle_output, (int, float)):
        if solver_output < oracle_output:
            return "F3"
    return "F3"


SEVERITY = {"F4": 1, "F1": 2, "F2": 3, "F3": 3}


def estimator_c_genuine(obs_failure_dirs, obs_failure_count):
    non_none = [d for d in obs_failure_dirs if d is not None]
    if not non_none:
        return "ACCEPT"
    counts = Counter(non_none)
    has_f2_or_f3 = any(d in counts for d in ("F2", "F3"))
    if has_f2_or_f3:
        return "REJECT"
    if obs_failure_count <= 1:
        return "ACCEPT"
    return "REJECT"


def estimator_b1(obs_failure_count):
    return "REJECT" if obs_failure_count > 0 else "ACCEPT"


def estimator_b2(obs_pass_rate):
    return "REJECT" if obs_pass_rate < 1.0 else "ACCEPT"


def make_frozen_split():
    """Frozen split: seed=42, 3 obs/dir."""
    rng = random.Random(RANDOM_SEED)
    by_dir = {
        "F1": list(range(0, 6)),
        "F2": list(range(6, 12)),
        "F3": list(range(12, 18)),
        "F4": list(range(18, 24)),
    }
    observed = []
    target = []
    for d, indices in by_dir.items():
        shuffled = list(indices)
        rng.shuffle(shuffled)
        observed.extend(shuffled[:3])
        target.extend(shuffled[3:])
    observed.sort()
    target.sort()
    return observed, target


def run_single(threshold, observed_indices, target_indices):
    """Run C-4 evaluation for a single threshold. Returns structured result."""
    n_obs = len(observed_indices)
    n_tgt = len(target_indices)
    n_solvers = len(SOLVER_REGISTRY)

    solver_data = {}
    for sid, meta in SOLVER_REGISTRY.items():
        fn = meta["fn"]
        all_results = []
        for case in CANONICAL_TEST_SUITE:
            try:
                result = fn(case["times"], case["n"], case["k"])
            except Exception:
                result = None
            all_results.append(result)

        obs_dirs = []
        obs_fails = 0
        for i in observed_indices:
            case = CANONICAL_TEST_SUITE[i]
            result = all_results[i]
            if result != case["expected"]:
                obs_fails += 1
                d = classify_failure(result, case["expected"], case["times"], case["n"], case["k"])
                obs_dirs.append(d)

        tgt_fails = 0
        for i in target_indices:
            case = CANONICAL_TEST_SUITE[i]
            result = all_results[i]
            if result != case["expected"]:
                tgt_fails += 1

        tgt_rate = tgt_fails / n_tgt if n_tgt else 0.0
        obs_rate = (n_obs - obs_fails) / n_obs if n_obs else 0.0
        gt = "REJECT" if tgt_rate >= threshold else "ACCEPT"

        solver_data[sid] = {
            "obs_fails": obs_fails,
            "obs_rate": obs_rate,
            "obs_dirs": obs_dirs,
            "tgt_fails": tgt_fails,
            "tgt_rate": tgt_rate,
            "ground_truth": gt,
        }

    preds_c = {}
    preds_b1 = {}
    preds_b2 = {}
    for sid in SOLVER_REGISTRY:
        d = solver_data[sid]
        preds_c[sid] = estimator_c_genuine(d["obs_dirs"], d["obs_fails"])
        preds_b1[sid] = estimator_b1(d["obs_fails"])
        preds_b2[sid] = estimator_b2(d["obs_rate"])

    gt = {sid: solver_data[sid]["ground_truth"] for sid in SOLVER_REGISTRY}

    def compute_loss(preds):
        wa = wr = 0
        for sid, pred in preds.items():
            truth = gt[sid]
            if pred == "ACCEPT" and truth == "REJECT":
                wa += 1
            elif pred == "REJECT" and truth == "ACCEPT":
                wr += 1
        return wa, wr, float(wa + wr)

    wa_c, wr_c, dl_c = compute_loss(preds_c)
    wa_b1, wr_b1, dl_b1 = compute_loss(preds_b1)
    wa_b2, wr_b2, dl_b2 = compute_loss(preds_b2)
    gap = dl_b1 - dl_c

    n_accept = sum(1 for v in gt.values() if v == "ACCEPT")
    n_reject = sum(1 for v in gt.values() if v == "REJECT")

    verdict = "PASS" if gap > 0 else "FAIL"

    return {
        "threshold": threshold,
        "observed_indices": observed_indices,
        "target_indices": target_indices,
        "n_obs": n_obs,
        "n_tgt": n_tgt,
        "ground_truth_counts": {"ACCEPT": n_accept, "REJECT": n_reject},
        "estimators": {
            "C_genuine": {"wrong_accepts": wa_c, "wrong_rejects": wr_c, "decision_loss": dl_c},
            "B1": {"wrong_accepts": wa_b1, "wrong_rejects": wr_b1, "decision_loss": dl_b1},
            "B2": {"wrong_accepts": wa_b2, "wrong_rejects": wr_b2, "decision_loss": dl_b2},
        },
        "gap": gap,
        "verdict": verdict,
        "per_solver_preds": {
            sid: {"c": preds_c[sid], "b1": preds_b1[sid], "b2": preds_b2[sid]}
            for sid in sorted(SOLVER_REGISTRY)
        },
    }


def main():
    observed_indices, target_indices = make_frozen_split()

    thresholds = [0.01, 0.05, 0.10, 0.20, 0.50]
    results = []

    for t in thresholds:
        r = run_single(t, observed_indices, target_indices)
        results.append(r)

    # Verdict stability
    verdicts = [r["verdict"] for r in results]
    gaps = [r["gap"] for r in results]
    unique_verdicts = set(verdicts)

    # Agreement matrix: per solver, per threshold, what did each estimator predict?
    agreement_matrix = {}
    for sid in sorted(SOLVER_REGISTRY):
        row = {}
        for r in results:
            t = r["threshold"]
            row[t] = r["per_solver_preds"][sid]
        agreement_matrix[sid] = row

    output = {
        "phase": "3B_decision_perturbation",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "estimators": ["C_genuine", "B1", "B2"],
            "oracle": "LC743",
            "canonical_test_suite": "24-case",
            "frozen_split": {"seed": RANDOM_SEED, "observed": observed_indices, "target": target_indices},
        },
        "conditions": [
            {
                "threshold": r["threshold"],
                "ground_truth_counts": r["ground_truth_counts"],
                "estimators": r["estimators"],
                "gap": r["gap"],
                "verdict": r["verdict"],
            }
            for r in results
        ],
        "verdict_stability": {
            "unique_verdicts": list(unique_verdicts),
            "stable": len(unique_verdicts) == 1,
            "verdicts": verdicts,
            "gaps": gaps,
        },
        "agreement_matrix": agreement_matrix,
    }

    out_path = ROOT / "results" / "step3b_decision.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output["verdict_stability"], indent=2))


if __name__ == "__main__":
    main()
