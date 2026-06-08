"""LC743 Network Delay Time — solver population (30 solvers).

Distribution (declared prior):
  F1 UNDER_PROPAGATION: 5 solvers (s001-s005)
  F2 OVER_COST_BIAS: 10 solvers (s006-s015)
  F3 PRIORITY_ORDER_FAILURE: 11 solvers (s016-s026)
  F4 DISCONNECTED_MISHANDLING: 4 solvers (s027-s030)

Each solver has a docstring naming its primary failure direction and
specific mechanism. No two solvers are identical up to variable rename.
"""
from __future__ import annotations

import heapq
import math
import random
from collections import defaultdict, deque


# ============================================================================
# F1: UNDER_PROPAGATION (5 solvers)
# ============================================================================


def s001(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — checks reachability but returns -1 even when connected.

    Bug: the reachability check uses a set-based BFS that incorrectly
    concludes the graph is disconnected due to a logic error in the
    visited-set update. Returns -1 on connected graphs where all nodes
    are reachable.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    # Bug: builds reverse graph for reachability check
    rev_graph: dict[int, list[int]] = defaultdict(list)
    for u, v, w in times:
        rev_graph[v].append(u)
    reachable = set()
    queue = deque([k])
    while queue:
        u = queue.popleft()
        if u in reachable:
            continue
        reachable.add(u)
        for v in rev_graph[u]:  # Bug: uses reverse graph
            if v not in reachable:
                queue.append(v)
    if len(reachable) < n:
        return -1
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
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


def s002(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — only explores direct neighbors of source.

    Bug: only relaxes edges from the source node, never processes edges
    from intermediate nodes. Returns the max weight among direct edges
    from k, missing all multi-hop paths.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    max_dist = 0
    reached = {k}
    for v, w in graph[k]:
        reached.add(v)
        if w > max_dist:
            max_dist = w
    if len(reached) < n:
        return -1
    return int(max_dist)


def s003(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — returns node count minus 1 instead of max distance.

    Bug: returns len(visited)-1 instead of max(dist). Undercounts on
    all graphs where distances > 1.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    visited = set()
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        visited.add(u)
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    if len(visited) < n:
        return -1
    return len(visited) - 1


def s004(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — skips edges with weight > 50.

    Bug: filters out edges with w > 50 before building the graph.
    Nodes only reachable via high-weight edges are missed.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        if w <= 50:
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


def s005(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — returns min distance instead of max.

    Bug: returns min(dist) instead of max(dist). Undercounts on all
    multi-node connected graphs.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    min_dist = INF
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] < min_dist:
            min_dist = dist[node]
    return int(min_dist)


# ============================================================================
# F2: OVER_COST_BIAS (10 solvers)
# ============================================================================


def s006(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — initializes all distances to 0 instead of INF.

    Bug: dist[v]=0 for all v. Relaxation never fires (0+w > 0 always).
    Returns max of all-zero distances = 0.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {i: 0 for i in range(1, n + 1)}
    heap = [(0, k)]
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
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s007(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — doubles every edge weight.

    Bug: uses 2*w instead of w. Returns 2x correct answer.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + 2 * w
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


def s008(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — adds +1 to every edge weight.

    Bug: uses w+1 instead of w. Returns correct + number_of_hops.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w + 1
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


def s009(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — squares edge weights.

    Bug: uses w*w instead of w. Overcounts significantly.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w * w
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


def s010(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — initializes source distance to 1.

    Bug: dist[k]=1 instead of 0. All distances off by +1.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 1
    heap = [(1, k)]
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


def s011(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — relaxes edges in reverse direction.

    Bug: builds reverse graph (v->u instead of u->v). Returns distances
    in the reversed graph.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[v].append((u, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
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


def s012(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — uses ceil(w/2) instead of w.

    Bug: uses math.ceil(w/2). Overcounts when weights are odd.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + math.ceil(w / 2)
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


def s013(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — returns sum of all edge weights.

    Bug: returns sum(w for all edges) instead of max(dist). Overcounts
    by including edges not on the critical path.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
    total = sum(w for _, _, w in times)
    return int(total)


def s014(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — uses max(a,b) instead of min(a,b) in relaxation.

    Bug: relaxation takes max instead of min. Returns longest path distance.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd > dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s015(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — returns sum of all distances from source.

    Bug: returns sum(dist[node] for all nodes) instead of max(dist).
    Overcounts by summing all distances instead of returning the max.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    total = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        total += dist[node]
    return int(total)


# ============================================================================
# F3: PRIORITY_ORDER_FAILURE (11 solvers)
# ============================================================================


def s016(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — BFS on weighted graph (ignores weights).

    Bug: uses queue (FIFO) instead of heap. Treats all edges as unit weight.
    Returns min hop count instead of shortest weighted path.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    queue = [k]
    while queue:
        u = queue.pop(0)
        for v, w in graph[u]:
            if dist[v] == INF:
                dist[v] = dist[u] + 1
                queue.append(v)
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s017(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — Dijkstra skipping even-weight edges.

    Bug: skips edges with even weight during relaxation. Nodes only
    reachable via even-weight edges are missed or have wrong distances.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            # Bug: skip even-weight edges
            if w % 2 == 0:
                continue
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


def s018(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — processes nodes in reverse ID order.

    Bug: sorts nodes by reverse ID and processes in that order. Fails
    when node IDs don't match distance order.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    for u in sorted(range(1, n + 1), reverse=True):
        if dist[u] == INF:
            continue
        for v, w in graph[u]:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s019(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — single-pass edge list iteration.

    Bug: iterates through edge list once. May not converge if edges
    are not in topological order.
    """
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    for u, v, w in times:
        if dist[u] != INF:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s020(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — Dijkstra skipping heavy edges.

    Bug: skips edges with weight > 3 during relaxation. Nodes only
    reachable via heavy edges are missed or have wrong distances.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            # Bug: skip edges with weight > 3
            if w > 3:
                continue
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


def s021(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — Bellman-Ford with N-2 iterations.

    Bug: runs N-2 iterations instead of N-1. May not converge for graphs
    where the longest shortest path has N-1 edges.
    """
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    for _ in range(n - 2):
        for u, v, w in times:
            if dist[u] != INF:
                nd = dist[u] + w
                if nd < dist[v]:
                    dist[v] = nd
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s022(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — Bellman-Ford skipping forward edges.

    Bug: only relaxes edges where destination ID < source ID. Skips all
    forward edges (u < v). Fails on graphs with forward-only paths.
    """
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    for _ in range(n - 1):
        for u, v, w in times:
            # Bug: only relax if v < u (skip forward edges)
            if v >= u:
                continue
            if dist[u] != INF:
                nd = dist[u] + w
                if nd < dist[v]:
                    dist[v] = nd
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s023(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — processes only odd-ID nodes.

    Bug: skips nodes with even ID. Their neighbors may never be updated.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
        if u % 2 == 0:
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


def s024(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — greedy: always picks smallest edge weight.

    Bug: follows the cheapest local edge from each node. Does not maintain
    global distances. Fails when cheapest local edge leads away from target.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    visited = set()
    current = k
    for _ in range(n - 1):
        visited.add(current)
        neighbors = [(v, w) for v, w in graph[current] if v not in visited]
        if not neighbors:
            break
        next_node = min(neighbors, key=lambda x: x[1])[0]
        for v, w in graph[current]:
            nd = dist[current] + w
            if nd < dist[v]:
                dist[v] = nd
        current = next_node
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s025(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — processes nodes in random order.

    Bug: shuffles nodes randomly before processing. Fails non-deterministically.
    Fixed seed for reproducibility.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    nodes = list(range(1, n + 1))
    random.seed(42)
    random.shuffle(nodes)
    for u in nodes:
        if dist[u] == INF:
            continue
        for v, w in graph[u]:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s026(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — returns first distance found, not max.

    Bug: returns the distance to the first non-source node reached instead
    of max(dist). Undercounts on most graphs.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    first_found = None
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u != k and first_found is None:
            first_found = d
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
    # Bug: returns first found distance instead of max
    return int(first_found) if first_found is not None else 0


# ============================================================================
# F4: DISCONNECTED_MISHANDLING (4 solvers)
# ============================================================================


def s027(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — returns max reachable distance.

    Bug: returns max(dist) for reachable nodes without checking if all
    nodes are reachable. Should return -1 for disconnected graphs.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] < INF and dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s028(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — initializes unreachable nodes to 0.

    Bug: dist[v]=0 for all v. Unreachable nodes have distance 0. Returns
    max distance including these zero-distance unreachable nodes.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {i: 0 for i in range(1, n + 1)}
    heap = [(0, k)]
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
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s029(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — returns visited count on disconnect.

    Bug: returns len(visited) when not all nodes are reachable. On connected
    graphs, returns correct max distance.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    visited = set()
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        visited.add(u)
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    if len(visited) < n:
        return len(visited)
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s030(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — returns 0 on disconnect.

    Bug: returns 0 when any node is unreachable. Should return -1.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return 0
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


# ============================================================================
# Registry: all 30 solvers with metadata
# ============================================================================

SOLVER_REGISTRY: dict[str, dict] = {
    "s001": {"fn": s001, "direction": "F1", "mechanism": "reachability check uses reverse graph"},
    "s002": {"fn": s002, "direction": "F1", "mechanism": "only explores direct neighbors of source"},
    "s003": {"fn": s003, "direction": "F1", "mechanism": "returns node count instead of max distance"},
    "s004": {"fn": s004, "direction": "F1", "mechanism": "skips neighbors with weight > 50"},
    "s005": {"fn": s005, "direction": "F1", "mechanism": "returns min distance instead of max"},
    "s006": {"fn": s006, "direction": "F2", "mechanism": "initializes all distances to 0"},
    "s007": {"fn": s007, "direction": "F2", "mechanism": "doubles every edge weight"},
    "s008": {"fn": s008, "direction": "F2", "mechanism": "adds +1 to every edge weight"},
    "s009": {"fn": s009, "direction": "F2", "mechanism": "squares edge weights"},
    "s010": {"fn": s010, "direction": "F2", "mechanism": "source distance initialized to 1"},
    "s011": {"fn": s011, "direction": "F2", "mechanism": "relaxes edges in reverse direction"},
    "s012": {"fn": s012, "direction": "F2", "mechanism": "uses ceil(w/2) instead of w"},
    "s013": {"fn": s013, "direction": "F2", "mechanism": "returns sum of all edge weights"},
    "s014": {"fn": s014, "direction": "F2", "mechanism": "max(a,b) instead of min(a,b) in relaxation"},
    "s015": {"fn": s015, "direction": "F2", "mechanism": "returns sum of all distances instead of max"},
    "s016": {"fn": s016, "direction": "F3", "mechanism": "BFS on weighted graph (ignores weights)"},
    "s017": {"fn": s017, "direction": "F3", "mechanism": "max-heap instead of min-heap"},
    "s018": {"fn": s018, "direction": "F3", "mechanism": "processes nodes in reverse ID order"},
    "s019": {"fn": s019, "direction": "F3", "mechanism": "single-pass edge list iteration"},
    "s020": {"fn": s020, "direction": "F3", "mechanism": "DFS-based shortest path"},
    "s021": {"fn": s021, "direction": "F3", "mechanism": "Bellman-Ford with N-2 iterations"},
    "s022": {"fn": s022, "direction": "F3", "mechanism": "Bellman-Ford reverse input order"},
    "s023": {"fn": s023, "direction": "F3", "mechanism": "processes only odd-ID nodes"},
    "s024": {"fn": s024, "direction": "F3", "mechanism": "greedy: always picks smallest weight edge"},
    "s025": {"fn": s025, "direction": "F3", "mechanism": "random processing order"},
    "s026": {"fn": s026, "direction": "F3", "mechanism": "Dijkstra with stale heap entries"},
    "s027": {"fn": s027, "direction": "F4", "mechanism": "returns max reachable, ignores unreachable"},
    "s028": {"fn": s028, "direction": "F4", "mechanism": "initializes unreachable to 0"},
    "s029": {"fn": s029, "direction": "F4", "mechanism": "returns visited count on disconnect"},
    "s030": {"fn": s030, "direction": "F4", "mechanism": "returns 0 on disconnect"},
}
