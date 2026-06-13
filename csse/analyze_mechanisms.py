"""Analyze solver failure mechanisms for LC322 and LC3946."""
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, evaluate_frozen_solvers, load_observed_target_split,
    load_ground_truth_from_json,
    lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
)

# LC322 Analysis
print("=" * 70)
print("  LC322 FAILURE MECHANISM ANALYSIS")
print("=" * 70)

probes_322 = load_probes("lc322")
evals_322 = evaluate_frozen_solvers("lc322", lc322_to_input, lc322_oracle, "single")
obs_322, tgt_322 = load_observed_target_split("lc322")
gt_322 = load_ground_truth_from_json("lc322")

print(f"\n  Probes: {len(probes_322)}")
print(f"  Solvers: {len(evals_322)}")
print(f"  Correct: {sum(1 for v in gt_322.values() if v)}")
print(f"  Incorrect: {sum(1 for v in gt_322.values() if not v)}")

# Analyze input features
print(f"\n  Input features across probes:")
for p in probes_322[:5]:
    coins = p.get("coins", [])
    amount = p.get("amount", 0)
    print(f"    {p['probe_id']}: coins={coins}, amount={amount}")

# Analyze failure patterns per probe
print(f"\n  Failure rate per probe (across all solvers):")
for pid in sorted(obs_322):
    fails = sum(1 for sid in evals_322 if not evals_322[sid].get(pid, True))
    rate = fails / len(evals_322)
    probe = [p for p in probes_322 if p["probe_id"] == pid][0]
    coins = probe.get("coins", [])
    amount = probe.get("amount", 0)
    print(f"    {pid}: {fails}/{len(evals_322)} = {rate:.2f} (coins={coins}, amount={amount})")

# LC3946 Analysis
print("\n" + "=" * 70)
print("  LC3946 FAILURE MECHANISM ANALYSIS")
print("=" * 70)

probes_3946 = load_probes("lc3946")
evals_3946 = evaluate_frozen_solvers("lc3946", lc3946_to_input, lc3946_oracle, "single")
obs_3946, tgt_3946 = load_observed_target_split("lc3946")
gt_3946 = load_ground_truth_from_json("lc3946")

print(f"\n  Probes: {len(probes_3946)}")
print(f"  Solvers: {len(evals_3946)}")
print(f"  Correct: {sum(1 for v in gt_3946.values() if v)}")
print(f"  Incorrect: {sum(1 for v in gt_3946.values() if not v)}")

print(f"\n  Input features across probes:")
for p in probes_3946[:5]:
    items = p.get("items", [])
    budget = p.get("budget", 0)
    print(f"    {p['probe_id']}: items={items}, budget={budget}")

print(f"\n  Failure rate per probe (across all solvers):")
for pid in sorted(obs_3946):
    fails = sum(1 for sid in evals_3946 if not evals_3946[sid].get(pid, True))
    rate = fails / len(evals_3946)
    probe = [p for p in probes_3946 if p["probe_id"] == pid][0]
    items = probe.get("items", [])
    budget = probe.get("budget", 0)
    print(f"    {pid}: {fails}/{len(evals_3946)} = {rate:.2f} (items={items}, budget={budget})")
