"""LC743 Network Delay Time — oracle (Dijkstra shortest paths).

Correct implementation: Dijkstra's algorithm from source k.
Returns max shortest distance to all reachable nodes.
Returns -1 if any node in {1..n} is unreachable from k.
"""
from __future__ import annotations

import heapq
from collections import defaultdict


class OracleDomainError(Exception):
    """Raised when input is not in the LC743 domain."""


def lc743_oracle(
    times: list[list[int]],
    n: int,
    k: int,
) -> int:
    """Return the minimum time for all n nodes to receive the signal from k.

    Uses Dijkstra's algorithm. Returns -1 if any node is unreachable.

    Args:
        times: List of [u, v, w] directed edges with weight w.
        n: Number of nodes (labeled 1 to n).
        k: Source node.

    Returns:
        Maximum shortest distance from k to any reachable node, or -1.
    """
    if n < 1:
        raise OracleDomainError(f"n must be >= 1, got {n}")
    if k < 1 or k > n:
        raise OracleDomainError(f"k must be in [1, n], got k={k}, n={n}")

    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        if u < 1 or u > n or v < 1 or v > n:
            raise OracleDomainError(f"node out of range: u={u}, v={v}, n={n}")
        if w < 0:
            raise OracleDomainError(f"negative weight: {w}")
        graph[u].append((v, w))

    INF = float("inf")
    dist: dict[int, float] = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap: list[tuple[float, int]] = [(0, k)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
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


# Canonical test suite — 24 cases covering all four failure directions
CANONICAL_TEST_SUITE: list[dict] = [
    # === F1: UNDER_PROPAGATION (6 cases) ===
    # s001 fails on these: returns -1 on connected graphs
    {
        "times": [[1, 2, 1], [2, 3, 1]],
        "n": 3,
        "k": 1,
        "expected": 2,
        "label": "f1_chain_3",
        "note": "F1: s001 returns -1 (bug: returns -1 on connected)",
    },
    {
        "times": [[1, 2, 5], [2, 3, 3], [3, 4, 2]],
        "n": 4,
        "k": 1,
        "expected": 10,
        "label": "f1_chain_4_weighted",
        "note": "F1: s001 returns -1 (bug: returns -1 on connected)",
    },
    # s002 fails on these: only explores direct neighbors
    {
        "times": [[1, 2, 1], [2, 3, 1], [3, 4, 1]],
        "n": 4,
        "k": 1,
        "expected": 3,
        "label": "f2_multihop_4",
        "note": "F1: s002 returns 1 (bug: only direct neighbors)",
    },
    {
        "times": [[1, 2, 2], [2, 3, 3], [3, 4, 4], [4, 5, 5]],
        "n": 5,
        "k": 1,
        "expected": 14,
        "label": "f2_multihop_5",
        "note": "F1: s002 returns 2 (bug: only direct neighbors)",
    },
    # s003 fails on these: returns n-1 instead of max distance
    {
        "times": [[1, 2, 10], [2, 3, 10]],
        "n": 3,
        "k": 1,
        "expected": 20,
        "label": "f3_hop_count_bug",
        "note": "F1: s003 returns 2 (bug: returns n-1)",
    },
    # s004 fails on these: skips edges with weight > 50
    {
        "times": [[1, 2, 60]],
        "n": 2,
        "k": 1,
        "expected": 60,
        "label": "f4_high_weight",
        "note": "F1: s004 returns -1 (bug: skips weight>50)",
    },
    # === F2: OVER_COST_BIAS (6 cases) ===
    # s006 fails on these: initializes all distances to 0
    {
        "times": [[1, 2, 5], [2, 3, 3]],
        "n": 3,
        "k": 1,
        "expected": 8,
        "label": "f2_init_zero",
        "note": "F2: s006 returns 0 (bug: init all to 0)",
    },
    # s007 fails on these: doubles edge weights
    {
        "times": [[1, 2, 5], [2, 3, 3]],
        "n": 3,
        "k": 1,
        "expected": 8,
        "label": "f2_double_weights",
        "note": "F2: s007 returns 16 (bug: 2x weights)",
    },
    # s008 fails on these: adds +1 to every edge weight
    {
        "times": [[1, 2, 1], [2, 3, 1]],
        "n": 3,
        "k": 1,
        "expected": 2,
        "label": "f2_add_one",
        "note": "F2: s008 returns 4 (bug: +1 per edge)",
    },
    # s010 fails on these: source distance = 1
    {
        "times": [[1, 2, 5]],
        "n": 2,
        "k": 1,
        "expected": 5,
        "label": "f2_source_offset",
        "note": "F2: s010 returns 6 (bug: source=1)",
    },
    # s011 fails on these: reverses edge directions
    {
        "times": [[1, 2, 1], [2, 3, 10]],
        "n": 3,
        "k": 1,
        "expected": 11,
        "label": "f2_reverse_edges",
        "note": "F2: s011 returns 10 (bug: reversed edges)",
    },
    # s013 fails on these: returns sum of all weights
    {
        "times": [[1, 2, 5], [2, 3, 3]],
        "n": 3,
        "k": 1,
        "expected": 8,
        "label": "f2_sum_weights",
        "note": "F2: s013 returns 8 (bug: sum of weights = 8, happens to match!)",
    },
    # === F3: PRIORITY_ORDER_FAILURE (6 cases) ===
    # s016 fails on these: BFS on weighted graph
    {
        "times": [[1, 2, 10], [2, 3, 10]],
        "n": 3,
        "k": 1,
        "expected": 20,
        "label": "f3_bfs_weighted",
        "note": "F3: s016 returns 2 (bug: BFS ignores weights)",
    },
    # s017 fails on these: max-heap
    {
        "times": [[1, 2, 1], [1, 3, 5], [3, 4, 1]],
        "n": 4,
        "k": 1,
        "expected": 6,
        "label": "f3_max_heap",
        "note": "F3: s017 returns wrong (bug: max-heap)",
    },
    # s018 fails on these: reverse ID order
    {
        "times": [[1, 2, 1], [2, 3, 10], [3, 4, 1]],
        "n": 4,
        "k": 1,
        "expected": 12,
        "label": "f3_reverse_id",
        "note": "F3: s018 returns wrong (bug: reverse ID order)",
    },
    # s019 fails on these: single-pass edge list
    {
        "times": [[3, 4, 1], [1, 2, 1], [2, 3, 1]],
        "n": 4,
        "k": 1,
        "expected": 3,
        "label": "f3_single_pass",
        "note": "F3: s019 returns wrong (bug: single pass)",
    },
    # s021 fails on these: Bellman-Ford N-2 iterations
    {
        "times": [[1, 2, 1], [2, 3, 1], [3, 4, 1], [4, 5, 1]],
        "n": 5,
        "k": 1,
        "expected": 4,
        "label": "f3_bf_few_iters",
        "note": "F3: s021 returns wrong (bug: N-2 iters)",
    },
    # s023 fails on these: only odd-ID nodes
    {
        "times": [[1, 2, 1], [2, 3, 10], [3, 4, 1]],
        "n": 4,
        "k": 1,
        "expected": 12,
        "label": "f3_odd_nodes",
        "note": "F3: s023 returns wrong (bug: odd-only skips node 2)",
    },
    # === F4: DISCONNECTED_MISHANDLING (6 cases) ===
    # s027 fails on these: returns max reachable instead of -1
    {
        "times": [[1, 2, 1]],
        "n": 3,
        "k": 1,
        "expected": -1,
        "label": "f4_max_reachable",
        "note": "F4: s027 returns 1 (bug: no -1 check)",
    },
    # s028 fails on these: initializes unreachable to 0
    {
        "times": [[1, 2, 5]],
        "n": 3,
        "k": 1,
        "expected": -1,
        "label": "f4_init_zero_unreachable",
        "note": "F4: s028 returns 5 (bug: unreachable=0)",
    },
    # s029 fails on these: returns visited count
    {
        "times": [[1, 2, 1], [2, 3, 1]],
        "n": 5,
        "k": 1,
        "expected": -1,
        "label": "f4_visited_count",
        "note": "F4: s029 returns 3 (bug: returns count)",
    },
    # s030 fails on these: returns 0 on disconnect
    {
        "times": [[1, 2, 10]],
        "n": 4,
        "k": 1,
        "expected": -1,
        "label": "f4_return_zero",
        "note": "F4: s030 returns 0 (bug: returns 0 on disconnect)",
    },
    # Additional F4 cases for coverage
    {
        "times": [],
        "n": 3,
        "k": 1,
        "expected": -1,
        "label": "f4_no_edges",
        "note": "F4: no edges, all unreachable",
    },
    {
        "times": [[2, 1, 1], [2, 3, 1]],
        "n": 4,
        "k": 2,
        "expected": -1,
        "label": "f4_partial_disconnect",
        "note": "F4: node 4 unreachable",
    },
]
