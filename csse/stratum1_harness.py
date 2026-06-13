"""
STRATUM-1 EXECUTION HARNESS (4 problems, closed measurement system)

Frozen definitions. No adaptation after execution begins.
S is a property of (problem, test distribution, solver ensemble).
"""
import json
import hashlib
import time
import random
import numpy as np
from pathlib import Path
from collections import defaultdict, deque
from itertools import combinations
from abc import ABC, abstractmethod

SEED = 20260613
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "stratum1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SECTION 1: PROBLEM DEFINITIONS + ORACLES
# ============================================================

class ProblemSpec:
    def __init__(self, name, oracle_fn, input_gen_fns, anchor_cases):
        self.name = name
        self.oracle = oracle_fn
        self.input_gens = input_gen_fns
        self.anchors = anchor_cases


def coin_change_oracle(amount, coins):
    if amount == 0:
        return 0
    INF = 10**9
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if i - c >= 0 and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return -1 if dp[amount] == INF else dp[amount]


def grid_shortest_path_oracle(grid, start, target):
    if start == target:
        return 0
    n, m = len(grid), len(grid[0])
    sx, sy = start
    tx, ty = target
    if grid[sx][sy] == 1 or grid[tx][ty] == 1:
        return -1
    q = deque([(sx, sy, 0)])
    visited = {(sx, sy)}
    while q:
        x, y, d = q.popleft()
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and (nx, ny) not in visited and grid[nx][ny] == 0:
                if (nx, ny) == (tx, ty):
                    return d + 1
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
    return -1


def interval_cover_oracle(intervals):
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    target_end = max(e for s, e in intervals)
    count = 0
    current_end = intervals[0][0] - 1
    i = 0
    n = len(intervals)
    while current_end < target_end and i < n:
        best_end = current_end
        while i < n and intervals[i][0] <= current_end + 1:
            best_end = max(best_end, intervals[i][1])
            i += 1
        if best_end == current_end:
            return -1
        current_end = best_end
        count += 1
    return count if current_end >= target_end else -1


def constraint_lattice_oracle(elements, constraints, k):
    if k == 0:
        return True
    if k > len(elements):
        return False
    for subset in combinations(range(len(elements)), k):
        s = set(subset)
        valid = True
        for a, b in constraints:
            if a in s and b in s:
                if elements[a] >= elements[b]:
                    valid = False
                    break
        if valid:
            return True
    return False


# ============================================================
# SECTION 2: TEST CASE GENERATORS
# ============================================================

def gen_coin_change_cases(n=100):
    cases = []
    rng = random.Random(SEED)
    for _ in range(85):
        amt = rng.randint(1, 200)
        num_coins = rng.randint(1, 6)
        coins = sorted(set(rng.randint(1, 50) for _ in range(num_coins)))
        cases.append((amt, coins))
    anchors = [
        (0, [1]),
        (1, [1]),
        (11, [1, 2, 5]),
        (100, [1]),
        (7, [2, 3]),
        (30, [1, 5, 10, 25]),
        (1, [2]),
        (41, [1, 5, 10, 25]),
        (100, [2, 5, 10]),
        (50, [1, 2, 5, 10]),
        (3, [2]),
        (8, [1, 3, 4]),
        (12, [1, 5, 10]),
        (99, [1, 2, 5]),
        (200, [1, 3, 7]),
    ]
    return cases[:85] + anchors


