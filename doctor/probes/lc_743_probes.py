"""LC743 Network Delay Time — input-space probes (30 probes, 6 families).

Each probe is a pure function: probe(times, n, k) -> float.
No solver calls. No oracle calls. Probes are input features only.

Families:
  CONNECTIVITY_STRESS (c1-c5): reachability structure from k
  WEIGHT_MAGNITUDE_STRESS (w1-w5): edge weight values
  SOURCE_CENTRALITY_STRESS (s1-s5): structural position of k
  DENSITY_STRESS (d1-d5): edge count relative to node count
  PATH_MULTIPLICITY_STRESS (m1-m5): number of distinct shortest paths
  SCALE_STRESS (z1-z5): node count n
"""
from __future__ import annotations

import math
from collections import defaultdict, deque


# ============================================================================
# Helpers
# ============================================================================

def _build_graph(times):
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    return graph


def _bfs_reachable(graph, k, n):
    reachable = set()
    queue = deque([k])
    while queue:
        u = queue.popleft()
        if u in reachable:
            continue
        reachable.add(u)
        for v, _ in graph.get(u, []):
            if v not in reachable:
                queue.append(v)
    return reachable


def _dijkstra_all(graph, k, n):
    import heapq
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def _shortest_path_count(graph, k, n):
    """Count number of shortest paths from k to each node."""
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    count = {i: 0 for i in range(1, n + 1)}
    dist[k] = 0
    count[k] = 1
    import heapq
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                count[v] = count[u]
                heapq.heappush(heap, (nd, v))
            elif nd == dist[v]:
                count[v] += count[u]
    return dist, count


def _weakly_connected_components(times, n):
    """Count weakly connected components."""
    adj = defaultdict(list)
    for u, v, _ in times:
        adj[u].append(v)
        adj[v].append(u)
    visited = set()
    components = 0
    for node in range(1, n + 1):
        if node not in visited:
            components += 1
            queue = deque([node])
            while queue:
                u = queue.popleft()
                if u in visited:
                    continue
                visited.add(u)
                for v in adj.get(u, []):
                    if v not in visited:
                        queue.append(v)
    return components


# ============================================================================
# Family 1: CONNECTIVITY_STRESS
# ============================================================================

def c1(times, n, k):
    """Fraction of nodes reachable from k.

    Ranges from 0 (isolated source) to 1 (fully connected from k).
    Varies between connected and disconnected graphs.
    """
    graph = _build_graph(times)
    reachable = _bfs_reachable(graph, k, n)
    return len(reachable) / n


def c2(times, n, k):
    """Number of weakly connected components in the graph.

    Higher values indicate more fragmented graph structure.
    """
    return _weakly_connected_components(times, n)


def c3(times, n, k):
    """Out-degree of source node k.

    0 means isolated source (no outgoing edges).
    """
    graph = _build_graph(times)
    return len(graph.get(k, []))


def c4(times, n, k):
    """Number of bridge edges in the reachable subgraph from k.

    A bridge is an edge whose removal increases the number of unreachable
    nodes from k.
    """
    graph = _build_graph(times)
    reachable = _bfs_reachable(graph, k, n)
    bridges = 0
    for u in list(reachable):
        for v, w in graph.get(u, []):
            if v not in reachable:
                continue
            # Check if removing (u,v) disconnects anything
            test_graph = defaultdict(list)
            for u2, v2, w2 in times:
                if u2 == u and v2 == v:
                    continue
                test_graph[u2].append((v2, w2))
            test_reachable = _bfs_reachable(test_graph, k, n)
            if len(test_reachable) < len(reachable):
                bridges += 1
    return bridges


def c5(times, n, k):
    """Diameter of the reachable subgraph from k.

    Longest shortest path from k to any reachable node.
    Tests boundary between long paths and unreachable nodes.
    """
    graph = _build_graph(times)
    dist = _dijkstra_all(graph, k, n)
    max_d = 0
    for node in range(1, n + 1):
        if dist[node] < float("inf") and dist[node] > max_d:
            max_d = dist[node]
    return max_d


# ============================================================================
# Family 2: WEIGHT_MAGNITUDE_STRESS
# ============================================================================

def w1(times, n, k):
    """Mean edge weight."""
    if not times:
        return 0
    return sum(w for _, _, w in times) / len(times)


