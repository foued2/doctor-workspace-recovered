"""LC743 — v2 solver population (31 solvers, different strategies)."""
from __future__ import annotations
from collections import defaultdict
import heapq


def solver_001(times, n, k):
    """Dijkstra with adjacency list."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_002(times, n, k):
    """BFS (ignores weights)."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    queue = [k]
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if dist[v] == float('inf'):
                dist[v] = dist[u] + 1
                queue.append(v)
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_003(times, n, k):
    """Bellman-Ford."""
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    
    for _ in range(n - 1):
        for u, v, w in times:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_004(times, n, k):
    """Floyd-Warshall."""
    INF = float('inf')
    dist = [[INF] * (n + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        dist[i][i] = 0
    
    for u, v, w in times:
        dist[u][v] = w
    
    for mid in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][mid] + dist[mid][j] < dist[i][j]:
                    dist[i][j] = dist[i][mid] + dist[mid][j]
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[k][node] == INF:
            return -1
        max_dist = max(max_dist, dist[k][node])
    
    return max_dist


def solver_005(times, n, k):
    """Dijkstra with matrix."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = [float('inf')] * (n + 1)
    dist[k] = 0
    visited = [False] * (n + 1)
    
    for _ in range(n):
        u = -1
        min_dist = float('inf')
        for i in range(1, n + 1):
            if not visited[i] and dist[i] < min_dist:
                min_dist = dist[i]
                u = i
        
        if u == -1:
            break
        visited[u] = True
        
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_006(times, n, k):
    """BFS with weight tracking."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    queue = [k]
    
    while queue:
        u = queue.pop(0)
        for v, w in graph[u]:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
                queue.append(v)
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_007(times, n, k):
    """Dijkstra with early termination."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    reached = 0
    
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        reached += 1
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    
    if reached < n:
        return -1
    
    return max(dist[node] for node in range(1, n + 1))


def solver_008(times, n, k):
    """BFS from source, returns count of visited nodes."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    visited = set()
    queue = [k]
    visited.add(k)
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    
    if len(visited) < n:
        return -1
    
    return len(visited) - 1


def solver_009(times, n, k):
    """Dijkstra returning sum of all distances."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
    
    return sum(dist[node] for node in range(1, n + 1))


def solver_010(times, n, k):
    """Greedy: pick shortest edge from source."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    if k not in graph:
        return -1 if n > 1 else 0
    
    return min(w for _, w in graph[k])


def solver_011(times, n, k):
    """Dijkstra with reversed edges."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[v].append((u, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_012(times, n, k):
    """Dijkstra ignoring weights."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v in graph[u]:
            nd = d + 1
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_013(times, n, k):
    """Returns n-1 if connected, else -1."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    visited = set()
    queue = [k]
    visited.add(k)
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    
    return n - 1 if len(visited) == n else -1


def solver_014(times, n, k):
    """BFS returning edge count instead of max distance."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    queue = [k]
    edges = 0
    
    while queue:
        u = queue.pop(0)
        for v, w in graph[u]:
            if dist[v] == float('inf'):
                dist[v] = dist[u] + 1
                edges += 1
                queue.append(v)
    
    if any(dist[node] == float('inf') for node in range(1, n + 1)):
        return -1
    
    return edges


def solver_015(times, n, k):
    """Dijkstra with wrong initialization."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: 1 for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_016(times, n, k):
    """BFS on weighted graph (ignores weights)."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    queue = [k]
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if dist[v] == float('inf'):
                dist[v] = dist[u] + 1
                queue.append(v)
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_017(times, n, k):
    """Dijkstra with max-heap (wrong)."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_018(times, n, k):
    """Dijkstra with random tie-breaking."""
    import random
    rng = random.Random(42)
    
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        neighbors = list(graph[u])
        rng.shuffle(neighbors)
        for v, w in neighbors:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_019(times, n, k):
    """BFS returning visited count."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    visited = set()
    queue = [k]
    visited.add(k)
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    
    return len(visited)


def solver_020(times, n, k):
    """Dijkstra returning min distance."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
    
    reachable = [dist[node] for node in range(1, n + 1) if dist[node] != float('inf')]
    
    if len(reachable) < n:
        return -1
    
    return min(reachable)


def solver_021(times, n, k):
    """Bellman-Ford with N-2 iterations (wrong)."""
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    
    for _ in range(n - 2):
        for u, v, w in times:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_022(times, n, k):
    """Dijkstra with source distance = 1."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_023(times, n, k):
    """BFS on odd-ID nodes only."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    queue = [k]
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if v % 2 == 1 and dist[v] == float('inf'):
                dist[v] = dist[u] + 1
                queue.append(v)
    
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_024(times, n, k):
    """Dijkstra returning sum of all weights."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
    
    return sum(w for _, _, w in times)


def solver_025(times, n, k):
    """Dijkstra with wrong edge weight direction."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[v].append((u, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] == float('inf'):
            return -1
        max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_026(times, n, k):
    """BFS returning 0 on disconnect."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    visited = set()
    queue = [k]
    visited.add(k)
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    
    if len(visited) < n:
        return 0
    
    return max(dist[node] for node in range(1, n + 1))


def solver_027(times, n, k):
    """Dijkstra returning max reachable distance."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
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
        if dist[node] != float('inf'):
            max_dist = max(max_dist, dist[node])
    
    return max_dist


def solver_028(times, n, k):
    """Dijkstra with unreachable = 0."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: 0 for i in range(1, n + 1)}
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
    
    return max(dist[node] for node in range(1, n + 1))


def solver_029(times, n, k):
    """BFS returning visited count."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append(v)
    
    visited = set()
    queue = [k]
    visited.add(k)
    
    while queue:
        u = queue.pop(0)
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    
    return len(visited) - 1


def solver_030(times, n, k):
    """Dijkstra returning edge count."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    edges = 0
    
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                edges += 1
                heapq.heappush(heap, (nd, v))
    
    if any(dist[node] == float('inf') for node in range(1, n + 1)):
        return -1
    
    return edges


def solver_031(times, n, k):
    """Dijkstra returning 0."""
    return 0