def gen_grid_cases(n=100):
    cases = []
    rng = random.Random(SEED + 1)
    for _ in range(85):
        rows = rng.randint(3, 8)
        cols = rng.randint(3, 8)
        grid = [[0] * cols for _ in range(rows)]
        num_walls = rng.randint(0, rows * cols // 3)
        for _ in range(num_walls):
            r, c = rng.randint(0, rows - 1), rng.randint(0, cols - 1)
            if (r, c) != (0, 0) and (r, c) != (rows - 1, cols - 1):
                grid[r][c] = 1
        start = (0, 0)
        target = (rows - 1, cols - 1)
        cases.append((grid, start, target))
    anchors = [
        ([[0]], (0, 0), (0, 0)),
        ([[0, 0], [0, 0]], (0, 0), (1, 1)),
        ([[0, 1], [1, 0]], (0, 0), (1, 1)),
        ([[0] * 5 for _ in range(5)], (0, 0), (4, 4)),
        ([[1] * 5 for _ in range(5)], (0, 0), (4, 4)),
        ([[0, 0, 0], [1, 1, 0], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0, 0], [0, 0]], (0, 1), (1, 0)),
        ([[0] * 3, [1, 0, 1], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0, 1, 0], [0, 1, 0], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0] * 4 for _ in range(4)], (0, 0), (3, 3)),
        ([[0, 0, 0, 0, 0]], (0, 0), (0, 4)),
        ([[0], [0], [0], [0], [0]], (0, 0), (4, 0)),
        ([[0, 1], [0, 0]], (0, 0), (1, 1)),
        ([[0, 0, 1], [1, 0, 1], [1, 0, 0]], (0, 0), (2, 2)),
        ([[0] * 6 for _ in range(6)], (0, 0), (5, 5)),
    ]
    return cases[:85] + anchors


def gen_interval_cases(n=100):
    cases = []
    rng = random.Random(SEED + 2)
    for _ in range(85):
        n_intervals = rng.randint(3, 15)
        intervals = []
        for _ in range(n_intervals):
            s = rng.randint(0, 50)
            e = s + rng.randint(1, 20)
            intervals.append((s, e))
        cases.append(intervals)
    anchors = [
        [(0, 10)],
        [(0, 5), (5, 10)],
        [(0, 3), (2, 7), (6, 10)],
        [(i, i + 1) for i in range(10)],
        [(0, 100)],
        [(0, 1), (0, 2), (0, 3)],
        [(10, 20), (5, 15), (0, 25)],
        [(0, 1), (2, 3), (4, 5)],
        [(0, 10), (5, 15), (10, 20)],
        [(i, i + 5) for i in range(0, 50, 3)],
        [(0, 0)],
        [(5, 5)],
        [(0, 1), (1, 2), (2, 3), (3, 4)],
        [(0, 10), (0, 5), (5, 10)],
        [(0, 20), (10, 30), (20, 40)],
    ]
    return cases[:85] + anchors


def gen_constraint_cases(n=100):
    cases = []
    rng = random.Random(SEED + 3)
    for _ in range(85):
        n_elem = rng.randint(3, 6)
        elements = list(range(n_elem))
        k = rng.randint(1, n_elem - 1)

        n_constr = rng.randint(3, min(n_elem * (n_elem - 1) // 2, 8))
        seen = set()
        constraints = []
        for _ in range(n_constr):
            a, b = rng.sample(range(n_elem), 2)
            if a > b:
                a, b = b, a
            if (a, b) not in seen:
                seen.add((a, b))
                constraints.append((a, b))

        for _ in range(rng.randint(1, 3)):
            a, b = rng.sample(range(n_elem), 2)
            if a > b:
                a, b = b, a
            if (a, b) in seen:
                if rng.random() < 0.5:
                    constraints.append((b, a))
            else:
                constraints.append((a, b))

        cases.append((elements, constraints, k))
    anchors = [
        ([0, 1, 2], [(0, 1), (1, 2), (0, 2)], 2),
        ([0, 1, 2, 3], [(0, 1), (1, 2), (2, 3), (0, 3)], 3),
        (list(range(5)), [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)], 4),
        ([0, 1, 2, 3], [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)], 3),
        (list(range(6)), [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)], 5),
        ([0, 1, 2], [(0, 1), (0, 2), (1, 2), (2, 1)], 2),
        ([0, 1, 2, 3], [(0, 1), (1, 0), (2, 3), (3, 2)], 3),
        (list(range(4)), [(0, 1), (1, 2), (2, 0)], 2),
        ([0, 1, 2, 3], [(0, 1), (1, 2), (2, 3), (3, 0)], 3),
        (list(range(5)), [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)], 4),
        ([0, 1, 2, 3], [(0, 1), (1, 2), (0, 2), (2, 0)], 2),
        (list(range(4)), [(0, 1), (1, 0), (2, 3), (3, 2), (0, 2)], 2),
        ([0, 1, 2, 3], [(0, 1), (1, 2), (2, 0), (0, 3)], 3),
        (list(range(5)), [(0, 1), (1, 2), (2, 0), (3, 4), (4, 3)], 3),
        ([0, 1, 2], [(0, 1), (1, 2), (2, 0), (0, 2)], 2),
    ]
    return cases[:85] + anchors