def w2(times, n, k):
    """Max edge weight."""
    if not times:
        return 0
    return max(w for _, _, w in times)


def w3(times, n, k):
    """Min edge weight."""
    if not times:
        return 0
    return min(w for _, _, w in times)


def w4(times, n, k):
    """Weight standard deviation."""
    if len(times) < 2:
        return 0
    weights = [w for _, _, w in times]
    mean = sum(weights) / len(weights)
    variance = sum((w - mean) ** 2 for w in weights) / len(weights)
    return math.sqrt(variance)


def w5(times, n, k):
    """Max/min weight ratio.

    Returns 0 if no edges. Returns inf if min weight is 0.
    """
    if not times:
        return 0
    weights = [w for _, _, w in times]
    return max(weights) / min(weights) if min(weights) > 0 else float("inf")


# ============================================================================
# Family 3: SOURCE_CENTRALITY_STRESS
# ============================================================================

def s1(times, n, k):
    """Fraction of nodes reachable from k in 1 hop.

    Higher values mean k is more central (hub-like).
    """
    graph = _build_graph(times)
    neighbors = set(v for v, _ in graph.get(k, []))
    return len(neighbors) / (n - 1) if n > 1 else 0


def s2(times, n, k):
    """Average distance from k to reachable nodes.

    Lower values mean k is closer to all nodes on average.
    """
    graph = _build_graph(times)
    dist = _dijkstra_all(graph, k, n)
    reachable_dists = [dist[node] for node in range(1, n + 1) if dist[node] < float("inf") and node != k]
    if not reachable_dists:
        return 0
    return sum(reachable_dists) / len(reachable_dists)


def s3(times, n, k):
    """Number of nodes at distance > n/2 from k.

    Tests whether k is peripheral (many distant nodes) vs central (few).
    """
    graph = _build_graph(times)
    dist = _dijkstra_all(graph, k, n)
    threshold = n / 2
    distant = 0
    for node in range(1, n + 1):
        if dist[node] < float("inf") and dist[node] > threshold:
            distant += 1
    return distant


def s4(times, n, k):
    """Number of nodes reachable from k in exactly 2 hops.

    Tests two-hop propagation from k.
    """
    graph = _build_graph(times)
    hop1 = set(v for v, _ in graph.get(k, []))
    hop2 = set()
    for v in hop1:
        for w, _ in graph.get(v, []):
            if w != k and w not in hop1:
                hop2.add(w)
    return len(hop2)


def s5(times, n, k):
    """Number of nodes reachable from k in exactly 3 hops.

    Tests three-hop propagation from k.
    """
    graph = _build_graph(times)
    hop1 = set(v for v, _ in graph.get(k, []))
    hop2 = set()
    for v in hop1:
        for w, _ in graph.get(v, []):
            if w != k and w not in hop1:
                hop2.add(w)
    hop3 = set()
    for v in hop2:
        for w, _ in graph.get(v, []):
            if w != k and w not in hop1 and w not in hop2:
                hop3.add(w)
    return len(hop3)


# ============================================================================
# Family 4: DENSITY_STRESS
# ============================================================================

def d1(times, n, k):
    """Edge count / (n * (n-1)) — density ratio.

    0 for empty graph, 1 for complete directed graph.
    """
    if n <= 1:
        return 0
    return len(times) / (n * (n - 1))


def d2(times, n, k):
    """Standard deviation of out-degrees.

    Measures degree heterogeneity. 0 for regular graphs.
    """
    if n <= 1:
        return 0
    out_degrees = [0] * (n + 1)
    for u, v, w in times:
        out_degrees[u] += 1
    degrees = out_degrees[1:]
    mean = sum(degrees) / n
    variance = sum((d - mean) ** 2 for d in degrees) / n
    return math.sqrt(variance)


def d3(times, n, k):
    """Average out-degree."""
    if n <= 1:
        return 0
    return len(times) / n


def d4(times, n, k):
    """Fraction of nodes with out-degree > 0."""
    if n <= 1:
        return 0
    has_out = set(u for u, v, w in times)
    return len(has_out) / n


