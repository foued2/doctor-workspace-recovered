"""
CORRELATION GEOMETRY SPACE

Three independent decorrelation axes:
  α — action corruption (mixture of policies)
  β — state blindness (history corruption)
  γ — bias orthogonalization (strategy decorrelation)

Object: G(α, β, γ) → failure spectrum manifold

Phase transition detectors:
  1. rank discontinuity (Δrank/Δθ)
  2. spectral gap ratio (σ₁/σ₂)
  3. cluster persistence (co-clustering fraction)
  4. subspace rotation (principal angles)
"""
import json
import random
import numpy as np
from pathlib import Path
from collections import deque
from itertools import combinations

SEED = 20260613

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "correlation_geometry"
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
# SECTION 3: THREE-AXIS DECORRELATION KERNELS
# ============================================================

class ActionCorruptor:
    """α-axis: action corruption via policy mixture."""

    def __init__(self, alpha, rng):
        self.alpha = alpha
        self.rng = rng

    def corrupt(self, original_action, null_action):
        if self.rng.random() < self.alpha:
            return null_action
        return original_action


class StateBlindness:
    """β-axis: history/state corruption."""

    def __init__(self, beta, rng):
        self.beta = beta
        self.rng = rng

    def corrupt_state(self, state_vector):
        if self.rng.random() >= self.beta:
            return state_vector
        corrupted = list(state_vector)
        n_corrupt = max(1, int(len(corrupted) * self.beta))
        indices = self.rng.sample(range(len(corrupted)), min(n_corrupt, len(corrupted)))
        for i in indices:
            corrupted[i] = self.rng.choice([0, 1])
        return tuple(corrupted)

    def corrupt_history(self, history):
        if self.rng.random() >= self.beta:
            return history
        if not history:
            return history
        n_keep = max(1, int(len(history) * (1 - self.beta)))
        return history[-n_keep:]


class BiasOrthogonalizer:
    """γ-axis: strategy/utility landscape reshuffling."""

    def __init__(self, gamma, rng):
        self.gamma = gamma
        self.rng = rng

    def corrupt_preference(self, preference_ordering):
        if self.rng.random() >= self.gamma:
            return preference_ordering
        n = len(preference_ordering)
        n_shuffle = max(1, int(n * self.gamma))
        indices = self.rng.sample(range(n), min(n_shuffle, n))
        shuffled_vals = [preference_ordering[i] for i in indices]
        self.rng.shuffle(shuffled_vals)
        result = list(preference_ordering)
        for idx, val in zip(indices, shuffled_vals):
            result[idx] = val
        return result


# ============================================================
# SECTION 4: INTERPOLATED SOLVERS (3-axis)
# ============================================================

class CoinSolver3Axis:
    def __init__(self, solver_id, strategy, alpha, beta, gamma, rng_seed):
        self.solver_id = solver_id
        self.strategy = strategy
        self.rng = random.Random(rng_seed)
        self.alpha_corruptor = ActionCorruptor(alpha, self.rng)
        self.state_blind = StateBlindness(beta, self.rng)
        self.bias_ortho = BiasOrthogonalizer(gamma, self.rng)

    def solve(self, amount, coins):
        if amount == 0:
            return 0

        preference = self._get_preference(coins)
        corrupted_pref = self.bias_ortho.corrupt_preference(preference)

        state = (0, 0)
        spent = 0
        for _ in range(amount + 10):
            if spent == amount:
                return _
            corrupted_state = self.state_blind.corrupt_state(state)
            original_action = self._original_choice(corrupted_pref, amount - spent)
            null_action = self._null_choice(coins, amount - spent)
            action = self.alpha_corruptor.corrupt(original_action, null_action)
            if action is None or action <= 0:
                break
            spent += action
            state = (spent, _ + 1)
        return -1 if spent != amount else _

    def _get_preference(self, coins):
        if self.strategy == 'greedy_largest':
            return sorted(coins, reverse=True)
        elif self.strategy == 'greedy_smallest':
            return sorted(coins)
        else:
            return sorted(coins, reverse=True)

    def _original_choice(self, preference, remaining):
        for c in preference:
            if c <= remaining:
                return c
        return None

    def _null_choice(self, coins, remaining):
        legal = [c for c in coins if c <= remaining]
        if not legal:
            return None
        return min(legal)


