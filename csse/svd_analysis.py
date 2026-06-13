"""Low-rank analysis of failure matrices.

Compare LC3946 vs LC322 using SVD to determine:
- Intrinsic dimensionality
- Reconstruction fidelity
- Separability in latent space
- Stability across train/test
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
    SEED, lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
)


def compute_failure_matrix(problem_class, to_input, oracle_fn, style):
    """Compute binary failure matrix (solvers x probes)."""
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    sids = sorted(solver_evals.keys())
    failure_matrix = []
    for sid in sids:
        vector = []
        for pid in obs:
            passed = solver_evals[sid].get(pid, True)
            vector.append(0 if passed else 1)
        failure_matrix.append(vector)
    
    return sids, obs, failure_matrix, ground_truth


def simple_svd(matrix):
    """Compute SVD using power iteration (no numpy dependency)."""
    import numpy as np
    
    # Convert to numpy for SVD
    M = np.array(matrix, dtype=float)
    
    # Center the data (subtract mean)
    M = M - M.mean(axis=0)
    
    # Compute SVD
    U, S, Vt = np.linalg.svd(M, full_matrices=False)
    
    return U, S, Vt


def compute_reconstruction_error(M, U, S, Vt, rank):
    """Compute reconstruction error for given rank."""
    import numpy as np
    
    M_approx = U[:, :rank] @ np.diag(S[:rank]) @ Vt[:rank, :]
    error = np.linalg.norm(M - M_approx, 'fro') / np.linalg.norm(M, 'fro')
    return error


def compute_svd_analysis(problem_class, to_input, oracle_fn, style):
    """Full SVD analysis for one problem."""
    print(f"\n{'='*70}")
    print(f"  SVD ANALYSIS: {problem_class.upper()}")
    print(f"{'='*70}")
    
    sids, obs, fm, gt = compute_failure_matrix(problem_class, to_input, oracle_fn, style)
    
    print(f"\n  Solvers: {len(sids)}")
    print(f"  Probes: {len(obs)}")
    print(f"  Matrix shape: {len(sids)} x {len(obs)}")
    
    # Compute SVD
    U, S, Vt = simple_svd(fm)
    
    # Singular values
    print(f"\n  === SINGULAR VALUES ===")
    total_var = sum(s**2 for s in S)
    for i, s in enumerate(S):
        var_explained = s**2 / total_var * 100
        cumulative = sum(sv**2 for sv in S[:i+1]) / total_var * 100
        print(f"    Rank {i+1}: singular_value={s:.4f}, variance={var_explained:.1f}%, cumulative={cumulative:.1f}%")
    
    # Reconstruction error for different ranks
    print(f"\n  === RECONSTRUCTION ERROR ===")
    for rank in range(1, min(len(sids), len(obs)) + 1):
        error = compute_reconstruction_error(fm, U, S, Vt, rank)
        print(f"    Rank {rank}: error={error:.4f}")
    
    # Intrinsic dimensionality (90% variance threshold)
    cumulative_var = 0
    intrinsic_dim = 0
    for i, s in enumerate(S):
        cumulative_var += s**2
        if cumulative_var / total_var >= 0.9:
            intrinsic_dim = i + 1
            break
    
    print(f"\n  Intrinsic dimensionality (90% variance): {intrinsic_dim}")
    
    # Compute latent space coordinates
    import numpy as np
    M = np.array(fm, dtype=float)
    M = M - M.mean(axis=0)
    
    # Project onto top 2 components
    latent_2d = M @ Vt[:2, :].T
    
    # Separability in latent space
    print(f"\n  === SEPARABILITY IN LATENT SPACE ===")
    
    # Compute cluster centers
    correct_indices = [i for i, sid in enumerate(sids) if gt.get(sid, False)]
    incorrect_indices = [i for i, sid in enumerate(sids) if not gt.get(sid, False)]
    
    if correct_indices and incorrect_indices:
        correct_center = latent_2d[correct_indices].mean(axis=0)
        incorrect_center = latent_2d[incorrect_indices].mean(axis=0)
        
        # Distance between centers
        center_dist = np.linalg.norm(correct_center - incorrect_center)
        
        # Within-cluster spread
        correct_spread = np.mean([np.linalg.norm(latent_2d[i] - correct_center) for i in correct_indices])
        incorrect_spread = np.mean([np.linalg.norm(latent_2d[i] - incorrect_center) for i in incorrect_indices])
        
        print(f"  Correct center: {correct_center}")
        print(f"  Incorrect center: {incorrect_center}")
        print(f"  Center distance: {center_dist:.4f}")
        print(f"  Correct spread: {correct_spread:.4f}")
        print(f"  Incorrect spread: {incorrect_spread:.4f}")
        print(f"  Ratio (distance/spread): {center_dist / (correct_spread + incorrect_spread):.4f}")
    
    return {
        "singular_values": S.tolist(),
        "intrinsic_dim": intrinsic_dim,
        "total_variance": total_var,
        "reconstruction_errors": {
            rank: compute_reconstruction_error(fm, U, S, Vt, rank)
            for rank in range(1, min(len(sids), len(obs)) + 1)
        },
        "latent_2d": latent_2d.tolist(),
    }


def run_train_test_svd(problem_class, to_input, oracle_fn, style):
    """Run SVD analysis on train/test split."""
    print(f"\n{'='*70}")
    print(f"  TRAIN/TEST SVD: {problem_class.upper()}")
    print(f"{'='*70}")
    
    sids, obs, fm, gt = compute_failure_matrix(problem_class, to_input, oracle_fn, style)
    
    # Split solvers
    rng = random.Random(SEED)
    indices = list(range(len(sids)))
    rng.shuffle(indices)
    
    split_idx = int(0.8 * len(indices))
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    train_sids = [sids[i] for i in train_idx]
    test_sids = [sids[i] for i in test_idx]
    fm_train = [fm[i] for i in train_idx]
    fm_test = [fm[i] for i in test_idx]
    
    print(f"  Train: {len(train_sids)}, Test: {len(test_sids)}")
    
    # SVD on train
    U_train, S_train, Vt_train = simple_svd(fm_train)
    
    # SVD on test
    U_test, S_test, Vt_test = simple_svd(fm_test)
    
    # Compare singular value spectra
    print(f"\n  === SINGULAR VALUE COMPARISON ===")
    print(f"  {'Rank':<6} | {'Train SV':>10} | {'Test SV':>10} | {'Ratio':>8}")
    print("  " + "-"*40)
    
    for i in range(min(5, len(S_train), len(S_test))):
        ratio = S_test[i] / S_train[i] if S_train[i] > 0 else 0
        print(f"  {i+1:<6} | {S_train[i]:>10.4f} | {S_test[i]:>10.4f} | {ratio:>8.4f}")
    
    # Reconstruction error comparison
    print(f"\n  === RECONSTRUCTION ERROR COMPARISON ===")
    for rank in [1, 2, 3]:
        if rank <= len(S_train) and rank <= len(S_test):
            error_train = compute_reconstruction_error(fm_train, U_train, S_train, Vt_train, rank)
            error_test = compute_reconstruction_error(fm_test, U_test, V_test, Vt_test, rank)
            print(f"  Rank {rank}: train={error_train:.4f}, test={error_test:.4f}")
    
    return {
        "train_singular_values": S_train.tolist(),
        "test_singular_values": S_test.tolist(),
    }


if __name__ == "__main__":
    import numpy as np
    
    # Run full SVD analysis
    lc3946_results = compute_svd_analysis("lc3946", lc3946_to_input, lc3946_oracle, "single")
    lc322_results = compute_svd_analysis("lc322", lc322_to_input, lc322_oracle, "single")
    
    # Comparison summary
    print(f"\n{'='*70}")
    print(f"  COMPARISON SUMMARY")
    print(f"{'='*70}")
    
    print(f"\n  {'Metric':<30} | {'LC3946':>10} | {'LC322':>10}")
    print("  " + "-"*55)
    
    print(f"  {'Intrinsic dimensionality':<30} | {lc3946_results['intrinsic_dim']:>10} | {lc322_results['intrinsic_dim']:>10}")
    print(f"  {'Rank-1 error':<30} | {lc3946_results['reconstruction_errors'][1]:>10.4f} | {lc322_results['reconstruction_errors'][1]:>10.4f}")
    print(f"  {'Rank-2 error':<30} | {lc3946_results['reconstruction_errors'][2]:>10.4f} | {lc322_results['reconstruction_errors'][2]:>10.4f}")
    print(f"  {'Rank-3 error':<30} | {lc3946_results['reconstruction_errors'][3]:>10.4f} | {lc322_results['reconstruction_errors'][3]:>10.4f}")
    
    # Interpretation
    print(f"\n  === INTERPRETATION ===")
    if lc3946_results['intrinsic_dim'] < lc322_results['intrinsic_dim']:
        print(f"  LC3946 has LOWER intrinsic dimensionality ({lc3946_results['intrinsic_dim']} vs {lc322_results['intrinsic_dim']})")
        print(f"  This confirms: LC3946 has coherent latent geometry")
    else:
        print(f"  LC3946 has HIGHER intrinsic dimensionality")
        print(f"  This contradicts the hypothesis")
    
    # Save results
    out_path = ROOT / "results" / "svd_analysis_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "lc3946": lc3946_results,
            "lc322": lc322_results,
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")
