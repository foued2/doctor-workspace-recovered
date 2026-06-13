"""Step 2: Compute problem-side descriptors for all 4 problems.

Three descriptor classes:
1. Constraint tightness: rejection density under random policy
2. State-space branching: effective branching factor
3. Symmetry / redundancy: input equivalence under permutation
"""
import json
import random
import numpy as np
from pathlib import Path
from collections import Counter

import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SEED = 20260611
random.seed(SEED)
np.random.seed(SEED)

from csse.phi_robustness import load_probes, load_observed_target_split


# ============================================================
# PROBLEM-SPECIFIC COMPUTATION FUNCTIONS
# ============================================================

def lc45_descriptors(probes, obs):
    """Compute descriptors for LC45 (Jump Game II)."""
    results = []
    for pid in obs:
        probe = next(p for p in probes if p["probe_id"] == pid)
        nums = probe["nums"]
        n = len(nums)

        # 1. Constraint tightness: fraction of dead-end positions
        dead_ends = sum(1 for i in range(n) if nums[i] == 0 and i < n - 1)
        tightness = dead_ends / max(n - 1, 1)

        # 2. Branching factor: average reachable positions per step
        total_branches = 0
        for i in range(n - 1):
            reachable = min(nums[i], n - 1 - i)
            total_branches += reachable
        branching = total_branches / max(n - 1, 1)

        # 3. Symmetry: fraction of positions with same jump value
        value_counts = Counter(nums)
        max_dup = max(value_counts.values())
        symmetry = max_dup / n

        results.append({
            "probe_id": pid,
            "constraint_tightness": tightness,
            "branching_factor": branching,
            "symmetry": symmetry,
        })
    return results


def lc322_descriptors(probes, obs):
    """Compute descriptors for LC322 (Coin Change)."""
    results = []
    for pid in obs:
        probe = next(p for p in probes if p["probe_id"] == pid)
        coins = probe["coins"]
        amount = probe["amount"]

        # 1. Constraint tightness: fraction of amounts unreachable by greedy
        reachable_by_greedy = set()
        for c in coins:
            for multiple in range(0, amount + 1, c):
                reachable_by_greedy.add(multiple)
        tightness = 1.0 - len(reachable_by_greedy) / max(amount + 1, 1)

        # 2. Branching factor: average coin choices per sub-problem
        branching = len(coins)

        # 3. Symmetry: fraction of coins with same value
        value_counts = Counter(coins)
        max_dup = max(value_counts.values()) if coins else 1
        symmetry = max_dup / max(len(coins), 1)

        results.append({
            "probe_id": pid,
            "constraint_tightness": tightness,
            "branching_factor": branching,
            "symmetry": symmetry,
        })
    return results


def lc3946_descriptors(probes, obs):
    """Compute descriptors for LC3946 (Max Items from Sale)."""
    results = []
    for pid in obs:
        probe = next(p for p in probes if p["probe_id"] == pid)
        items = probe["items"]
        budget = probe["budget"]

        # 1. Constraint tightness: fraction of budget usable
        prices = [item[1] for item in items]
        min_price = min(prices) if prices else budget
        max_affordable = budget // min_price if min_price > 0 else 0
        tightness = 1.0 - max_affordable / max(budget, 1)

        # 2. Branching factor: average affordable items per budget level
        affordable_counts = []
        for fraction in [0.25, 0.5, 0.75]:
            sub_budget = int(budget * fraction)
            affordable = sum(1 for p in prices if p <= sub_budget)
            affordable_counts.append(affordable)
        branching = np.mean(affordable_counts)

        # 3. Symmetry: fraction of items with same price
        value_counts = Counter(prices)
        max_dup = max(value_counts.values()) if prices else 1
        symmetry = max_dup / max(len(items), 1)

        results.append({
            "probe_id": pid,
            "constraint_tightness": tightness,
            "branching_factor": branching,
            "symmetry": symmetry,
        })
    return results


def lc743_descriptors(probes, obs):
    """Compute descriptors for LC743 (Network Delay)."""
    results = []
    for pid in obs:
        probe = next(p for p in probes if p["probe_id"] == pid)
        times = probe["times"]
        n = probe["n"]
        k = probe["k"]

        # 1. Constraint tightness: fraction of nodes unreachable from source
        if not times:
            tightness = 1.0 if n > 1 else 0.0
        else:
            from collections import defaultdict, deque
            graph = defaultdict(list)
            for u, v, w in times:
                graph[u].append(v)
            visited = set()
            queue = deque([k])
            visited.add(k)
            while queue:
                u = queue.popleft()
                for v in graph[u]:
                    if v not in visited:
                        visited.add(v)
                        queue.append(v)
            unreachable = n - len(visited)
            tightness = unreachable / max(n, 1)

        # 2. Branching factor: average out-degree
        out_degree = Counter(u for u, v, w in times)
        if out_degree:
            branching = np.mean(list(out_degree.values()))
        else:
            branching = 0.0

        # 3. Symmetry: fraction of nodes with same out-degree
        degree_values = list(out_degree.values())
        if degree_values:
            degree_counts = Counter(degree_values)
            max_dup = max(degree_counts.values())
            symmetry = max_dup / max(n, 1)
        else:
            symmetry = 1.0

        results.append({
            "probe_id": pid,
            "constraint_tightness": tightness,
            "branching_factor": branching,
            "symmetry": symmetry,
        })
    return results


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("  PROBLEM-SIDE DESCRIPTORS")
print("=" * 70)

all_results = {}

for problem_class, descriptor_fn in [
    ("lc322", lc322_descriptors),
    ("lc3946", lc3946_descriptors),
    ("lc45", lc45_descriptors),
    ("lc743", lc743_descriptors),
]:
    probes = load_probes(problem_class)
    obs, _ = load_observed_target_split(problem_class)

    descriptors = descriptor_fn(probes, obs)

    # Aggregate to problem level (mean across probes)
    constraint_vals = [d["constraint_tightness"] for d in descriptors]
    branching_vals = [d["branching_factor"] for d in descriptors]
    symmetry_vals = [d["symmetry"] for d in descriptors]

    all_results[problem_class] = {
        "constraint_tightness": {
            "mean": float(np.mean(constraint_vals)),
            "std": float(np.std(constraint_vals)),
            "per_probe": descriptors,
        },
        "branching_factor": {
            "mean": float(np.mean(branching_vals)),
            "std": float(np.std(branching_vals)),
        },
        "symmetry": {
            "mean": float(np.mean(symmetry_vals)),
            "std": float(np.std(symmetry_vals)),
        },
    }

    print(f"\n  {problem_class.upper()}:")
    print(f"    Constraint tightness: {np.mean(constraint_vals):.4f} (+/- {np.std(constraint_vals):.4f})")
    print(f"    Branching factor:     {np.mean(branching_vals):.4f} (+/- {np.std(branching_vals):.4f})")
    print(f"    Symmetry:             {np.mean(symmetry_vals):.4f} (+/- {np.std(symmetry_vals):.4f})")

# Save
out_path = ROOT / "results" / "problem_descriptors.json"
with open(out_path, "w") as f:
    json.dump(all_results, f, indent=2)
print(f"\nSaved to {out_path}")
