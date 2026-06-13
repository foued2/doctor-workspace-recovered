"""CSDT-1: Cross-Solver Structural Decomposition Test

Determines whether LC756 solvers contain true compositional modules
or whether all apparent modules are projections of a single latent control process.

Selected solvers:
  s001 (F1): stops BFS early when target node is found
  s008 (F2): uses w^2 instead of w in relaxation
  s016 (F3): uses stack (LIFO) instead of heap

Subcomponents extracted:
  1. Input parsing / state initialization (identical across all)
  2. Graph construction (identical across all)
  3. Transition / relaxation / update logic (differs per solver)
  4. Termination / scoring / output (differs per solver)
"""
from __future__ import annotations

import heapq
import math
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

# --- CONFIG ---
PYTHON = r"C:\Users\pakla\AppData\Local\Programs\Python\Python314\python.exe"
SOLVER_PATH = Path("doctor/solvers/lc756/lc_756_solvers.py")
ORACLE_PATH = Path("doctor/oracles/lc743_oracle.py")
TIMEOUT_SECONDS = 2

# --- TIMEOUT MECHANISM ---

class TimeoutError(Exception):
    pass

def timeout_handler():
    raise TimeoutError("Solver execution timed out")

def run_with_timeout(func, args, timeout=TIMEOUT_SECONDS):
    """Run func with timeout using threading."""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"Timeout after {timeout}s")
    
    if exception[0] is not None:
        raise exception[0]
    
    return result[0]

# --- SOLVER DEFINITIONS ---

