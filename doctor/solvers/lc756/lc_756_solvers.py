"""LC756 Network Delay Time — fresh solver population (30 solvers).

Distribution (declared prior):
  F1 UNDER_PROPAGATION: 5 solvers (s001-s005)
  F2 OVER_COST_BIAS: 10 solvers (s006-s015)
  F3 PRIORITY_ORDER_FAILURE: 11 solvers (s016-s026)
  F4 DISCONNECTED_MISHANDLING: 4 solvers (s027-s030)

Each solver has a docstring naming its primary failure direction and
specific mechanism. No two solvers are identical up to variable rename.
No solver code is reused from LC743 — all implementations are fresh.
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
    """F1: UNDER_PROPAGATION — stops BFS early when target node is found.

    Bug: terminates propagation as soon as node n is visited, missing
    nodes that are farther away. Returns the distance to node n instead
    of max distance to all nodes.
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
        if u == n:
            break  # Bug: stops early when target found
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
    """F1: UNDER_PROPAGATION — only follows edges with weight <= 1.

    Bug: skips all edges with weight > 1 during relaxation. Nodes only
    reachable via heavy edges are marked unreachable.
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
            if w > 1:  # Bug: skips heavy edges
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


def s003(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — uses visited set to block revisits incorrectly.

    Bug: adds nodes to visited before relaxing edges, so a node visited
    via a longer path blocks relaxation via a shorter path.
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
        if u in visited:  # Bug: blocks revisits prematurely
            continue
        visited.add(u)
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


def s004(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — returns number of reachable nodes instead of max distance.

    Bug: returns len(dist) where dist[node] < INF, instead of max(dist).
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
    reachable = sum(1 for node in range(1, n + 1) if dist[node] < INF)
    if reachable < n:
        return -1
    return reachable  # Bug: returns count instead of max distance


def s005(times: list[list[int]], n: int, k: int) -> int:
    """F1: UNDER_PROPAGATION — initializes source distance to infinity.

    Bug: dist[k] = INF instead of 0. Source never relaxes any edges.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = INF  # Bug: source initialized to INF
    heap = [(INF, k)]
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


# ============================================================================
# F2: OVER_COST_BIAS (10 solvers)
# ============================================================================