class GridSolver3Axis:
    def __init__(self, solver_id, strategy, alpha, beta, gamma, rng_seed):
        self.solver_id = solver_id
        self.strategy = strategy
        self.rng = random.Random(rng_seed)
        self.alpha_corruptor = ActionCorruptor(alpha, self.rng)
        self.state_blind = StateBlindness(beta, self.rng)
        self.bias_ortho = BiasOrthogonalizer(gamma, self.rng)

    def solve(self, grid, start, target):
        if start == target:
            return 0
        n, m = len(grid), len(grid[0])
        sx, sy = start
        tx, ty = target
        if grid[sx][sy] == 1 or grid[tx][ty] == 1:
            return -1

        visited = {(sx, sy)}
        x, y = sx, sy
        d = 0
        max_steps = n * m + 1

        while (x, y) != (tx, ty) and d < max_steps:
            neighbors = self._get_neighbors(grid, x, y, visited, n, m)
            if not neighbors:
                break

            corrupted_visited = self.state_blind.corrupt_history(list(visited))
            preference = self._get_preference(neighbors, tx, ty)
            corrupted_pref = self.bias_ortho.corrupt_preference(preference)
            original_action = corrupted_pref[0] if corrupted_pref else neighbors[0]
            null_action = self._null_choice(neighbors, tx, ty)
            action = self.alpha_corruptor.corrupt(original_action, null_action)

            if action not in neighbors:
                action = neighbors[0]

            visited.add(action)
            x, y = action
            d += 1

        return d if (x, y) == (tx, ty) else -1

    def _get_neighbors(self, grid, x, y, visited, n, m):
        neighbors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                neighbors.append((nx, ny))
        return neighbors

    def _get_preference(self, neighbors, tx, ty):
        if self.strategy == 'greedy':
            return sorted(neighbors, key=lambda p: abs(p[0] - tx) + abs(p[1] - ty))
        elif self.strategy == 'bfs':
            return list(neighbors)
        else:
            return list(reversed(neighbors))

    def _null_choice(self, neighbors, tx, ty):
        return max(neighbors, key=lambda p: abs(p[0] - tx) + abs(p[1] - ty))


class IntervalSolver3Axis:
    def __init__(self, solver_id, strategy, alpha, beta, gamma, rng_seed):
        self.solver_id = solver_id
        self.strategy = strategy
        self.rng = random.Random(rng_seed)
        self.alpha_corruptor = ActionCorruptor(alpha, self.rng)
        self.state_blind = StateBlindness(beta, self.rng)
        self.bias_ortho = BiasOrthogonalizer(gamma, self.rng)

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

            corrupted_used = self.state_blind.corrupt_history(list(used))
            preference = self._get_preference(valid_indices, sorted_ints)
            corrupted_pref = self.bias_ortho.corrupt_preference(preference)
            original_action = corrupted_pref[0] if corrupted_pref else valid_indices[0]
            null_action = self._null_choice(valid_indices, sorted_ints)
            action = self.alpha_corruptor.corrupt(original_action, null_action)

            if action not in valid_indices:
                action = valid_indices[0]

            used.add(action)
            if sorted_ints[action][1] > current_end:
                current_end = sorted_ints[action][1]
                count += 1

        return count if current_end >= target_end else -1

    def _get_preference(self, valid_indices, sorted_ints):
        if self.strategy == 'greedy':
            return sorted(valid_indices, key=lambda i: sorted_ints[i][1], reverse=True)
        else:
            return list(valid_indices)

    def _null_choice(self, valid_indices, sorted_ints):
        return min(valid_indices, key=lambda i: sorted_ints[i][1])


