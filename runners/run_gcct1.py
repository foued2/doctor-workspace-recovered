"""GCCT-1: Graph Construction Causality Test

Determines whether graph construction has any causal effect on reachable
state space, given fixed relaxation dynamics.

Experimental design:
- Keep relaxation logic fixed (Dijkstra-like)
- Vary only graph construction under representational invariance classes
- Measure: state visitation, attractor stability, trajectory divergence

Decision rule:
- Case 1: Complete invariance → causally inert (A)
- Case 2: Trajectory divergence but same final cluster → constrained encoder (B)
- Case 3: New clusters emerge → second-order operator (violates minimal model)
"""
from __future__ import annotations

import heapq
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

import numpy as np

# --- CONFIG ---
TIMEOUT_SECONDS = 2


class TimeoutError(Exception):
    pass


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


# --- GRAPH ENCODING INTERFACES ---


class GraphEncoding(ABC):
    """Abstract base class for graph encodings."""

    @abstractmethod
    def build(self, edges: list[tuple[int, int, int]], n: int) -> None:
        """Build graph from edge list."""
        pass

    @abstractmethod
    def neighbors(self, u: int) -> list[tuple[int, int]]:
        """Return list of (neighbor, weight) pairs."""
        pass

    @abstractmethod
    def get_encoding_name(self) -> str:
        pass


class AdjacencyList(GraphEncoding):
    """Standard adjacency list (dict of lists)."""

    def __init__(self):
        self.graph: dict[int, list[tuple[int, int]]] = defaultdict(list)

    def build(self, edges, n):
        self.graph = defaultdict(list)
        for u, v, w in edges:
            self.graph[u].append((v, w))

    def neighbors(self, u):
        return self.graph[u]

    def get_encoding_name(self):
        return "adjacency_list"


class AdjacencyMatrix(GraphEncoding):
    """Dense adjacency matrix."""

    def __init__(self):
        self.matrix: list[list[int]] = []
        self.n = 0

    def build(self, edges, n):
        self.n = n
        self.matrix = [[0] * (n + 1) for _ in range(n + 1)]
        for u, v, w in edges:
            self.matrix[u][v] = w

    def neighbors(self, u):
        result = []
        for v in range(1, self.n + 1):
            if self.matrix[u][v] > 0:
                result.append((v, self.matrix[u][v]))
        return result

    def get_encoding_name(self):
        return "adjacency_matrix"


class EdgeList(GraphEncoding):
    """Explicit edge list (filtered at query time)."""

    def __init__(self):
        self.edges: list[tuple[int, int, int]] = []

    def build(self, edges, n):
        self.edges = edges

    def neighbors(self, u):
        return [(v, w) for src, v, w in self.edges if src == u]

    def get_encoding_name(self):
        return "edge_list"


class CSRGraph(GraphEncoding):
    """Compressed Sparse Row (CSR) style."""

    def __init__(self):
        self.row_ptr: list[int] = []
        self.col_idx: list[int] = []
        self.weights: list[int] = []

    def build(self, edges, n):
        # Group edges by source
        edge_dict = defaultdict(list)
        for u, v, w in edges:
            edge_dict[u].append((v, w))

        # Build CSR arrays
        self.row_ptr = [0] * (n + 2)
        self.col_idx = []
        self.weights = []

        offset = 0
        for u in range(1, n + 1):
            self.row_ptr[u] = offset
            for v, w in sorted(edge_dict[u]):
                self.col_idx.append(v)
                self.weights.append(w)
                offset += 1
        self.row_ptr[n + 1] = offset

    def neighbors(self, u):
        start = self.row_ptr[u]
        end = self.row_ptr[u + 1]
        return [(self.col_idx[i], self.weights[i]) for i in range(start, end)]

    def get_encoding_name(self):
        return "csr"


class ImplicitGraph(GraphEncoding):
    """Implicit graph (lazy neighbor generation via function)."""

    def __init__(self):
        self.edge_set: set[tuple[int, int, int]] = set()

    def build(self, edges, n):
        self.edge_set = set(edges)

    def neighbors(self, u):
        return [(v, w) for src, v, w in self.edge_set if src == u]

    def get_encoding_name(self):
        return "implicit"


