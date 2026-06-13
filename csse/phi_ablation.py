"""Phi ablation tests: decompose phi into components A, B, C.

A = coarse structural grouping (input type / size regime)
B = mid-level structural interaction (shared constraints / patterns)
C = fine-grained residual grouping (anything left)
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
from csse.define_phi_structured import (
    extract_features_lc322, extract_features_lc3946,
    normalize_features, kmeans_cluster
)


def decompose_phi_A_lc322(probe):
    """Coarse structural grouping for LC322.
    
    A: amount regime (tiny/small/medium/large)
    """
    amount = probe.get("amount", 0)
    
    if amount <= 5:
        return "tiny"
    elif amount <= 20:
        return "small"
    elif amount <= 100:
        return "medium"
    else:
        return "large"


def decompose_phi_B_lc322(probe):
    """Mid-level structural interaction for LC322.
    
    B: coin structure (canonical/non-canonical, coin count)
    """
    coins = probe.get("coins", [])
    
    if not coins:
        return "empty"
    
    # Check if canonical
    canonical_sets = [[1], [1, 5], [1, 5, 10], [1, 5, 10, 25], [1, 2, 5, 10], [1, 2, 5, 10, 50]]
    is_canonical = sorted(coins) in canonical_sets
    
    if is_canonical:
        return f"canonical_{len(coins)}"
    else:
        return f"noncanonical_{len(coins)}"


def decompose_phi_C_lc322(probe):
    """Fine-grained residual grouping for LC322.
    
    C: specific coin denomination patterns
    """
    coins = probe.get("coins", [])
    amount = probe.get("amount", 0)
    
    if not coins:
        return "empty"
    
    # Specific patterns
    if coins == [1]:
        return "single_coin"
    elif len(coins) == 2 and 1 in coins:
        return "two_coins_with_one"
    elif len(coins) >= 3 and all(c > 1 for c in coins):
        return "many_coins_no_one"
    else:
        return "other"


def decompose_phi_A_lc45(probe):
    """Coarse structural grouping for LC45.
    
    A: array length regime (short/medium/long)
    """
    nums = probe.get("nums", [])
    n = len(nums)
    
    if n <= 4:
        return "short"
    elif n <= 7:
        return "medium"
    else:
        return "long"


def decompose_phi_B_lc45(probe):
    """Mid-level structural interaction for LC45.
    
    B: max jump value regime (small/medium/large) - affects reachability
    """
    nums = probe.get("nums", [])
    max_jump = max(nums) if nums else 0
    
    if max_jump <= 1:
        return "tiny_jumps"
    elif max_jump <= 3:
        return "small_jumps"
    elif max_jump <= 5:
        return "medium_jumps"
    else:
        return "large_jumps"


def decompose_phi_C_lc45(probe):
    """Fine-grained residual grouping for LC45.
    
    C: trap structure - does first element trap naive max-jump strategy?
    """
    nums = probe.get("nums", [])
    if len(nums) < 2:
        return "trivial"
    
    # If nums[0] is small relative to array, naive max-jump gets stuck
    first_jump = nums[0]
    array_len = len(nums)
    
    if first_jump >= array_len - 1:
        return "one_step_reachable"
    elif first_jump <= 1:
        return "trapped_start"
    elif nums[1] == 1 and first_jump < array_len - 1:
        return "second_element_trap"
    else:
        return "open_path"


def decompose_phi_A_lc3946(probe):
    """Coarse structural grouping for LC3946.
    
    A: item count regime (few/medium/many)
    """
    items = probe.get("items", [])
    n_items = len(items)
    
    if n_items <= 3:
        return "few"
    elif n_items <= 5:
        return "medium"
    else:
        return "many"


def decompose_phi_B_lc3946(probe):
    """Mid-level structural interaction for LC3946.
    
    B: budget tightness relative to items
    """
    items = probe.get("items", [])
    budget = probe.get("budget", 0)
    
    if not items:
        return "empty"
    
    total_weight = sum(w for w, v in items)
    budget_ratio = budget / total_weight if total_weight > 0 else 0
    
    if budget_ratio < 0.3:
        return "very_tight"
    elif budget_ratio < 0.6:
        return "tight"
    elif budget_ratio < 1.0:
        return "moderate"
    else:
        return "loose"


def decompose_phi_C_lc3946(probe):
    """Fine-grained residual grouping for LC3946.
    
    C: value-to-weight ratio patterns
    """
    items = probe.get("items", [])
    
    if not items:
        return "empty"
    
    # Compute value-to-weight ratios
    ratios = [v / w if w > 0 else 0 for w, v in items]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    
    if avg_ratio < 0.5:
        return "low_value_density"
    elif avg_ratio < 1.0:
        return "medium_value_density"
    else:
        return "high_value_density"


def build_phi_decomposed(problem_class, component):
    """Build decomposed phi for a problem class."""
    probes = load_probes(problem_class)
    
    if problem_class == "lc322":
        if component == "A":
            phi_fn = decompose_phi_A_lc322
        elif component == "B":
            phi_fn = decompose_phi_B_lc322
        elif component == "C":
            phi_fn = decompose_phi_C_lc322
        else:
            raise ValueError(f"Unknown component: {component}")
    elif problem_class == "lc3946":
        if component == "A":
            phi_fn = decompose_phi_A_lc3946
        elif component == "B":
            phi_fn = decompose_phi_B_lc3946
        elif component == "C":
            phi_fn = decompose_phi_C_lc3946
        else:
            raise ValueError(f"Unknown component: {component}")
    elif problem_class == "lc45":
        if component == "A":
            phi_fn = decompose_phi_A_lc45
        elif component == "B":
            phi_fn = decompose_phi_B_lc45
        elif component == "C":
            phi_fn = decompose_phi_C_lc45
        else:
            raise ValueError(f"Unknown component: {component}")
    else:
        raise ValueError(f"Unknown problem class: {problem_class}")
    
    phi = {}
    for p in probes:
        pid = p["probe_id"]
        phi[pid] = phi_fn(p)
    
    return phi


def build_phi_AB(problem_class):
    """Build combined A+B phi."""
    phi_A = build_phi_decomposed(problem_class, "A")
    phi_B = build_phi_decomposed(problem_class, "B")
    
    # Combine A and B
    phi_AB = {}
    for pid in phi_A:
        phi_AB[pid] = f"{phi_A[pid]}_{phi_B[pid]}"
    
    return phi_AB


def build_phi_ABC(problem_class):
    """Build combined A+B+C phi (full decomposition)."""
    phi_A = build_phi_decomposed(problem_class, "A")
    phi_B = build_phi_decomposed(problem_class, "B")
    phi_C = build_phi_decomposed(problem_class, "C")
    
    # Combine A, B, and C
    phi_ABC = {}
    for pid in phi_A:
        phi_ABC[pid] = f"{phi_A[pid]}_{phi_B[pid]}_{phi_C[pid]}"
    
    return phi_ABC


def build_phi_rand(problem_class):
    """Build random phi baseline."""
    probes = load_probes(problem_class)
    probe_ids = [p["probe_id"] for p in probes]
    
    rng = random.Random(42)
    k = 4
    assignments = [rng.randint(0, k - 1) for _ in range(len(probes))]
    
    phi = {}
    for pid, cluster in zip(probe_ids, assignments):
        phi[pid] = f"random_{cluster}"
    
    return phi


def build_phi_noise(problem_class, solver_evals, probe_ids):
    """Build noise phi (random reassignment per solver)."""
    # For each solver, randomly reassign probe families
    # This breaks any systematic relationship between phi and outcomes
    rng = random.Random(42)
    
    # Get canonical phi to get family count
    from csse.define_phi_frozen import build_phi_frozen
    phi_canonical = build_phi_frozen(problem_class)
    n_families = len(set(phi_canonical.values()))
    
    # Random reassignment
    phi_noise = {}
    for pid in probe_ids:
        phi_noise[pid] = f"noise_{rng.randint(0, n_families - 1)}"
    
    return phi_noise


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


def run_ablation(problem_class, to_input, oracle_fn, style):
    """Run ablation experiments for one problem."""
    print(f"\n{'='*70}")
    print(f"  PHI ABLATION: {problem_class.upper()}")
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
    
    # Build phi variants
    phi_A = build_phi_decomposed(problem_class, "A")
    phi_B = build_phi_decomposed(problem_class, "B")
    phi_C = build_phi_decomposed(problem_class, "C")
    phi_AB = build_phi_AB(problem_class)
    phi_ABC = build_phi_ABC(problem_class)
    phi_rand = build_phi_rand(problem_class)
    phi_noise = build_phi_noise(problem_class, solver_evals, obs)
    
    # Compute B0 baseline
    rates_b0 = compute_empirical_rates(failure_vectors, train_sids, obs)
    
    # Compute predictions for each phi variant
    phi_variants = {
        "A": phi_A,
        "B": phi_B,
        "C": phi_C,
        "AB": phi_AB,
        "ABC": phi_ABC,
        "rand": phi_rand,
        "noise": phi_noise,
    }
    
    results = {}
    
    for name, phi in phi_variants.items():
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
    
    # Bootstrap CI for delta gain of ABC vs B0
    boot_deltas = []
    for _ in range(N_BOOTSTRAP):
        rng_boot = random.Random(SEED + len(boot_deltas))
        resampled_test = rng_boot.choices(test_sids, k=len(test_sids))
        
        loss_b0_boot = compute_prediction_loss(failure_vectors, rates_b0, resampled_test, obs)
        
        family_rates, family_probes = compute_family_rates(failure_vectors, phi_ABC, train_sids, obs)
        pred_bphi = predict_failure_vector_bphi(family_rates, family_probes, obs)
        loss_bphi_boot = compute_prediction_loss(failure_vectors, pred_bphi, resampled_test, obs)
        
        boot_deltas.append(loss_b0_boot - loss_bphi_boot)
    
    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * N_BOOTSTRAP)]
    ci_hi = boot_deltas[int(0.975 * N_BOOTSTRAP)]
    
    print(f"\n  Bootstrap CI for Delta(B0 - B_phi_ABC):")
    print(f"    Point estimate: {results['ABC']['delta_gain']:.6f}")
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
        "train_test_split": {
            "train_size": len(train_sids),
            "test_size": len(test_sids),
        },
        "results": results,
        "bootstrap_ci": {
            "point_estimate": results["ABC"]["delta_gain"],
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
        },
        "classification": classification,
    }


if __name__ == "__main__":
    all_results = []
    
    # Run LC322 first
    all_results.append(run_ablation("lc322", lc322_to_input, lc322_oracle, "single"))
    
    # Run LC3946
    all_results.append(run_ablation("lc3946", lc3946_to_input, lc3946_oracle, "single"))
    
    # Run LC45
    all_results.append(run_ablation("lc45", lc45_to_input, lc45_oracle, "single"))
    
    # Save results
    out_path = ROOT / "results" / "phi_ablation_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")
