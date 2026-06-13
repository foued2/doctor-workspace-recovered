"""SVD analysis for LC3946 v2 solver population."""
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
    load_ground_truth_from_json,
    SEED, lc3946_to_input, lc3946_oracle,
)
from csse.svd_analysis import simple_svd, compute_reconstruction_error


def evaluate_v2_solvers(to_input, oracle_fn, style):
    """Evaluate the v2 solver population."""
    probes = load_probes("lc3946")
    obs, tgt = load_observed_target_split("lc3946")
    
    # Load v2 solvers
    v2_dir = ROOT.parent / "experiments" / "frozen_taxonomy_lc3946_v2" / "solvers"
    solver_files = sorted(v2_dir.glob("solver_*.py"))
    
    solver_evals = {}
    for solver_path in solver_files:
        solver_id = solver_path.stem
        
        # Import solver
        import importlib.util
        spec = importlib.util.spec_from_file_location(solver_id, solver_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Evaluate on probes
        results = {}
        for pid in obs:
            probe = next(p for p in probes if p["probe_id"] == pid)
            solver_input = to_input(probe)
            
            try:
                result = module.solve(solver_input)
                gt = oracle_fn(solver_input)
                results[pid] = (result == gt)
            except Exception as e:
                results[pid] = False
        
        solver_evals[solver_id] = results
    
    return solver_evals


def compute_failure_matrix(solver_evals, obs):
    """Compute binary failure matrix."""
    sids = sorted(solver_evals.keys())
    failure_matrix = []
    for sid in sids:
        vector = []
        for pid in obs:
            passed = solver_evals[sid][pid]
            vector.append(0 if passed else 1)
        failure_matrix.append(vector)
    return sids, failure_matrix


def run_analysis():
    """Run full SVD analysis on v2 population."""
    print("="*70)
    print("  LC3946 V2 POPULATION SVD ANALYSIS")
    print("="*70)
    
    # Load data
    probes = load_probes("lc3946")
    obs, tgt = load_observed_target_split("lc3946")
    gt = load_ground_truth_from_json("lc3946")
    
    print(f"\n  Probes: {len(obs)}")
    
    # Evaluate v2 solvers
    print(f"\n  Evaluating v2 solvers...")
    solver_evals = evaluate_v2_solvers(lc3946_to_input, lc3946_oracle, "single")
    
    sids, fm = compute_failure_matrix(solver_evals, obs)
    print(f"  Solvers: {len(sids)}")
    
    # Compute SVD
    U, S, Vt = simple_svd(fm)
    
    # Singular values
    print(f"\n  === SINGULAR VALUES ===")
    total_var = sum(s**2 for s in S)
    for i, s in enumerate(S):
        var_explained = s**2 / total_var * 100
        cumulative = sum(sv**2 for sv in S[:i+1]) / total_var * 100
        print(f"    Rank {i+1}: singular_value={s:.4f}, variance={var_explained:.1f}%, cumulative={cumulative:.1f}%")
    
    # Reconstruction error
    print(f"\n  === RECONSTRUCTION ERROR ===")
    for rank in range(1, min(len(sids), len(obs)) + 1):
        error = compute_reconstruction_error(fm, U, S, Vt, rank)
        print(f"    Rank {rank}: error={error:.4f}")
    
    # Intrinsic dimensionality
    cumulative_var = 0
    intrinsic_dim = 0
    for i, s in enumerate(S):
        cumulative_var += s**2
        if cumulative_var / total_var >= 0.9:
            intrinsic_dim = i + 1
            break
    
    print(f"\n  Intrinsic dimensionality (90% variance): {intrinsic_dim}")
    
    # Separability
    import numpy as np
    M = np.array(fm, dtype=float)
    M = M - M.mean(axis=0)
    latent_2d = M @ Vt[:2, :].T
    
    correct_indices = [i for i, sid in enumerate(sids) if gt.get(sid, False)]
    incorrect_indices = [i for i, sid in enumerate(sids) if not gt.get(sid, False)]
    
    if correct_indices and incorrect_indices:
        correct_center = latent_2d[correct_indices].mean(axis=0)
        incorrect_center = latent_2d[incorrect_indices].mean(axis=0)
        
        center_dist = np.linalg.norm(correct_center - incorrect_center)
        correct_spread = np.mean([np.linalg.norm(latent_2d[i] - correct_center) for i in correct_indices])
        incorrect_spread = np.mean([np.linalg.norm(latent_2d[i] - incorrect_center) for i in incorrect_indices])
        
        print(f"\n  === SEPARABILITY IN LATENT SPACE ===")
        print(f"  Center distance: {center_dist:.4f}")
        print(f"  Correct spread: {correct_spread:.4f}")
        print(f"  Incorrect spread: {incorrect_spread:.4f}")
        print(f"  Ratio (distance/spread): {center_dist / (correct_spread + incorrect_spread):.4f}")
    
    # Load original results for comparison
    orig_path = ROOT / "results" / "svd_analysis_results.json"
    if orig_path.exists():
        with open(orig_path) as f:
            orig_data = json.load(f)
        
        orig_lc3946 = orig_data.get("lc3946", {})
        orig_sv = orig_lc3946.get("singular_values", [])
        orig_dim = orig_lc3946.get("intrinsic_dim")
        
        print(f"\n  === COMPARISON WITH ORIGINAL ===")
        print(f"  {'Rank':<6} | {'Original SV':>12} | {'V2 SV':>12} | {'Ratio':>8}")
        print("  " + "-"*45)
        
        for i in range(min(5, len(orig_sv), len(S))):
            ratio = S[i] / orig_sv[i] if orig_sv[i] > 0 else 0
            print(f"  {i+1:<6} | {orig_sv[i]:>12.4f} | {S[i]:>12.4f} | {ratio:>8.4f}")
        
        print(f"\n  Original intrinsic dim: {orig_dim}")
        print(f"  V2 intrinsic dim: {intrinsic_dim}")
    
    # Save results
    results = {
        "singular_values": S.tolist(),
        "intrinsic_dim": intrinsic_dim,
        "total_variance": total_var,
        "reconstruction_errors": {
            rank: compute_reconstruction_error(fm, U, S, Vt, rank)
            for rank in range(1, min(len(sids), len(obs)) + 1)
        },
    }
    
    out_path = ROOT / "results" / "svd_analysis_lc3946_v2.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    run_analysis()