# --- FIXED RELAXATION LOGIC ---


def dijkstra_relaxation(
    graph: GraphEncoding,
    n: int,
    k: int,
    weight_transform: callable = lambda w: w,
) -> tuple[dict[int, float], list[tuple[int, int]], int]:
    """Fixed Dijkstra relaxation with configurable weight transform.

    Returns:
        dist: distance dictionary
        visitation_order: list of (node, distance) in visit order
        node_count: number of nodes processed
    """
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    visitation_order = []
    node_count = 0

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue

        visitation_order.append((u, d))
        node_count += 1

        for v, w in graph.neighbors(u):
            nd = d + weight_transform(w)
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist, visitation_order, node_count


def compute_max_distance(dist: dict[int, float], n: int) -> int:
    """Compute max distance from distance dict."""
    INF = float("inf")
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


# --- PROBE GENERATION ---


def generate_probes(seed=42, n_probes=20):
    """Generate identical micro-probe set."""
    rng = np.random.RandomState(seed)
    probes = []

    for i in range(n_probes):
        n = rng.randint(3, 8)
        k = rng.randint(1, n)
        n_edges = rng.randint(n - 1, min(n * (n - 1), 15))

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

        for node in range(1, n + 1):
            if node not in reachable:
                edges.add((k, node, rng.randint(1, 10)))
                reachable.add(node)

        times = list(edges)
        probes.append((times, n, k))

    return probes


# --- BEHAVIORAL ANALYSIS ---


def compute_behavioral_signature(encoding_class, probes):
    """Compute behavioral signature for a graph encoding."""
    signature = []
    trajectories = []

    for times, n, k in probes:
        try:
            graph = encoding_class()
            graph.build(times, n)
            dist, visit_order, node_count = run_with_timeout(
                dijkstra_relaxation, (graph, n, k)
            )
            result = compute_max_distance(dist, n)
            signature.append(result)
            trajectories.append(visit_order)
        except (TimeoutError, Exception) as e:
            signature.append(None)
            trajectories.append(None)

    return signature, trajectories


def compute_pairwise_distance(sig1, sig2):
    """Compute Hamming distance between signatures."""
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


