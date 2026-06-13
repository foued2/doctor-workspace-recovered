"""Structured-feature phi: non-trivial exogenous clustering.

Uses static input properties only. No failure information.
Clusters inputs using structural features.
"""
import sys
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import load_probes


def extract_features_lc322(probe):
    """Extract static structural features for LC322.
    
    Features:
    - amount: target amount
    - n_coins: number of coin denominations
    - min_coin: minimum coin value
    - max_coin: maximum coin value
    - coin_range: max_coin - min_coin
    - amount_to_max_ratio: amount / max_coin
    - gcd_coins: GCD of all coins (affects reachability)
    - n_distinct: number of distinct coin values
    """
    coins = probe.get("coins", [])
    amount = probe.get("amount", 0)
    
    if not coins:
        return {
            "amount": amount,
            "n_coins": 0,
            "min_coin": 0,
            "max_coin": 0,
            "coin_range": 0,
            "amount_to_max_ratio": 0,
            "gcd_coins": 0,
            "n_distinct": 0,
        }
    
    # Compute GCD of coins
    coin_gcd = coins[0]
    for c in coins[1:]:
        coin_gcd = gcd(coin_gcd, c)
    
    return {
        "amount": amount,
        "n_coins": len(coins),
        "min_coin": min(coins),
        "max_coin": max(coins),
        "coin_range": max(coins) - min(coins),
        "amount_to_max_ratio": amount / max(coins) if max(coins) > 0 else 0,
        "gcd_coins": coin_gcd,
        "n_distinct": len(set(coins)),
    }


def extract_features_lc3946(probe):
    """Extract static structural features for LC3946.
    
    Features:
    - n_items: number of items
    - budget: budget value
    - total_weight: sum of weights
    - total_value: sum of values
    - avg_weight: average weight
    - avg_value: average value
    - weight_variance: variance of weights
    - value_variance: variance of values
    - budget_to_weight_ratio: budget / total_weight
    - n_items_in_budget: count of items with weight <= budget
    """
    items = probe.get("items", [])
    budget = probe.get("budget", 0)
    
    if not items:
        return {
            "n_items": 0,
            "budget": budget,
            "total_weight": 0,
            "total_value": 0,
            "avg_weight": 0,
            "avg_value": 0,
            "weight_variance": 0,
            "value_variance": 0,
            "budget_to_weight_ratio": 0,
            "n_items_in_budget": 0,
        }
    
    weights = [w for w, v in items]
    values = [v for w, v in items]
    
    n = len(items)
    avg_w = sum(weights) / n
    avg_v = sum(values) / n
    
    w_var = sum((w - avg_w) ** 2 for w in weights) / n if n > 0 else 0
    v_var = sum((v - avg_v) ** 2 for v in values) / n if n > 0 else 0
    
    total_w = sum(weights)
    budget_ratio = budget / total_w if total_w > 0 else 0
    n_in_budget = sum(1 for w in weights if w <= budget)
    
    return {
        "n_items": n,
        "budget": budget,
        "total_weight": total_w,
        "total_value": sum(values),
        "avg_weight": avg_w,
        "avg_value": avg_v,
        "weight_variance": w_var,
        "value_variance": v_var,
        "budget_to_weight_ratio": budget_ratio,
        "n_items_in_budget": n_in_budget,
    }


def normalize_features(features_list):
    """Normalize features to [0, 1] range."""
    if not features_list:
        return []
    
    # Get all feature names
    feature_names = list(features_list[0].keys())
    
    # Compute min/max for each feature
    mins = {}
    maxs = {}
    for name in feature_names:
        values = [f[name] for f in features_list]
        mins[name] = min(values)
        maxs[name] = max(values)
    
    # Normalize
    normalized = []
    for f in features_list:
        norm_f = {}
        for name in feature_names:
            range_val = maxs[name] - mins[name]
            if range_val > 0:
                norm_f[name] = (f[name] - mins[name]) / range_val
            else:
                norm_f[name] = 0.0
        normalized.append(norm_f)
    
    return normalized


def kmeans_cluster(features, k, max_iterations=100):
    """Simple K-means clustering."""
    import random
    
    if not features or k <= 0:
        return []
    
    feature_names = list(features[0].keys())
    n = len(features)
    
    # Initialize centroids randomly
    rng = random.Random(42)
    centroid_indices = rng.sample(range(n), min(k, n))
    centroids = [features[i] for i in centroid_indices]
    
    assignments = [0] * n
    
    for _ in range(max_iterations):
        # Assign points to nearest centroid
        new_assignments = []
        for i in range(n):
            min_dist = float("inf")
            best_cluster = 0
            for j, centroid in enumerate(centroids):
                dist = sum((features[i][name] - centroid[name]) ** 2 for name in feature_names)
                if dist < min_dist:
                    min_dist = dist
                    best_cluster = j
            new_assignments.append(best_cluster)
        
        # Check convergence
        if new_assignments == assignments:
            break
        assignments = new_assignments
        
        # Update centroids
        for j in range(k):
            cluster_points = [features[i] for i in range(n) if assignments[i] == j]
            if cluster_points:
                centroids[j] = {
                    name: sum(p[name] for p in cluster_points) / len(cluster_points)
                    for name in feature_names
                }
    
    return assignments


def build_phi_structured(problem_class, k=4):
    """Build structured-feature phi using clustering."""
    probes = load_probes(problem_class)
    
    if problem_class == "lc322":
        extract_fn = extract_features_lc322
    elif problem_class == "lc3946":
        extract_fn = extract_features_lc3946
    else:
        raise ValueError(f"Unknown problem class: {problem_class}")
    
    # Extract features
    probe_ids = [p["probe_id"] for p in probes]
    raw_features = [extract_fn(p) for p in probes]
    
    # Normalize
    norm_features = normalize_features(raw_features)
    
    # Cluster
    assignments = kmeans_cluster(norm_features, k)
    
    # Build phi
    phi = {}
    for pid, cluster in zip(probe_ids, assignments):
        phi[pid] = f"cluster_{cluster}"
    
    return phi


def build_phi_random(problem_class, k=4):
    """Build random phi baseline (fixed seed, once)."""
    import random
    
    probes = load_probes(problem_class)
    probe_ids = [p["probe_id"] for p in probes]
    
    rng = random.Random(42)
    assignments = [rng.randint(0, k - 1) for _ in range(len(probes))]
    
    phi = {}
    for pid, cluster in zip(probe_ids, assignments):
        phi[pid] = f"random_{cluster}"
    
    return phi


if __name__ == "__main__":
    for pc in ["lc322", "lc3946"]:
        phi_struct = build_phi_structured(pc, k=4)
        phi_rand = build_phi_random(pc, k=4)
        
        struct_counts = {}
        for fam in phi_struct.values():
            struct_counts[fam] = struct_counts.get(fam, 0) + 1
        
        rand_counts = {}
        for fam in phi_rand.values():
            rand_counts[fam] = rand_counts.get(fam, 0) + 1
        
        print(f"{pc}:")
        print(f"  Structured: {struct_counts}")
        print(f"  Random: {rand_counts}")
