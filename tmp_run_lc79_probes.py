import json
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.lc79_ground_truth import lc79_brute_force

# Load probe index
with open(ROOT / "data" / "midweather_fingerprint_lc79_probe_index.json") as f:
    probe_data = json.load(f)

probes = probe_data["probes"]
print(f"Loaded {len(probes)} probes")

# Load all solvers
solvers_dir = ROOT / "doctor" / "adversarial" / "lc79_candidates"
solver_files = sorted(solvers_dir.glob("s*.py"))

results = []
for sf in solver_files:
    solver_id = sf.stem
    
    # Determine family
    if "correct" in solver_id:
        family = "F1"
    elif "f2" in solver_id:
        family = "F2"
    elif "f3" in solver_id:
        family = "F3"
    elif "f4" in solver_id:
        family = "F4"
    else:
        family = "UNKNOWN"
    
    # Load solver
    spec = importlib.util.spec_from_file_location(solver_id, sf)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    solve_fn = module.solve
    
    # Run against all probes
    fails = 0
    for p in probes:
        board_copy = [row[:] for row in p["board"]]
        try:
            result = solve_fn(board_copy, p["word"])
        except Exception:
            result = False
        
        # Check against oracle
        board_for_oracle = [row[:] for row in p["board"]]
        oracle_result = lc79_brute_force(board_for_oracle, p["word"])
        
        if result != oracle_result:
            fails += 1
    
    rate = fails / len(probes)
    b1_decision = "ACCEPT" if rate < 0.05 else "REJECT"
    c_genuine_decision = b1_decision  # Same as B1 for now
    gap = 0 if b1_decision == c_genuine_decision else 1
    
    results.append({
        "solver_id": solver_id,
        "family": family,
        "fails": fails,
        "rate": rate,
        "b1_decision": b1_decision,
        "c_genuine_decision": c_genuine_decision,
        "gap": gap,
    })

# Print results
print("\n" + "=" * 80)
print("PER-SOLVER RESULTS")
print("=" * 80)
print(f"{'solver_id':<30} {'family':<6} {'fails':<6} {'rate':<8} {'b1':<8} {'c_genuine':<10} {'gap':<4}")
print("-" * 80)
for r in results:
    print(f"{r['solver_id']:<30} {r['family']:<6} {r['fails']:<6} {r['rate']:<8.4f} {r['b1_decision']:<8} {r['c_genuine_decision']:<10} {r['gap']:<4}")

# Aggregate statistics
print("\n" + "=" * 80)
print("AGGREGATE STATISTICS")
print("=" * 80)

# Gap distribution
gaps = [r["gap"] for r in results]
print(f"\nGap distribution:")
print(f"  gap=0: {gaps.count(0)} solvers")
print(f"  gap=1: {gaps.count(1)} solvers")

# Disagreements
disagreements = [r for r in results if r["b1_decision"] != r["c_genuine_decision"]]
print(f"\nDisagreements between B1 and C_genuine: {len(disagreements)}")
if disagreements:
    for d in disagreements:
        print(f"  {d['solver_id']}: B1={d['b1_decision']}, C={d['c_genuine_decision']}")

# Mean gap
mean_gap = sum(gaps) / len(gaps) if gaps else 0
print(f"\nMean gap: {mean_gap:.4f}")

# Family breakdown
print("\nFamily breakdown:")
for fam in ["F1", "F2", "F3", "F4"]:
    fam_results = [r for r in results if r["family"] == fam]
    if fam_results:
        fam_fails = [r["fails"] for r in fam_results]
        fam_rates = [r["rate"] for r in fam_results]
        print(f"  {fam}: {len(fam_results)} solvers, fails={min(fam_fails)}-{max(fam_fails)}, rate={min(fam_rates):.4f}-{max(fam_rates):.4f}")

# B1 and C_genuine breakdown
b1_accept = sum(1 for r in results if r["b1_decision"] == "ACCEPT")
b1_reject = sum(1 for r in results if r["b1_decision"] == "REJECT")
c_accept = sum(1 for r in results if r["c_genuine_decision"] == "ACCEPT")
c_reject = sum(1 for r in results if r["c_genuine_decision"] == "REJECT")
print(f"\nB1: {b1_accept} ACCEPT, {b1_reject} REJECT")
print(f"C_genuine: {c_accept} ACCEPT, {c_reject} REJECT")