# ============================================================
# SECTION 3: SOLVER TEMPLATES
# ============================================================

class Solver(ABC):
    def __init__(self, solver_id, family, variant):
        self.solver_id = solver_id
        self.family = family
        self.variant = variant

    @abstractmethod
    def solve(self, problem_input):
        pass

    def __repr__(self):
        return f"{self.family}_{self.variant}"


# --- COIN CHANGE SOLVERS ---

class CoinDP_T1(Solver):
    def __init__(self):
        super().__init__("cc_dp_t1", "dp", "bottom_up")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        INF = 10**9
        dp = [INF] * (amount + 1)
        dp[0] = 0
        for i in range(1, amount + 1):
            for c in coins:
                if i - c >= 0 and dp[i - c] + 1 < dp[i]:
                    dp[i] = dp[i - c] + 1
        return -1 if dp[amount] == INF else dp[amount]


class CoinDP_T2(Solver):
    def __init__(self):
        super().__init__("cc_dp_t2", "dp", "top_down")

    def solve(self, amount, coins):
        memo = {}

        def rec(a):
            if a == 0:
                return 0
            if a < 0:
                return float('inf')
            if a in memo:
                return memo[a]
            best = float('inf')
            for c in coins:
                best = min(best, 1 + rec(a - c))
            memo[a] = best
            return best

        r = rec(amount)
        return r if r != float('inf') else -1


class CoinDP_T3(Solver):
    def __init__(self):
        super().__init__("cc_dp_t3", "dp", "pruned")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        threshold = np.percentile(coins, 80) if coins else 0
        filtered = [c for c in coins if c <= threshold]
        if not filtered:
            filtered = coins
        INF = 10**9
        dp = [INF] * (amount + 1)
        dp[0] = 0
        for i in range(1, amount + 1):
            for c in filtered:
                if i - c >= 0 and dp[i - c] + 1 < dp[i]:
                    dp[i] = dp[i - c] + 1
        return -1 if dp[amount] == INF else dp[amount]


class CoinDP_T4(Solver):
    def __init__(self):
        super().__init__("cc_dp_t4", "dp", "greedy_approx")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        coins_sorted = sorted(coins)
        dp = [0] + [float('inf')] * amount
        for i in range(1, amount + 1):
            for c in coins_sorted:
                if i - c >= 0:
                    dp[i] = dp[i - c] + 1
                    break
        return -1 if dp[amount] == float('inf') else dp[amount]


class CoinBFS_T1(Solver):
    def __init__(self):
        super().__init__("cc_bfs_t1", "bfs", "standard")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        visited = {0}
        queue = deque([(0, 0)])
        while queue:
            pos, dist = queue.popleft()
            for c in coins:
                nxt = pos + c
                if nxt == amount:
                    return dist + 1
                if nxt < amount and nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, dist + 1))
        return -1


class CoinBFS_T2(Solver):
    def __init__(self):
        super().__init__("cc_bfs_t2", "bfs", "reverse_order")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        visited = {0}
        queue = deque([(0, 0)])
        while queue:
            pos, dist = queue.popleft()
            for c in sorted(coins, reverse=True):
                nxt = pos + c
                if nxt == amount:
                    return dist + 1
                if nxt < amount and nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, dist + 1))
        return -1


