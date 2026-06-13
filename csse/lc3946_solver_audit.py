"""LC3946 solver audit: is the R1-R2 effect solver-driven or probe-driven?

For every LC3946 solver:
- compute contribution to Delta(R1-R2)
- rank solvers by contribution
- identify top 20% contributing solvers
- test if removing top 10% collapses the advantage
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    SEED, N_BOOTSTRAP,
    lc3946_to_input, lc3946_oracle,
)
from csse.representation_invariance import (
    build_R1, build_R2, features_to_phi,
    compute_failure_vectors, compute_empirical_rates,
    compute_family_rates, predict_failure_vector_bphi,
    compute_prediction_loss,
)


def compute_solver_contributions(problem_class, to_input, oracle_fn, style):
    """Compute per-solver contribution to Delta(R1-R2)."""
    # Load data
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    
    # Compute failure vectors
    failure_vectors = compute_failure_vectors(solver_evals, obs)
    
    # Split solvers into train/test (80/20)
    all_sids = sorted(solver_evals.keys())
    rng = random.Random(SEED)
    rng.shuffle(all_sids)
    split_idx = int(0.8 * len(all_sids))
    train_sids = all_sids[:split_idx]
    test_sids = all_sids[split_idx:]
    
    # Build R1 and R2 features
    R1_features = build_R1(problem_class)
    R2_features = build_R2(R1_features, seed=42)
    
    # Convert to phi assignments
    phi_R1 = features_to_phi(R1_features, n_clusters=4, seed=42)
    phi_R2 = features_to_phi(R2_features, n_clusters=4, seed=42)
    
    # Compute B0 baseline
    rates_b0 = compute_empirical_rates(failure_vectors, train_sids, obs)
    
    # Compute per-solver contribution
    # For each solver, compute how much it contributes to the loss difference
    contributions = []
    
    for sid in test_sids:
        # Compute loss for this solver under R1, R2, and B0
        loss_R1 = 0.0
        loss_R2 = 0.0
        loss_b0 = 0.0
        
        for j, pid in enumerate(obs):
            true_val = failure_vectors[sid][j]
            
            # R1 family rate for this probe's family
            fam_R1 = phi_R1.get(pid, "unknown")
            fam_probes_R1 = [k for k, v in phi_R1.items() if v == fam_R1]
            fam_indices_R1 = [obs.index(k) for k in fam_probes_R1 if k in obs]
            
            fails_R1 = sum(1 for sid2 in train_sids for jj in fam_indices_R1 if failure_vectors[sid2][jj] == 1)
            total_R1 = len(train_sids) * len(fam_indices_R1)
            rate_R1 = fails_R1 / total_R1 if total_R1 > 0 else 0
            
            # R2 family rate
            fam_R2 = phi_R2.get(pid, "unknown")
            fam_probes_R2 = [k for k, v in phi_R2.items() if v == fam_R2]
            fam_indices_R2 = [obs.index(k) for k in fam_probes_R2 if k in obs]
            
            fails_R2 = sum(1 for sid2 in train_sids for jj in fam_indices_R2 if failure_vectors[sid2][jj] == 1)
            total_R2 = len(train_sids) * len(fam_indices_R2)
            rate_R2 = fails_R2 / total_R2 if total_R2 > 0 else 0
            
            # B0 rate
            rate_b0 = rates_b0[j]
            
            # Compute losses
            pred_prob_R1 = max(min(rate_R1, 0.999), 0.001)
            pred_prob_R2 = max(min(rate_R2, 0.999), 0.001)
            pred_prob_b0 = max(min(rate_b0, 0.999), 0.001)
            
            if true_val == 1:
                loss_R1 += -math.log(pred_prob_R1)
                loss_R2 += -math.log(pred_prob_R2)
                loss_b0 += -math.log(pred_prob_b0)
            else:
                loss_R1 += -math.log(1 - pred_prob_R1)
                loss_R2 += -math.log(1 - pred_prob_R2)
                loss_b0 += -math.log(1 - pred_prob_b0)
        
        # Average per probe
        n_probes = len(obs)
        avg_loss_R1 = loss_R1 / n_probes
        avg_loss_R2 = loss_R2 / n_probes
        avg_loss_b0 = loss_b0 / n_probes
        
        # Contribution to Delta(R1-R2) = (loss_b0 - loss_R1) - (loss_b0 - loss_R2) = loss_R2 - loss_R1
        contribution = avg_loss_R2 - avg_loss_R1
        
        # Also compute ground truth accuracy
        gt = load_ground_truth_from_json(problem_class)
        correct = 1 if gt.get(sid, False) == (failure_vectors[sid][0] == 0) else 0
        
        contributions.append({
            "solver_id": sid,
            "contribution": contribution,
            "loss_R1": avg_loss_R1,
            "loss_R2": avg_loss_R2,
            "loss_b0": avg_loss_b0,
            "n_failures": sum(failure_vectors[sid]),
            "correct": correct,
        })
    
    return contributions


def audit_solver_contributions(contributions):
    """Audit the solver contribution distribution."""
    # Sort by contribution (descending)
    sorted_contribs = sorted(contributions, key=lambda x: x["contribution"], reverse=True)
    
    n = len(sorted_contribs)
    top_20_pct = int(0.2 * n)
    bottom_20_pct = max(1, int(0.2 * n))
    top_10_pct = max(1, int(0.1 * n))
    
    print(f"\n  Total solvers: {n}")
    print(f"  Top 20% count: {top_20_pct}")
    print(f"  Bottom 20% count: {bottom_20_pct}")
    print(f"  Top 10% count: {top_10_pct}")
    
    # Top 20%
    top_20 = sorted_contribs[:top_20_pct]
    print(f"\n  === TOP 20% CONTRIBUTING SOLVERS ===")
    for i, c in enumerate(top_20):
        print(f"    {i+1}. {c['solver_id']}: contribution={c['contribution']:+.6f}, "
              f"n_failures={c['n_failures']}, correct={c['correct']}")
    
    # Bottom 20%
    bottom_20 = sorted_contribs[-bottom_20_pct:]
    print(f"\n  === BOTTOM 20% CONTRIBUTING SOLVERS ===")
    for i, c in enumerate(bottom_20):
        print(f"    {i+1}. {c['solver_id']}: contribution={c['contribution']:+.6f}, "
              f"n_failures={c['n_failures']}, correct={c['correct']}")
    
    # Summary statistics
    all_contribs = [c["contribution"] for c in contributions]
    top_20_contribs = [c["contribution"] for c in top_20]
    
    total_contribution = sum(all_contribs)
    top_20_total = sum(top_20_contribs)
    top_20_share = top_20_total / total_contribution if total_contribution > 0 else 0
    
    print(f"\n  === CONTRIBUTION STATISTICS ===")
    print(f"  Mean: {sum(all_contribs)/len(all_contribs):+.6f}")
    print(f"  Std:  {(sum((x - sum(all_contribs)/len(all_contribs))**2 for x in all_contribs) / len(all_contribs))**0.5:.6f}")
    print(f"  Top 20% mean: {sum(top_20_contribs)/len(top_20_contribs):+.6f}")
    print(f"  Top 20% total: {top_20_total:+.6f}")
    print(f"  Total contribution: {total_contribution:+.6f}")
    print(f"  Top 20% share of total: {top_20_share:.1%}")
    
    # Failure count distribution
    print(f"\n  === FAILURE COUNT DISTRIBUTION ===")
    for c in sorted_contribs:
        marker = " <-- TOP" if c in top_20 else (" <-- BOTTOM" if c in bottom_20 else "")
        print(f"    {c['solver_id']}: {c['n_failures']} failures, contribution={c['contribution']:+.6f}{marker}")
    
    return sorted_contribs, top_20_pct, top_10_pct


def test_solver_removal(problem_class, to_input, oracle_fn, style, contributions, top_10_pct):
    """Test if removing top 10% contributing solvers collapses the R1-R2 advantage."""
    sorted_contribs = sorted(contributions, key=lambda x: x["contribution"], reverse=True)
    top_10_ids = set(c["solver_id"] for c in sorted_contribs[:top_10_pct])
    
    print(f"\n  === SOLVER REMOVAL TEST (top {top_10_pct} solvers) ===")
    print(f"  Removing: {top_10_ids}")
    
    # Load data
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    
    # Compute failure vectors
    failure_vectors = compute_failure_vectors(solver_evals, obs)
    
    # Split solvers - exclude removed ones
    all_sids = sorted(solver_evals.keys())
    rng = random.Random(SEED)
    rng.shuffle(all_sids)
    
    # Filter out removed solvers
    all_sids_filtered = [s for s in all_sids if s not in top_10_ids]
    split_idx = int(0.8 * len(all_sids_filtered))
    train_sids = all_sids_filtered[:split_idx]
    test_sids = all_sids_filtered[split_idx:]
    
    print(f"  Solvers before: {len(all_sids)}, after: {len(all_sids_filtered)}")
    print(f"  Train: {len(train_sids)}, Test: {len(test_sids)}")
    
    # Build features
    R1_features = build_R1(problem_class)
    R2_features = build_R2(R1_features, seed=42)
    
    # Phi assignments
    phi_R1 = features_to_phi(R1_features, n_clusters=4, seed=42)
    phi_R2 = features_to_phi(R2_features, n_clusters=4, seed=42)
    
    # Compute B0 baseline
    rates_b0 = compute_empirical_rates(failure_vectors, train_sids, obs)
    
    # Compute R1 and R2 performance
    results = {}
    for name, phi in [("R1", phi_R1), ("R2", phi_R2)]:
        family_rates, family_probes = compute_family_rates(failure_vectors, phi, train_sids, obs)
        pred_bphi = predict_failure_vector_bphi(family_rates, family_probes, obs)
        
        loss_bphi = compute_prediction_loss(failure_vectors, pred_bphi, test_sids, obs)
        loss_b0 = compute_prediction_loss(failure_vectors, rates_b0, test_sids, obs)
        
        delta_gain = loss_b0 - loss_bphi
        results[name] = delta_gain
        
        print(f"  {name}: Delta={delta_gain:+.6f}")
    
    delta_filtered = results["R1"] - results["R2"]
    print(f"  Delta(R1-R2) filtered: {delta_filtered:+.6f}")
    
    return delta_filtered


if __name__ == "__main__":
    print("="*70)
    print("  LC3946 SOLVER AUDIT")
    print("="*70)
    
    contributions = compute_solver_contributions(
        "lc3946", lc3946_to_input, lc3946_oracle, "single"
    )
    
    sorted_contribs, top_20_pct, top_10_pct = audit_solver_contributions(contributions)
    
    delta_filtered = test_solver_removal(
        "lc3946", lc3946_to_input, lc3946_oracle, "single",
        contributions, top_10_pct
    )
    
    # Save full results
    out_path = ROOT / "results" / "lc3946_solver_audit_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "contributions": sorted_contribs,
            "top_20_pct": top_20_pct,
            "top_10_pct": top_10_pct,
            "delta_filtered": delta_filtered,
            "original_delta": 0.022386,  # From representation invariance test
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")
