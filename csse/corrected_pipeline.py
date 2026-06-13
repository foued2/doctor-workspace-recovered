"""Corrected pipeline: predictive gain measurement (not agreement).

B0: failure count only
B_rand: failure count + random partition (frozen)
Bφ: failure count + family partition

Measures: Δ predictive gain of φ over baselines.
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    b1_decision, c_genuine_decision, decision_loss_single,
    SEED, N_BOOTSTRAP,
    lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
)
from csse.define_phi_frozen import build_phi_frozen


def compute_features(solver_evals, phi, probe_ids, sid):
    """Compute feature vector for a solver.
    
    Features:
    - obs_fails: total failure count
    - family_histogram: failure count per family (normalized)
    """
    results = solver_evals[sid]
    obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
    
    # Family histogram
    family_fails = defaultdict(int)
    for pid in probe_ids:
        if not results.get(pid, True):
            fam = phi.get(pid, "unknown")
            family_fails[fam] += 1
    
    # Normalize by total failures
    if obs_fails > 0:
        family_hist = {fam: count / obs_fails for fam, count in family_fails.items()}
    else:
        family_hist = {}
    
    return {
        "obs_fails": obs_fails,
        "family_hist": family_hist,
    }


def compute_predictive_loss(solver_evals, phi, probe_ids, ground_truth,
                            wrong_accept_cost, wrong_reject_cost,
                            train_sids, test_sids):
    """Compute predictive loss for decision policies.
    
    Returns loss for B0 (count only) and Bφ (count + family).
    """
    # Compute features for all solvers
    features = {}
    for sid in list(train_sids) + list(test_sids):
        features[sid] = compute_features(solver_evals, phi, probe_ids, sid)
    
    # Compute decisions for all solvers
    # B0: count-only decision (threshold = 1)
    # Bφ: family-aware decision (C_genuine)
    decisions_b0 = {}
    decisions_bphi = {}
    
    for sid in list(train_sids) + list(test_sids):
        obs_fails = features[sid]["obs_fails"]
        family_hist = features[sid]["family_hist"]
        
        # B0: count-only (threshold = 1)
        decisions_b0[sid] = "ACCEPT" if obs_fails <= 1 else "REJECT"
        
        # Bφ: family-aware (C_genuine)
        family_fails = {fam: int(count * obs_fails) for fam, count in family_hist.items()}
        decisions_bphi[sid] = c_genuine_decision(family_fails)
    
    # Compute loss on test set
    losses_b0 = []
    losses_bphi = []
    
    for sid in test_sids:
        is_correct = ground_truth[sid]
        loss_b0 = decision_loss_single(decisions_b0[sid], is_correct,
                                       wrong_accept_cost, wrong_reject_cost)
        loss_bphi = decision_loss_single(decisions_bphi[sid], is_correct,
                                         wrong_accept_cost, wrong_reject_cost)
        losses_b0.append(loss_b0)
        losses_bphi.append(loss_bphi)
    
    avg_loss_b0 = sum(losses_b0) / len(losses_b0) if losses_b0 else 0
    avg_loss_bphi = sum(losses_bphi) / len(losses_bphi) if losses_bphi else 0
    
    return avg_loss_b0, avg_loss_bphi


def run_corrected_pipeline(problem_class, to_input, oracle_fn, style):
    """Run corrected pipeline for one problem."""
    print(f"\n{'='*70}")
    print(f"  CORRECTED PIPELINE: {problem_class.upper()}")
    print(f"{'='*70}")
    
    # Load data
    probes = load_probes(problem_class)
    phi_frozen = build_phi_frozen(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    print(f"\n  Probes: {len(probes)}")
    print(f"  Frozen phi families: {len(set(phi_frozen.values()))}")
    print(f"  Frozen solvers: {len(solver_evals)}")
    
    # Split solvers into train/test (80/20)
    all_sids = sorted(solver_evals.keys())
    rng = random.Random(SEED)
    rng.shuffle(all_sids)
    split_idx = int(0.8 * len(all_sids))
    train_sids = all_sids[:split_idx]
    test_sids = all_sids[split_idx:]
    
    print(f"  Train solvers: {len(train_sids)}")
    print(f"  Test solvers: {len(test_sids)}")
    
    # Run evaluation at different lambda values
    results = {}
    
    for lam in [10, 50, 100]:
        wa = 1.0
        wr = float(lam)
        
        # Compute predictive loss
        loss_b0, loss_bphi = compute_predictive_loss(
            solver_evals, phi_frozen, obs, ground_truth,
            wa, wr, train_sids, test_sids
        )
        
        # Delta gain: how much better is Bφ than B0?
        delta_gain = loss_b0 - loss_bphi
        
        results[f"lambda_{lam}"] = {
            "loss_b0": loss_b0,
            "loss_bphi": loss_bphi,
            "delta_gain": delta_gain,
        }
        
        print(f"\n  lambda={lam}:")
        print(f"    B0 loss: {loss_b0:.6f}")
        print(f"    Bphi loss: {loss_bphi:.6f}")
        print(f"    Delta gain: {delta_gain:.6f}")
    
    # Bootstrap CI for delta gain at lambda=50
    boot_deltas = []
    for _ in range(N_BOOTSTRAP):
        # Resample test set
        rng_boot = random.Random(SEED + len(boot_deltas))
        resampled_test = rng_boot.choices(test_sids, k=len(test_sids))
        
        loss_b0_boot, loss_bphi_boot = compute_predictive_loss(
            solver_evals, phi_frozen, obs, ground_truth,
            1.0, 50.0, train_sids, resampled_test
        )
        boot_deltas.append(loss_b0_boot - loss_bphi_boot)
    
    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * N_BOOTSTRAP)]
    ci_hi = boot_deltas[int(0.975 * N_BOOTSTRAP)]
    
    print(f"\n  Bootstrap CI for delta gain (lambda=50):")
    print(f"    Point estimate: {results['lambda_50']['delta_gain']:.6f}")
    print(f"    95% CI: [{ci_lo:.6f}, {ci_hi:.6f}]")
    
    # Classification
    if ci_lo > 0:
        classification = "phi adds predictive signal"
    elif ci_hi < 0:
        classification = "phi reduces predictive power"
    else:
        classification = "phi does not add predictive signal"
    
    print(f"\n  Classification: {classification}")
    
    return {
        "problem": problem_class,
        "frozen_phi": {
            "definition": "exogenous, input-length only",
            "distribution": dict(defaultdict(int, {fam: sum(1 for v in phi_frozen.values() if v == fam) for fam in set(phi_frozen.values())})),
        },
        "train_test_split": {
            "train_size": len(train_sids),
            "test_size": len(test_sids),
        },
        "results": results,
        "bootstrap_ci": {
            "lambda_50": {
                "point_estimate": results["lambda_50"]["delta_gain"],
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
            }
        },
        "classification": classification,
    }


if __name__ == "__main__":
    all_results = []
    
    # Run LC3946 first
    all_results.append(run_corrected_pipeline("lc3946", lc3946_to_input, lc3946_oracle, "single"))
    
    # Run LC322
    all_results.append(run_corrected_pipeline("lc322", lc322_to_input, lc322_oracle, "single"))
    
    # Save results
    out_path = ROOT / "results" / "corrected_pipeline_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")