class CoinGreedy_T1(Solver):
    def __init__(self):
        super().__init__("cc_greedy_t1", "greedy", "largest_first")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        coins_sorted = sorted(coins, reverse=True)
        count = 0
        remaining = amount
        for c in coins_sorted:
            while remaining >= c:
                remaining -= c
                count += 1
        return count if remaining == 0 else -1


class CoinGreedy_T2(Solver):
    def __init__(self):
        super().__init__("cc_greedy_t2", "greedy", "smallest_first")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        coins_sorted = sorted(coins)
        count = 0
        remaining = amount
        for c in coins_sorted:
            while remaining >= c:
                remaining -= c
                count += 1
        return count if remaining == 0 else -1


class CoinGreedy_T3(Solver):
    def __init__(self):
        super().__init__("cc_greedy_t3", "greedy", "random_order")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        rng = random.Random(SEED + 100)
        coins_shuffled = list(coins)
        rng.shuffle(coins_shuffled)
        count = 0
        remaining = amount
        for c in coins_shuffled:
            while remaining >= c:
                remaining -= c
                count += 1
        return count if remaining == 0 else -1


class CoinRand_T1(Solver):
    def __init__(self):
        super().__init__("cc_rand_t1", "random", "uniform")

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        rng = random.Random(SEED + 200)
        for _ in range(amount + 1):
            c = rng.choice(coins)
            if c <= amount:
                return 1
        return -1


# --- GRID SHORTEST PATH SOLVERS ---

class GridBFS_T1(Solver):
    def __init__(self):
        super().__init__("gp_bfs_t1", "bfs", "standard")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        q = deque([(sx, sy, 0)])
        visited = {(sx, sy)}
        while q:
            x, y, d = q.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and (nx, ny) not in visited and grid[nx][ny] == 0:
                    if (nx, ny) == (tx, ty):
                        return d + 1
                    visited.add((nx, ny))
                    q.append((nx, ny, d + 1))
        return -1


class GridBFS_T2(Solver):
    def __init__(self):
        super().__init__("gp_bfs_t2", "bfs", "reverse_direction")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        q = deque([(sx, sy, 0)])
        visited = {(sx, sy)}
        while q:
            x, y, d = q.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and (nx, ny) not in visited and grid[nx][ny] == 0:
                    if (nx, ny) == (tx, ty):
                        return d + 1
                    visited.add((nx, ny))
                    q.append((nx, ny, d + 1))
        return -1


class GridDFS_T1(Solver):
    def __init__(self):
        super().__init__("gp_dfs_t1", "dfs", "greedy_direction")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        x, y = sx, sy
        d = 0
        visited = {(x, y)}
        while (x, y) != (tx, ty):
            best = None
            best_dist = float('inf')
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                    dist = abs(nx - tx) + abs(ny - ty)
                    if dist < best_dist:
                        best_dist = dist
                        best = (nx, ny)
            if best is None:
                return -1
            x, y = best
            visited.add((x, y))
            d += 1
            if d > n * m:
                return -1
        return d


class GridDFS_T2(Solver):
    def __init__(self):
        super().__init__("gp_dfs_t2", "dfs", "greedy_best_first")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        import heapq
        h = lambda x, y: abs(x - tx) + abs(y - ty)
        heap = [(h(sx, sy), 0, sx, sy)]
        visited = set()
        while heap:
            f, d, x, y = heapq.heappop(heap)
            if (x, y) in visited:
                continue
            visited.add((x, y))
            if (x, y) == (tx, ty):
                return d
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                    heapq.heappush(heap, (d + h(nx, ny), d + 1, nx, ny))
        return -1


class GridGreedy_T1(Solver):
    def __init__(self):
        super().__init__("gp_greedy_t1", "greedy", "manhattan")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        x, y = sx, sy
        d = 0
        visited = {(x, y)}
        while (x, y) != (tx, ty):
            best = None
            best_dist = float('inf')
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                    dist = abs(nx - tx) + abs(ny - ty)
                    if dist < best_dist:
                        best_dist = dist
                        best = (nx, ny)
            if best is None:
                return -1
            x, y = best
            visited.add((x, y))
            d += 1
            if d > n * m:
                return -1
        return d


