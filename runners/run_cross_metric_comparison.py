"""Cross-metric comparison: discrete oracle vs continuous scoring.

Tests whether the discrete oracle quantization hides latent behavioral variation.

Key question: Are there solvers with discrete_mismatches = 0 but avg_abs_error > 0?
If yes → discrete oracle quantization was hiding latent behavioral variation.
If no → solvers with zero discrete mismatches genuinely have zero continuous error.

Also tests: Are there solvers with discrete_mismatches > 0 but avg_abs_error = 0?
If yes → discrete oracle penalizes behavior that is continuously identical.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# Load O2-A results
o2a_path = ROOT / "results" / "o2a_scoring.json"
if not o2a_path.exists():
    # Try parent directory
    o2a_path = ROOT.parent / "results" / "o2a_scoring.json"

o2a = json.loads(o2a_path.read_text(encoding="utf-8"))

# Load O2-B results
o2b_path = ROOT / "results" / "o2b_resolution.json"
if not o2b_path.exists():
    o2b_path = ROOT.parent / "results" / "o2b_resolution.json"

o2b = json.loads(o2b_path.read_text(encoding="utf-8"))

# Cross-reference
print("=" * 70)
print("CROSS-METRIC COMPARISON: discrete oracle vs continuous scoring")
print("=" * 70)

# Build lookup for O2-B
o2b_by_solver = {s["solver_id"]: s for s in o2b["per_solver"]}

# Question 1: discrete_mismatches = 0 AND avg_abs_error > 0?
q1_solvers = []
for s in o2a["per_solver"]:
    if s["discrete_mismatches"] == 0 and s["avg_abs_error"] > 0:
        q1_solvers.append(s)

print(f"\nQ1: discrete_mismatches = 0 AND avg_abs_error > 0?")
print(f"    Count: {len(q1_solvers)}")
if q1_solvers:
    for s in q1_solvers:
        print(f"    {s['solver_id']}: discrete_mismatches=0, avg_abs_error={s['avg_abs_error']:.4f}")
    print("    => DISCRETE ORACLE HIDES LATENT VARIATION")
else:
    print("    => NO: zero discrete mismatches implies zero continuous error")

# Question 2: discrete_mismatches > 0 AND avg_abs_error = 0?
q2_solvers = []
for s in o2a["per_solver"]:
    if s["discrete_mismatches"] > 0 and s["avg_abs_error"] == 0:
        q2_solvers.append(s)

print(f"\nQ2: discrete_mismatches > 0 AND avg_abs_error = 0?")
print(f"    Count: {len(q2_solvers)}")
if q2_solvers:
    for s in q2_solvers:
        print(f"    {s['solver_id']}: discrete_mismatches={s['discrete_mismatches']}, avg_abs_error={s['avg_abs_error']:.4f}")
    print("    => DISCRETE ORACLE PENALIZES CONTINUOUSLY IDENTICAL BEHAVIOR")
else:
    print("    => NO: zero continuous error implies zero discrete mismatches")

# Question 3: Correlation between discrete_mismatches and avg_abs_error
discrete_vals = [s["discrete_mismatches"] for s in o2a["per_solver"]]
abs_error_vals = [s["avg_abs_error"] for s in o2a["per_solver"]]
n = len(discrete_vals)
mean_d = sum(discrete_vals) / n
mean_e = sum(abs_error_vals) / n
cov = sum((d - mean_d) * (e - mean_e) for d, e in zip(discrete_vals, abs_error_vals)) / n
std_d = (sum((d - mean_d) ** 2 for d in discrete_vals) / n) ** 0.5
std_e = (sum((e - mean_e) ** 2 for e in abs_error_vals) / n) ** 0.5
correlation = cov / (std_d * std_e) if std_d > 0 and std_e > 0 else 0

print(f"\nQ3: Pearson correlation(discrete_mismatches, avg_abs_error)")
print(f"    r = {correlation:.4f}")
if correlation > 0.9:
    print("    => STRONG POSITIVE: discrete and continuous metrics co-vary")
elif correlation > 0.5:
    print("    => MODERATE POSITIVE: partial co-variation")
else:
    print("    => WEAK: metrics are largely independent")

# Question 4: reach_agree from O2-B — does it separate solvers that discrete oracle collapsed?
print(f"\nQ4: reach_agree from O2-B — does it separate solvers that discrete oracle collapsed?")
q4_solvers = []
for s in o2a["per_solver"]:
    if s["discrete_mismatches"] == 0:
        b = o2b_by_solver[s["solver_id"]]
        if b["avg_reach_agree"] < 1.0:
            q4_solvers.append((s["solver_id"], s["discrete_mismatches"], s["avg_abs_error"], b["avg_reach_agree"]))

print(f"    Solvers with discrete_mismatches=0 AND reach_agree < 1.0: {len(q4_solvers)}")
if q4_solvers:
    for sid, dm, ae, ra in q4_solvers:
        print(f"    {sid}: discrete_mismatches={dm}, avg_abs_error={ae:.4f}, reach_agree={ra:.4f}")
    print("    => REACH_AGREE SEPARATES SOLVERS THAT DISCRETE ORACLE COLLAPSED")
else:
    print("    => NO: reach_agree is 1.0 for all zero-discrete-mismatch solvers")

# Summary table
print(f"\n{'=' * 70}")
print("SUMMARY TABLE")
print(f"{'=' * 70}")
print(f"{'Solver':<8} {'Fam':<5} {'Disc':<6} {'AbsErr':<10} {'Reach':<8} {'PathCt':<8} {'EdgeUs':<8}")
print("-" * 70)
for s in o2a["per_solver"]:
    b = o2b_by_solver[s["solver_id"]]
    print(f"{s['solver_id']:<8} {s['declared']:<5} {s['discrete_mismatches']:<6} "
          f"{s['avg_abs_error']:<10.4f} {b['avg_reach_agree']:<8.4f} "
          f"{b['avg_path_count']:<8.4f} {b['avg_edge_usage']:<8.4f}")

# Key finding
print(f"\n{'=' * 70}")
print("KEY FINDING")
print(f"{'=' * 70}")
if q1_solvers:
    print("The discrete oracle hides latent behavioral variation.")
    print(f"{len(q1_solvers)} solvers have zero discrete mismatches but nonzero continuous error.")
elif q2_solvers:
    print("The discrete oracle penalizes behavior that is continuously identical.")
    print(f"{len(q2_solvers)} solvers have nonzero discrete mismatches but zero continuous error.")
else:
    print("The discrete oracle is injective over the continuous error space.")
    print("Zero discrete mismatches ⟺ zero continuous error.")
    print("The oracle quotienting is lossless for this solver population.")
