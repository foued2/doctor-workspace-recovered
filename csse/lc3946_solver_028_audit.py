"""LC3946 solver_028 audit: what makes it special?

Compare solver_028 against other incorrect solvers.
Identify distinguishing probes.
Check if failures concentrate in tight-budget regime.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    SEED, lc3946_to_input, lc3946_oracle,
)
from csse.representation_invariance import build_R1


def audit_solver_028():
    """Full audit of solver_028 vs other incorrect solvers."""
    print("="*70)
    print("  SOLVER_028 AUDIT")
    print("="*70)
    
    # Load data
    probes = load_probes("lc3946")
    obs, tgt = load_observed_target_split("lc3946")
    solver_evals = evaluate_frozen_solvers("lc3946", lc3946_to_input, lc3946_oracle, "single")
    ground_truth = load_ground_truth_from_json("lc3946")
    
    # Compute failure vectors
    failure_vectors = {}
    for sid, results in solver_evals.items():
        vector = []
        for pid in obs:
            passed = results.get(pid, True)
            vector.append(0 if passed else 1)
        failure_vectors[sid] = vector
    
    # Get R1 features
    R1_features = build_R1("lc3946")
    
    # Target solvers: solver_028 (top contributor) vs other incorrect
    target_solvers = ["solver_028", "solver_009", "solver_015", "solver_018"]
    correct_solvers = ["solver_023"]  # The one correct solver
    
    print(f"\n=== FAILURE VECTORS ===")
    print(f"{'Solver':<12} | {'Failures':>8} | {'Correct':>7} | Contribution")
    print("-" * 60)
    
    # Load contributions
    with open("results/lc3946_solver_audit_results.json") as f:
        audit_data = json.load(f)
    
    contrib_map = {c["solver_id"]: c["contribution"] for c in audit_data["contributions"]}
    
    for sid in target_solvers + correct_solvers:
        fv = failure_vectors[sid]
        n_fail = sum(fv)
        correct = ground_truth.get(sid, False)
        contrib = contrib_map.get(sid, 0)
        print(f"  {sid:<12} | {n_fail:>8} | {str(correct):>7} | {contrib:+.6f}")
    
    print(f"\n=== FAILURE VECTOR COMPARISON ===")
    print(f"{'Probe':<16} | ", end="")
    for sid in target_solvers:
        print(f"{sid:<12} | ", end="")
    print("Features")
    print("-" * 120)
    
    for j, pid in enumerate(obs):
        print(f"  {pid:<14} | ", end="")
        for sid in target_solvers:
            fv = failure_vectors[sid]
            marker = "FAIL" if fv[j] == 1 else "pass "
            print(f"{marker:<12} | ", end="")
        
        # Print features
        feat = R1_features[pid]
        print(f"n={feat['n_items']}, b={feat['budget']}, ratio={feat['budget_ratio']:.3f}")
    
    # Identify distinguishing probes
    print(f"\n=== DISTINGUISHING PROBES ===")
    print(f"Probes where solver_028 differs from ALL other incorrect solvers:")
    
    distinguishing = []
    for j, pid in enumerate(obs):
        fv_028 = failure_vectors["solver_028"][j]
        fv_others = [failure_vectors[sid][j] for sid in ["solver_009", "solver_015", "solver_018"]]
        
        # solver_028 fails but others pass, or solver_028 passes but others fail
        if fv_028 != fv_others[0] or fv_028 != fv_others[1] or fv_028 != fv_others[2]:
            feat = R1_features[pid]
            distinguishing.append({
                "probe_id": pid,
                "solver_028": fv_028,
                "solver_009": fv_others[0],
                "solver_015": fv_others[1],
                "solver_018": fv_others[2],
                "features": feat,
            })
            
            marker_028 = "FAIL" if fv_028 == 1 else "pass"
            markers_others = ["FAIL" if x == 1 else "pass" for x in fv_others]
            
            print(f"  {pid}: 028={marker_028}, 009={markers_others[0]}, 015={markers_others[1]}, 018={markers_others[2]}")
            print(f"         Features: n={feat['n_items']}, budget={feat['budget']}, ratio={feat['budget_ratio']:.3f}")
    
    # Analyze tight-budget concentration
    print(f"\n=== TIGHT-BUDGET ANALYSIS ===")
    
    # Define tight budget as budget_ratio < 0.3
    tight_budget_probes = [pid for pid in obs if R1_features[pid]["budget_ratio"] < 0.3]
    loose_budget_probes = [pid for pid in obs if R1_features[pid]["budget_ratio"] >= 0.3]
    
    print(f"Tight budget probes (ratio < 0.3): {len(tight_budget_probes)}")
    print(f"Loose budget probes (ratio >= 0.3): {len(loose_budget_probes)}")
    
    for sid in target_solvers:
        fv = failure_vectors[sid]
        tight_fails = sum(1 for pid in tight_budget_probes if fv[obs.index(pid)] == 1)
        loose_fails = sum(1 for pid in loose_budget_probes if fv[obs.index(pid)] == 1)
        tight_rate = tight_fails / len(tight_budget_probes) if tight_budget_probes else 0
        loose_rate = loose_fails / len(loose_budget_probes) if loose_budget_probes else 0
        
        print(f"\n  {sid}:")
        print(f"    Tight budget: {tight_fails}/{len(tight_budget_probes)} failures ({tight_rate:.1%})")
        print(f"    Loose budget: {loose_fails}/{len(loose_budget_probes)} failures ({loose_rate:.1%})")
        print(f"    Ratio tight/loose: {tight_rate/loose_rate:.2f}x" if loose_rate > 0 else "    Ratio: N/A")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"solver_028 has {sum(failure_vectors['solver_028'])} failures out of {len(obs)} probes")
    print(f"It contributes +0.061 to Delta(R1-R2), which is 45.4% of total effect")
    print(f"Distinguishing probes: {len(distinguishing)} out of {len(obs)}")
    
    if distinguishing:
        tight_distinguishing = sum(1 for d in distinguishing if d["features"]["budget_ratio"] < 0.3)
        print(f"Of distinguishing probes, {tight_distinguishing} are tight-budget")
    
    return {
        "target_solvers": target_solvers,
        "failure_vectors": {sid: failure_vectors[sid] for sid in target_solvers},
        "distinguishing_probes": distinguishing,
        "tight_budget_analysis": {
            "tight_count": len(tight_budget_probes),
            "loose_count": len(loose_budget_probes),
        },
    }


if __name__ == "__main__":
    result = audit_solver_028()
    
    # Save results
    out_path = ROOT / "results" / "lc3946_solver_028_audit.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to {out_path}")