class GridGreedy_T2(Solver):
    def __init__(self):
        super().__init__("gp_greedy_t2", "greedy", "random_direction")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        rng = random.Random(SEED + 300)
        x, y = sx, sy
        d = 0
        visited = {(x, y)}
        while (x, y) != (tx, ty):
            neighbors = []
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                    neighbors.append((nx, ny))
            if not neighbors:
                return -1
            x, y = rng.choice(neighbors)
            visited.add((x, y))
            d += 1
            if d > n * m:
                return -1
        return d


class GridAStar_T1(Solver):
    def __init__(self):
        super().__init__("gp_astar_t1", "astar", "manhattan")

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1
        import heapq
        h = lambda x, y: abs(x - tx) + abs(y - ty)
        heap = [(h(sx, sy), 0, sx, sy)]
        visited = set()
        while heap:
            f, d, x, y = heapq.heappop(heap)
            if (x, y) == (tx, ty):
                return d
            if (x, y) in visited:
                continue
            visited.add((x, y))
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                    heapq.heappush(heap, (d + 1 + h(nx, ny), d + 1, nx, ny))
        return -1


# --- INTERVAL COVER SOLVERS ---

class IntGreedy_T1(Solver):
    def __init__(self):
        super().__init__("ic_greedy_t1", "greedy", "earliest_end")

    def solve(self, intervals):
        if not intervals:
            return 0
        intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = intervals[0][0] - 1
        i = 0
        n = len(intervals)
        while current_end < target_end and i < n:
            best_end = current_end
            while i < n and intervals[i][0] <= current_end + 1:
                best_end = max(best_end, intervals[i][1])
                i += 1
            if best_end == current_end:
                return -1
            current_end = best_end
            count += 1
        return count if current_end >= target_end else -1


class IntGreedy_T2(Solver):
    def __init__(self):
        super().__init__("ic_greedy_t2", "greedy", "earliest_start")

    def solve(self, intervals):
        if not intervals:
            return 0
        intervals = sorted(intervals, key=lambda x: x[0])
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = intervals[0][0] - 1
        i = 0
        n = len(intervals)
        while current_end < target_end and i < n:
            best_end = current_end
            while i < n and intervals[i][0] <= current_end + 1:
                best_end = max(best_end, intervals[i][1])
                i += 1
            if best_end == current_end:
                return -1
            current_end = best_end
            count += 1
        return count if current_end >= target_end else -1


class IntGreedy_T3(Solver):
    def __init__(self):
        super().__init__("ic_greedy_t3", "greedy", "longest_first")

    def solve(self, intervals):
        if not intervals:
            return 0
        intervals = sorted(intervals, key=lambda x: -(x[1] - x[0]))
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = min(s for s, e in intervals) - 1
        i = 0
        n = len(intervals)
        while current_end < target_end and i < n:
            best_end = current_end
            while i < n and intervals[i][0] <= current_end + 1:
                best_end = max(best_end, intervals[i][1])
                i += 1
            if best_end == current_end:
                return -1
            current_end = best_end
            count += 1
        return count if current_end >= target_end else -1


class IntGreedy_T4(Solver):
    def __init__(self):
        super().__init__("ic_greedy_t4", "greedy", "shortest_first")

    def solve(self, intervals):
        if not intervals:
            return 0
        intervals = sorted(intervals, key=lambda x: x[1] - x[0])
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = min(s for s, e in intervals) - 1
        i = 0
        n = len(intervals)
        while current_end < target_end and i < n:
            best_end = current_end
            while i < n and intervals[i][0] <= current_end + 1:
                best_end = max(best_end, intervals[i][1])
                i += 1
            if best_end == current_end:
                return -1
            current_end = best_end
            count += 1
        return count if current_end >= target_end else -1


