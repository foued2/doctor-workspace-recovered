"""
OPERATOR INTERPOLATION HARNESS

Mixture-of-policies interpolation: π_{s,α} = (1-α)π_s + απ_0

At each decision point:
  if random() < α: take null-policy action
  else: take original solver action

α grid: {0, 0.1, 0.25, 0.5, 0.75, 1.0}

Measures: spectrum trajectory, subspace alignment, rank collapse
"""
import json
import random
import numpy as np
from pathlib import Path
from collections import deque
from itertools import combinations

SEED = 20260613

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "operator_interpolation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SECTION 1: ORACLES
# ============================================================

def coin_oracle(amount, coins):
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


def grid_oracle(grid, start, target):
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


def interval_oracle(intervals):
    if not intervals:
        return 0
    sorted_ints = sorted(intervals, key=lambda x: x[0])
    target_start = sorted_ints[0][0]
    target_end = max(e for s, e in intervals)
    if target_start >= target_end:
        return 1 if any(e >= target_end for s, e in intervals) else -1
    count = 0
    current_end = target_start - 1
    i = 0
    while current_end < target_end and i < len(sorted_ints):
        best_end = current_end
        while i < len(sorted_ints) and sorted_ints[i][0] <= current_end + 1:
            if sorted_ints[i][1] > best_end:
                best_end = sorted_ints[i][1]
            i += 1
        if best_end == current_end:
            return -1
        current_end = best_end
        count += 1
    return count if current_end >= target_end else -1


def constraint_oracle(elements, constraints, k):
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
# SECTION 2: TEST CASE GENERATORS (frozen)
# ============================================================

