"""Representation invariance probe.

Tests whether φ instability is due to bad feature basis vs genuinely absent shared structure.

R1: Problem-native encoding (raw structural features)
R2: Permuted-but-information-preserving encoding (marginals preserved, semantics destroyed)
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
    SEED, N_BOOTSTRAP,
    lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
    lc45_to_input, lc45_oracle,
)
from csse.phi_ablation import (
    compute_failure_vectors, compute_empirical_rates,
    compute_family_rates, predict_failure_vector_bphi,
    compute_prediction_loss, compute_mutual_information,
)


# =============================================================================
# R1: Problem-native feature extraction
# =============================================================================

def extract_R1_lc322(probe):
    """LC322: arithmetic / coin structure / DP recurrence stats."""
    coins = probe.get("coins", [])
    amount = probe.get("amount", 0)
    
    if not coins:
        return {"amount": amount, "n_coins": 0, "coin_range": 0, "gcd": 0, "amount_per_coin": 0}
    
    from math import gcd as math_gcd
    coin_gcd = coins[0]
    for c in coins[1:]:
        coin_gcd = math_gcd(coin_gcd, c)
    
    return {
        "amount": amount,
        "n_coins": len(coins),
        "coin_range": max(coins) - min(coins) if len(coins) > 1 else 0,
        "gcd": coin_gcd,
        "amount_per_coin": amount / len(coins) if coins else 0,
    }


def extract_R1_lc3946(probe):
    """LC3946: graph density / constraint tightness / budget ratio."""
    items = probe.get("items", [])
    budget = probe.get("budget", 0)
    
    if not items:
        return {"n_items": 0, "budget": budget, "total_weight": 0, "avg_value": 0, "budget_ratio": 0}
    
    total_weight = sum(w for w, v in items)
    total_value = sum(v for w, v in items)
    avg_value = total_value / len(items) if items else 0
    budget_ratio = budget / total_weight if total_weight > 0 else 0
    
    return {
        "n_items": len(items),
        "budget": budget,
        "total_weight": total_weight,
        "avg_value": avg_value,
        "budget_ratio": budget_ratio,
    }


def extract_R1_lc45(probe):
    """LC45: jump distribution statistics."""
    nums = probe.get("nums", [])
    
    if not nums:
        return {"array_len": 0, "max_jump": 0, "min_jump": 0, "avg_jump": 0, "first_jump": 0}
    
    return {
        "array_len": len(nums),
        "max_jump": max(nums),
        "min_jump": min(nums),
        "avg_jump": sum(nums) / len(nums),
        "first_jump": nums[0],
    }


EXTRACTORS = {
    "lc322": extract_R1_lc322,
    "lc3946": extract_R1_lc3946,
    "lc45": extract_R1_lc45,
}


def build_R1(problem_class):
    """Build R1 feature matrix for a problem."""
    probes = load_probes(problem_class)
    extractor = EXTRACTORS[problem_class]
    
    features = {}
    for p in probes:
        pid = p["probe_id"]
        features[pid] = extractor(p)
    
    return features


def build_R2(features, seed=42):
    """Build R2: permuted-but-information-preserving encoding.
    
    For each feature column, independently permute values across probes.
    Preserves marginal distributions but destroys semantics.
    """
    probe_ids = list(features.keys())
    feature_names = list(features[probe_ids[0]].keys())
    
    rng = random.Random(seed)
    
    # Create permuted copies
    r2 = {pid: {} for pid in probe_ids}
    
    for fname in feature_names:
        # Extract values for this feature
        values = [features[pid][fname] for pid in probe_ids]
        
        # Create permutation
        permuted = values.copy()
        rng.shuffle(permuted)
        
        # Assign permuted values
        for pid, val in zip(probe_ids, permuted):
            r2[pid][fname] = val
    
    return r2


def features_to_phi(features, n_clusters=4, seed=42):
    """Convert feature dict to phi assignment via simple binning.
    
    Uses quantile-based binning per feature, then combines.
    """
    probe_ids = list(features.keys())
    feature_names = list(features[probe_ids[0]].keys())
    
    # Normalize each feature to [0, 1]
    normalized = {pid: {} for pid in probe_ids}
    for fname in feature_names:
        values = [features[pid][fname] for pid in probe_ids]
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val > min_val else 1
        
        for pid in probe_ids:
            normalized[pid][fname] = (features[pid][fname] - min_val) / range_val
    
    # Combine features into single score (equal weight)
    combined = {}
    for pid in probe_ids:
        combined[pid] = sum(normalized[pid][fname] for fname in feature_names) / len(feature_names)
    
    # Bin into n_clusters using quantiles
    sorted_vals = sorted(combined.values())
    n = len(sorted_vals)
    bin_edges = [sorted_vals[int(i * n / n_clusters)] for i in range(n_clusters)]
    bin_edges.append(float('inf'))
    
    phi = {}
    for pid in probe_ids:
        val = combined[pid]
        for i in range(n_clusters):
            if val <= bin_edges[i + 1]:
                phi[pid] = f"cluster_{i}"
                break
    
    return phi


def compute_failure_vectors(solver_evals, probe_ids):
    """Compute full binary failure vectors."""
    failure_vectors = {}
    for sid, results in solver_evals.items():
        vector = []
        for pid in probe_ids:
            passed = results.get(pid, True)
            vector.append(0 if passed else 1)
        failure_vectors[sid] = vector
    return failure_vectors


def compute_empirical_rates(failure_vectors, train_sids, probe_ids):
    """Compute empirical failure rates per test."""
    n_tests = len(probe_ids)
    rates = []
    for j in range(n_tests):
        fails = sum(1 for sid in train_sids if failure_vectors[sid][j] == 1)
        rate = fails / len(train_sids) if train_sids else 0
        rates.append(rate)
    return rates


def compute_family_rates(failure_vectors, phi, train_sids, probe_ids):
    """Compute empirical failure rates per family."""
    family_probes = defaultdict(list)
    for j, pid in enumerate(probe_ids):
        fam = phi.get(pid, "unknown")
        family_probes[fam].append(j)
    
    family_rates = {}
    for fam, indices in family_probes.items():
        fails = sum(1 for sid in train_sids for j in indices if failure_vectors[sid][j] == 1)
        total = len(train_sids) * len(indices)
        family_rates[fam] = fails / total if total > 0 else 0
    
    return family_rates, family_probes


def predict_failure_vector_bphi(family_rates, family_probes, probe_ids):
    """Predict failure vector using family-structured model."""
    predictions = [0.0] * len(probe_ids)
    for fam, indices in family_probes.items():
        rate = family_rates[fam]
        for j in indices:
            predictions[j] = rate
    return predictions


def compute_prediction_loss(true_vectors, pred_vectors, test_sids, probe_ids):
    """Compute prediction loss (log-likelihood)."""
    import math
    
    n_tests = len(probe_ids)
    total_loss = 0.0
    count = 0
    
    for sid in test_sids:
        true_vec = true_vectors[sid]
        pred_vec = pred_vectors
        
        for j in range(n_tests):
            true_val = true_vec[j]
            pred_prob = max(min(pred_vec[j], 0.999), 0.001)
            
            if true_val == 1:
                loss = -math.log(pred_prob)
            else:
                loss = -math.log(1 - pred_prob)
            
            total_loss += loss
            count += 1
    
    return total_loss / count if count > 0 else 0


def compute_mutual_information(failure_vectors, phi, probe_ids, train_sids):
    """Compute mutual information between family assignment and failure patterns."""
    import math
    
    family_probes = defaultdict(list)
    for j, pid in enumerate(probe_ids):
        fam = phi.get(pid, "unknown")
        family_probes[fam].append(j)
    
    family_rates = {}
    for fam, indices in family_probes.items():
        fails = sum(1 for sid in train_sids for j in indices if failure_vectors[sid][j] == 1)
        total = len(train_sids) * len(indices)
        family_rates[fam] = fails / total if total > 0 else 0
    
    all_fails = sum(sum(vec) for vec in [failure_vectors[sid] for sid in train_sids])
    all_total = len(train_sids) * len(probe_ids)
    overall_rate = all_fails / all_total if all_total > 0 else 0
    
    mi = 0.0
    for fam, indices in family_probes.items():
        p_fam = len(indices) / len(probe_ids)
        p_fail_given_fam = family_rates[fam]
        p_fail = overall_rate
        
        if p_fail_given_fam > 0 and p_fail > 0:
            mi += p_fam * p_fail_given_fam * math.log(p_fail_given_fam / p_fail)
        if (1 - p_fail_given_fam) > 0 and (1 - p_fail) > 0:
            mi += p_fam * (1 - p_fail_given_fam) * math.log((1 - p_fail_given_fam) / (1 - p_fail))
    
    return mi


# =============================================================================
# Main experiment
# =============================================================================

def run_representation_test(problem_class, to_input, oracle_fn, style):
    """Run representation invariance test for one problem."""
    print(f"\n{'='*70}")
    print(f"  REPRESENTATION INVARIANCE TEST: {problem_class.upper()}")
    print(f"{'='*70}")
    
    # Load data
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    print(f"\n  Probes: {len(probes)}")
    print(f"  Frozen solvers: {len(solver_evals)}")
    
    # Compute failure vectors
    failure_vectors = compute_failure_vectors(solver_evals, obs)
    
    # Split solvers into train/test (80/20)
    all_sids = sorted(solver_evals.keys())
    rng = random.Random(SEED)
    rng.shuffle(all_sids)
    split_idx = int(0.8 * len(all_sids))
    train_sids = all_sids[:split_idx]
    test_sids = all_sids[split_idx:]
    
    print(f"  Train solvers: {len(train_sids)}")
    print(f"  Test solvers: {len(test_sids)}")
    
    # Build R1 and R2 features
    R1_features = build_R1(problem_class)
    R2_features = build_R2(R1_features, seed=42)
    
    # Convert to phi assignments
    phi_R1 = features_to_phi(R1_features, n_clusters=4, seed=42)
    phi_R2 = features_to_phi(R2_features, n_clusters=4, seed=42)
    
    print(f"\n  R1 families: {len(set(phi_R1.values()))}")
    print(f"  R2 families: {len(set(phi_R2.values()))}")
    
    # Compute B0 baseline
    rates_b0 = compute_empirical_rates(failure_vectors, train_sids, obs)
    
    results = {}
    
    for name, phi in [("R1", phi_R1), ("R2", phi_R2)]:
        family_rates, family_probes = compute_family_rates(failure_vectors, phi, train_sids, obs)
        pred_bphi = predict_failure_vector_bphi(family_rates, family_probes, obs)
        
        loss_bphi = compute_prediction_loss(failure_vectors, pred_bphi, test_sids, obs)
        loss_b0 = compute_prediction_loss(failure_vectors, rates_b0, test_sids, obs)
        
        delta_gain = loss_b0 - loss_bphi
        mi = compute_mutual_information(failure_vectors, phi, obs, train_sids)
        
        results[name] = {
            "loss": loss_bphi,
            "delta_gain": delta_gain,
            "mutual_information": mi,
            "n_families": len(set(phi.values())),
        }
        
        print(f"\n  {name}:")
        print(f"    Loss: {loss_bphi:.6f}")
        print(f"    Delta gain: {delta_gain:.6f}")
        print(f"    MI: {mi:.6f}")
        print(f"    Families: {len(set(phi.values()))}")
    
    # Bootstrap CI for delta gain difference (R1 - R2)
    boot_deltas = []
    for _ in range(N_BOOTSTRAP):
        rng_boot = random.Random(SEED + len(boot_deltas))
        resampled_test = rng_boot.choices(test_sids, k=len(test_sids))
        
        # R1
        family_rates_R1, family_probes_R1 = compute_family_rates(failure_vectors, phi_R1, train_sids, obs)
        pred_R1 = predict_failure_vector_bphi(family_rates_R1, family_probes_R1, obs)
        loss_R1 = compute_prediction_loss(failure_vectors, pred_R1, resampled_test, obs)
        
        # R2
        family_rates_R2, family_probes_R2 = compute_family_rates(failure_vectors, phi_R2, train_sids, obs)
        pred_R2 = predict_failure_vector_bphi(family_rates_R2, family_probes_R2, obs)
        loss_R2 = compute_prediction_loss(failure_vectors, pred_R2, resampled_test, obs)
        
        # B0
        loss_b0_boot = compute_prediction_loss(failure_vectors, rates_b0, resampled_test, obs)
        
        delta_R1 = loss_b0_boot - loss_R1
        delta_R2 = loss_b0_boot - loss_R2
        
        boot_deltas.append(delta_R1 - delta_R2)
    
    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * N_BOOTSTRAP)]
    ci_hi = boot_deltas[int(0.975 * N_BOOTSTRAP)]
    
    delta_R1_R2 = results["R1"]["delta_gain"] - results["R2"]["delta_gain"]
    
    print(f"\n  Delta(R1 - R2):")
    print(f"    Point estimate: {delta_R1_R2:.6f}")
    print(f"    95% CI: [{ci_lo:.6f}, {ci_hi:.6f}]")
    
    # Classification
    if ci_lo > 0:
        classification = "representation-sensitive signal exists"
    elif ci_hi < 0:
        classification = "R2 outperforms R1 (unexpected)"
    else:
        classification = "representation-invariant null"
    
    print(f"\n  Classification: {classification}")
    
    return {
        "problem": problem_class,
        "train_test_split": {
            "train_size": len(train_sids),
            "test_size": len(test_sids),
        },
        "results": results,
        "delta_R1_R2": delta_R1_R2,
        "bootstrap_ci": {
            "point_estimate": delta_R1_R2,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
        },
        "classification": classification,
    }


if __name__ == "__main__":
    all_results = []
    
    # Run LC322
    all_results.append(run_representation_test("lc322", lc322_to_input, lc322_oracle, "single"))
    
    # Run LC3946
    all_results.append(run_representation_test("lc3946", lc3946_to_input, lc3946_oracle, "single"))
    
    # Run LC45
    all_results.append(run_representation_test("lc45", lc45_to_input, lc45_oracle, "single"))
    
    # Save results
    out_path = ROOT / "results" / "representation_invariance_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")
