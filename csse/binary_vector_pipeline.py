"""Corrected pipeline: full binary failure vectors (not scalar count).

Outcome = full binary failure vector v_s = [f1, f2, ..., fn] where fi ∈ {0,1}
φ = partition of test indices
Model comparison = prediction of failure patterns, not accept/reject scalar

B0: independent Bernoulli model per test
Bφ: structured dependence model via families
B_rand: random grouping baseline
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
)
from csse.define_phi_frozen import build_phi_frozen
from csse.define_phi_structured import build_phi_structured, build_phi_random


def compute_failure_vectors(solver_evals, probe_ids):
    """Compute full binary failure vectors for all solvers.
    
    Returns {solver_id: [f1, f2, ..., fn]} where fi = 1 if solver fails on probe i.
    """
    failure_vectors = {}
    for sid, results in solver_evals.items():
        vector = []
        for pid in probe_ids:
            passed = results.get(pid, True)
            vector.append(0 if passed else 1)
        failure_vectors[sid] = vector
    return failure_vectors


def compute_empirical_rates(failure_vectors, train_sids, probe_ids):
    """Compute empirical failure rates per test (B0 model)."""
    n_tests = len(probe_ids)
    rates = []
    for j in range(n_tests):
        fails = sum(1 for sid in train_sids if failure_vectors[sid][j] == 1)
        rate = fails / len(train_sids) if train_sids else 0
        rates.append(rate)
    return rates


def compute_family_rates(failure_vectors, phi, train_sids, probe_ids):
    """Compute empirical failure rates per family (Bφ model)."""
    # Group probes by family
    family_probes = defaultdict(list)
    for j, pid in enumerate(probe_ids):
        fam = phi.get(pid, "unknown")
        family_probes[fam].append(j)
    
    # Compute rate per family
    family_rates = {}
    for fam, indices in family_probes.items():
        fails = 0
        total = 0
        for sid in train_sids:
            for j in indices:
                fails += failure_vectors[sid][j]
                total += 1
        family_rates[fam] = fails / total if total > 0 else 0
    
    return family_rates, family_probes


def predict_failure_vector_b0(rates, probe_ids):
    """Predict failure vector using independent Bernoulli model (B0)."""
    return rates  # Just return the rates as predictions


def predict_failure_vector_bphi(family_rates, family_probes, probe_ids):
    """Predict failure vector using family-structured model (Bφ)."""
    predictions = [0.0] * len(probe_ids)
    for fam, indices in family_probes.items():
        rate = family_rates[fam]
        for j in indices:
            predictions[j] = rate
    return predictions


def compute_prediction_loss(true_vectors, pred_vectors, test_sids, probe_ids):
    """Compute prediction loss (log-likelihood) for failure vectors."""
    n_tests = len(probe_ids)
    total_loss = 0.0
    count = 0
    
    for sid in test_sids:
        true_vec = true_vectors[sid]
        pred_vec = pred_vectors
        
        for j in range(n_tests):
            true_val = true_vec[j]
            pred_prob = max(min(pred_vec[j], 0.999), 0.001)  # Clip to avoid log(0)
            
            # Binary cross-entropy loss
            if true_val == 1:
                loss = -log(pred_prob)
            else:
                loss = -log(1 - pred_prob)
            
            total_loss += loss
            count += 1
    
    return total_loss / count if count > 0 else 0


def log(x):
    """Natural log."""
    import math
    return math.log(x)


def compute_mutual_information(failure_vectors, phi, probe_ids, train_sids):
    """Compute mutual information between family assignment and failure patterns."""
    # Group probes by family
    family_probes = defaultdict(list)
    for j, pid in enumerate(probe_ids):
        fam = phi.get(pid, "unknown")
        family_probes[fam].append(j)
    
    # Compute failure rate per family
    family_rates = {}
    for fam, indices in family_probes.items():
        fails = sum(1 for sid in train_sids for j in indices if failure_vectors[sid][j] == 1)
        total = len(train_sids) * len(indices)
        family_rates[fam] = fails / total if total > 0 else 0
    
    # Overall failure rate
    all_fails = sum(sum(vec) for vec in [failure_vectors[sid] for sid in train_sids])
    all_total = len(train_sids) * len(probe_ids)
    overall_rate = all_fails / all_total if all_total > 0 else 0
    
    # Mutual information (simplified)
    mi = 0.0
    for fam, indices in family_probes.items():
        p_fam = len(indices) / len(probe_ids)
        p_fail_given_fam = family_rates[fam]
        p_fail = overall_rate
        
        if p_fail_given_fam > 0 and p_fail > 0:
            mi += p_fam * p_fail_given_fam * log(p_fail_given_fam / p_fail)
        if (1 - p_fail_given_fam) > 0 and (1 - p_fail) > 0:
            mi += p_fam * (1 - p_fail_given_fam) * log((1 - p_fail_given_fam) / (1 - p_fail))
    
    return mi


def run_full_pipeline(problem_class, to_input, oracle_fn, style):
    """Run full pipeline with binary failure vectors."""
    print(f"\n{'='*70}")
    print(f"  FULL PIPELINE (Binary Vectors): {problem_class.upper()}")
    print(f"{'='*70}")
    
    # Load data
    probes = load_probes(problem_class)
    phi_frozen = build_phi_frozen(problem_class)
    phi_struct = build_phi_structured(problem_class, k=4)
    phi_rand = build_phi_random(problem_class, k=4)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    print(f"\n  Probes: {len(probes)}")
    print(f"  Frozen phi families: {len(set(phi_frozen.values()))}")
    print(f"  Structured phi families: {len(set(phi_struct.values()))}")
    print(f"  Random phi families: {len(set(phi_rand.values()))}")
    print(f"  Frozen solvers: {len(solver_evals)}")
    
    # Compute failure vectors
    failure_vectors = compute_failure_vectors(solver_evals, obs)
    print(f"  Failure vector dimension: {len(obs)}")
    
    # Split solvers into train/test (80/20)
    all_sids = sorted(solver_evals.keys())
    rng = random.Random(SEED)
    rng.shuffle(all_sids)
    split_idx = int(0.8 * len(all_sids))
    train_sids = all_sids[:split_idx]
    test_sids = all_sids[split_idx:]
    
    print(f"  Train solvers: {len(train_sids)}")
    print(f"  Test solvers: {len(test_sids)}")
    
    # Compute models
    # B0: independent Bernoulli
    rates_b0 = compute_empirical_rates(failure_vectors, train_sids, obs)
    pred_b0 = predict_failure_vector_b0(rates_b0, obs)
    
    # Bφ_frozen: family-structured (frozen phi)
    family_rates_frozen, family_probes_frozen = compute_family_rates(
        failure_vectors, phi_frozen, train_sids, obs
    )
    pred_bphi_frozen = predict_failure_vector_bphi(family_rates_frozen, family_probes_frozen, obs)
    
    # Bφ_structured: family-structured (structured phi)
    family_rates_struct, family_probes_struct = compute_family_rates(
        failure_vectors, phi_struct, train_sids, obs
    )
    pred_bphi_struct = predict_failure_vector_bphi(family_rates_struct, family_probes_struct, obs)
    
    # B_rand: random grouping baseline
    family_rates_rand, family_probes_rand = compute_family_rates(
        failure_vectors, phi_rand, train_sids, obs
    )
    pred_brand = predict_failure_vector_bphi(family_rates_rand, family_probes_rand, obs)
    
    # Compute prediction losses
    loss_b0 = compute_prediction_loss(failure_vectors, pred_b0, test_sids, obs)
    loss_bphi_frozen = compute_prediction_loss(failure_vectors, pred_bphi_frozen, test_sids, obs)
    loss_bphi_struct = compute_prediction_loss(failure_vectors, pred_bphi_struct, test_sids, obs)
    loss_brand = compute_prediction_loss(failure_vectors, pred_brand, test_sids, obs)
    
    # Delta gains
    delta_frozen_b0 = loss_b0 - loss_bphi_frozen
    delta_struct_b0 = loss_b0 - loss_bphi_struct
    delta_rand_b0 = loss_b0 - loss_brand
    
    print(f"\n  Prediction losses (log-likelihood):")
    print(f"    B0 (independent): {loss_b0:.6f}")
    print(f"    B_phi_frozen: {loss_bphi_frozen:.6f}")
    print(f"    B_phi_structured: {loss_bphi_struct:.6f}")
    print(f"    B_rand: {loss_brand:.6f}")
    
    print(f"\n  Delta gains (B0 - B_model):")
    print(f"    Delta(B0 - B_phi_frozen): {delta_frozen_b0:.6f}")
    print(f"    Delta(B0 - B_phi_structured): {delta_struct_b0:.6f}")
    print(f"    Delta(B0 - B_rand): {delta_rand_b0:.6f}")
    
    # Mutual information
    mi_frozen = compute_mutual_information(failure_vectors, phi_frozen, obs, train_sids)
    mi_struct = compute_mutual_information(failure_vectors, phi_struct, obs, train_sids)
    mi_rand = compute_mutual_information(failure_vectors, phi_rand, obs, train_sids)
    
    print(f"\n  Mutual information (family vs failure):")
    print(f"    MI(phi_frozen): {mi_frozen:.6f}")
    print(f"    MI(phi_structured): {mi_struct:.6f}")
    print(f"    MI(phi_rand): {mi_rand:.6f}")
    
    # Bootstrap CI for delta gain (frozen phi)
    boot_deltas = []
    for _ in range(N_BOOTSTRAP):
        rng_boot = random.Random(SEED + len(boot_deltas))
        resampled_test = rng_boot.choices(test_sids, k=len(test_sids))
        
        loss_b0_boot = compute_prediction_loss(failure_vectors, pred_b0, resampled_test, obs)
        loss_bphi_boot = compute_prediction_loss(failure_vectors, pred_bphi_frozen, resampled_test, obs)
        boot_deltas.append(loss_b0_boot - loss_bphi_boot)
    
    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * N_BOOTSTRAP)]
    ci_hi = boot_deltas[int(0.975 * N_BOOTSTRAP)]
    
    print(f"\n  Bootstrap CI for Delta(B0 - B_phi_frozen):")
    print(f"    Point estimate: {delta_frozen_b0:.6f}")
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
        "outcome_representation": "binary_failure_vector",
        "frozen_phi": {
            "distribution": dict(defaultdict(int, {fam: sum(1 for v in phi_frozen.values() if v == fam) for fam in set(phi_frozen.values())})),
        },
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
        "prediction_losses": {
            "b0": loss_b0,
            "bphi_frozen": loss_bphi_frozen,
            "bphi_structured": loss_bphi_struct,
            "brand": loss_brand,
        },
        "delta_gains": {
            "frozen": delta_frozen_b0,
            "structured": delta_struct_b0,
            "random": delta_rand_b0,
        },
        "mutual_information": {
            "frozen": mi_frozen,
            "structured": mi_struct,
            "random": mi_rand,
        },
        "bootstrap_ci": {
            "point_estimate": delta_frozen_b0,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
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
    out_path = ROOT / "results" / "binary_vector_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")
