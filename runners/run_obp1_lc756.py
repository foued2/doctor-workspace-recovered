"""OBP-1: Oracle Boundary Perturbation Test — LC756.

Protocol:
  1. Freeze the solver population (no changes to solvers, relaxation, or harness).
  2. Perturb the oracle boundary in four orthogonal ways:
     - Threshold sweep: vary the decision threshold across a narrow grid.
     - Probe reweighting: change the weighting of probe families.
     - Leave-one-family-out: remove one probe family at a time.
     - Boundary-noise injection: perturb oracle-side tie-breaking/ranking.
  3. Hold the state space fixed (no changes to problem graph, solver inputs, or relaxation).
  4. Record four outputs per perturbation: gap, verdict, contamination_flag, cluster_stability.
  5. Evaluate by differential response.

Key invariant:
  If boundary perturbations move the verdict without moving solver behavior,
  the evaluator is compressing the system.
  If they do nothing, the collapse is inside the solver dynamics.
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

# Baseline failure threshold
BASELINE_FAILURE_THRESHOLD = 0.05


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


def compute_loss(preds, gt):
    wa = wr = 0
    for sid, pred in preds.items():
        truth = gt[sid]
        if pred == "ACCEPT" and truth == "REJECT":
            wa += 1
        elif pred == "REJECT" and truth == "ACCEPT":
            wr += 1
    return wa, wr, float(wa + wr)


def run_frozen_protocol(observed_indices, target_indices, failure_threshold=BASELINE_FAILURE_THRESHOLD):
    """Run the frozen protocol and return solver data + ground truth."""
    n_obs = len(observed_indices)
    n_tgt = len(target_indices)

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
        gt = "REJECT" if tgt_rate >= failure_threshold else "ACCEPT"

        solver_data[sid] = {
            "declared": meta["direction"],
            "obs_fails": obs_fails,
            "obs_rate": obs_rate,
            "obs_dirs": obs_dirs,
            "tgt_fails": tgt_fails,
            "tgt_rate": tgt_rate,
            "ground_truth": gt,
            "all_results": all_results,
        }

    gt_map = {sid: solver_data[sid]["ground_truth"] for sid in SOLVER_REGISTRY}
    return solver_data, gt_map


def get_solver_outputs(solver_data):
    """Extract raw solver output vectors for cluster stability."""
    return {sid: solver_data[sid]["all_results"] for sid in solver_data}


def compute_cluster_stability(outputs_a, outputs_b):
    """Compute Jaccard similarity between two sets of solver output patterns."""
    patterns_a = set()
    patterns_b = set()
    for sid in outputs_a:
        patterns_a.add(tuple(outputs_a[sid]))
    for sid in outputs_b:
        patterns_b.add(tuple(outputs_b[sid]))
    if not patterns_a and not patterns_b:
        return 1.0
    if not patterns_a or not patterns_b:
        return 0.0
    intersection = patterns_a & patterns_b
    union = patterns_a | patterns_b
    return len(intersection) / len(union)


# ============================================================================
# Perturbation 1: Threshold Sweep
# ============================================================================

def threshold_sweep(observed_indices, target_indices, thresholds):
    """Vary the failure threshold across a grid."""
    results = []
    baseline_data, baseline_gt = run_frozen_protocol(observed_indices, target_indices)
    baseline_outputs = get_solver_outputs(baseline_data)

    for thresh in thresholds:
        data, gt = run_frozen_protocol(observed_indices, target_indices, failure_threshold=thresh)

        preds_c = {}
        preds_b1 = {}
        for sid in SOLVER_REGISTRY:
            d = data[sid]
            preds_c[sid] = estimator_c_genuine(d["obs_dirs"], d["obs_fails"])
            preds_b1[sid] = estimator_b1(d["obs_fails"])

        wa_c, wr_c, dl_c = compute_loss(preds_c, gt)
        wa_b1, wr_b1, dl_b1 = compute_loss(preds_b1, gt)
        gap = dl_b1 - dl_c
        verdict = "PASS" if gap > 0 else "FAIL"

        # Check contamination: did any solver's ground truth label flip?
        contamination = any(
            data[sid]["ground_truth"] != baseline_data[sid]["ground_truth"]
            for sid in SOLVER_REGISTRY
        )

        outputs = get_solver_outputs(data)
        stability = compute_cluster_stability(baseline_outputs, outputs)

        results.append({
            "perturbation_type": "threshold_sweep",
            "parameter": {"failure_threshold": thresh},
            "gap": gap,
            "verdict": verdict,
            "contamination_flag": contamination,
            "cluster_stability": stability,
            "decision_loss_c": dl_c,
            "decision_loss_b1": dl_b1,
        })

    return results


# ============================================================================
# Perturbation 2: Probe Reweighting
# ============================================================================

def probe_reweighting(observed_indices, target_indices, weights_per_direction):
    """Change the weighting of probe families while keeping raw cases the same.

    Weights are applied by adjusting the contribution of each direction's
    observed failures to the failure count. A direction with weight 2.0
    counts each failure in that direction as 2 failures.
    """
    results = []
    baseline_data, baseline_gt = run_frozen_protocol(observed_indices, target_indices)
    baseline_outputs = get_solver_outputs(baseline_data)

    for weight_name, weights in weights_per_direction.items():
        # Compute reweighted failure counts
        data, gt = run_frozen_protocol(observed_indices, target_indices)
        preds_c = {}
        preds_b1 = {}

        for sid in SOLVER_REGISTRY:
            d = data[sid]
            # Reweight: count each failure direction according to its weight
            weighted_fails = 0
            for d_name in d["obs_dirs"]:
                if d_name is not None:
                    weighted_fails += weights.get(d_name, 1.0)

            # C_genuine still uses direction structure
            preds_c[sid] = estimator_c_genuine(d["obs_dirs"], d["obs_fails"])

            # B1 uses reweighted count
            preds_b1[sid] = "REJECT" if weighted_fails > 0 else "ACCEPT"

        wa_c, wr_c, dl_c = compute_loss(preds_c, gt)
        wa_b1, wr_b1, dl_b1 = compute_loss(preds_b1, gt)
        gap = dl_b1 - dl_c
        verdict = "PASS" if gap > 0 else "FAIL"

        contamination = any(
            data[sid]["ground_truth"] != baseline_data[sid]["ground_truth"]
            for sid in SOLVER_REGISTRY
        )

        outputs = get_solver_outputs(data)
        stability = compute_cluster_stability(baseline_outputs, outputs)

        results.append({
            "perturbation_type": "probe_reweighting",
            "parameter": {"weights": weight_name, "values": weights},
            "gap": gap,
            "verdict": verdict,
            "contamination_flag": contamination,
            "cluster_stability": stability,
            "decision_loss_c": dl_c,
            "decision_loss_b1": dl_b1,
        })

    return results


# ============================================================================
# Perturbation 3: Leave-One-Family-Out
# ============================================================================

def leave_one_family_out(observed_indices, target_indices):
    """Remove one probe family at a time and re-evaluate."""
    results = []
    baseline_data, baseline_gt = run_frozen_protocol(observed_indices, target_indices)
    baseline_outputs = get_solver_outputs(baseline_data)

    # Direction mapping: 0-5=F1, 6-11=F2, 12-17=F3, 18-23=F4
    direction_ranges = {
        "F1": list(range(0, 6)),
        "F2": list(range(6, 12)),
        "F3": list(range(12, 18)),
        "F4": list(range(18, 24)),
    }

    for leave_out_dir in ["F1", "F2", "F3", "F4"]:
        # Remove all cases of this direction from both observed and target
        leave_out_indices = set(direction_ranges[leave_out_dir])
        new_obs = [i for i in observed_indices if i not in leave_out_indices]
        new_tgt = [i for i in target_indices if i not in leave_out_indices]

        if not new_obs or not new_tgt:
            continue

        data, gt = run_frozen_protocol(new_obs, new_tgt)

        preds_c = {}
        preds_b1 = {}
        for sid in SOLVER_REGISTRY:
            d = data[sid]
            preds_c[sid] = estimator_c_genuine(d["obs_dirs"], d["obs_fails"])
            preds_b1[sid] = estimator_b1(d["obs_fails"])

        wa_c, wr_c, dl_c = compute_loss(preds_c, gt)
        wa_b1, wr_b1, dl_b1 = compute_loss(preds_b1, gt)
        gap = dl_b1 - dl_c
        verdict = "PASS" if gap > 0 else "FAIL"

        contamination = any(
            data[sid]["ground_truth"] != baseline_data[sid]["ground_truth"]
            for sid in SOLVER_REGISTRY
        )

        outputs = get_solver_outputs(data)
        stability = compute_cluster_stability(baseline_outputs, outputs)

        results.append({
            "perturbation_type": "leave_one_family_out",
            "parameter": {"removed_direction": leave_out_dir, "n_obs": len(new_obs), "n_tgt": len(new_tgt)},
            "gap": gap,
            "verdict": verdict,
            "contamination_flag": contamination,
            "cluster_stability": stability,
            "decision_loss_c": dl_c,
            "decision_loss_b1": dl_b1,
        })

    return results


# ============================================================================
# Perturbation 4: Boundary-Noise Injection
# ============================================================================

def boundary_noise_injection(observed_indices, target_indices, noise_configs):
    """Perturb oracle-side tie-breaking or ranking rule.

    This perturbs the comparator/scoring surface, not the solver output.
    We simulate this by adding small random perturbations to the oracle's
    expected output comparison (e.g., allowing ±1 tolerance).
    """
    results = []
    baseline_data, baseline_gt = run_frozen_protocol(observed_indices, target_indices)
    baseline_outputs = get_solver_outputs(baseline_data)

    for config_name, tolerance in noise_configs:
        # Run with tolerance: solver output is "correct" if within tolerance of oracle
        n_obs = len(observed_indices)
        n_tgt = len(target_indices)

        data = {}
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
                expected = case["expected"]
                # Tolerance-based comparison
                if result is not None and expected is not None:
                    if isinstance(result, (int, float)) and isinstance(expected, (int, float)):
                        is_correct = abs(result - expected) <= tolerance
                    else:
                        is_correct = result == expected
                else:
                    is_correct = result == expected

                if not is_correct:
                    obs_fails += 1
                    d = classify_failure(result, expected, case["times"], case["n"], case["k"])
                    obs_dirs.append(d)

            tgt_fails = 0
            for i in target_indices:
                case = CANONICAL_TEST_SUITE[i]
                result = all_results[i]
                expected = case["expected"]
                if result is not None and expected is not None:
                    if isinstance(result, (int, float)) and isinstance(expected, (int, float)):
                        is_correct = abs(result - expected) <= tolerance
                    else:
                        is_correct = result == expected
                else:
                    is_correct = result == expected
                if not is_correct:
                    tgt_fails += 1

            tgt_rate = tgt_fails / n_tgt if n_tgt else 0.0
            obs_rate = (n_obs - obs_fails) / n_obs if n_obs else 0.0
            gt = "REJECT" if tgt_rate >= BASELINE_FAILURE_THRESHOLD else "ACCEPT"

            data[sid] = {
                "declared": meta["direction"],
                "obs_fails": obs_fails,
                "obs_rate": obs_rate,
                "obs_dirs": obs_dirs,
                "tgt_fails": tgt_fails,
                "tgt_rate": tgt_rate,
                "ground_truth": gt,
                "all_results": all_results,
            }

        gt_map = {sid: data[sid]["ground_truth"] for sid in SOLVER_REGISTRY}

        preds_c = {}
        preds_b1 = {}
        for sid in SOLVER_REGISTRY:
            d = data[sid]
            preds_c[sid] = estimator_c_genuine(d["obs_dirs"], d["obs_fails"])
            preds_b1[sid] = estimator_b1(d["obs_fails"])

        wa_c, wr_c, dl_c = compute_loss(preds_c, gt_map)
        wa_b1, wr_b1, dl_b1 = compute_loss(preds_b1, gt_map)
        gap = dl_b1 - dl_c
        verdict = "PASS" if gap > 0 else "FAIL"

        contamination = any(
            data[sid]["ground_truth"] != baseline_data[sid]["ground_truth"]
            for sid in SOLVER_REGISTRY
        )

        outputs = get_solver_outputs(data)
        stability = compute_cluster_stability(baseline_outputs, outputs)

        results.append({
            "perturbation_type": "boundary_noise_injection",
            "parameter": {"config": config_name, "tolerance": tolerance},
            "gap": gap,
            "verdict": verdict,
            "contamination_flag": contamination,
            "cluster_stability": stability,
            "decision_loss_c": dl_c,
            "decision_loss_b1": dl_b1,
        })

    return results


# ============================================================================
# Main
# ============================================================================

def main():
    rng = random.Random(RANDOM_SEED)

    # Stratified split: 3 observed + 3 target per direction (frozen protocol)
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

    print(f"[OBP-1] LC756 Oracle Boundary Perturbation Test")
    print(f"[OBP-1] Solvers: {len(SOLVER_REGISTRY)}, Cases: {N_CASES}")
    print(f"[OBP-1] Observed: {len(observed_indices)}, Target: {len(target_indices)}")
    print(f"[OBP-1] Observed indices: {observed_indices}")
    print(f"[OBP-1] Target indices: {target_indices}")

    # Control: baseline frozen protocol
    baseline_data, baseline_gt = run_frozen_protocol(observed_indices, target_indices)
    preds_c_base = {}
    preds_b1_base = {}
    for sid in SOLVER_REGISTRY:
        d = baseline_data[sid]
        preds_c_base[sid] = estimator_c_genuine(d["obs_dirs"], d["obs_fails"])
        preds_b1_base[sid] = estimator_b1(d["obs_fails"])

    wa_c_base, wr_c_base, dl_c_base = compute_loss(preds_c_base, baseline_gt)
    wa_b1_base, wr_b1_base, dl_b1_base = compute_loss(preds_b1_base, baseline_gt)
    gap_base = dl_b1_base - dl_c_base
    verdict_base = "PASS" if gap_base > 0 else "FAIL"

    n_accept = sum(1 for v in baseline_gt.values() if v == "ACCEPT")
    n_reject = sum(1 for v in baseline_gt.values() if v == "REJECT")

    print(f"\n[OBP-1] Control (baseline):")
    print(f"  Ground truth: {n_accept} ACCEPT, {n_reject} REJECT")
    print(f"  C_genuine: WA={wa_c_base}, WR={wr_c_base}, loss={dl_c_base:.0f}")
    print(f"  B1: WA={wa_b1_base}, WR={wr_b1_base}, loss={dl_b1_base:.0f}")
    print(f"  gap = {gap_base:.0f}, verdict = {verdict_base}")

    # Run all perturbations
    all_results = []

    # 1. Threshold sweep
    print(f"\n[OBP-1] Perturbation 1: Threshold sweep")
    thresholds = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
    thresh_results = threshold_sweep(observed_indices, target_indices, thresholds)
    all_results.extend(thresh_results)
    for r in thresh_results:
        print(f"  threshold={r['parameter']['failure_threshold']:.2f}: "
              f"gap={r['gap']:.0f}, verdict={r['verdict']}, "
              f"contamination={r['contamination_flag']}, stability={r['cluster_stability']:.3f}")

    # 2. Probe reweighting
    print(f"\n[OBP-1] Perturbation 2: Probe reweighting")
    weight_configs = {
        "equal": {"F1": 1.0, "F2": 1.0, "F3": 1.0, "F4": 1.0},
        "f4_heavy": {"F1": 1.0, "F2": 1.0, "F3": 1.0, "F4": 3.0},
        "f2_f3_heavy": {"F1": 1.0, "F2": 2.0, "F3": 2.0, "F4": 1.0},
        "f1_heavy": {"F1": 3.0, "F2": 1.0, "F3": 1.0, "F4": 1.0},
    }
    reweight_results = probe_reweighting(observed_indices, target_indices, weight_configs)
    all_results.extend(reweight_results)
    for r in reweight_results:
        print(f"  weights={r['parameter']['weights']}: "
              f"gap={r['gap']:.0f}, verdict={r['verdict']}, "
              f"contamination={r['contamination_flag']}, stability={r['cluster_stability']:.3f}")

    # 3. Leave-one-family-out
    print(f"\n[OBP-1] Perturbation 3: Leave-one-family-out")
    lofo_results = leave_one_family_out(observed_indices, target_indices)
    all_results.extend(lofo_results)
    for r in lofo_results:
        print(f"  removed={r['parameter']['removed_direction']}: "
              f"gap={r['gap']:.0f}, verdict={r['verdict']}, "
              f"contamination={r['contamination_flag']}, stability={r['cluster_stability']:.3f}")

    # 4. Boundary-noise injection
    print(f"\n[OBP-1] Perturbation 4: Boundary-noise injection")
    noise_configs = [
        ("tolerance_0", 0),
        ("tolerance_1", 1),
        ("tolerance_2", 2),
        ("tolerance_3", 3),
    ]
    noise_results = boundary_noise_injection(observed_indices, target_indices, noise_configs)
    all_results.extend(noise_results)
    for r in noise_results:
        print(f"  {r['parameter']['config']}: "
              f"gap={r['gap']:.0f}, verdict={r['verdict']}, "
              f"contamination={r['contamination_flag']}, stability={r['cluster_stability']:.3f}")

    # Differential response analysis
    print(f"\n[OBP-1] Differential Response Analysis")
    print(f"{'='*60}")

    verdict_changes = [r for r in all_results if r["verdict"] != verdict_base]
    gap_changes = [r for r in all_results if r["gap"] != gap_base]
    contaminations = [r for r in all_results if r["contamination_flag"]]
    stability_drops = [r for r in all_results if r["cluster_stability"] < 1.0]

    print(f"  Total perturbations: {len(all_results)}")
    print(f"  Verdict changes: {len(verdict_changes)}")
    print(f"  Gap changes: {len(gap_changes)}")
    print(f"  Contaminations: {len(contaminations)}")
    print(f"  Stability drops: {len(stability_drops)}")

    # Classify regime
    if len(verdict_changes) == 0 and len(gap_changes) == 0:
        regime = "INTRINSIC_LOW_RANK"
        regime_desc = "Verdict/gap stable across all boundary perturbations. Low-rank dynamics are intrinsic to the system."
    elif len(verdict_changes) > 0 and len(contaminations) == 0:
        regime = "ORACLE_INDUCED"
        regime_desc = "Verdict changes while solver behavior stable. Collapse is oracle-induced."
    elif len(contaminations) > 0:
        regime = "MIXED_ORACLE_DEPENDENT"
        regime_desc = "System is boundary-sensitive but not fully oracle-determined. Contamination detected."
    else:
        regime = "MIXED_RESPONSE"
        regime_desc = "Mixed response: some boundary sensitivity, some intrinsic structure."

    print(f"\n  Regime: {regime}")
    print(f"  Description: {regime_desc}")

    # Detailed verdict change analysis
    if verdict_changes:
        print(f"\n  Verdict changes detail:")
        for r in verdict_changes:
            print(f"    {r['perturbation_type']} {r['parameter']}: "
                  f"{verdict_base} -> {r['verdict']} (gap {gap_base:.0f} -> {r['gap']:.0f})")

    # Output
    output = {
        "experiment": "OBP-1",
        "population": "LC756",
        "n_solvers": len(SOLVER_REGISTRY),
        "n_cases": N_CASES,
        "observed_indices": observed_indices,
        "target_indices": target_indices,
        "random_seed": RANDOM_SEED,
        "baseline": {
            "failure_threshold": BASELINE_FAILURE_THRESHOLD,
            "ground_truth_counts": {"ACCEPT": n_accept, "REJECT": n_reject},
            "decision_loss_c": dl_c_base,
            "decision_loss_b1": dl_b1_base,
            "gap": gap_base,
            "verdict": verdict_base,
        },
        "perturbations": all_results,
        "analysis": {
            "total_perturbations": len(all_results),
            "verdict_changes": len(verdict_changes),
            "gap_changes": len(gap_changes),
            "contaminations": len(contaminations),
            "stability_drops": len(stability_drops),
            "regime": regime,
            "regime_description": regime_desc,
        },
    }

    out_path = ROOT / "results" / "obp1_lc756_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n[OBP-1] Written -> {out_path}")


if __name__ == "__main__":
    main()
