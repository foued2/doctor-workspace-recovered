"""SVD analysis for LC45 and LC743 (original populations)."""
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
    SEED,
    lc45_to_input, lc45_oracle,
    lc743_to_input, lc743_oracle,
)
from csse.svd_analysis import simple_svd, compute_reconstruction_error


def evaluate_solvers(problem_class, to_input, oracle_fn, style):
    """Evaluate frozen solver population."""
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    
    solvers_dir = ROOT / "experiments" / f"frozen_taxonomy_{problem_class}" / "solvers"
    solver_files = sorted(solvers_dir.glob("solver_*.py"))
    
    solver_evals = {}
    for solver_path in solver_files:
        solver_id = solver_path.stem
        
        import importlib.util
        spec = importlib.util.spec_from_file_location(solver_id, solver_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        results = {}
        for pid in obs:
            probe = next(p for p in probes if p["probe_id"] == pid)
            solver_input = to_input(probe)
            
            try:
                # Handle different solver signatures
                if problem_class == "lc743":
                    # LC743 solvers expect (times, n, k) as separate args
                    times, n, k = solver_input
                    result = module.solve(times, n, k)
                    gt = oracle_fn(times, n, k)
                else:
                    result = module.solve(solver_input)
                    gt = oracle_fn(solver_input)
                results[pid] = (result == gt)
            except Exception as e:
                results[pid] = False
        
        solver_evals[solver_id] = results
    
    return solver_evals


def compute_failure_matrix(solver_evals, obs):
    sids = sorted(solver_evals.keys())
    failure_matrix = []
    for sid in sids:
        vector = []
        for pid in obs:
            passed = solver_evals[sid][pid]
            vector.append(0 if passed else 1)
        failure_matrix.append(vector)
    return sids, failure_matrix


def run_svd(problem_class, to_input, oracle_fn):
    """Run SVD analysis for one problem."""
    print(f"\n{'='*70}")
    print(f"  SVD ANALYSIS: {problem_class.upper()}")
    print(f"{'='*70}")
    
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    gt = load_ground_truth_from_json(problem_class)
    
    print(f"\n  Probes: {len(obs)}")
    
    print(f"\n  Evaluating solvers...")
    solver_evals = evaluate_solvers(problem_class, to_input, oracle_fn, "single")
    
    sids, fm = compute_failure_matrix(solver_evals, obs)
    print(f"  Solvers: {len(sids)}")
    
    U, S, Vt = simple_svd(fm)
    
    print(f"\n  === SINGULAR VALUES ===")
    total_var = sum(s**2 for s in S)
    for i, s in enumerate(S[:6]):
        var_explained = s**2 / total_var * 100
        cumulative = sum(sv**2 for sv in S[:i+1]) / total_var * 100
        print(f"    Rank {i+1}: singular_value={s:.4f}, variance={var_explained:.1f}%, cumulative={cumulative:.1f}%")
    
    cumulative_var = 0
    intrinsic_dim = 0
    for i, s in enumerate(S):
        cumulative_var += s**2
        if cumulative_var / total_var >= 0.9:
            intrinsic_dim = i + 1
            break
    
    print(f"\n  Intrinsic dimensionality (90% variance): {intrinsic_dim}")
    
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
        
        ratio = center_dist / (correct_spread + incorrect_spread) if (correct_spread + incorrect_spread) > 0 else 0
        
        print(f"\n  === SEPARABILITY ===")
        print(f"  Center distance: {center_dist:.4f}")
        print(f"  Ratio (distance/spread): {ratio:.4f}")
    
    return {
        "singular_values": S.tolist(),
        "intrinsic_dim": intrinsic_dim,
        "total_variance": total_var,
    }


if __name__ == "__main__":
    results = {}
    
    results["lc45"] = run_svd("lc45", lc45_to_input, lc45_oracle)
    results["lc743"] = run_svd("lc743", lc743_to_input, lc743_oracle)
    
    out_path = ROOT / "results" / "svd_analysis_lc45_lc743.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")
