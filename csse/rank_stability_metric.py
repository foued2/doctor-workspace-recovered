"""Step 1: Compute rank stability metric S for all 4 problems."""
import json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "results" / "svd_analysis_results.json") as f:
    orig_lc3946_lc322 = json.load(f)

with open(ROOT / "results" / "svd_analysis_lc45_lc743.json") as f:
    orig_lc45_lc743 = json.load(f)

with open(ROOT / "results" / "svd_analysis_lc3946_v2.json") as f:
    v2_lc3946 = json.load(f)

with open(ROOT / "results" / "svd_analysis_lc322_v2.json") as f:
    v2_lc322 = json.load(f)

with open(ROOT / "results" / "svd_analysis_v2_extended.json") as f:
    v2_lc45_lc743 = json.load(f)

sv = {
    "lc3946": {
        "orig": np.array(orig_lc3946_lc322["lc3946"]["singular_values"]),
        "v2": np.array(v2_lc3946["singular_values"]),
    },
    "lc322": {
        "orig": np.array(orig_lc3946_lc322["lc322"]["singular_values"]),
        "v2": np.array(v2_lc322["singular_values"]),
    },
    "lc45": {
        "orig": np.array(orig_lc45_lc743["lc45"]["singular_values"]),
        "v2": np.array(v2_lc45_lc743[0]["singular_values"]),
    },
    "lc743": {
        "orig": np.array(orig_lc45_lc743["lc743"]["singular_values"]),
        "v2": np.array(v2_lc45_lc743[1]["singular_values"]),
    },
}

print("=" * 70)
print("  RANK STABILITY METRIC: S = E[|s_orig - s_v2|]")
print("  Low S = stable, high S = unstable")
print("=" * 70)

results = {}
for problem in ["lc3946", "lc322", "lc45", "lc743"]:
    orig = sv[problem]["orig"]
    v2 = sv[problem]["v2"]

    max_len = max(len(orig), len(v2))
    orig_padded = np.pad(orig, (0, max_len - len(orig)))
    v2_padded = np.pad(v2, (0, max_len - len(v2)))

    abs_diff = np.abs(orig_padded - v2_padded)
    S = abs_diff.mean()

    if problem in orig_lc3946_lc322:
        orig_dim = orig_lc3946_lc322[problem]["intrinsic_dim"]
    else:
        orig_dim = orig_lc45_lc743[problem]["intrinsic_dim"]

    if problem == "lc3946":
        v2_dim = v2_lc3946["intrinsic_dim"]
    elif problem == "lc322":
        v2_dim = v2_lc322["intrinsic_dim"]
    elif problem == "lc45":
        v2_dim = v2_lc45_lc743[0]["intrinsic_dim"]
    else:
        v2_dim = v2_lc45_lc743[1]["intrinsic_dim"]

    dim_change = abs(orig_dim - v2_dim)

    results[problem] = {
        "S": float(S),
        "orig_dim": int(orig_dim),
        "v2_dim": int(v2_dim),
        "dim_change": int(dim_change),
        "abs_diff_top5": abs_diff[:5].tolist(),
    }

    print(f"\n  {problem.upper()}:")
    print(f"    S (mean |ds|): {S:.4f}")
    print(f"    Intrinsic dim: {orig_dim} -> {v2_dim} (d={dim_change})")
    print(f"    Top-5 |ds|: {[f'{x:.3f}' for x in abs_diff[:5]]}")

print("\n" + "=" * 70)
print("  STABILITY RANKING (low S = stable)")
print("=" * 70)
ranked = sorted(results.items(), key=lambda x: x[1]["S"])
for i, (problem, data) in enumerate(ranked):
    stable = "STABLE" if data["dim_change"] <= 1 else "UNSTABLE"
    print(f"    {i+1}. {problem}: S={data['S']:.4f}, dim {data['orig_dim']}->{data['v2_dim']}, {stable}")

out_path = ROOT / "results" / "rank_stability_metric.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_path}")