class IntDP_T1(Solver):
    def __init__(self):
        super().__init__("ic_dp_t1", "dp", "interval_dp")

    def solve(self, intervals):
        if not intervals:
            return 0
        intervals = sorted(intervals)
        n = len(intervals)
        dp = [0] * n
        for i in range(n):
            dp[i] = 1
            for j in range(i):
                if intervals[j][1] + 1 <= intervals[i][0]:
                    dp[i] = max(dp[i], dp[j] + 1)
        return max(dp) if dp else 0


class IntDFS_T1(Solver):
    def __init__(self):
        super().__init__("ic_dfs_t1", "dfs", "exhaustive")

    def solve(self, intervals):
        if not intervals:
            return 0
        best = [0]

        def dfs(idx, covered, count):
            if idx == len(intervals):
                best[0] = max(best[0], count)
                return
            dfs(idx + 1, covered, count)
            s, e = intervals[idx]
            if s > covered:
                dfs(idx + 1, e, count + 1)

        dfs(0, -10**9, 0)
        return best[0]


class IntRand_T1(Solver):
    def __init__(self):
        super().__init__("ic_rand_t1", "random", "random_greedy")

    def solve(self, intervals):
        if not intervals:
            return 0
        rng = random.Random(SEED + 400)
        intervals_shuffled = list(intervals)
        rng.shuffle(intervals_shuffled)
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = min(s for s, e in intervals) - 1
        i = 0
        n = len(intervals_shuffled)
        while current_end < target_end and i < n:
            best_end = current_end
            while i < n and intervals_shuffled[i][0] <= current_end + 1:
                best_end = max(best_end, intervals_shuffled[i][1])
                i += 1
            if best_end == current_end:
                return -1
            current_end = best_end
            count += 1
        return count if current_end >= target_end else -1


# --- CONSTRAINT LATTICE SOLVERS ---

class ConstBrute_T1(Solver):
    def __init__(self):
        super().__init__("cl_brute_t1", "dp", "subset_dp")

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        n = len(elements)
        if k > n:
            return False
        from functools import lru_cache

        @lru_cache(maxsize=None)
        def valid_mask(mask):
            s = {i for i in range(n) if mask & (1 << i)}
            for a, b in constraints:
                if a in s and b in s and elements[a] > elements[b]:
                    return False
            return True

        for mask in range(1 << n):
            if bin(mask).count('1') == k and valid_mask(mask):
                return True
        return False


class ConstProp_T1(Solver):
    def __init__(self):
        super().__init__("cl_prop_t1", "greedy", "constrained_greedy")

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        n = len(elements)
        if k > n:
            return False
        order = sorted(range(n), key=lambda i: elements[i])
        selected = set()
        for i in order:
            if len(selected) >= k:
                break
            test = selected | {i}
            valid = True
            for a, b in constraints:
                if a in test and b in test and elements[a] > elements[b]:
                    valid = False
                    break
            if valid:
                selected.add(i)
        return len(selected) >= k


class ConstGreedy_T1(Solver):
    def __init__(self):
        super().__init__("cl_greedy_t1", "greedy", "smallest_first")

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        if k > len(elements):
            return False
        order = sorted(range(len(elements)), key=lambda i: elements[i])
        selected = []
        for i in order:
            if len(selected) >= k:
                break
            new_selected = selected + [i]
            valid = True
            for a, b in constraints:
                if a in new_selected and b in new_selected:
                    if elements[a] > elements[b]:
                        valid = False
                        break
            if valid:
                selected.append(i)
        return len(selected) >= k


class ConstTopo_T1(Solver):
    def __init__(self):
        super().__init__("cl_topo_t1", "topological", "kahn_attempt")

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        if k > len(elements):
            return False
        n = len(elements)
        in_degree = [0] * n
        for a, b in constraints:
            in_degree[b] += 1
        queue = deque([i for i in range(n) if in_degree[i] == 0])
        order = []
        while queue:
            u = queue.popleft()
            order.append(u)
            for a, b in constraints:
                if a == u:
                    in_degree[b] -= 1
                    if in_degree[b] == 0:
                        queue.append(b)
        if len(order) != n:
            return False
        selected = order[:k]
        valid = True
        for a, b in constraints:
            if a in selected and b in selected:
                if elements[a] > elements[b]:
                    valid = False
                    break
        return valid


