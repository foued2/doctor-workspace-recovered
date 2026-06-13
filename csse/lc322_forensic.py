"""Forensic report on LC322 disagreement solvers."""
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, extract_canonical_phi, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    b1_decision, c_genuine_decision,
    decision_loss_single,
    lc322_to_input, lc322_oracle,
)

def c_count_decision(obs_fails, threshold):
    return "ACCEPT" if obs_fails <= threshold else "REJECT"

pc = "lc322"
probes = load_probes(pc)
phi = extract_canonical_phi(probes)
obs, tgt = load_observed_target_split(pc)
solver_evals = evaluate_frozen_solvers(pc, lc322_to_input, lc322_oracle, "single")
ground_truth = load_ground_truth_from_json(pc)

T_star = 3

print("=" * 70)
print("  FORENSIC REPORT: LC322 Disagreement Solvers")
print("=" * 70)
print(f"\n  T* = {T_star}")
print(f"  C_count(T*): ACCEPT if obs_fails <= {T_star}, else REJECT")
print(f"  C_genuine: ACCEPT if failures span <= 1 family, else REJECT")

# Find disagreements
disagreements = []
for sid in sorted(solver_evals.keys()):
    results = solver_evals[sid]
    obs_fails = sum(1 for pid in obs if not results.get(pid, True))
    family_fails = defaultdict(int)
    for pid in obs:
        if not results.get(pid, True):
            fam = phi.get(pid, "unknown")
            family_fails[fam] += 1

    b1 = b1_decision(obs_fails)
    cgen = c_genuine_decision(dict(family_fails))
    ccons = c_count_decision(obs_fails, T_star)

    if cgen != ccons:
        disagreements.append({
            "sid": sid,
            "obs_fails": obs_fails,
            "family_fails": dict(family_fails),
            "n_families": len([f for f, c in family_fails.items() if c > 0]),
            "b1": b1,
            "cgen": cgen,
            "ccons": ccons,
            "gt_correct": ground_truth.get(sid, None),
            "probe_results": {pid: results.get(pid, True) for pid in obs},
        })

print(f"\n  Disagreements found: {len(disagreements)}")
print()

for d in disagreements:
    print(f"  {'='*60}")
    print(f"  Solver: {d['sid']}")
    print(f"  Ground truth: {'ACCEPT (correct)' if d['gt_correct'] else 'REJECT (incorrect)'}")
    print(f"\n  Failure count on observed probes: {d['obs_fails']}")
    print(f"  Families with failures: {d['n_families']}")
    print(f"  Family failure distribution:")
    for fam, count in sorted(d["family_fails"].items()):
        print(f"    {fam}: {count}")
    print(f"\n  Per-probe results (observed probes):")
    for pid in sorted(d["probe_results"].keys()):
        passed = d["probe_results"][pid]
        fam = phi.get(pid, "unknown")
        status = "PASS" if passed else "FAIL"
        print(f"    {pid} [{fam}]: {status}")
    print(f"\n  Decisions:")
    print(f"    B1:            {d['b1']}")
    print(f"    C_genuine:     {d['cgen']}")
    print(f"    C_conservative(T*={T_star}): {d['ccons']}")
    print(f"\n  Decision loss at different lambda values:")
    for lam in [10, 50, 100]:
        wa = 1.0
        wr = float(lam)
        loss_b1 = decision_loss_single(d["b1"], d["gt_correct"], wa, wr)
        loss_cgen = decision_loss_single(d["cgen"], d["gt_correct"], wa, wr)
        loss_ccons = decision_loss_single(d["ccons"], d["gt_correct"], wa, wr)
        print(f"    lambda={lam:>3}: B1={loss_b1:.1f}  C_genuine={loss_cgen:.1f}  C_conservative={loss_ccons:.1f}  "
              f"(C_genuine-B1={loss_cgen-loss_b1:+.1f}  C_conservative-B1={loss_ccons-loss_b1:+.1f}  "
              f"C_conservative-C_genuine={loss_ccons-loss_cgen:+.1f})")
    print()

# Summary table
print(f"\n  {'='*60}")
print(f"  SUMMARY")
print(f"  {'='*60}")
print(f"\n  Both solvers: C_genuine=REJECT, C_conservative=ACCEPT")
print(f"  Both solvers have obs_fails <= {T_star} (so C_count accepts them)")
print(f"  Both solvers have failures in 2+ families (so C_genuine rejects them)")
print(f"\n  At lambda=50:")
for d in disagreements:
    loss_cgen = decision_loss_single(d["cgen"], d["gt_correct"], 1.0, 50.0)
    loss_ccons = decision_loss_single(d["ccons"], d["gt_correct"], 1.0, 50.0)
    delta = loss_ccons - loss_cgen
    print(f"    {d['sid']}: C_genuine loss={loss_cgen:.1f}, C_conservative loss={loss_ccons:.1f}, "
          f"residual={delta:+.1f}")