def d5(times, n, k):
    """Max out-degree."""
    if n <= 1:
        return 0
    out_degrees = [0] * (n + 1)
    for u, v, w in times:
        out_degrees[u] += 1
    return max(out_degrees[1:]) if n >= 1 else 0


# ============================================================================
# Family 5: PATH_MULTIPLICITY_STRESS
# ============================================================================

def m1(times, n, k):
    """Number of distinct shortest paths from k to the farthest node.

    Higher values indicate more path ambiguity.
    """
    graph = _build_graph(times)
    dist, count = _shortest_path_count(graph, k, n)
    max_dist = 0
    farthest_count = 0
    for node in range(1, n + 1):
        if dist[node] < float("inf") and dist[node] > max_dist:
            max_dist = dist[node]
            farthest_count = count[node]
    return farthest_count


def m2(times, n, k):
    """Number of nodes with multiple shortest paths from k.

    Tests path multiplicity across the graph.
    """
    graph = _build_graph(times)
    dist, count = _shortest_path_count(graph, k, n)
    multi = 0
    for node in range(1, n + 1):
        if count[node] > 1:
            multi += 1
    return multi


def m3(times, n, k):
    """Average number of shortest paths per reachable node.

    Measures overall path multiplicity.
    """
    graph = _build_graph(times)
    dist, count = _shortest_path_count(graph, k, n)
    reachable_counts = [count[node] for node in range(1, n + 1) if dist[node] < float("inf") and node != k]
    if not reachable_counts:
        return 0
    return sum(reachable_counts) / len(reachable_counts)


def m4(times, n, k):
    """Fraction of edges that lie on shortest path trees.

    Higher values mean more edges are on critical paths.
    """
    graph = _build_graph(times)
    dist = _dijkstra_all(graph, k, n)
    on_tree = 0
    for u, v, w in times:
        if dist[u] < float("inf") and dist[u] + w == dist[v]:
            on_tree += 1
    return on_tree / len(times) if times else 0


def m5(times, n, k):
    """Number of parallel edges (multiple edges between same node pair).

    Tests edge multiplicity structure.
    """
    edge_counts = defaultdict(int)
    for u, v, w in times:
        edge_counts[(u, v)] += 1
    parallel = sum(1 for count in edge_counts.values() if count > 1)
    return parallel


# ============================================================================
# Family 6: SCALE_STRESS
# ============================================================================

def z1(times, n, k):
    """Node count n."""
    return n


def z2(times, n, k):
    """log(n) — logarithmic scale."""
    return math.log(n) if n > 0 else 0


def z3(times, n, k):
    """Edge count."""
    return len(times)


def z4(times, n, k):
    """Edge count / log(n) — scale-normalized density.

    Returns 0 if n <= 1.
    """
    return len(times) / math.log(n) if n > 1 else 0


def z5(times, n, k):
    """n * (n-1) — maximum possible edges."""
    return n * (n - 1)


# ============================================================================
# Probe registry
# ============================================================================

PROBE_REGISTRY = {
    # Family 1: CONNECTIVITY_STRESS
    "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5,
    # Family 2: WEIGHT_MAGNITUDE_STRESS
    "w1": w1, "w2": w2, "w3": w3, "w4": w4, "w5": w5,
    # Family 3: SOURCE_CENTRALITY_STRESS
    "s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5,
    # Family 4: DENSITY_STRESS
    "d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5,
    # Family 5: PATH_MULTIPLICITY_STRESS
    "m1": m1, "m2": m2, "m3": m3, "m4": m4, "m5": m5,
    # Family 6: SCALE_STRESS
    "z1": z1, "z2": z2, "z3": z3, "z4": z4, "z5": z5,
}

PROBE_FAMILIES = {
    "CONNECTIVITY_STRESS": ["c1", "c2", "c3", "c4", "c5"],
    "WEIGHT_MAGNITUDE_STRESS": ["w1", "w2", "w3", "w4", "w5"],
    "SOURCE_CENTRALITY_STRESS": ["s1", "s2", "s3", "s4", "s5"],
    "DENSITY_STRESS": ["d1", "d2", "d3", "d4", "d5"],
    "PATH_MULTIPLICITY_STRESS": ["m1", "m2", "m3", "m4", "m5"],
    "SCALE_STRESS": ["z1", "z2", "z3", "z4", "z5"],
}