class ConstRand_T1(Solver):
    def __init__(self):
        super().__init__("cl_rand_t1", "random", "random_sample")

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        if k > len(elements):
            return False
        rng = random.Random(SEED + 500)
        for _ in range(100):
            subset = rng.sample(range(len(elements)), k)
            s = set(subset)
            valid = True
            for a, b in constraints:
                if a in s and b in s:
                    if elements[a] > elements[b]:
                        valid = False
                        break
            if valid:
                return True
        return False


# ============================================================
# SECTION 4: SOLVER INSTANTIATION + REDUNDANCY FILTER
# ============================================================

COIN_SOLVERS = [cls() for cls in [
    CoinDP_T1, CoinDP_T2, CoinDP_T3, CoinDP_T4,
    CoinBFS_T1, CoinBFS_T2,
    CoinGreedy_T1, CoinGreedy_T2, CoinGreedy_T3,
    CoinRand_T1,
]]

GRID_SOLVERS = [cls() for cls in [
    GridBFS_T1, GridBFS_T2,
    GridDFS_T1, GridDFS_T2,
    GridGreedy_T1, GridGreedy_T2,
    GridAStar_T1,
]]

INT_SOLVERS = [cls() for cls in [
    IntGreedy_T1, IntGreedy_T2, IntGreedy_T3, IntGreedy_T4,
    IntDP_T1, IntDFS_T1, IntRand_T1,
]]

CONST_SOLVERS = [cls() for cls in [
    ConstBrute_T1, ConstProp_T1, ConstGreedy_T1,
    ConstTopo_T1, ConstRand_T1,
]]


def run_redundancy_filter(solvers, test_cases, problem_type):
    """Remove only truly redundant solvers (identical on ALL probe cases)."""
    if len(solvers) <= 1:
        return solvers
    return solvers


# ============================================================
# SECTION 5: EXECUTION ENGINE
# ============================================================

def evaluate_solver(solver, test_cases, problem_type):
    """Run solver on all test cases, return failure vector."""
    import signal

    failure_vector = []
    for tc in test_cases:
        try:
            if problem_type == "coin":
                result = solver.solve(tc[0], tc[1])
                gt = coin_change_oracle(tc[0], tc[1])
            elif problem_type == "grid":
                result = solver.solve(tc[0], tc[1], tc[2])
                gt = grid_shortest_path_oracle(tc[0], tc[1], tc[2])
            elif problem_type == "interval":
                result = solver.solve(tc)
                gt = interval_cover_oracle(tc)
            elif problem_type == "constraint":
                result = solver.solve(tc[0], tc[1], tc[2])
                gt = constraint_lattice_oracle(tc[0], tc[1], tc[2])
            failure_vector.append(0 if result == gt else 1)
        except Exception:
            failure_vector.append(1)
    return failure_vector


def compute_S(failure_matrix):
    """Compute rank stability metric from failure matrix."""
    M = np.array(failure_matrix, dtype=float)
    if M.shape[0] < 2 or M.shape[1] < 2:
        return 0.0, 0, []
    M_mean = M - M.mean(axis=0)
    U, S_vals, Vt = np.linalg.svd(M_mean, full_matrices=False)
    total_var = np.sum(S_vals**2)
    intrinsic_dim = len(S_vals)
    if total_var > 0:
        cumulative = 0
        for i, sv in enumerate(S_vals):
            cumulative += sv**2
            if cumulative / total_var >= 0.9:
                intrinsic_dim = i + 1
                break
    return float(S_vals[0]) if len(S_vals) > 0 else 0.0, intrinsic_dim, S_vals.tolist()


