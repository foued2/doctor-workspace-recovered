"""Check if S varies across probe families within each problem.

If S is stable across families, it's a problem property.
If S varies by family, probe quality matters.
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

# Load failure matrices for both populations
# We need to recompute S per family
import sys
sys.path.insert(0, str(ROOT))
from csse.phi_robustness import load_probes, load_observed_target_split
import importlib.util


def evaluate_solvers(problem_class, to_input, oracle_fn, solvers_dir):
    probes = load_probes(problem_class)
    obs, _ = load_observed_target_split(problem_class)
    
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


def compute_S_for_probes(solver_evals, probe_ids):
    """Compute S for a subset of probes."""
    if len(probe_ids) < 2:
        return None
    
    sids = sorted(solver_evals.keys())
    matrix = []
    for sid in sids:
        vector = [0 if solver_evals[sid][pid] else 1 for pid in probe_ids]
        matrix.append(vector)
    
    M = np.array(matrix, dtype=float)
    if M.ndim < 2 or M.shape[1] < 2:
        return None
    
    M_mean = M - M.mean(axis=0)
    U, S, Vt = np.linalg.svd(M_mean, full_matrices=False)
    return S


from csse.phi_robustness import lc45_to_input, lc45_oracle, lc322_to_input, lc322_oracle, lc3946_to_input, lc3946_oracle, lc743_to_input, lc743_oracle

problems = {
    "lc322": (lc322_to_input, lc322_oracle),
    "lc3946": (lc3946_to_input, lc3946_oracle),
    "lc45": (lc45_to_input, lc45_oracle),
    "lc743": (lc743_to_input, lc743_oracle),
}

print("=" * 70)
print("  S PER PROBE FAMILY (within each problem)")
print("=" * 70)

for problem_class, (to_input, oracle_fn) in problems.items():
    probes = load_probes(problem_class)
    obs, _ = load_observed_target_split(problem_class)
    
    # Group probes by family
    family_probes = defaultdict(list)
    for pid in obs:
        probe = next(p for p in probes if p["probe_id"] == pid)
        family_probes[probe.get("family", "unknown")].append(pid)
    
    # Evaluate both populations
    orig_dir = ROOT / "experiments" / f"frozen_taxonomy_{problem_class}" / "solvers"
    v2_dir = ROOT / "experiments" / f"frozen_taxonomy_{problem_class}_v2" / "solvers"
    
    orig_evals = evaluate_solvers(problem_class, to_input, oracle_fn, orig_dir)
    v2_evals = evaluate_solvers(problem_class, to_input, oracle_fn, v2_dir)
    
    print(f"\n  {problem_class.upper()}:")
    
    for family, pids in sorted(family_probes.items()):
        # Compute S for this family
        sv_orig = compute_S_for_probes(orig_evals, pids)
        sv_v2 = compute_S_for_probes(v2_evals, pids)
        
        if sv_orig is not None and sv_v2 is not None:
            try:
                max_len = max(len(sv_orig), len(sv_v2))
                orig_padded = np.pad(sv_orig, (0, max_len - len(sv_orig)))
                v2_padded = np.pad(sv_v2, (0, max_len - len(sv_v2)))
                S_family = np.mean(np.abs(orig_padded - v2_padded))
                print(f"    {family}: S={S_family:.4f} (n={len(pids)} probes)")
            except Exception as e:
                print(f"    {family}: error computing S: {e}")
        else:
            print(f"    {family}: insufficient probes (n={len(pids)})")
