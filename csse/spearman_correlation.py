"""Step 3: Spearman correlation between descriptors and rank stability.

N=4 problems. Small-N caveat applies.
Manual implementation (no scipy).
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "results" / "rank_stability_metric.json") as f:
    stability = json.load(f)

with open(ROOT / "results" / "problem_descriptors.json") as f:
    descriptors = json.load(f)


def rankdata(x):
    """Rank data with average ties."""
    n = len(x)
    order = np.argsort(x)
    ranks = np.empty(n, dtype=float)
    ranks[order] = np.arange(1, n + 1, dtype=float)
    # Handle ties
    sorted_x = np.sort(x)
    i = 0
    while i < n:
        j = i
        while j < n - 1 and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        if j > i:
            avg_rank = (i + 1 + j + 1) / 2.0
            for k in range(i, j + 1):
                idx = order[k]
                ranks[idx] = avg_rank
        i = j + 1
    return ranks


def spearman(x, y):
    """Spearman rho with permutation p-value."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    n = len(x)

    rx = rankdata(x)
    ry = rankdata(y)

    # Pearson on ranks
    rx_centered = rx - rx.mean()
    ry_centered = ry - ry.mean()
    rho = float(np.sum(rx_centered * ry_centered) /
                 np.sqrt(np.sum(rx_centered**2) * np.sum(ry_centered**2)))

    # Permutation p-value (all permutations for N=4 = 24)
    from itertools import permutations
    count = 0
    total = 0
    for perm in permutations(range(n)):
        total += 1
        ry_perm = ry[list(perm)]
        ry_perm_centered = ry_perm - ry_perm.mean()
        rho_perm = float(np.sum(rx_centered * ry_perm_centered) /
                         np.sqrt(np.sum(rx_centered**2) * np.sum(ry_perm_centered**2)))
        if abs(rho_perm) >= abs(rho):
            count += 1
    pval = count / total

    return rho, pval


problems = ["lc322", "lc3946", "lc45", "lc743"]
S_values = [stability[p]["S"] for p in problems]
constraint_values = [descriptors[p]["constraint_tightness"]["mean"] for p in problems]
branching_values = [descriptors[p]["branching_factor"]["mean"] for p in problems]
symmetry_values = [descriptors[p]["symmetry"]["mean"] for p in problems]

print("=" * 70)
print("  SPEARMAN CORRELATIONS: Descriptor vs Stability (S)")
print("  N=4. Permutation p-value (exact, 24 permutations).")
print("=" * 70)

print(f"\n  {'Problem':<10} {'S':>8} {'Constraint':>12} {'Branching':>12} {'Symmetry':>12}")
print("  " + "-" * 56)
for i, p in enumerate(problems):
    print(f"  {p:<10} {S_values[i]:>8.4f} {constraint_values[i]:>12.4f} {branching_values[i]:>12.4f} {symmetry_values[i]:>12.4f}")

print("\n  --- Spearman rho, permutation p-value ---\n")

descriptors_dict = {
    "constraint_tightness": constraint_values,
    "branching_factor": branching_values,
    "symmetry": symmetry_values,
}

results = {}
for name, values in descriptors_dict.items():
    rho, pval = spearman(S_values, values)
    results[name] = {"rho": rho, "pval": pval}
    sig = " *" if pval < 0.05 else "  "
    print(f"  {name}:")
    print(f"    rho = {rho:+.4f}, p = {pval:.4f}{sig}")
    print()

# Also check dim_change
dim_change = [stability[p]["dim_change"] for p in problems]
print("  --- Also: descriptor vs dim_change ---\n")
for name, values in descriptors_dict.items():
    rho, pval = spearman(dim_change, values)
    print(f"  {name}: rho = {rho:+.4f}, p = {pval:.4f}")

print("\n" + "=" * 70)
print("  FALSIFICATION CHECK")
print("=" * 70)
any_monotonic = any(abs(r["rho"]) > 0.5 for r in results.values())
any_significant = any(r["pval"] < 0.05 for r in results.values())

if not any_monotonic:
    print("  FALSIFIED: No descriptor shows |rho| > 0.5 with stability.")
elif not any_significant:
    print("  INCONCLUSIVE: Some |rho| > 0.5 but none significant (p < 0.05).")
    print("  N=4 is too small. Signal exists but unconfirmed.")
else:
    print("  SURVIVED: At least one descriptor shows monotonic alignment (p < 0.05).")
    for name, r in results.items():
        if r["pval"] < 0.05:
            print(f"    {name}: rho={r['rho']:+.4f}, p={r['pval']:.4f}")

out_path = ROOT / "results" / "spearman_correlations.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_path}")
