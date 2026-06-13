"""MECHANISM_REBUILD_SPEC v1.0 — Input-structure partitions test."""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, extract_canonical_phi, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    b1_decision, c_genuine_decision, decision_loss_single,
    compute_deltaU, bootstrap_ci_deltaU,
    SEED, N_BOOTSTRAP,
    lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
)
from csse.define_phi_new import build_phi_new, validate_no_leakage


def c_count_decision(obs_fails, threshold):
    return "ACCEPT" if obs_fails <= threshold else "REJECT"


def find_best_threshold(solver_evals, phi, probe_ids, ground_truth):
    """Find T* that best approximates C_genuine decisions."""
    genuine_decisions = {}
    fail_counts = {}
    for sid, results in solver_evals.items():
        obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
        fail_counts[sid] = obs_fails
        family_fails = defaultdict(int)
        for pid in probe_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1
        genuine_decisions[sid] = c_genuine_decision(dict(family_fails))

    max_fails = max(fail_counts.values()) if fail_counts else 0
    best_T = 0
    best_agreement = -1.0
    for T in range(0, max_fails + 2):
        count_decisions = {sid: c_count_decision(fail_counts[sid], T) for sid in fail_counts}
        agreements = sum(1 for sid in genuine_decisions if genuine_decisions[sid] == count_decisions[sid])
        agreement_rate = agreements / len(genuine_decisions)
        if agreement_rate > best_agreement:
            best_agreement = agreement_rate
            best_T = T

    return best_T, best_agreement, genuine_decisions


def compute_family_signal(solver_evals, phi, probe_ids):
    """Compute family informativeness metrics."""
    n_solvers = len(solver_evals)
    
    # Compute failure distribution across families for each solver
    family_failures = defaultdict(list)
    for sid, results in solver_evals.items():
        fails_per_family = defaultdict(int)
        for pid in probe_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                fails_per_family[fam] += 1
        for fam, count in fails_per_family.items():
            family_failures[fam].append(count)
    
    # Concentration index: variance of failures per family / total failures
    total_failures_per_solver = []
    variances_per_solver = []
    for sid, results in solver_evals.items():
        fails_per_family = defaultdict(int)
        for pid in probe_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                fails_per_family[fam] += 1
        
        total_fails = sum(fails_per_family.values())
        total_failures_per_solver.append(total_fails)
        
        if total_fails > 0 and len(fails_per_family) > 1:
            counts = list(fails_per_family.values())
            mean = sum(counts) / len(counts)
            var = sum((c - mean) ** 2 for c in counts) / len(counts)
            variances_per_solver.append(var)
        else:
            variances_per_solver.append(0.0)
    
    avg_total = sum(total_failures_per_solver) / len(total_failures_per_solver) if total_failures_per_solver else 0
    avg_var = sum(variances_per_solver) / len(variances_per_solver) if variances_per_solver else 0
    
    concentration_index = avg_var / avg_total if avg_total > 0 else 0.0
    
    return {
        "avg_total_failures": avg_total,
        "avg_family_variance": avg_var,
        "concentration_index": concentration_index,
    }


def permutation_test(solver_evals, phi_new, probe_ids, ground_truth, observed_ids,
                     wrong_accept_cost, wrong_reject_cost, n_permutations=1000):
    """Permutation test: shuffle φ_new assignments and compute ΔU shift."""
    rng = random.Random(SEED)
    canonical_du = compute_deltaU(solver_evals, phi_new, observed_ids, ground_truth,
                                  wrong_accept_cost, wrong_reject_cost)
    
    perm_deltas = []
    for i in range(n_permutations):
        # Shuffle family assignments
        probe_list = list(phi_new.keys())
        shuffled_families = list(phi_new.values())
        rng.shuffle(shuffled_families)
        perm_phi = dict(zip(probe_list, shuffled_families))
        
        perm_du = compute_deltaU(solver_evals, perm_phi, observed_ids, ground_truth,
                                 wrong_accept_cost, wrong_reject_cost)
        perm_deltas.append(perm_du)
    
    perm_deltas_sorted = sorted(perm_deltas)
    n_below = sum(1 for d in perm_deltas_sorted if d < canonical_du)
    percentile = (n_below / n_permutations) * 100
    
    mean_shift = sum(perm_deltas) / len(perm_deltas)
    std_shift = (sum((d - mean_shift) ** 2 for d in perm_deltas) / len(perm_deltas)) ** 0.5
    
    return {
        "canonical_du": canonical_du,
        "mean_shift": mean_shift,
        "std_shift": std_shift,
        "canonical_percentile": percentile,
    }