def gen_coin_cases(n=100):
    cases = []
    rng = random.Random(SEED)
    for _ in range(85):
        amt = rng.randint(1, 200)
        num_coins = rng.randint(1, 6)
        coins = sorted(set(rng.randint(1, 50) for _ in range(num_coins)))
        cases.append((amt, coins))
    anchors = [
        (0, [1]), (1, [1]), (11, [1, 2, 5]), (100, [1]), (7, [2, 3]),
        (30, [1, 5, 10, 25]), (1, [2]), (41, [1, 5, 10, 25]),
        (100, [2, 5, 10]), (50, [1, 2, 5, 10]), (3, [2]), (8, [1, 3, 4]),
        (12, [1, 5, 10]), (99, [1, 2, 5]), (200, [1, 3, 7]),
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
        cases.append((grid, (0, 0), (rows - 1, cols - 1)))
    anchors = [
        ([[0]], (0, 0), (0, 0)),
        ([[0, 0], [0, 0]], (0, 0), (1, 1)),
        ([[0, 1], [1, 0]], (0, 0), (1, 1)),
        ([[0] * 5 for _ in range(5)], (0, 0), (4, 4)),
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
        ([[0, 0], [0, 0]], (0, 0), (1, 1)),
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
        [(0, 10)], [(0, 5), (5, 10)], [(0, 3), (2, 7), (6, 10)],
        [(i, i + 1) for i in range(10)], [(0, 100)],
        [(0, 1), (0, 2), (0, 3)], [(10, 20), (5, 15), (0, 25)],
        [(0, 1), (2, 3), (4, 5)], [(0, 10), (5, 15), (10, 20)],
        [(i, i + 5) for i in range(0, 50, 3)],
        [(0, 0)], [(5, 5)],
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
# SECTION 3: NULL POLICIES (one per problem class)
# ============================================================

class NullPolicy:
    """Fixed, legal, weak, decorrelated null policy.

    Key: makes choices OPPOSITE to the original solver's strategy.
    This ensures true decorrelation, not just noise.
    """

    def __init__(self, problem_type, rng_seed=SEED + 9999):
        self.problem_type = problem_type
        self.rng = random.Random(rng_seed)

    def coin_action(self, amount, coins, state):
        """Opposite of greedy: pick smallest coin (worst for DP)."""
        legal = [c for c in coins if c <= amount - state['spent']]
        if not legal:
            return None
        return min(legal)

    def grid_action(self, grid, current, target, visited):
        """Opposite of heuristic: pick neighbor FARTHEST from target."""
        n, m = len(grid), len(grid[0])
        x, y = current
        tx, ty = target
        neighbors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                neighbors.append((nx, ny))
        if not neighbors:
            return None
        return max(neighbors, key=lambda p: abs(p[0] - tx) + abs(p[1] - ty))

    def interval_action(self, intervals, current_end, used):
        """Opposite of greedy: pick interval with SMALLEST end."""
        valid_indices = []
        for i, (s, e) in enumerate(intervals):
            if i not in used and s <= current_end + 1:
                valid_indices.append(i)
        if not valid_indices:
            return None
        return min(valid_indices, key=lambda i: intervals[i][1])

    def constraint_action(self, elements, constraints, selected, k):
        """Random extension (already decorrelated)."""
        if len(selected) >= k:
            return None
        candidates = []
        for i in range(len(elements)):
            if i in selected:
                continue
            test = selected | {i}
            valid = True
            for a, b in constraints:
                if a in test and b in test and elements[a] >= elements[b]:
                    valid = False
                    break
            if valid:
                candidates.append(i)
        if not candidates:
            return None
        return self.rng.choice(candidates)


# ============================================================
# SECTION 4: INTERPOLATED SOLVERS
# ============================================================

class InterpolatedCoinSolver:
    def __init__(self, solver_id, original_fn, null_policy, alpha):
        self.solver_id = solver_id
        self.original_fn = original_fn
        self.null = null_policy
        self.alpha = alpha
        self.rng = random.Random(hash((solver_id, alpha)) % 2**31)

    def solve(self, amount, coins):
        if self.alpha == 0:
            return self.original_fn(amount, coins)
        if self.alpha == 1:
            return self._null_solve(amount, coins)

        state = {'spent': 0}
        total = 0
        remaining = amount
        for _ in range(amount + 10):
            if remaining == 0:
                return total
            if self.rng.random() < self.alpha:
                c = self.null.coin_action(amount, coins, state)
                if c is None:
                    break
            else:
                c = self.original_fn_choice(amount, coins, remaining)
                if c is None:
                    break
            remaining -= c
            state['spent'] += c
            total += 1
            if remaining < 0:
                return -1
        return -1 if remaining != 0 else total

    def _null_solve(self, amount, coins):
        state = {'spent': 0}
        total = 0
        remaining = amount
        for _ in range(amount + 10):
            if remaining == 0:
                return total
            c = self.null.coin_action(amount, coins, state)
            if c is None:
                break
            remaining -= c
            state['spent'] += c
            total += 1
            if remaining < 0:
                return -1
        return -1 if remaining != 0 else total

    def original_fn_choice(self, amount, coins, remaining):
        """Extract a single choice from original solver logic."""
        coins_sorted = sorted(coins, reverse=True)
        for c in coins_sorted:
            if c <= remaining:
                return c
        return None


class InterpolatedGridSolver:
    def __init__(self, solver_id, strategy, null_policy, alpha):
        self.solver_id = solver_id
        self.strategy = strategy
        self.null = null_policy
        self.alpha = alpha
        self.rng = random.Random(hash((solver_id, alpha)) % 2**31)

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1

        if self.alpha == 0:
            return self._original_solve(grid, start, target)
        if self.alpha == 1:
            return self._null_solve(grid, start, target)

        q = deque([(sx, sy, 0)])
        visited = {(sx, sy)}
        while q:
            x, y, d = q.popleft()
            neighbors = self._get_neighbors(grid, x, y, visited, n, m)
            if not neighbors:
                continue

            if self.rng.random() < self.alpha:
                nx, ny = self.null.grid_action(grid, (x, y), target, visited)
                if nx is None:
                    continue
            else:
                nx, ny = self._original_choice(grid, (x, y), target, neighbors, n, m)

            if (nx, ny) == (tx, ty):
                return d + 1
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
        return -1

    def _get_neighbors(self, grid, x, y, visited, n, m):
        neighbors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                neighbors.append((nx, ny))
        return neighbors

    def _original_choice(self, grid, current, target, neighbors, n, m):
        tx, ty = target
        if self.strategy == 'bfs':
            return neighbors[0]
        elif self.strategy == 'greedy':
            best = min(neighbors, key=lambda p: abs(p[0] - tx) + abs(p[1] - ty))
            return best
        elif self.strategy == 'dfs':
            return neighbors[-1]
        else:
            return neighbors[0]

    def _original_solve(self, grid, start, target):
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        q = deque([(sx, sy, 0)])
        visited = {(sx, sy)}
        while q:
            x, y, d = q.popleft()
            neighbors = self._get_neighbors(grid, x, y, visited, n, m)
            for nx, ny in neighbors:
                if (nx, ny) == (tx, ty):
                    return d + 1
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
        return -1

    def _null_solve(self, grid, start, target):
        n, m = len(grid), len(grid[0])
        q = deque([(start[0], start[1], 0)])
        visited = {start}
        while q:
            x, y, d = q.popleft()
            action = self.null.grid_action(grid, (x, y), target, visited)
            if action is None:
                continue
            nx, ny = action
            if (nx, ny) == target:
                return d + 1
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
        return -1


class InterpolatedIntervalSolver:
    def __init__(self, solver_id, strategy, null_policy, alpha):
        self.solver_id = solver_id
        self.strategy = strategy
        self.null = null_policy
        self.alpha = alpha
        self.rng = random.Random(hash((solver_id, alpha)) % 2**31)

    def solve(self, intervals):
        if not intervals:
            return 0
        sorted_ints = sorted(intervals, key=lambda x: x[0])
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = sorted_ints[0][0] - 1
        used = set()
        i = 0

        while current_end < target_end and i < len(sorted_ints):
            valid_indices = []
            while i < len(sorted_ints) and sorted_ints[i][0] <= current_end + 1:
                valid_indices.append(i)
                i += 1

            if not valid_indices:
                break

            if self.rng.random() < self.alpha:
                chosen_idx = self.null.interval_action(sorted_ints, current_end, used)
                if chosen_idx is None or chosen_idx not in valid_indices:
                    chosen_idx = valid_indices[0]
            else:
                chosen_idx = self._original_choice(valid_indices, sorted_ints)

            used.add(chosen_idx)
            if sorted_ints[chosen_idx][1] > current_end:
                current_end = sorted_ints[chosen_idx][1]
                count += 1

        return count if current_end >= target_end else -1

    def _original_choice(self, valid_indices, sorted_ints):
        if self.strategy == 'greedy':
            return max(valid_indices, key=lambda i: sorted_ints[i][1])
        elif self.strategy == 'first':
            return valid_indices[0]
        else:
            return valid_indices[0]


class InterpolatedConstraintSolver:
    def __init__(self, solver_id, strategy, null_policy, alpha):
        self.solver_id = solver_id
        self.strategy = strategy
        self.null = null_policy
        self.alpha = alpha
        self.rng = random.Random(hash((solver_id, alpha)) % 2**31)

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        if k > len(elements):
            return False

        selected = set()
        for _ in range(k):
            candidates = self._get_candidates(elements, constraints, selected)
            if not candidates:
                return False

            if self.rng.random() < self.alpha:
                choice = self.null.constraint_action(elements, constraints, selected, k)
                if choice is None or choice not in candidates:
                    choice = candidates[0]
            else:
                choice = self._original_choice(candidates, elements)

            selected.add(choice)

        for a, b in constraints:
            if a in selected and b in selected:
                if elements[a] >= elements[b]:
                    return False
        return True

    def _get_candidates(self, elements, constraints, selected):
        candidates = []
        for i in range(len(elements)):
            if i in selected:
                continue
            test = selected | {i}
            valid = True
            for a, b in constraints:
                if a in test and b in test and elements[a] >= elements[b]:
                    valid = False
                    break
            if valid:
                candidates.append(i)
        return candidates

    def _original_choice(self, candidates, elements):
        if self.strategy == 'min_first':
            return min(candidates, key=lambda i: elements[i])
        elif self.strategy == 'max_first':
            return max(candidates, key=lambda i: elements[i])
        else:
            return candidates[0]


# ============================================================
# SECTION 5: SVD COMPUTATION
# ============================================================

def compute_geometry(matrix):
    """Compute spectrum, intrinsic dimension, subspace alignment."""
    m = matrix.astype(float)
    m_centered = m - m.mean(axis=1, keepdims=True)
    U, s, Vt = np.linalg.svd(m_centered, full_matrices=False)
    total_var = np.sum(s ** 2)
    if total_var == 0:
        return {
            'spectrum': [0.0] * min(6, matrix.shape[0]),
            'intrinsic_dim': matrix.shape[0],
            'spectral_entropy': 0.0,
            'S': 0.0,
        }
    cumvar = np.cumsum(s ** 2) / total_var
    dim = int(np.searchsorted(cumvar, 0.90) + 1)
    dim = min(dim, len(s))
    probs = s ** 2 / total_var
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log2(probs))
    return {
        'spectrum': s.tolist()[:6],
        'intrinsic_dim': dim,
        'spectral_entropy': float(entropy),
        'S': float(s[0]),
    }


def subspace_alignment(B0, B1):
    """Cosine of principal angle between row spaces."""
    if B0.shape[0] < 2 or B1.shape[0] < 2:
        return 0.0
    U0, s0, _ = np.linalg.svd(B0.astype(float) - B0.astype(float).mean(axis=1, keepdims=True), full_matrices=False)
    U1, s1, _ = np.linalg.svd(B1.astype(float) - B1.astype(float).mean(axis=1, keepdims=True), full_matrices=False)
    k = min(3, U0.shape[1], U1.shape[1])
    if k == 0:
        return 0.0
    U0_k = U0[:, :k]
    U1_k = U1[:, :k]
    M = U0_k.T @ U1_k
    _, sigma, _ = np.linalg.svd(M)
    return float(np.mean(sigma[:k]))


# ============================================================
# SECTION 6: SOLVER ENSEMBLES PER PROBLEM
# ============================================================

def get_coin_solvers(null_policy, alpha):
    """Return interpolated coin solvers."""
    def greedy_largest(amount, coins):
        for c in sorted(coins, reverse=True):
            if c <= amount:
                return c
        return None

    def greedy_smallest(amount, coins):
        for c in sorted(coins):
            if c <= amount:
                return c
        return None

    def dp_best(amount, coins):
        for c in sorted(coins):
            if c <= amount:
                return c
        return None

    strategies = [
        ('cc_greedy_largest', greedy_largest),
        ('cc_greedy_smallest', greedy_smallest),
        ('cc_dp_first', dp_best),
    ]
    return [InterpolatedCoinSolver(sid, fn, null_policy, alpha) for sid, fn in strategies]


def get_grid_solvers(null_policy, alpha):
    """Return interpolated grid solvers."""
    strategies = ['bfs', 'greedy', 'dfs']
    return [InterpolatedGridSolver(f'gp_{s}', s, null_policy, alpha) for s in strategies]


def get_interval_solvers(null_policy, alpha):
    """Return interpolated interval solvers."""
    strategies = ['greedy', 'first']
    return [InterpolatedIntervalSolver(f'ic_{s}', s, null_policy, alpha) for s in strategies]


def get_constraint_solvers(null_policy, alpha):
    """Return interpolated constraint solvers."""
    strategies = ['min_first', 'max_first']
    return [InterpolatedConstraintSolver(f'cl_{s}', s, null_policy, alpha) for s in strategies]


# ============================================================
# SECTION 7: MAIN EXPERIMENT
# ============================================================

def run_experiment():
    alpha_grid = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]
    n_seeds = 3

    problems = {
        'coin': {
            'cases_fn': gen_coin_cases,
            'oracle_fn': lambda tc: coin_oracle(tc[0], tc[1]),
            'solve_fn': lambda s, tc: s.solve(tc[0], tc[1]),
            'solvers_fn': get_coin_solvers,
        },
        'grid': {
            'cases_fn': gen_grid_cases,
            'oracle_fn': lambda tc: grid_oracle(tc[0], tc[1], tc[2]),
            'solve_fn': lambda s, tc: s.solve(tc[0], tc[1], tc[2]),
            'solvers_fn': get_grid_solvers,
        },
        'interval': {
            'cases_fn': gen_interval_cases,
            'oracle_fn': lambda tc: interval_oracle(tc),
            'solve_fn': lambda s, tc: s.solve(tc),
            'solvers_fn': get_interval_solvers,
        },
        'constraint': {
            'cases_fn': gen_constraint_cases,
            'oracle_fn': lambda tc: constraint_oracle(tc[0], tc[1], tc[2]),
            'solve_fn': lambda s, tc: s.solve(tc[0], tc[1], tc[2]),
            'solvers_fn': get_constraint_solvers,
        },
    }

    all_results = {}

    for prob_name, prob in problems.items():
        print('=' * 60)
        print('  PROBLEM: ' + prob_name.upper())
        print('=' * 60)
        cases = prob['cases_fn']()
        oracle_fn = prob['oracle_fn']
        solve_fn = prob['solve_fn']

        alpha_results = []

        for alpha in alpha_grid:
            print('  alpha = ' + str(alpha) + ' ...', end=' ', flush=True)
            seed_results = []

            for seed_offset in range(n_seeds):
                seed = SEED + seed_offset * 10000
                rng = random.Random(seed)
                null = NullPolicy(prob_name, rng_seed=seed + 5000)
                solvers = prob['solvers_fn'](null, alpha)

                matrix = np.zeros((len(solvers), len(cases)), dtype=int)
                for si, s in enumerate(solvers):
                    for ci, tc in enumerate(cases):
                        oracle_val = oracle_fn(tc)
                        try:
                            solver_val = solve_fn(s, tc)
                            matrix[si, ci] = 0 if solver_val == oracle_val else 1
                        except Exception:
                            matrix[si, ci] = 1

                geom = compute_geometry(matrix)
                seed_results.append({
                    'seed': seed,
                    'matrix_shape': list(matrix.shape),
                    'total_failures': int(matrix.sum()),
                    **geom,
                })

            avg_S = np.mean([r['S'] for r in seed_results])
            avg_dim = np.mean([r['intrinsic_dim'] for r in seed_results])
            avg_entropy = np.mean([r['spectral_entropy'] for r in seed_results])
            avg_failures = np.mean([r['total_failures'] for r in seed_results])
            std_S = np.std([r['S'] for r in seed_results])

            alpha_results.append({
                'alpha': alpha,
                'avg_S': float(avg_S),
                'std_S': float(std_S),
                'avg_dim': float(avg_dim),
                'avg_entropy': float(avg_entropy),
                'avg_failures': float(avg_failures),
                'seeds': seed_results,
            })

            print('S=' + str(round(avg_S, 3)) + ' dim=' + str(round(avg_dim, 1)) +
                  ' entropy=' + str(round(avg_entropy, 3)) + ' failures=' + str(int(avg_failures)))

        all_results[prob_name] = alpha_results

        print()
        print('  Trajectory: alpha -> S')
        for ar in alpha_results:
            print('    ' + str(ar['alpha']) + ' -> ' + str(round(ar['avg_S'], 3)) +
                  ' (std=' + str(round(ar['std_S'], 3)) + ')')
        print()

    # Compute subspace alignment against alpha=0
    print('=' * 60)
    print('  SUBSPACE ALIGNMENT vs alpha=0')
    print('=' * 60)

    alignment_results = {}
    for prob_name, prob in problems.items():
        cases = prob['cases_fn']()
        oracle_fn = prob['oracle_fn']
        solve_fn = prob['solve_fn']

        null = NullPolicy(prob_name)
        solvers_a0 = prob['solvers_fn'](null, 0.0)

        matrix_a0 = np.zeros((len(solvers_a0), len(cases)), dtype=int)
        for si, s in enumerate(solvers_a0):
            for ci, tc in enumerate(cases):
                oracle_val = oracle_fn(tc)
                try:
                    solver_val = solve_fn(s, tc)
                    matrix_a0[si, ci] = 0 if solver_val == oracle_val else 1
                except Exception:
                    matrix_a0[si, ci] = 1

        alignments = []
        for alpha in alpha_grid:
            if alpha == 0.0:
                alignments.append(1.0)
                continue

            solvers_a = prob['solvers_fn'](null, alpha)
            matrix_a = np.zeros((len(solvers_a), len(cases)), dtype=int)
            for si, s in enumerate(solvers_a):
                for ci, tc in enumerate(cases):
                    oracle_val = oracle_fn(tc)
                    try:
                        solver_val = solve_fn(s, tc)
                        matrix_a[si, ci] = 0 if solver_val == oracle_val else 1
                    except Exception:
                        matrix_a[si, ci] = 1

            align = subspace_alignment(matrix_a0, matrix_a)
            alignments.append(align)

        alignment_results[prob_name] = dict(zip(alpha_grid, alignments))
        print('  ' + prob_name + ':')
        for a, align in zip(alpha_grid, alignments):
            print('    alpha=' + str(a) + ' alignment=' + str(round(align, 4)))

    # Save results
    output = {
        'trajectories': all_results,
        'alignments': alignment_results,
        'metadata': {
            'alpha_grid': alpha_grid,
            'n_seeds': n_seeds,
            'seed_base': SEED,
        }
    }

    with open(OUTPUT_DIR / 'operator_interpolation_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print('=' * 60)
    print('  SAVED: ' + str(OUTPUT_DIR / 'operator_interpolation_results.json'))
    print('=' * 60)


if __name__ == '__main__':
    run_experiment()