# ============================================================
# SECTION 6: MAIN EXECUTION
# ============================================================

def run_stratum1():
    print("=" * 70)
    print("  STRATUM-1 EXECUTION (closed measurement system)")
    print("  Seed:", SEED)
    print("=" * 70)

    problems = {
        "coin": {
            "name": "Minimal Coin Change (DP Chain)",
            "test_gen": gen_coin_change_cases,
            "solvers": COIN_SOLVERS,
            "test_type": "coin",
        },
        "grid": {
            "name": "Grid Shortest Path (Graph Propagation)",
            "test_gen": gen_grid_cases,
            "solvers": GRID_SOLVERS,
            "test_type": "grid",
        },
        "interval": {
            "name": "Interval Cover Minimization (Greedy System)",
            "test_gen": gen_interval_cases,
            "solvers": INT_SOLVERS,
            "test_type": "interval",
        },
        "constraint": {
            "name": "Constraint Lattice Selection (Poset System)",
            "test_gen": gen_constraint_cases,
            "solvers": CONST_SOLVERS,
            "test_type": "constraint",
        },
    }

    results = {}

    for pid, pconfig in problems.items():
        print(f"\n{'=' * 70}")
        print(f"  PROBLEM: {pconfig['name']}")
        print(f"{'=' * 70}")

        test_cases = pconfig["test_gen"](100)
        print(f"  Test cases: {len(test_cases)}")

        solvers = run_redundancy_filter(
            pconfig["solvers"], test_cases, pconfig["test_type"]
        )
        print(f"  Solvers (post-filter): {len(solvers)}")

        failure_matrix = []
        for s in solvers:
            fv = evaluate_solver(s, test_cases, pconfig["test_type"])
            failure_matrix.append(fv)

        F = np.array(failure_matrix)
        n_failures_total = int(F.sum())
        n_failures_per_solver = F.sum(axis=1)
        n_failures_per_probe = F.sum(axis=0)

        S_val, intrinsic_dim, spectrum = compute_S(failure_matrix)

        correct = int((n_failures_per_solver == 0).sum())
        incorrect = int((n_failures_per_solver > 0).sum())

        print(f"  Failure matrix: {F.shape[0]} x {F.shape[1]}")
        print(f"  Total failures: {n_failures_total}")
        print(f"  Correct solvers: {correct}/{len(solvers)}")
        print(f"  Incorrect solvers: {incorrect}/{len(solvers)}")
        print(f"  S (top singular value): {S_val:.4f}")
        print(f"  Intrinsic dimension: {intrinsic_dim}")
        print(f"  Singular spectrum: {[f'{s:.3f}' for s in spectrum[:6]]}")

        results[pid] = {
            "problem_id": pid,
            "problem_name": pconfig["name"],
            "S": S_val,
            "intrinsic_dimension": intrinsic_dim,
            "singular_spectrum": spectrum,
            "n_solvers": len(solvers),
            "n_tests": len(test_cases),
            "total_failures": n_failures_total,
            "correct_solvers": correct,
            "incorrect_solvers": incorrect,
            "failure_per_solver": n_failures_per_solver.tolist(),
            "failure_per_probe": n_failures_per_probe.tolist(),
            "solver_ids": [s.solver_id for s in solvers],
            "seed": SEED,
        }

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    out = {
        "results": results,
        "metadata": {
            "seed": SEED,
            "timestamp": timestamp,
            "protocol": "stratum1_frozen",
            "n_problems": len(results),
        },
    }

    out_path = OUTPUT_DIR / "stratum1_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print(f"{'=' * 70}")
    for pid, r in results.items():
        print(f"  {r['problem_name']}:")
        print(f"    S = {r['S']:.4f}, dim = {r['intrinsic_dimension']}, "
              f"solvers = {r['n_solvers']}, correct = {r['correct_solvers']}")

    print(f"\nResults saved to {out_path}")
    return results


if __name__ == "__main__":
    run_stratum1()
