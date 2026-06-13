"""SVD analysis for LC45 and LC743 v2 populations."""
import json
import math
import numpy as np
from pathlib import Path
import sys
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, load_observed_target_split,
    load_ground_truth_from_json,
    lc45_to_input, lc45_oracle,
    lc743_to_input, lc743_oracle,
    SEED,
)


def evaluate_solvers(problem_class, to_input, oracle_fn):
    """Evaluate frozen solvers on observed probes."""
    probes = load_probes(problem_class)
    obs, _ = load_observed_target_split(problem_class)
    
    solvers_dir = ROOT / "experiments" / f"frozen_taxonomy_{problem_class}_v2" / "solvers"
    solver_files = sorted(solvers_dir.glob("solver_*.py"))
    
    solver_evals = {}
    for solver_path in solver_files:
        solver_id = solver_path.stem
        
        spec = importlib.util.spec_from_file_location(solver_id, solver_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        results = {}
        for pid in obs:
            probe = next(p for p in probes if p["probe_id"] == pid)
            solver_input = to_input(probe)
            
            try:
                if problem_class == "lc743":
                    times, n, k = solver_input
                    result = module.solve(times, n, k)
                    gt = oracle_fn(times, n, k)
                else:
                    result = module.solve(solver_input)
                    gt = oracle_fn(solver_input)
                results[pid] = (result == gt)
            except Exception:
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
    print(f"  SVD ANALYSIS: {problem_class.upper()} v2")
    print(f"{'='*70}")
    
    probes = load_probes(problem_class)
    obs, _ = load_observed_target_split(problem_class)
    
    print(f"\n  Probes: {len(obs)}")
    
    print(f"\n  Evaluating solvers...")
    solver_evals = evaluate_solvers(problem_class, to_input, oracle_fn)
    print(f"  Solvers: {len(solver_evals)}")
    
    sids, failure_matrix = compute_failure_matrix(solver_evals, obs)
    M = np.array(failure_matrix, dtype=float)
    
    n_solvers, n_probes = M.shape
    n_failures_per_solver = M.sum(axis=1)
    n_failures_per_probe = M.sum(axis=0)
    
    print(f"\n  === FAILURE DISTRIBUTION ===")
    print(f"  Failures/solver: mean={n_failures_per_solver.mean():.1f}, "
          f"std={n_failures_per_solver.std():.1f}, "
          f"min={n_failures_per_solver.min():.0f}, max={n_failures_per_solver.max():.0f}")
    print(f"  Failures/probe: mean={n_failures_per_probe.mean():.1f}, "
          f"std={n_failures_per_probe.std():.1f}")
    
    correct_mask = n_failures_per_solver == 0
    incorrect_mask = n_failures_per_solver > 0
    n_correct = correct_mask.sum()
    n_incorrect = incorrect_mask.sum()
    print(f"  Correct: {n_correct}/{n_solvers}")
    print(f"  Incorrect: {n_incorrect}/{n_solvers}")
    
    M_mean = M - M.mean(axis=0)
    
    U, S, Vt = np.linalg.svd(M_mean, full_matrices=False)
    
    total_var = np.sum(S**2)
    print(f"\n  === SINGULAR VALUES ===")
    cumulative = 0
    for i, sv in enumerate(S[:10]):
        var_explained = sv**2 / total_var * 100 if total_var > 0 else 0
        cumulative += var_explained
        print(f"    Rank {i+1}: singular_value={sv:.4f}, "
              f"variance={var_explained:.1f}%, cumulative={cumulative:.1f}%")
    
    intrinsic_dim = 0
    cumulative_var = 0
    for i, sv in enumerate(S):
        cumulative_var += sv**2
        if total_var > 0 and cumulative_var / total_var >= 0.9:
            intrinsic_dim = i + 1
            break
    if intrinsic_dim == 0:
        intrinsic_dim = len(S)
    
    print(f"\n  Intrinsic dimensionality (90% variance): {intrinsic_dim}")
    
    correct_proj = U[correct_mask] @ np.diag(S) @ Vt
    incorrect_proj = U[incorrect_mask] @ np.diag(S) @ Vt
    
    center_correct = correct_proj.mean(axis=0) if len(correct_proj) > 0 else np.zeros(n_probes)
    center_incorrect = incorrect_proj.mean(axis=0) if len(incorrect_proj) > 0 else np.zeros(n_probes)
    
    center_distance = np.linalg.norm(center_correct - center_incorrect)
    
    all_proj = U @ np.diag(S) @ Vt
    spread = np.std(all_proj, axis=0).mean()
    
    ratio = center_distance / spread if spread > 0 else 0
    
    print(f"\n  === SEPARABILITY ===")
    print(f"  Center distance: {center_distance:.4f}")
    print(f"  Ratio (distance/spread): {ratio:.4f}")
    
    if ratio > 1.5:
        verdict = "SEPARABLE"
    elif ratio > 0.8:
        verdict = "MIXED"
    else:
        verdict = "NOT_SEPARABLE"
    print(f"  Verdict: {verdict}")
    
    return {
        "problem_class": problem_class,
        "population": "v2",
        "n_solvers": n_solvers,
        "n_probes": n_probes,
        "n_correct": int(n_correct),
        "n_incorrect": int(n_incorrect),
        "singular_values": S.tolist(),
        "intrinsic_dim": intrinsic_dim,
        "center_distance": float(center_distance),
        "spread": float(spread),
        "ratio": float(ratio),
        "verdict": verdict,
        "failure_per_solver": n_failures_per_solver.tolist(),
        "failure_per_probe": n_failures_per_probe.tolist(),
    }


if __name__ == "__main__":
    results = []
    
    results.append(run_svd("lc45", lc45_to_input, lc45_oracle))
    results.append(run_svd("lc743", lc743_to_input, lc743_oracle))
    
    out_path = ROOT / "results" / "svd_analysis_v2_extended.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n\nResults saved to {out_path}")