def s001(times, n, k):
    """F1: UNDER_PROPAGATION — stops BFS early when target node is found."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == n:
            break  # Bug: stops early
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s008(times, n, k):
    """F2: OVER_COST_BIAS — uses w^2 instead of w."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w ** 2  # Bug: squares weight
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s016(times, n, k):
    """F3: PRIORITY_ORDER_FAILURE — uses stack (LIFO) instead of heap."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    stack = [k]  # Bug: uses stack instead of heap
    while stack:
        u = stack.pop()
        for v, w in graph[u]:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
                stack.append(v)
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


# --- HYBRID DEFINITIONS ---

def hybrid_h018(times, n, k):
    """H(001,008): graph from s001, relaxation from s008 (w^2), termination from s001."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == n:
            break  # from s001
        for v, w in graph[u]:
            nd = d + w ** 2  # from s008
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def hybrid_h081(times, n, k):
    """H(008,001): graph from s008, relaxation from s001 (w), termination from s008."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == n:
            break  # from s001
        for v, w in graph[u]:
            nd = d + w  # from s001
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def hybrid_h016(times, n, k):
    """H(001,016): graph from s001, relaxation from s016 (stack), termination from s001."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    stack = [k]  # from s016
    while stack:
        u = stack.pop()
        if u == n:
            break  # from s001
        for v, w in graph[u]:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
                stack.append(v)
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def hybrid_h160(times, n, k):
    """H(016,001): graph from s016, relaxation from s001 (w), termination from s016."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]  # from s001
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w  # from s001
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def hybrid_h086(times, n, k):
    """H(008,016): graph from s008, relaxation from s016 (stack), termination from s008."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    stack = [k]  # from s016
    while stack:
        u = stack.pop()
        for v, w in graph[u]:
            nd = dist[u] + w  # from s016
            if nd < dist[v]:
                dist[v] = nd
                stack.append(v)
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def hybrid_h608(times, n, k):
    """H(016,008): graph from s016, relaxation from s008 (w^2), termination from s016."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    stack = [k]  # from s016
    while stack:
        u = stack.pop()
        for v, w in graph[u]:
            nd = dist[u] + w ** 2  # from s008
            if nd < dist[v]:
                dist[v] = nd
                stack.append(v)
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


# --- PROBE GENERATION ---

def generate_probes(seed=42, n_probes=20):
    """Generate identical micro-probe set for all solvers."""
    rng = np.random.RandomState(seed)
    probes = []
    
    for i in range(n_probes):
        n = rng.randint(2, 8)
        k = rng.randint(1, n)
        n_edges = rng.randint(n - 1, min(n * (n - 1), 20))
        
        # Generate random edges
        edges = set()
        for _ in range(n_edges):
            u = rng.randint(1, n)
            v = rng.randint(1, n)
            if u != v:
                w = rng.randint(1, 10)
                edges.add((u, v, w))
        
        # Ensure connectivity from k
        reachable = {k}
        for _ in range(n):
            new_reachable = set()
            for u, v, w in edges:
                if u in reachable:
                    new_reachable.add(v)
            reachable.update(new_reachable)
        
        # Add edges to make all nodes reachable
        for node in range(1, n + 1):
            if node not in reachable:
                edges.add((k, node, rng.randint(1, 10)))
                reachable.add(node)
        
        times = list(edges)
        probes.append((times, n, k))
    
    return probes


# --- ORACLE ---

def load_oracle():
    """Load LC743 oracle for reference."""
    # Import from the oracle file
    sys.path.insert(0, str(ORACLE_PATH.parent.parent))
    from doctor.oracles.lc743_oracle import dijkstra_oracle
    return dijkstra_oracle


# --- BEHAVIORAL ANALYSIS ---

def compute_behavioral_signature(solver_func, probes):
    """Compute behavioral signature: list of outputs for each probe."""
    signature = []
    for times, n, k in probes:
        try:
            result = run_with_timeout(solver_func, (times, n, k))
            signature.append(result)
        except (TimeoutError, Exception) as e:
            signature.append(None)
    return signature


def compute_pairwise_distance(sig1, sig2):
    """Compute Hamming distance between two behavioral signatures."""
    if len(sig1) != len(sig2):
        return 1.0
    
    mismatches = 0
    valid_pairs = 0
    for r1, r2 in zip(sig1, sig2):
        if r1 is not None and r2 is not None:
            valid_pairs += 1
            if r1 != r2:
                mismatches += 1
    
    if valid_pairs == 0:
        return 1.0
    return mismatches / valid_pairs


def cluster_signatures(signatures, names, threshold=0.3):
    """Cluster behavioral signatures using hierarchical clustering."""
    n = len(signatures)
    dist_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            d = compute_pairwise_distance(signatures[i], signatures[j])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d
    
    # Simple agglomerative clustering (single linkage)
    clusters = [[i] for i in range(n)]
    merge_history = []
    
    while len(clusters) > 1:
        # Find closest pair of clusters
        min_dist = float('inf')
        min_i, min_j = 0, 1
        
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                # Single linkage: min distance between any two points
                for ci in clusters[i]:
                    for cj in clusters[j]:
                        if dist_matrix[ci, cj] < min_dist:
                            min_dist = dist_matrix[ci, cj]
                            min_i, min_j = i, j
        
        if min_dist > threshold:
            break
        
        # Merge clusters
        merge_history.append({
            'clusters': (clusters[min_i][:], clusters[min_j][:]),
            'distance': min_dist
        })
        clusters[min_i] = clusters[min_i] + clusters[min_j]
        clusters.pop(min_j)
    
    return clusters, merge_history


# --- MAIN ---

def main():
    print("=" * 70)
    print("CSDT-1: Cross-Solver Structural Decomposition Test")
    print("=" * 70)
    
    # Step 1: Generate probes
    print("\n[1/6] Generating identical micro-probe set...")
    probes = generate_probes(seed=42, n_probes=20)
    print(f"  Generated {len(probes)} probes")
    
    # Step 2: Define solvers and hybrids
    print("\n[2/6] Defining solver matrix...")
    solvers = {
        's001': s001,
        's008': s008,
        's016': s016,
    }
    hybrids = {
        'H(001,008)': hybrid_h018,
        'H(008,001)': hybrid_h081,
        'H(001,016)': hybrid_h016,
        'H(016,001)': hybrid_h160,
        'H(008,016)': hybrid_h086,
        'H(016,008)': hybrid_h608,
    }
    
    all_solvers = {**solvers, **hybrids}
    print(f"  Parent solvers: {list(solvers.keys())}")
    print(f"  Hybrids: {list(hybrids.keys())}")
    
    # Step 3: Compute behavioral signatures
    print("\n[3/6] Computing behavioral signatures...")
    signatures = {}
    for name, func in all_solvers.items():
        sig = compute_behavioral_signature(func, probes)
        signatures[name] = sig
        # Count valid results
        valid = sum(1 for r in sig if r is not None)
        print(f"  {name}: {valid}/{len(probes)} valid results")
    
    # Step 4: Compute pairwise distances
    print("\n[4/6] Computing pairwise behavioral distances...")
    names = list(all_solvers.keys())
    n = len(names)
    dist_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            d = compute_pairwise_distance(signatures[names[i]], signatures[names[j]])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d
    
    # Print distance matrix
    print("\n  Distance matrix (Hamming):")
    print("  " + " " * 12 + " ".join(f"{name:>10}" for name in names))
    for i, name in enumerate(names):
        row = " ".join(f"{dist_matrix[i, j]:10.4f}" for j in range(n))
        print(f"  {name:>12} {row}")
    
    # Step 5: Cluster analysis
    print("\n[5/6] Clustering analysis...")
    clusters, merge_history = cluster_signatures(
        [signatures[name] for name in names],
        names,
        threshold=0.3
    )
    
    print(f"\n  Clusters formed (threshold=0.3):")
    for i, cluster in enumerate(clusters):
        member_names = [names[idx] for idx in cluster]
        print(f"    Cluster {i+1}: {member_names}")
    
    # Step 6: Decision rule
    print("\n[6/6] Decision rule application...")
    
    # Check if hybrids form new stable behavioral clusters
    hybrid_indices = [i for i, name in enumerate(names) if name in hybrids]
    parent_indices = [i for i, name in enumerate(names) if name in solvers]
    
    # Check if any hybrid is in a different cluster than all parents
    hybrid_clusters = set()
    parent_clusters = set()
    
    for i, cluster in enumerate(clusters):
        for idx in cluster:
            if names[idx] in hybrids:
                hybrid_clusters.add(i)
            if names[idx] in solvers:
                parent_clusters.add(i)
    
    new_cluster_only_hybrids = hybrid_clusters - parent_clusters
    
    # Compute within-cluster vs between-cluster distances
    within_dists = []
    between_dists = []
    
    for cluster in clusters:
        for i in cluster:
            for j in cluster:
                if i < j:
                    within_dists.append(dist_matrix[i, j])
    
    for i in range(n):
        for j in range(i + 1, n):
            ci = next(idx for idx, cluster in enumerate(clusters) if i in cluster)
            cj = next(idx for idx, cluster in enumerate(clusters) if j in cluster)
            if ci != cj:
                between_dists.append(dist_matrix[i, j])
    
    avg_within = np.mean(within_dists) if within_dists else 0
    avg_between = np.mean(between_dists) if between_dists else 0
    
    print(f"\n  Average within-cluster distance: {avg_within:.4f}")
    print(f"  Average between-cluster distance: {avg_between:.4f}")
    print(f"  Cluster separation ratio: {avg_between / avg_within:.2f}x" if avg_within > 0 else "  N/A")
    
    print(f"\n  Hybrid clusters: {hybrid_clusters}")
    print(f"  Parent clusters: {parent_clusters}")
    print(f"  New clusters (hybrids only): {new_cluster_only_hybrids}")
    
    # Final decision
    print("\n" + "=" * 70)
    print("DECISION")
    print("=" * 70)
    
    if new_cluster_only_hybrids:
        print("\n  RESULT: MODULAR INDEPENDENCE EXISTS")
        print("  Hybrids form new stable behavioral clusters not occupied by parents.")
        print("  This suggests separable algorithmic subspaces.")
    elif avg_between > 2 * avg_within:
        print("\n  RESULT: PARTIAL MODULAR INDEPENDENCE")
        print("  Clusters exist but hybrids don't form entirely new clusters.")
        print("  Some compositional structure may exist.")
    else:
        print("\n  RESULT: HARD COUPLING (SINGLE LATENT GENERATOR)")
        print("  All solvers and hybrids collapse to similar behavioral clusters.")
        print("  No evidence of separable algorithmic subspaces.")
        print("  Apparent modules are projections of a single latent control process.")
    
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
  The CSDT-1 test falsifies decomposability if:
  - Hybrids collapse to one parent's behavior (hard coupling)
  - Or hybrids behave inconsistently (uncontrolled interference)

  The test supports modular independence if:
  - Hybrids form new stable behavioral clusters

  Given rank=1 from the effective rank audit, the prior expectation is
  hard coupling. The empirical result will confirm or falsify this.
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
