"""Step 4A: Permutation null test for descriptors vs S.

For N=4 problems, there are 4! = 24 permutations.
We compute exact null distribution (no sampling needed).
"""
import json
import numpy as np
from pathlib import Path
from itertools import permutations

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "results" / "rank_stability_metric.json") as f:
    stability = json.load(f)

with open(ROOT / "results" / "problem_descriptors.json") as f:
    descriptors = json.load(f)


def rankdata(x):
    n = len(x)
    order = np.argsort(x)
    ranks = np.empty(n, dtype=float)
    ranks[order] = np.arange(1, n + 1, dtype=float)
    sorted_x = np.sort(x)
    i = 0
    while i < n:
        j = i
        while j < n - 1 and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        if j > i:
            avg_rank = (i + 1 + j + 1) / 2.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman_rho(x, y):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    rx = rankdata(x) - np.mean(rankdata(x))
    ry = rankdata(y) - np.mean(rankdata(y))
    return float(np.sum(rx * ry) / np.sqrt(np.sum(rx**2) * np.sum(ry**2)))


problems = ["lc322", "lc3946", "lc45", "lc743"]
S_values = [stability[p]["S"] for p in problems]

descriptors_dict = {
    "constraint_tightness": [descriptors[p]["constraint_tightness"]["mean"] for p in problems],
    "branching_factor": [descriptors[p]["branching_factor"]["mean"] for p in problems],
    "symmetry": [descriptors[p]["symmetry"]["mean"] for p in problems],
}

print("=" * 70)
print("  PERMUTATION NULL TEST (exact, 4! = 24 permutations)")
print("=" * 70)

results = {}
for name, values in descriptors_dict.items():
    observed_rho = spearman_rho(S_values, values)

    # Build null distribution
    null_rhos = []
    for perm in permutations(range(4)):
        permuted_values = [values[i] for i in perm]
        rho = spearman_rho(S_values, permuted_values)
        null_rhos.append(rho)

    null_rhos = np.array(null_rhos)

    # p-value: fraction of null |rho| >= observed |rho|
    p_value = np.mean(np.abs(null_rhos) >= abs(observed_rho))

    # Null stats
    null_mean = null_rhos.mean()
    null_std = null_rhos.std()
    null_95 = np.percentile(null_rhos, [2.5, 97.5])

    results[name] = {
        "observed_rho": float(observed_rho),
        "null_mean": float(null_mean),
        "null_std": float(null_std),
        "null_95_ci": [float(null_95[0]), float(null_95[1])],
        "p_value": float(p_value),
    }

    print(f"\n  {name}:")
    print(f"    Observed rho:  {observed_rho:+.4f}")
    print(f"    Null mean:     {null_mean:+.4f} (+/- {null_std:.4f})")
    print(f"    Null 95% CI:   [{null_95[0]:+.4f}, {null_95[1]:+.4f}]")
    print(f"    p-value:       {p_value:.4f}")

    if p_value < 0.05:
        print(f"    VERDICT: SIGNIFICANT (p < 0.05)")
    elif p_value < 0.10:
        print(f"    VERDICT: MARGINAL (p < 0.10)")
    else:
        print(f"    VERDICT: NOT SIGNIFICANT")

print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)

for name, r in results.items():
    sig = "YES" if r["p_value"] < 0.05 else "NO"
    print(f"  {name}: observed={r['observed_rho']:+.4f}, p={r['p_value']:.4f}, significant={sig}")

out_path = ROOT / "results" / "permutation_null_test.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_path}")
