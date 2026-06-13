"""LC3946 representation audit: where does the R1 advantage come from?

For every LC3946 probe:
- compute contribution to Delta(R1-R2)
- rank probes by contribution
- identify top 20% contributing probes
- report their feature distributions
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


def compute_probe_contributions(problem_class, to_input, oracle_fn, style):
    """Compute per-probe contribution to Delta(R1-R2)."""
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
    
    # Compute per-probe contribution
    # For each probe, compute how much it contributes to the loss difference
    contributions = []
    
    for j, pid in enumerate(obs):
        # R1 family rate for this probe's family
        fam_R1 = phi_R1.get(pid, "unknown")
        fam_R2 = phi_R2.get(pid, "unknown")
        
        # Compute loss contribution from this probe across all test solvers
        probe_loss_R1 = 0.0
        probe_loss_R2 = 0.0
        probe_loss_b0 = 0.0
        count = 0
        
        for sid in test_sids:
            true_val = failure_vectors[sid][j]
            
            # R1 prediction: rate for this probe's family
            # Need to compute family rates excluding this probe? No, use full train set
            # For simplicity, compute the family rate from train set
            fam_probes_R1 = [k for k, v in phi_R1.items() if v == fam_R1]
            fam_indices_R1 = [obs.index(k) for k in fam_probes_R1 if k in obs]
            
            fails_R1 = sum(1 for sid2 in train_sids for jj in fam_indices_R1 if failure_vectors[sid2][jj] == 1)
            total_R1 = len(train_sids) * len(fam_indices_R1)
            rate_R1 = fails_R1 / total_R1 if total_R1 > 0 else 0
            
            # R2 prediction
            fam_probes_R2 = [k for k, v in phi_R2.items() if v == fam_R2]
            fam_indices_R2 = [obs.index(k) for k in fam_probes_R2 if k in obs]
            
            fails_R2 = sum(1 for sid2 in train_sids for jj in fam_indices_R2 if failure_vectors[sid2][jj] == 1)
            total_R2 = len(train_sids) * len(fam_indices_R2)
            rate_R2 = fails_R2 / total_R2 if total_R2 > 0 else 0
            
            # B0 prediction
            rate_b0 = rates_b0[j]
            
            # Compute losses
            pred_prob_R1 = max(min(rate_R1, 0.999), 0.001)
            pred_prob_R2 = max(min(rate_R2, 0.999), 0.001)
            pred_prob_b0 = max(min(rate_b0, 0.999), 0.001)
            
            if true_val == 1:
                loss_R1 = -math.log(pred_prob_R1)
                loss_R2 = -math.log(pred_prob_R2)
                loss_b0 = -math.log(pred_prob_b0)
            else:
                loss_R1 = -math.log(1 - pred_prob_R1)
                loss_R2 = -math.log(1 - pred_prob_R2)
                loss_b0 = -math.log(1 - pred_prob_b0)
            
            probe_loss_R1 += loss_R1
            probe_loss_R2 += loss_R2
            probe_loss_b0 += loss_b0
            count += 1
        
        # Average contribution per test solver
        avg_loss_R1 = probe_loss_R1 / count if count > 0 else 0
        avg_loss_R2 = probe_loss_R2 / count if count > 0 else 0
        avg_loss_b0 = probe_loss_b0 / count if count > 0 else 0
        
        # Contribution to Delta(R1-R2) = (loss_b0 - loss_R1) - (loss_b0 - loss_R2) = loss_R2 - loss_R1
        contribution = avg_loss_R2 - avg_loss_R1
        
        contributions.append({
            "probe_id": pid,
            "contribution": contribution,
            "loss_R1": avg_loss_R1,
            "loss_R2": avg_loss_R2,
            "loss_b0": avg_loss_b0,
            "family_R1": fam_R1,
            "family_R2": fam_R2,
            "features": R1_features[pid],
        })
    
    return contributions, R1_features, phi_R1, phi_R2


def audit_contributions(contributions, R1_features):
    """Audit the contribution distribution."""
    # Sort by contribution (descending)
    sorted_contribs = sorted(contributions, key=lambda x: x["contribution"], reverse=True)
    
    n = len(sorted_contribs)
    top_20_pct = int(0.2 * n)
    top_10_pct = max(1, int(0.1 * n))
    
    print(f"\n  Total probes: {n}")
    print(f"  Top 20% count: {top_20_pct}")
    print(f"  Top 10% count: {top_10_pct}")
    
    # Top 20%
    top_20 = sorted_contribs[:top_20_pct]
    print(f"\n  === TOP 20% CONTRIBUTING PROBES ===")
    for i, c in enumerate(top_20):
        print(f"    {i+1}. {c['probe_id']}: contribution={c['contribution']:+.6f}, "
              f"R1_fam={c['family_R1']}, R2_fam={c['family_R2']}")
        print(f"       Features: {c['features']}")
    
    # Bottom 20%
    bottom_20 = sorted_contribs[-top_20_pct:]
    print(f"\n  === BOTTOM 20% CONTRIBUTING PROBES ===")
    for i, c in enumerate(bottom_20):
        print(f"    {i+1}. {c['probe_id']}: contribution={c['contribution']:+.6f}, "
              f"R1_fam={c['family_R1']}, R2_fam={c['family_R2']}")
    
    # Summary statistics
    all_contribs = [c["contribution"] for c in contributions]
    top_20_contribs = [c["contribution"] for c in top_20]
    
    print(f"\n  === CONTRIBUTION STATISTICS ===")
    print(f"  Mean: {sum(all_contribs)/len(all_contribs):+.6f}")
    print(f"  Std:  {(sum((x - sum(all_contribs)/len(all_contribs))**2 for x in all_contribs) / len(all_contribs))**0.5:.6f}")
    print(f"  Top 20% mean: {sum(top_20_contribs)/len(top_20_contribs):+.6f}")
    print(f"  Top 20% total: {sum(top_20_contribs):+.6f}")
    print(f"  Total contribution: {sum(all_contribs):+.6f}")
    
    # Feature distributions for top 20%
    print(f"\n  === TOP 20% FEATURE DISTRIBUTIONS ===")
    feature_names = list(top_20[0]["features"].keys())
    for fname in feature_names:
        vals = [c["features"][fname] for c in top_20]
        all_vals = [c["features"][fname] for c in contributions]
        print(f"  {fname}:")
        print(f"    Top 20%: mean={sum(vals)/len(vals):.4f}, range=[{min(vals):.4f}, {max(vals):.4f}]")
        print(f"    All:     mean={sum(all_vals)/len(all_vals):.4f}, range=[{min(all_vals):.4f}, {max(all_vals):.4f}]")
    
    return sorted_contribs, top_20_pct, top_10_pct


def test_removal_effect(problem_class, to_input, oracle_fn, style, contributions, top_10_pct):
    """Test if removing top 10% contributors collapses the R1 advantage."""
    sorted_contribs = sorted(contributions, key=lambda x: x["contribution"], reverse=True)
    top_10_ids = set(c["probe_id"] for c in sorted_contribs[:top_10_pct])
    
    print(f"\n  === REMOVAL TEST (top {top_10_pct} probes) ===")
    print(f"  Removing: {top_10_ids}")
    
    # Load data
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    
    # Compute failure vectors
    failure_vectors = compute_failure_vectors(solver_evals, obs)
    
    # Split solvers
    all_sids = sorted(solver_evals.keys())
    rng = random.Random(SEED)
    rng.shuffle(all_sids)
    split_idx = int(0.8 * len(all_sids))
    train_sids = all_sids[:split_idx]
    test_sids = all_sids[split_idx:]
    
    # Build features
    R1_features = build_R1(problem_class)
    R2_features = build_R2(R1_features, seed=42)
    
    # Remove top 10% probes
    obs_filtered = [pid for pid in obs if pid not in top_10_ids]
    print(f"  Probes before: {len(obs)}, after: {len(obs_filtered)}")
    
    # Recompute phi assignments with filtered probes
    R1_features_filtered = {pid: R1_features[pid] for pid in obs_filtered}
    R2_features_filtered = {pid: R2_features[pid] for pid in obs_filtered}
    
    phi_R1_filtered = features_to_phi(R1_features_filtered, n_clusters=4, seed=42)
    phi_R2_filtered = features_to_phi(R2_features_filtered, n_clusters=4, seed=42)
    
    # Compute failure vectors for filtered probes
    failure_vectors_filtered = {}
    for sid, results in solver_evals.items():
        vector = []
        for pid in obs_filtered:
            passed = results.get(pid, True)
            vector.append(0 if passed else 1)
        failure_vectors_filtered[sid] = vector
    
    # Compute B0 baseline
    rates_b0_filtered = compute_empirical_rates(failure_vectors_filtered, train_sids, obs_filtered)
    
    # Compute R1 and R2 performance
    results = {}
    for name, phi in [("R1_filtered", phi_R1_filtered), ("R2_filtered", phi_R2_filtered)]:
        family_rates, family_probes = compute_family_rates(failure_vectors_filtered, phi, train_sids, obs_filtered)
        pred_bphi = predict_failure_vector_bphi(family_rates, family_probes, obs_filtered)
        
        loss_bphi = compute_prediction_loss(failure_vectors_filtered, pred_bphi, test_sids, obs_filtered)
        loss_b0 = compute_prediction_loss(failure_vectors_filtered, rates_b0_filtered, test_sids, obs_filtered)
        
        delta_gain = loss_b0 - loss_bphi
        results[name] = delta_gain
        
        print(f"  {name}: Delta={delta_gain:+.6f}")
    
    delta_filtered = results["R1_filtered"] - results["R2_filtered"]
    print(f"  Delta(R1-R2) filtered: {delta_filtered:+.6f}")
    
    return delta_filtered


if __name__ == "__main__":
    print("="*70)
    print("  LC3946 REPRESENTATION AUDIT")
    print("="*70)
    
    contributions, R1_features, phi_R1, phi_R2 = compute_probe_contributions(
        "lc3946", lc3946_to_input, lc3946_oracle, "single"
    )
    
    sorted_contribs, top_20_pct, top_10_pct = audit_contributions(contributions, R1_features)
    
    delta_filtered = test_removal_effect(
        "lc3946", lc3946_to_input, lc3946_oracle, "single",
        contributions, top_10_pct
    )
    
    # Save full results
    out_path = ROOT / "results" / "lc3946_audit_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "contributions": sorted_contribs,
            "top_20_pct": top_20_pct,
            "top_10_pct": top_10_pct,
            "delta_filtered": delta_filtered,
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")