def s006(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — multiplies all weights by node count n.

    Bug: uses w * n instead of w in relaxation. All distances are inflated
    by factor n.
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
            nd = d + w * n  # Bug: multiplies by n
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


def s007(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — adds edge count to every weight.

    Bug: uses w + len(times) instead of w.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    edge_count = len(times)
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w + edge_count  # Bug: adds edge count
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
    """F2: OVER_COST_BIAS — uses w^2 instead of w.

    Bug: uses w**2 instead of w. Quadratic overestimation.
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


def s009(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — returns max distance + min distance.

    Bug: returns max(dist) + min(dist) instead of max(dist).
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
    min_dist = INF
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
        if dist[node] < min_dist:
            min_dist = dist[node]
    return int(max_dist + min_dist)  # Bug: adds min


def s010(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — returns max distance * 2.

    Bug: returns max(dist) * 2 instead of max(dist).
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
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist * 2)  # Bug: doubles result


def s011(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — adds sqrt(w) to every weight.

    Bug: uses w + sqrt(w) instead of w.
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
            nd = d + w + math.sqrt(w)  # Bug: adds sqrt
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
    """F2: OVER_COST_BIAS — returns sum of all distances.

    Bug: returns sum(dist[node]) instead of max(dist[node]).
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
    return int(total)  # Bug: returns sum


def s013(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — uses log(w+1) instead of w.

    Bug: uses log(w+1) which is much smaller than w for large weights,
    but adds extra cost for small weights.
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
            nd = d + math.log(w + 1)  # Bug: uses log
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


def s014(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — returns max distance + number of edges.

    Bug: returns max(dist) + len(times) instead of max(dist).
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
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist + len(times))  # Bug: adds edge count


def s015(times: list[list[int]], n: int, k: int) -> int:
    """F2: OVER_COST_BIAS — returns max distance + n.

    Bug: returns max(dist) + n instead of max(dist).
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
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist + n)  # Bug: adds n


# ============================================================================
# F3: PRIORITY_ORDER_FAILURE (11 solvers)
# ============================================================================


def s016(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — DFS instead of Dijkstra.

    Bug: uses stack (LIFO) instead of heap. Processes nodes in depth-first
    order, not shortest-distance order.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
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


def s017(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — processes nodes in reverse ID order.

    Bug: sorts nodes by descending ID instead of by distance.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    # Bug: processes nodes in reverse ID order
    nodes = list(range(1, n + 1))
    nodes.sort(reverse=True)
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


def s018(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — uses random processing order.

    Bug: processes nodes in random order instead of by distance.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    rng = random.Random(42)
    nodes = list(range(1, n + 1))
    rng.shuffle(nodes)  # Bug: random order
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


def s019(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — uses ascending ID order (BFS-like).

    Bug: processes nodes in ascending ID order, which is not
    shortest-distance order.
    """
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    nodes = list(range(1, n + 1))
    nodes.sort()  # Bug: ascending ID order
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


def s020(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — processes edges in reverse order.

    Bug: iterates edges in reverse order, which can affect which
    relaxation fires first.
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
        edges = graph[u][::-1]  # Bug: reverses edge order
        for v, w in edges:
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
    """F3: PRIORITY_ORDER_FAILURE — uses negative weights.

    Bug: negates all weights, turning shortest-path into longest-path.
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
            nd = d - w  # Bug: negates weight
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


def s022(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — uses weight modulo 3.

    Bug: uses w % 3 instead of w. Reduces all weights to 0, 1, or 2.
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
            nd = d + (w % 3)  # Bug: modulo 3
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


def s023(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — uses bitwise XOR on weights.

    Bug: uses w ^ (w >> 1) instead of w. Distorts weights unpredictably.
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
            nd = d + (w ^ (w >> 1))  # Bug: XOR distortion
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
    """F3: PRIORITY_ORDER_FAILURE — returns min distance instead of max.

    Bug: returns min(dist) instead of max(dist).
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
    return int(min_dist)  # Bug: returns min


def s025(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — returns distance to node 1.

    Bug: returns dist[1] instead of max(dist).
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
    if dist[1] == INF:
        return -1
    return int(dist[1])  # Bug: returns dist[1]


def s026(times: list[list[int]], n: int, k: int) -> int:
    """F3: PRIORITY_ORDER_FAILURE — returns first distance found.

    Bug: returns the distance to the first non-source node processed
    instead of max(dist).
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
    return int(first_found) if first_found is not None else 0  # Bug: returns first


# ============================================================================
# F4: DISCONNECTED_MISHANDLING (4 solvers)
# ============================================================================


def s027(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — returns 0 for disconnected graphs.

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
    for node in range(1, n + 1):
        if dist[node] == INF:
            return 0  # Bug: returns 0 instead of -1
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s028(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — returns n for disconnected graphs.

    Bug: returns n when any node is unreachable. Should return -1.
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
            return n  # Bug: returns n instead of -1
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s029(times: list[list[int]], n: int, k: int) -> int:
    """F4: DISCONNECTED_MISHANDLING — returns max reachable distance.

    Bug: returns max(dist) for reachable nodes without checking if all
    nodes are reachable. On disconnected graphs, returns a finite value
    instead of -1.
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
    # Bug: returns max of reachable distances, ignores unreachable
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] < INF and dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


def s030(times: list[list[int]], n: int, k: int) -> int:
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
        return len(visited)  # Bug: returns count
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


# ============================================================================
# Registry: all 30 solvers with metadata
# ============================================================================

SOLVER_REGISTRY: dict[str, dict] = {
    "s001": {"fn": s001, "direction": "F1", "mechanism": "stops BFS early when target found"},
    "s002": {"fn": s002, "direction": "F1", "mechanism": "only follows edges with weight <= 1"},
    "s003": {"fn": s003, "direction": "F1", "mechanism": "visited set blocks revisits incorrectly"},
    "s004": {"fn": s004, "direction": "F1", "mechanism": "returns reachable count instead of max distance"},
    "s005": {"fn": s005, "direction": "F1", "mechanism": "source distance initialized to infinity"},
    "s006": {"fn": s006, "direction": "F2", "mechanism": "multiplies all weights by node count n"},
    "s007": {"fn": s007, "direction": "F2", "mechanism": "adds edge count to every weight"},
    "s008": {"fn": s008, "direction": "F2", "mechanism": "uses w^2 instead of w"},
    "s009": {"fn": s009, "direction": "F2", "mechanism": "returns max + min distance"},
    "s010": {"fn": s010, "direction": "F2", "mechanism": "returns max distance * 2"},
    "s011": {"fn": s011, "direction": "F2", "mechanism": "adds sqrt(w) to every weight"},
    "s012": {"fn": s012, "direction": "F2", "mechanism": "returns sum of all distances"},
    "s013": {"fn": s013, "direction": "F2", "mechanism": "uses log(w+1) instead of w"},
    "s014": {"fn": s014, "direction": "F2", "mechanism": "returns max distance + number of edges"},
    "s015": {"fn": s015, "direction": "F2", "mechanism": "returns max distance + n"},
    "s016": {"fn": s016, "direction": "F3", "mechanism": "DFS instead of Dijkstra"},
    "s017": {"fn": s017, "direction": "F3", "mechanism": "processes nodes in reverse ID order"},
    "s018": {"fn": s018, "direction": "F3", "mechanism": "uses random processing order"},
    "s019": {"fn": s019, "direction": "F3", "mechanism": "uses ascending ID order (BFS-like)"},
    "s020": {"fn": s020, "direction": "F3", "mechanism": "processes edges in reverse order"},
    "s021": {"fn": s021, "direction": "F3", "mechanism": "uses negative weights"},
    "s022": {"fn": s022, "direction": "F3", "mechanism": "uses weight modulo 3"},
    "s023": {"fn": s023, "direction": "F3", "mechanism": "uses bitwise XOR on weights"},
    "s024": {"fn": s024, "direction": "F3", "mechanism": "returns min distance instead of max"},
    "s025": {"fn": s025, "direction": "F3", "mechanism": "returns distance to node 1"},
    "s026": {"fn": s026, "direction": "F3", "mechanism": "returns first distance found"},
    "s027": {"fn": s027, "direction": "F4", "mechanism": "returns 0 for disconnected graphs"},
    "s028": {"fn": s028, "direction": "F4", "mechanism": "returns n for disconnected graphs"},
    "s029": {"fn": s029, "direction": "F4", "mechanism": "returns max reachable distance"},
    "s030": {"fn": s030, "direction": "F4", "mechanism": "returns visited count on disconnect"},
}