class ConstraintSolver3Axis:
    def __init__(self, solver_id, strategy, alpha, beta, gamma, rng_seed):
        self.solver_id = solver_id
        self.strategy = strategy
        self.rng = random.Random(rng_seed)
        self.alpha_corruptor = ActionCorruptor(alpha, self.rng)
        self.state_blind = StateBlindness(beta, self.rng)
        self.bias_ortho = BiasOrthogonalizer(gamma, self.rng)

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

            corrupted_selected = self.state_blind.corrupt_history(list(selected))
            preference = self._get_preference(candidates, elements)
            corrupted_pref = self.bias_ortho.corrupt_preference(preference)
            original_action = corrupted_pref[0] if corrupted_pref else candidates[0]
            null_action = self._null_choice(candidates)
            action = self.alpha_corruptor.corrupt(original_action, null_action)

            if action not in candidates:
                action = candidates[0]

            selected.add(action)

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

    def _get_preference(self, candidates, elements):
        if self.strategy == 'min_first':
            return sorted(candidates, key=lambda i: elements[i])
        elif self.strategy == 'max_first':
            return sorted(candidates, key=lambda i: elements[i], reverse=True)
        else:
            return list(candidates)

    def _null_choice(self, candidates):
        return candidates[self.rng.randint(0, len(candidates) - 1)]


# ============================================================
# SECTION 5: GEOMETRY COMPUTATION
# ============================================================

def compute_geometry(matrix):
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
            'spectral_gap': 0.0,
        }
    cumvar = np.cumsum(s ** 2) / total_var
    dim = int(np.searchsorted(cumvar, 0.90) + 1)
    dim = min(dim, len(s))
    probs = s ** 2 / total_var
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log2(probs))
    spectral_gap = s[0] / s[1] if len(s) > 1 and s[1] > 0 else float('inf')
    return {
        'spectrum': s.tolist()[:6],
        'intrinsic_dim': dim,
        'spectral_entropy': float(entropy),
        'S': float(s[0]),
        'spectral_gap': float(spectral_gap),
    }


def compute_cluster_persistence(matrices):
    """Fraction of solver pairs that stay co-clustered across all matrices."""
    if len(matrices) < 2:
        return 1.0
    n_solvers = matrices[0].shape[0]
    n_pairs = 0
    co_clustered = 0
    for i in range(n_solvers):
        for j in range(i + 1, n_solvers):
            n_pairs += 1
            same_cluster = True
            for m in matrices:
                row_i = m[i, :]
                row_j = m[j, :]
                if not np.array_equal(row_i, row_j):
                    same_cluster = False
                    break
            if same_cluster:
                co_clustered += 1
    return co_clustered / n_pairs if n_pairs > 0 else 0.0


def compute_subspace_alignment(B0, B1):
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
# SECTION 6: PHASE TRANSITION DETECTORS
# ============================================================

def detect_transitions(trajectory):
    """Detect phase transitions along a trajectory.

    Returns list of (index, detector_name, magnitude) for detected transitions.
    """
    transitions = []
    if len(trajectory) < 2:
        return transitions

    for i in range(1, len(trajectory)):
        prev = trajectory[i - 1]
        curr = trajectory[i]

        rank_change = abs(curr['intrinsic_dim'] - prev['intrinsic_dim'])
        if rank_change >= 1:
            transitions.append((i, 'rank_discontinuity', rank_change))

        if prev['spectral_gap'] > 0 and curr['spectral_gap'] > 0:
            gap_change = abs(curr['spectral_gap'] - prev['spectral_gap']) / prev['spectral_gap']
            if gap_change > 0.5:
                transitions.append((i, 'spectral_gap_shift', gap_change))

        entropy_change = abs(curr['spectral_entropy'] - prev['spectral_entropy'])
        if entropy_change > 0.3:
            transitions.append((i, 'entropy_shift', entropy_change))

    return transitions


# ============================================================
# SECTION 7: SOLVER ENSEMBLE GENERATORS
# ============================================================

def get_coin_solvers(alpha, beta, gamma, rng_seed):
    strategies = ['greedy_largest', 'greedy_smallest', 'greedy_largest']
    return [CoinSolver3Axis(f'cc_{i}', s, alpha, beta, gamma, rng_seed + i * 100)
            for i, s in enumerate(strategies)]


def get_grid_solvers(alpha, beta, gamma, rng_seed):
    strategies = ['greedy', 'bfs', 'dfs']
    return [GridSolver3Axis(f'gp_{s}', s, alpha, beta, gamma, rng_seed + i * 100)
            for i, s in enumerate(strategies)]