def compute_trajectory_divergence(traj1, traj2):
    """Compute normalized edit distance between trajectories."""
    if traj1 is None or traj2 is None:
        return 1.0

    if len(traj1) == 0 and len(traj2) == 0:
        return 0.0

    if len(traj1) == 0 or len(traj2) == 0:
        return 1.0

    # Extract node sequences
    nodes1 = [u for u, d in traj1]
    nodes2 = [u for u, d in traj2]

    # Compute longest common subsequence
    m, n = len(nodes1), len(nodes2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if nodes1[i - 1] == nodes2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_len = dp[m][n]
    max_len = max(m, n)

    if max_len == 0:
        return 0.0

    return 1.0 - (lcs_len / max_len)


def compute_state_visitation_overlap(traj1, traj2):
    """Compute overlap of visited state sets."""
    if traj1 is None or traj2 is None:
        return 0.0

    states1 = set(u for u, d in traj1)
    states2 = set(u for u, d in traj2)

    if len(states1) == 0 and len(states2) == 0:
        return 1.0

    if len(states1) == 0 or len(states2) == 0:
        return 0.0

    intersection = len(states1 & states2)
    union = len(states1 | states2)

    return intersection / union if union > 0 else 0.0


# --- MAIN ---


def main():
    print("=" * 70)
    print("GCCT-1: Graph Construction Causality Test")
    print("=" * 70)

    # Step 1: Generate probes
    print("\n[1/6] Generating identical micro-probe set...")
    probes = generate_probes(seed=42, n_probes=20)
    print(f"  Generated {len(probes)} probes")

    # Step 2: Define encoding variants
    print("\n[2/6] Defining graph encoding variants...")
    encoding_classes = [
        AdjacencyList,
        AdjacencyMatrix,
        EdgeList,
        CSRGraph,
        ImplicitGraph,
    ]
    encoding_names = [cls().get_encoding_name() for cls in encoding_classes]
    print(f"  Encodings: {encoding_names}")

    # Step 3: Compute behavioral signatures
    print("\n[3/6] Computing behavioral signatures...")
    signatures = {}
    trajectories = {}

    for cls in encoding_classes:
        name = cls().get_encoding_name()
        sig, traj = compute_behavioral_signature(cls, probes)
        signatures[name] = sig
        trajectories[name] = traj
        valid = sum(1 for r in sig if r is not None)
        print(f"  {name}: {valid}/{len(probes)} valid results")

    # Step 4: Compute pairwise distances
    print("\n[4/6] Computing pairwise distances...")
    n_enc = len(encoding_names)

    # Output distance
    output_dist = np.zeros((n_enc, n_enc))
    for i in range(n_enc):
        for j in range(i + 1, n_enc):
            d = compute_pairwise_distance(
                signatures[encoding_names[i]], signatures[encoding_names[j]]
            )
            output_dist[i, j] = d
            output_dist[j, i] = d

    print("\n  Output distance matrix (Hamming):")
    print("  " + " " * 12 + " ".join(f"{name:>10}" for name in encoding_names))
    for i, name in enumerate(encoding_names):
        row = " ".join(f"{output_dist[i, j]:10.4f}" for j in range(n_enc))
        print(f"  {name:>12} {row}")

    # Trajectory divergence (average across probes)
    print("\n  Average trajectory divergence (LCS-based):")
    traj_div = np.zeros((n_enc, n_enc))
    for i in range(n_enc):
        for j in range(i + 1, n_enc):
            divs = []
            for p in range(len(probes)):
                t1 = trajectories[encoding_names[i]][p]
                t2 = trajectories[encoding_names[j]][p]
                divs.append(compute_trajectory_divergence(t1, t2))
            traj_div[i, j] = np.mean(divs)
            traj_div[j, i] = traj_div[i, j]

    print("  " + " " * 12 + " ".join(f"{name:>10}" for name in encoding_names))
    for i, name in enumerate(encoding_names):
        row = " ".join(f"{traj_div[i, j]:10.4f}" for j in range(n_enc))
        print(f"  {name:>12} {row}")

    # State visitation overlap (average across probes)
    print("\n  Average state visitation overlap (Jaccard):")
    state_overlap = np.zeros((n_enc, n_enc))
    for i in range(n_enc):
        for j in range(i + 1, n_enc):
            overlaps = []
            for p in range(len(probes)):
                t1 = trajectories[encoding_names[i]][p]
                t2 = trajectories[encoding_names[j]][p]
                overlaps.append(compute_state_visitation_overlap(t1, t2))
            state_overlap[i, j] = np.mean(overlaps)
            state_overlap[j, i] = state_overlap[i, j]

    print("  " + " " * 12 + " ".join(f"{name:>10}" for name in encoding_names))
    for i, name in enumerate(encoding_names):
        row = " ".join(f"{state_overlap[i, j]:10.4f}" for j in range(n_enc))
        print(f"  {name:>12} {row}")

    # Step 5: Cluster analysis
    print("\n[5/6] Cluster analysis...")

    # Cluster based on output signatures
    names = encoding_names
    n = len(names)
    dist_matrix = output_dist.copy()

    # Simple agglomerative clustering
    clusters = [[i] for i in range(n)]
    while len(clusters) > 1:
        min_dist = float("inf")
        min_i, min_j = 0, 1

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                for ci in clusters[i]:
                    for cj in clusters[j]:
                        if dist_matrix[ci, cj] < min_dist:
                            min_dist = dist_matrix[ci, cj]
                            min_i, min_j = i, j

        if min_dist > 0.3:
            break

        clusters[min_i] = clusters[min_i] + clusters[min_j]
        clusters.pop(min_j)

    print(f"\n  Clusters formed (threshold=0.3):")
    for i, cluster in enumerate(clusters):
        member_names = [names[idx] for idx in cluster]
        print(f"    Cluster {i+1}: {member_names}")

    # Step 6: Decision rule
    print("\n[6/6] Decision rule application...")

    # Compute within-cluster vs between-cluster metrics
    within_output = []
    between_output = []
    within_traj = []
    between_traj = []

    for cluster in clusters:
        for i in cluster:
            for j in cluster:
                if i < j:
                    within_output.append(output_dist[i, j])
                    within_traj.append(traj_div[i, j])

    for i in range(n):
        for j in range(i + 1, n):
            ci = next(idx for idx, cluster in enumerate(clusters) if i in cluster)
            cj = next(idx for idx, cluster in enumerate(clusters) if j in cluster)
            if ci != cj:
                between_output.append(output_dist[i, j])
                between_traj.append(traj_div[i, j])

    avg_within_output = np.mean(within_output) if within_output else 0
    avg_between_output = np.mean(between_output) if between_output else 0
    avg_within_traj = np.mean(within_traj) if within_traj else 0
    avg_between_traj = np.mean(between_traj) if between_traj else 0

    print(f"\n  Average within-cluster output distance: {avg_within_output:.4f}")
    print(f"  Average between-cluster output distance: {avg_between_output:.4f}")
    print(f"  Average within-cluster trajectory divergence: {avg_within_traj:.4f}")
    print(f"  Average between-cluster trajectory divergence: {avg_between_traj:.4f}")

    # Final decision
    print("\n" + "=" * 70)
    print("DECISION")
    print("=" * 70)

    # Check for complete invariance (Case 1)
    if avg_within_output < 0.01 and avg_between_output < 0.01:
        print("\n  CASE 1: COMPLETE INVARIANCE")
        print("  Graph construction is CAUSALLY INERT (A)")
        print("  All encodings produce identical behavioral signatures.")
        print("  Graph construction has no causal effect on output.")
        print("  Implication: graph construction is a pure no-op in the system.")

    # Check for constrained encoder (Case 2)
    elif avg_within_output < 0.1 and avg_within_traj > 0.1:
        print("\n  CASE 2: TRAJECTORY DIVERGENCE, SAME FINAL CLUSTER")
        print("  Graph construction is CONSTRAINED ENCODER (B)")
        print("  Intermediate states differ but final behavior is identical.")
        print("  Graph construction affects state traversal but not output basin.")
        print("  Implication: graph construction is a coordinate transformation.")

    # Check for second-order operator (Case 3)
    elif len(clusters) > 1:
        print("\n  CASE 3: NEW CLUSTERS EMERGE")
        print("  Graph construction is SECOND-ORDER OPERATOR")
        print("  Different encodings shift attractor basin membership.")
        print("  This violates the current minimal model.")
        print("  Implication: graph construction has independent control authority.")

    # Edge case: trajectory divergence with output divergence
    elif avg_within_output > 0.1:
        print("\n  MIXED CASE: OUTPUT DIVERGENCE WITHIN CLUSTERS")
        print("  Graph construction has partial causal effect.")
        print("  Both trajectory and output are affected.")
        print("  Implication: graph construction is a weak control surface.")

    else:
        print("\n  INCONCLUSIVE")
        print("  Metrics do not clearly separate Cases 1/2/3.")

    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
  The GCCT-1 test distinguishes three cases:

  Case 1 (causally inert):
    Graph construction has no effect on state space or output.
    The system treats it as a pure encoding step.
    All computational work happens in relaxation.

  Case 2 (constrained encoder):
    Graph construction affects which states are visited
    (trajectory divergence) but not which attractor basin
    the system converges to (same final cluster).
    The system uses graph construction as a state-space
    preconditioner, not an independent operator.

  Case 3 (second-order operator):
    Graph construction shifts attractor basin membership.
    Different encodings produce different behavioral clusters.
    This would mean graph construction has independent
    control authority over system dynamics.

  Given rank=1 and CSDT-1 results, the prior expectation
  is Case 1 or Case 2. Case 3 would require revising the
  minimal model.
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