def run_experiment(problem_class, to_input, oracle_fn, style):
    """Run full experiment for one problem."""
    print(f"\n{'='*70}")
    print(f"  MECHANISM REBUILD: {problem_class.upper()}")
    print(f"{'='*70}")
    
    probes = load_probes(problem_class)
    phi_new = build_phi_new(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    print(f"\n  Probes: {len(probes)}")
    print(f"  Families: {len(set(phi_new.values()))}")
    print(f"  Frozen solvers: {len(solver_evals)}")
    
    # Validate no leakage
    validate_no_leakage(phi_new, problem_class)
    
    # Find best threshold
    T_star, agreement, genuine_dec = find_best_threshold(solver_evals, phi_new, obs, ground_truth)
    print(f"\n  Best threshold T*: {T_star}")
    print(f"  Agreement with C_genuine: {agreement:.4f}")
    
    # Compute family signal
    family_signal = compute_family_signal(solver_evals, phi_new, obs)
    print(f"\n  Family signal:")
    print(f"    Avg total failures: {family_signal['avg_total_failures']:.4f}")
    print(f"    Avg family variance: {family_signal['avg_family_variance']:.4f}")
    print(f"    Concentration index: {family_signal['concentration_index']:.4f}")
    
    # Three-way comparison at different lambda values
    three_way = {}
    for lam in [10, 50, 100]:
        wa = 1.0
        wr = float(lam)
        
        def b1_fn(obs_fails, family_fails):
            return b1_decision(obs_fails)
        def cgen_fn(obs_fails, family_fails):
            return c_genuine_decision(family_fails)
        def ccons_fn(obs_fails, family_fails):
            return c_count_decision(obs_fails, T_star)
        
        du_b1_cgen, lo_b1_cgen, hi_b1_cgen = bootstrap_ci_deltaU(
            solver_evals, phi_new, obs, ground_truth, wa, wr, N_BOOTSTRAP
        )
        
        # Compute deltaU for B1 vs C_conservative
        from csse.mechanism_separation import compute_deltaU_two_classifiers, bootstrap_ci_two_classifiers
        du_b1_ccons, lo_b1_ccons, hi_b1_ccons = bootstrap_ci_two_classifiers(
            solver_evals, phi_new, obs, ground_truth, b1_fn, ccons_fn, wa, wr
        )
        du_ccons_cgen, lo_ccons_cgen, hi_ccons_cgen = bootstrap_ci_two_classifiers(
            solver_evals, phi_new, obs, ground_truth, ccons_fn, cgen_fn, wa, wr
        )
        
        three_way[f"lambda_{lam}"] = {
            "deltaU_b1_cgen": du_b1_cgen,
            "ci": [lo_b1_cgen, hi_b1_cgen],
            "deltaU_b1_ccons": du_b1_ccons,
            "ci": [lo_b1_ccons, hi_b1_ccons],
            "deltaU_ccons_cgen": du_ccons_cgen,
            "ci": [lo_ccons_cgen, hi_ccons_cgen],
        }
        
        print(f"\n  lambda={lam}:")
        print(f"    B1 vs C_genuine: {du_b1_cgen:.6f} [{lo_b1_cgen:.6f}, {hi_b1_cgen:.6f}]")
        print(f"    B1 vs C_conservative: {du_b1_ccons:.6f} [{lo_b1_ccons:.6f}, {hi_b1_ccons:.6f}]")
        print(f"    C_conservative vs C_genuine: {du_ccons_cgen:.6f} [{lo_ccons_cgen:.6f}, {hi_ccons_cgen:.6f}]")
    
    # Permutation test at lambda=50
    perm_result = permutation_test(solver_evals, phi_new, obs, ground_truth, obs, 1.0, 50.0)
    print(f"\n  Permutation test (lambda=50):")
    print(f"    Canonical DU: {perm_result['canonical_du']:.6f}")
    print(f"    Mean shift: {perm_result['mean_shift']:.6f}")
    print(f"    Std shift: {perm_result['std_shift']:.6f}")
    print(f"    Canonical percentile: {perm_result['canonical_percentile']:.1f}")
    
    # Classification
    if perm_result["canonical_percentile"] >= 80:
        classification = "ROBUST"
    elif perm_result["canonical_percentile"] >= 50:
        classification = "WEAK"
    else:
        classification = "NULL"
    
    print(f"\n  Classification: {classification}")
    
    return {
        "problem": problem_class,
        "families": {
            "definition": "input-structure-based",
            "distribution": dict(defaultdict(int, {fam: sum(1 for v in phi_new.values() if v == fam) for fam in set(phi_new.values())})),
        },
        "best_threshold_T": T_star,
        "agreement_rate": agreement,
        "family_signal": family_signal,
        "three_way": three_way,
        "permutation_test": perm_result,
        "classification": classification,
    }


if __name__ == "__main__":
    results = []
    
    # Run LC3946 first (sanity check)
    results.append(run_experiment("lc3946", lc3946_to_input, lc3946_oracle, "single"))
    
    # Run LC322
    results.append(run_experiment("lc322", lc322_to_input, lc322_oracle, "single"))
    
    # Save results
    out_path = ROOT / "results" / "mechanism_rebuild_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")