def get_interval_solvers(alpha, beta, gamma, rng_seed):
    strategies = ['greedy', 'first']
    return [IntervalSolver3Axis(f'ic_{s}', s, alpha, beta, gamma, rng_seed + i * 100)
            for i, s in enumerate(strategies)]


def get_constraint_solvers(alpha, beta, gamma, rng_seed):
    strategies = ['min_first', 'max_first']
    return [ConstraintSolver3Axis(f'cl_{s}', s, alpha, beta, gamma, rng_seed + i * 100)
            for i, s in enumerate(strategies)]


# ============================================================
# SECTION 8: MAIN EXPERIMENT
# ============================================================

def run_experiment():
    alpha_grid = [0.0, 0.25, 0.5, 0.75, 1.0]
    beta_grid = [0.0, 0.25, 0.5, 0.75]
    gamma_grid = [0.0, 0.25, 0.5, 0.75]
    n_seeds = 2

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

        cube_results = {}

        for alpha in alpha_grid:
            for beta in beta_grid:
                for gamma in gamma_grid:
                    theta = (alpha, beta, gamma)
                    seed_results = []

                    for seed_offset in range(n_seeds):
                        seed = SEED + seed_offset * 10000
                        solvers = prob['solvers_fn'](alpha, beta, gamma, seed)

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
                            'total_failures': int(matrix.sum()),
                            **geom,
                        })

                    avg_geom = {}
                    for key in ['S', 'intrinsic_dim', 'spectral_entropy', 'spectral_gap']:
                        vals = [r[key] for r in seed_results]
                        avg_geom[key] = float(np.mean(vals))
                        avg_geom[key + '_std'] = float(np.std(vals))

                    avg_geom['spectrum'] = seed_results[0]['spectrum'] if seed_results else []

                    cube_results[theta] = avg_geom

        all_results[prob_name] = cube_results

        print('  Cube scanned: ' + str(len(cube_results)) + ' points')

        # Find transitions along each axis
        print()
        print('  TRANSITIONS ALONG ALPHA (fixed beta=0, gamma=0):')
        trajectory = []
        for alpha in alpha_grid:
            theta = (alpha, 0.0, 0.0)
            if theta in cube_results:
                trajectory.append(cube_results[theta])
        transitions = detect_transitions(trajectory)
        if transitions:
            for idx, det, mag in transitions:
                print('    at alpha=' + str(alpha_grid[idx]) + ': ' + det + ' (mag=' + str(round(mag, 3)) + ')')
        else:
            print('    no transitions detected')

        print()
        print('  TRANSITIONS ALONG BETA (fixed alpha=0, gamma=0):')
        trajectory = []
        for beta in beta_grid:
            theta = (0.0, beta, 0.0)
            if theta in cube_results:
                trajectory.append(cube_results[theta])
        transitions = detect_transitions(trajectory)
        if transitions:
            for idx, det, mag in transitions:
                print('    at beta=' + str(beta_grid[idx]) + ': ' + det + ' (mag=' + str(round(mag, 3)) + ')')
        else:
            print('    no transitions detected')

        print()
        print('  TRANSITIONS ALONG GAMMA (fixed alpha=0, beta=0):')
        trajectory = []
        for gamma in gamma_grid:
            theta = (0.0, 0.0, gamma)
            if theta in cube_results:
                trajectory.append(cube_results[theta])
        transitions = detect_transitions(trajectory)
        if transitions:
            for idx, det, mag in transitions:
                print('    at gamma=' + str(gamma_grid[idx]) + ': ' + det + ' (mag=' + str(round(mag, 3)) + ')')
        else:
            print('    no transitions detected')
        print()

    # Save results
    output = {
        'cube_results': {k: {str(kk): vv for kk, vv in v.items()} for k, v in all_results.items()},
        'metadata': {
            'alpha_grid': alpha_grid,
            'beta_grid': beta_grid,
            'gamma_grid': gamma_grid,
            'n_seeds': n_seeds,
            'seed_base': SEED,
        }
    }

    with open(OUTPUT_DIR / 'correlation_geometry_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print('=' * 60)
    print('  SAVED: ' + str(OUTPUT_DIR / 'correlation_geometry_results.json'))
    print('=' * 60)


if __name__ == '__main__':
    run_experiment()
