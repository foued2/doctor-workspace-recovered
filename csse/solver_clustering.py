"""Solver clustering from binary failure vectors.

Discover latent structure directly from failure patterns without phi.
Test if discovered clusters predict correctness.
Identify probes with highest cluster-separation power.
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    SEED, lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
    lc45_to_input, lc45_oracle,
)


def compute_failure_matrix(problem_class, to_input, oracle_fn, style):
    """Compute binary failure matrix (solvers x probes)."""
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    # Build failure matrix
    sids = sorted(solver_evals.keys())
    failure_matrix = []
    for sid in sids:
        vector = []
        for pid in obs:
            passed = solver_evals[sid].get(pid, True)
            vector.append(0 if passed else 1)
        failure_matrix.append(vector)
    
    return sids, obs, failure_matrix, ground_truth


def hamming_distance(v1, v2):
    """Compute Hamming distance between two binary vectors."""
    return sum(a != b for a, b in zip(v1, v2))


def hierarchical_clustering(sids, failure_matrix, n_clusters=3):
    """Simple agglomerative clustering using Hamming distance."""
    n = len(sids)
    
    # Initialize: each solver is its own cluster
    clusters = {i: [i] for i in range(n)}
    cluster_list = list(range(n))
    
    # Compute distance matrix
    dist_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = hamming_distance(failure_matrix[i], failure_matrix[j])
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d
    
    # Merge until we have n_clusters
    while len(cluster_list) > n_clusters:
        # Find closest pair of clusters
        min_dist = float('inf')
        merge_i, merge_j = -1, -1
        
        for i in range(len(cluster_list)):
            for j in range(i + 1, len(cluster_list)):
                ci = cluster_list[i]
                cj = cluster_list[j]
                
                # Average linkage
                total_dist = 0
                count = 0
                for si in clusters[ci]:
                    for sj in clusters[cj]:
                        total_dist += dist_matrix[si][sj]
                        count += 1
                
                avg_dist = total_dist / count if count > 0 else 0
                
                if avg_dist < min_dist:
                    min_dist = avg_dist
                    merge_i, merge_j = i, j
        
        # Merge clusters
        ci = cluster_list[merge_i]
        cj = cluster_list[merge_j]
        
        clusters[ci].extend(clusters[cj])
        del clusters[cj]
        cluster_list.pop(merge_j)
    
    # Assign cluster labels
    labels = [0] * n
    for label, indices in clusters.items():
        for idx in indices:
            labels[idx] = label
    
    return labels


def compute_cluster_separation(failure_matrix, labels, probe_indices):
    """Compute how well each probe separates clusters."""
    n_probes = len(probe_indices)
    n_clusters = len(set(labels))
    
    separations = []
    
    for j in range(n_probes):
        # Compute failure rate per cluster
        cluster_rates = defaultdict(list)
        for i, label in enumerate(labels):
            cluster_rates[label].append(failure_matrix[i][j])
        
        # Compute variance between clusters
        rates = [sum(vals) / len(vals) for vals in cluster_rates.values()]
        overall_rate = sum(sum(vals) for vals in cluster_rates.values()) / sum(len(vals) for vals in cluster_rates.values())
        
        # Between-cluster variance
        between_var = sum(len(vals) * (rate - overall_rate) ** 2 
                         for vals, rate in zip(cluster_rates.values(), rates)) / n_clusters
        
        # Within-cluster variance
        within_var = 0
        for vals, rate in zip(cluster_rates.values(), rates):
            within_var += sum((v - rate) ** 2 for v in vals)
        within_var /= (len(labels) - n_clusters)
        
        # Separation score (F-ratio like)
        separation = between_var / (within_var + 1e-10)
        separations.append(separation)
    
    return separations


def analyze_clusters(sids, failure_matrix, labels, ground_truth, obs, problem_class):
    """Analyze discovered clusters."""
    n_clusters = len(set(labels))
    
    print(f"\n=== CLUSTER ANALYSIS ===")
    print(f"Number of clusters: {n_clusters}")
    
    # Cluster sizes
    cluster_sizes = defaultdict(int)
    for label in labels:
        cluster_sizes[label] += 1
    
    print(f"Cluster sizes: {dict(cluster_sizes)}")
    
    # Correctness per cluster
    print(f"\n=== CORRECTNESS PER CLUSTER ===")
    for cluster_id in sorted(cluster_sizes.keys()):
        cluster_sids = [sids[i] for i in range(len(sids)) if labels[i] == cluster_id]
        correct = sum(1 for sid in cluster_sids if ground_truth.get(sid, False))
        total = len(cluster_sids)
        accuracy = correct / total if total > 0 else 0
        
        print(f"  Cluster {cluster_id}: {correct}/{total} correct ({accuracy:.1%})")
        
        # Show solvers in this cluster
        for sid in cluster_sids:
            marker = "CORRECT" if ground_truth.get(sid, False) else "WRONG"
            n_fail = sum(failure_matrix[sids.index(sid)])
            print(f"    {sid}: {marker}, {n_fail} failures")
    
    # Compute separation power per probe
    probe_separations = compute_cluster_separation(failure_matrix, labels, range(len(obs)))
    
    # Rank probes by separation power
    ranked_probes = sorted(enumerate(probe_separations), key=lambda x: x[1], reverse=True)
    
    print(f"\n=== TOP 10 PROBES BY SEPARATION POWER ===")
    for rank, (j, sep) in enumerate(ranked_probes[:10]):
        pid = obs[j]
        # Get R1 features
        from csse.representation_invariance import build_R1
        R1_features = build_R1(problem_class)
        feat = R1_features[pid]
        
        print(f"  {rank+1}. {pid}: separation={sep:.4f}")
        print(f"     Features: {feat}")
        
        # Show failure rates per cluster
        for cluster_id in sorted(cluster_sizes.keys()):
            rate = sum(failure_matrix[i][j] for i in range(len(sids)) if labels[i] == cluster_id) / cluster_sizes[cluster_id]
            print(f"     Cluster {cluster_id}: {rate:.1%} failure rate")
    
    return {
        "n_clusters": n_clusters,
        "cluster_sizes": dict(cluster_sizes),
        "cluster_labels": {sids[i]: labels[i] for i in range(len(sids))},
        "correctness_per_cluster": {
            cluster_id: {
                "correct": sum(1 for i in range(len(sids)) if labels[i] == cluster_id and ground_truth.get(sids[i], False)),
                "total": cluster_sizes[cluster_id],
            }
            for cluster_id in cluster_sizes
        },
        "probe_separations": {obs[j]: probe_separations[j] for j in range(len(obs))},
    }


def run_clustering_analysis(problem_class, to_input, oracle_fn, style):
    """Run full clustering analysis for one problem."""
    print(f"\n{'='*70}")
    print(f"  SOLVER CLUSTERING: {problem_class.upper()}")
    print(f"{'='*70}")
    
    sids, obs, failure_matrix, ground_truth = compute_failure_matrix(
        problem_class, to_input, oracle_fn, style
    )
    
    print(f"\n  Solvers: {len(sids)}")
    print(f"  Probes: {len(obs)}")
    
    # Try different numbers of clusters
    results = {}
    for n_clusters in [2, 3, 4]:
        print(f"\n{'='*50}")
        print(f"  N_CLUSTERS = {n_clusters}")
        print(f"{'='*50}")
        
        labels = hierarchical_clustering(sids, failure_matrix, n_clusters)
        result = analyze_clusters(sids, failure_matrix, labels, ground_truth, obs, problem_class)
        results[n_clusters] = result
    
    return results


if __name__ == "__main__":
    all_results = {}
    
    # Run LC3946 (the interesting case)
    all_results["lc3946"] = run_clustering_analysis(
        "lc3946", lc3946_to_input, lc3946_oracle, "single"
    )
    
    # Run LC322 for comparison
    all_results["lc322"] = run_clustering_analysis(
        "lc322", lc322_to_input, lc322_oracle, "single"
    )
    
    # Save results
    out_path = ROOT / "results" / "solver_clustering_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")
