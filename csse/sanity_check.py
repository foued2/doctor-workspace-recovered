"""Sanity check: verify LC3946 λ=50 results are consistent across implementations."""
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, extract_canonical_phi, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    b1_decision, c_genuine_decision, decision_loss_single,
    lc3946_to_input, lc3946_oracle,
)

pc = "lc3946"
probes = load_probes(pc)
phi = extract_canonical_phi(probes)
obs, tgt = load_observed_target_split(pc)
solver_evals = evaluate_frozen_solvers(pc, lc3946_to_input, lc3946_oracle, "single")
ground_truth = load_ground_truth_from_json(pc)

print("=" * 70)
print("  SANITY CHECK: LC3946 at lambda=50")
print("=" * 70)

# 1. Verify failure counts
print("\n  1. Failure counts on observed probes:")
for sid in sorted(solver_evals.keys())[:5]:
    results = solver_evals[sid]
    obs_fails = sum(1 for pid in obs if not results.get(pid, True))
    print(f"    {sid}: {obs_fails}")

# 2. Verify C_genuine decisions
print("\n  2. C_genuine decisions:")
for sid in sorted(solver_evals.keys())[:5]:
    results = solver_evals[sid]
    obs_fails = sum(1 for pid in obs if not results.get(pid, True))
    family_fails = defaultdict(int)
    for pid in obs:
        if not results.get(pid, True):
            fam = phi.get(pid, "unknown")
            family_fails[fam] += 1
    cgen = c_genuine_decision(dict(family_fails))
    print(f"    {sid}: obs_fails={obs_fails}, families={dict(family_fails)}, C_genuine={cgen}")

# 3. Verify C_conservative decisions (T*=1)
T_star = 1
print(f"\n  3. C_conservative decisions (T*={T_star}):")
for sid in sorted(solver_evals.keys())[:5]:
    results = solver_evals[sid]
    obs_fails = sum(1 for pid in obs if not results.get(pid, True))
    ccons = "ACCEPT" if obs_fails <= T_star else "REJECT"
    print(f"    {sid}: obs_fails={obs_fails}, C_conservative={ccons}")

# 4. Compute ΔU at lambda=50
wa = 1.0
wr = 50.0
losses_b1 = []
losses_cgen = []
losses_ccons = []

for sid in sorted(solver_evals.keys()):
    results = solver_evals[sid]
    is_correct = ground_truth[sid]
    obs_fails = sum(1 for pid in obs if not results.get(pid, True))
    family_fails = defaultdict(int)
    for pid in obs:
        if not results.get(pid, True):
            fam = phi.get(pid, "unknown")
            family_fails[fam] += 1
    
    b1 = b1_decision(obs_fails)
    cgen = c_genuine_decision(dict(family_fails))
    ccons = "ACCEPT" if obs_fails <= T_star else "REJECT"
    
    losses_b1.append(decision_loss_single(b1, is_correct, wa, wr))
    losses_cgen.append(decision_loss_single(cgen, is_correct, wa, wr))
    losses_ccons.append(decision_loss_single(ccons, is_correct, wa, wr))

n = len(losses_b1)
du_b1_cgen = (sum(losses_b1) - sum(losses_cgen)) / n
du_b1_ccons = (sum(losses_b1) - sum(losses_ccons)) / n
du_ccons_cgen = (sum(losses_ccons) - sum(losses_cgen)) / n

print(f"\n  4. DU at lambda=50:")
print(f"    DU(B1 vs C_genuine) = {du_b1_cgen:.6f}")
print(f"    DU(B1 vs C_conservative) = {du_b1_ccons:.6f}")
print(f"    DU(C_conservative vs C_genuine) = {du_ccons_cgen:.6f}")

# 5. Check agreement between C_genuine and C_conservative
agreements = sum(1 for sid in sorted(solver_evals.keys())
                 if (c_genuine_decision(dict(defaultdict(int, {
                     fam: sum(1 for pid in obs if not solver_evals[sid].get(pid, True) and phi.get(pid) == fam)
                     for fam in set(phi.values())
                 })))) == ("ACCEPT" if sum(1 for pid in obs if not solver_evals[sid].get(pid, True)) <= T_star else "REJECT"))

print(f"\n  5. Agreement: {agreements}/{n} = {agreements/n:.4f}")

# Summary
print(f"\n  SUMMARY:")
print(f"    LC3946 ΔU(B1 vs C_genuine) = {du_b1_cgen:.6f} (expected ~1.667)")
print(f"    Agreement = {agreements/n:.4f} (expected 1.0)")
print(f"    ΔU(C_conservative vs C_genuine) = {du_ccons_cgen:.6f} (expected 0.0)")
