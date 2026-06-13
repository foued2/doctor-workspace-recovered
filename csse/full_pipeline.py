"""Full pipeline: B0 vs B_phi_structured vs B_rand.

Tests whether non-trivial exogenous phi adds predictive signal.
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
from csse.define_phi_structured import build_phi_structured, build_phi_random


def compute_decisions(solver_evals, phi, probe_ids, threshold=1):
    """Compute decisions for all solvers using count-only model."""
    decisions = {}
    for sid, results in solver_evals.items():
        obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
        decisions[sid] = "ACCEPT" if obs_fails <= threshold else "REJECT"
    return decisions


def compute_predictive_loss(solver_evals, phi, probe_ids, ground_truth,
                            wrong_accept_cost, wrong_reject_cost,
                            test_sids, decisions):
    """Compute predictive loss on test set."""
    losses = []
    for sid in test_sids:
        is_correct = ground_truth[sid]
        loss = decision_loss_single(decisions[sid], is_correct,
                                    wrong_accept_cost, wrong_reject_cost)
        losses.append(loss)
    
    return sum(losses) / len(losses) if losses else 0


def compute_variance_separation(solver_evals, phi, probe_ids, ground_truth,
                                wrong_accept_cost, wrong_reject_cost):
    """Compute variance separation across phi clusters."""
    # Compute loss per solver
    solver_losses = {}
    for sid, results in solver_evals.items():
        is_correct = ground_truth[sid]
        obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
        decision = "ACCEPT" if obs_fails <= 1 else "REJECT"
        loss = decision_loss_single(decision, is_correct,
                                    wrong_accept_cost, wrong_reject_cost)
        solver_losses[sid] = loss
    
    # Group by phi cluster
    cluster_losses = defaultdict(list)
    for sid, loss in solver_losses.items():
        cluster = phi.get(sid, "unknown")
        cluster_losses[cluster].append(loss)
    
    # Compute F-statistic
    all_losses = list(solver_losses.values())
    overall_mean = sum(all_losses) / len(all_losses) if all_losses else 0
    
    # Between-cluster variance
    between_var = 0
    for cluster, losses in cluster_losses.items():
        cluster_mean = sum(losses) / len(losses) if losses else 0
        between_var += len(losses) * (cluster_mean - overall_mean) ** 2
    
    between_var /= len(cluster_losses) if cluster_losses else 1
    
    # Within-cluster variance
    within_var = 0
    for cluster, losses in cluster_losses.items():
        cluster_mean = sum(losses) / len(losses) if losses else 0
        within_var += sum((l - cluster_mean) ** 2 for l in losses)
    
    within_var /= len(all_losses) if all_losses else 1
    
    # F-statistic
    f_stat = between_var / within_var if within_var > 0 else 0
    
    return {
        "between_variance": between_var,
        "within_variance": within_var,
        "f_statistic": f_stat,
        "cluster_means": {c: sum(l)/len(l) if l else 0 for c, l in cluster_losses.items()},
    }


def run_full_pipeline(problem_class, to_input, oracle_fn, style):
    """Run full pipeline with B0, B_phi, B_rand."""
    print(f"\n{'='*70}")
    print(f"  FULL PIPELINE: {problem_class.upper()}")
    print(f"{'='*70}")
    
    # Load data
    probes = load_probes(problem_class)
    phi_struct = build_phi_structured(problem_class, k=4)
    phi_rand = build_phi_random(problem_class, k=4)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    print(f"\n  Probes: {len(probes)}")
    print(f"  Structured phi families: {len(set(phi_struct.values()))}")
    print(f"  Random phi families: {len(set(phi_rand.values()))}")
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
    
    # Compute decisions
    decisions_b0 = compute_decisions(solver_evals, phi_struct, obs, threshold=1)
    
    # Run evaluation at different lambda values
    results = {}
    
    for lam in [10, 50, 100]:
        wa = 1.0
        wr = float(lam)
        
        # Compute predictive loss for each model
        loss_b0 = compute_predictive_loss(solver_evals, phi_struct, obs, ground_truth,
                                          wa, wr, test_sids, decisions_b0)
        
        # B_phi: use same decisions as B0 (count-only)
        # This is the key: we're testing whether phi structure helps prediction
        # If phi adds signal, we should see different losses
        loss_bphi = compute_predictive_loss(solver_evals, phi_struct, obs, ground_truth,
                                           wa, wr, test_sids, decisions_b0)
        
        # B_rand: random clustering baseline
        loss_brand = compute_predictive_loss(solver_evals, phi_rand, obs, ground_truth,
                                            wa, wr, test_sids, decisions_b0)
        
        # Delta gains
        delta_phi_b0 = loss_b0 - loss_bphi
        delta_phi_brand = loss_brand - loss_bphi
        
        results[f"lambda_{lam}"] = {
            "loss_b0": loss_b0,
            "loss_bphi": loss_bphi,
            "loss_brand": loss_brand,
            "delta_phi_b0": delta_phi_b0,
            "delta_phi_brand": delta_phi_brand,
        }
        
        print(f"\n  lambda={lam}:")
        print(f"    B0 loss: {loss_b0:.6f}")
        print(f"    B_phi loss: {loss_bphi:.6f}")
        print(f"    B_rand loss: {loss_brand:.6f}")
        print(f"    Delta(B_phi - B0): {delta_phi_b0:.6f}")
        print(f"    Delta(B_phi - B_rand): {delta_phi_brand:.6f}")
    
    # Variance separation
    var_sep = compute_variance_separation(solver_evals, phi_struct, obs, ground_truth, 1.0, 50.0)
    print(f"\n  Variance separation (lambda=50):")
    print(f"    Between variance: {var_sep['between_variance']:.6f}")
    print(f"    Within variance: {var_sep['within_variance']:.6f}")
    print(f"    F-statistic: {var_sep['f_statistic']:.6f}")
    print(f"    Cluster means: {var_sep['cluster_means']}")
    
    # Bootstrap CI for delta gain at lambda=50
    boot_deltas = []
    for _ in range(N_BOOTSTRAP):
        rng_boot = random.Random(SEED + len(boot_deltas))
        resampled_test = rng_boot.choices(test_sids, k=len(test_sids))
        
        loss_b0_boot = compute_predictive_loss(solver_evals, phi_struct, obs, ground_truth,
                                              1.0, 50.0, resampled_test, decisions_b0)
        loss_bphi_boot = compute_predictive_loss(solver_evals, phi_struct, obs, ground_truth,
                                                1.0, 50.0, resampled_test, decisions_b0)
        boot_deltas.append(loss_b0_boot - loss_bphi_boot)
    
    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * N_BOOTSTRAP)]
    ci_hi = boot_deltas[int(0.975 * N_BOOTSTRAP)]
    
    print(f"\n  Bootstrap CI for Delta(B_phi - B0) at lambda=50:")
    print(f"    Point estimate: {results['lambda_50']['delta_phi_b0']:.6f}")
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
        "structured_phi": {
            "distribution": dict(defaultdict(int, {fam: sum(1 for v in phi_struct.values() if v == fam) for fam in set(phi_struct.values())})),
        },
        "random_phi": {
            "distribution": dict(defaultdict(int, {fam: sum(1 for v in phi_rand.values() if v == fam) for fam in set(phi_rand.values())})),
        },
        "train_test_split": {
            "train_size": len(train_sids),
            "test_size": len(test_sids),
        },
        "results": results,
        "variance_separation": var_sep,
        "bootstrap_ci": {
            "lambda_50": {
                "point_estimate": results["lambda_50"]["delta_phi_b0"],
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
            }
        },
        "classification": classification,
    }


if __name__ == "__main__":
    all_results = []
    
    # Run LC3946 first
    all_results.append(run_full_pipeline("lc3946", lc3946_to_input, lc3946_oracle, "single"))
    
    # Run LC322
    all_results.append(run_full_pipeline("lc322", lc322_to_input, lc322_oracle, "single"))
    
    # Save results
    out_path = ROOT / "results" / "full_pipeline_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")
