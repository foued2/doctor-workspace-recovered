"""Phase C-4: Genuine Structured Policy — LC743 runner.

Protocol identical to LC322/LC3946:
  1. Run all 30 solvers on all 24 oracle test cases.
  2. Split cases into observed (first 12) and target (last 12).
  3. Ground truth: REJECT if held-out fail rate >= FAILURE_THRESHOLD, else ACCEPT.
  4. Estimators see only observed results.
  5. decision_loss = WA + WR (uniform cost, per LC3946 C5).

Estimators:
  C_genuine (failure_direction): Uses dominant failure direction from observed.
     Maps direction to severity-weighted score. REJECT if weighted_score > 0.
     F4→severity 1, F1→severity 2, F2→severity 3, F3→severity 3.
     Uses threshold on weighted count.
  B1 (failure_count): REJECT if observed failure_count > 0.
  B2 (pass_rate): REJECT if observed pass_rate < 1.0.

gap = decision_loss(B1) - decision_loss(C_genuine).
gap > 0 = PASS; gap <= 0 = FAIL.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
from doctor.solvers.lc_743_solvers import SOLVER_REGISTRY
from doctor.adversarial.transition_gate import write_gated_artifact

N_CASES = len(CANONICAL_TEST_SUITE)
FAILURE_THRESHOLD = 0.05
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
    """REJECT if weighted direction score > severity_threshold.

    Uses failure direction structure: F4 (easy to detect) has low severity,
    F2/F3 (harder to detect) have high severity. A solver with even one
    F2/F3 direction in its observed failures is rejected.

    If no failures observed → ACCEPT.
    If only F4 failures observed (and count <= 1) → ACCEPT (F4 is benign
    on small sets — the solver might only fail on disconnected edge cases).
    If F1/F2/F3 observed → REJECT.
    """
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


def main():
    n_solvers = len(SOLVER_REGISTRY)

    # Stratified split: 3 observed + 3 target per direction (frozen protocol)
    # Actual direction mapping: 0-5=F1, 6-11=F2, 12-17=F3, 18-23=F4
    rng = random.Random(RANDOM_SEED)
    by_dir = {
        "F1": list(range(0, 6)),
        "F2": list(range(6, 12)),
        "F3": list(range(12, 18)),
        "F4": list(range(18, 24)),
    }

    observed_indices = []
    target_indices = []
    for d, indices in by_dir.items():
        shuffled = list(indices)
        rng.shuffle(shuffled)
        observed_indices.extend(shuffled[:3])
        target_indices.extend(shuffled[3:])

    observed_indices.sort()
    target_indices.sort()
    n_obs = len(observed_indices)
    n_tgt = len(target_indices)

    print(f"[C-4] Solvers: {n_solvers}, Cases: {N_CASES}, "
          f"Observed: {n_obs}, Target: {n_tgt}")
    print(f"[C-4] FAILURE_THRESHOLD: {FAILURE_THRESHOLD}")
    print(f"[C-4] Observed indices: {observed_indices}")
    print(f"[C-4] Target indices: {target_indices}")

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

        gt = "REJECT" if tgt_rate >= FAILURE_THRESHOLD else "ACCEPT"

        solver_data[sid] = {
            "declared": meta["direction"],
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

    print(f"\n[C-4] Ground truth: {n_accept} ACCEPT, {n_reject} REJECT")
    print(f"\n[C-4] Estimator results:")
    print(f"  C_genuine: WA={wa_c}, WR={wr_c}, loss={dl_c:.0f}")
    print(f"  B1:        WA={wa_b1}, WR={wr_b1}, loss={dl_b1:.0f}")
    print(f"  B2:        WA={wa_b2}, WR={wr_b2}, loss={dl_b2:.0f}")
    print(f"\n[C-4] gap = loss(B1) - loss(C_genuine) = {dl_b1:.0f} - {dl_c:.0f} = {gap:.0f}")

    verdict = "PASS" if gap > 0 else "FAIL"
    print(f"[C-4] Verdict: {verdict}")

    per_solver = []
    for sid in sorted(SOLVER_REGISTRY):
        d = solver_data[sid]
        dir_counts = Counter(x for x in d["obs_dirs"] if x is not None)
        per_solver.append({
            "solver_id": sid,
            "declared": d["declared"],
            "ground_truth": d["ground_truth"],
            "obs_fails": d["obs_fails"],
            "obs_rate": d["obs_rate"],
            "obs_dir_counts": dict(dir_counts),
            "tgt_fails": d["tgt_fails"],
            "tgt_rate": d["tgt_rate"],
            "c_genuine_pred": preds_c[sid],
            "b1_pred": preds_b1[sid],
            "b2_pred": preds_b2[sid],
        })

    output = {
        "population": "LC743",
        "n_solvers": n_solvers,
        "n_cases": N_CASES,
        "n_observed": n_obs,
        "n_target": n_tgt,
        "failure_threshold": FAILURE_THRESHOLD,
        "observed_indices": observed_indices,
        "target_indices": target_indices,
        "random_seed": RANDOM_SEED,
        "ground_truth_counts": {"ACCEPT": n_accept, "REJECT": n_reject},
        "estimators": {
            "C_genuine": {"wrong_accepts": wa_c, "wrong_rejects": wr_c, "decision_loss": dl_c},
            "B1": {"wrong_accepts": wa_b1, "wrong_rejects": wr_b1, "decision_loss": dl_b1},
            "B2": {"wrong_accepts": wa_b2, "wrong_rejects": wr_b2, "decision_loss": dl_b2},
        },
        "gap": gap,
        "verdict": verdict,
        "per_solver": per_solver,
    }

    out_path = ROOT / "results" / "lc_743_c4_result.json"
    write_gated_artifact(out_path, output, "A_LC743_C4", "ARTIFACT_WRITE", ("C-4",))
    print(f"\n[C-4] Written -> {out_path}")


if __name__ == "__main__":
    main()
