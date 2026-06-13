"""
ORTHOGONAL SOLVER ENSEMBLE EXPERIMENT

Test: Does the equivalence relation itself change under perturbation of the observer ensemble?

Approach:
1. Construct solver ensembles with enforced orthogonality in failure directions
2. Compare quotient geometry (equivalence relations) between correlated and decorrelated ensembles
3. Classify: structure invariant (Outcome 1) vs structure instability (Outcome 2)
"""
import json
import random
import numpy as np
from pathlib import Path
from collections import deque
from itertools import combinations

SEED = 20260613
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "orthogonal_ensemble"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SECTION 1: ORACLES + TEST GENERATORS (frozen)
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


def gen_coin_cases():
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


def gen_grid_cases():
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


def gen_interval_cases():
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


def gen_constraint_cases():
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
# SECTION 2: CORRELATED SOLVER ENSEMBLES (original)
# ============================================================

class CorrelatedCoinSolver:
    def __init__(self, solver_id, strategy, rng_seed):
        self.solver_id = solver_id
        self.rng = random.Random(rng_seed)
        self.strategy = strategy

    def solve(self, amount, coins):
        if amount == 0:
            return 0
        if self.strategy == 'greedy_largest':
            for c in sorted(coins, reverse=True):
                if c <= amount:
                    return 1 + self.solve(amount - c, coins)
            return -1
        elif self.strategy == 'greedy_smallest':
            for c in sorted(coins):
                if c <= amount:
                    return 1 + self.solve(amount - c, coins)
            return -1
        else:
            INF = 10**9
            dp = [INF] * (amount + 1)
            dp[0] = 0
            for i in range(1, amount + 1):
                for c in coins:
                    if i - c >= 0 and dp[i - c] + 1 < dp[i]:
                        dp[i] = dp[i - c] + 1
            return -1 if dp[amount] == INF else dp[amount]


class CorrelatedGridSolver:
    def __init__(self, solver_id, strategy, rng_seed):
        self.solver_id = solver_id
        self.rng = random.Random(rng_seed)
        self.strategy = strategy

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
            neighbors = []
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == 0 and (nx, ny) not in visited:
                    neighbors.append((nx, ny))
            if self.strategy == 'greedy':
                neighbors.sort(key=lambda p: abs(p[0] - tx) + abs(p[1] - ty))
            elif self.strategy == 'reverse':
                neighbors.reverse()
            for nx, ny in neighbors:
                if (nx, ny) == (tx, ty):
                    return d + 1
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
        return -1


class CorrelatedIntervalSolver:
    def __init__(self, solver_id, strategy, rng_seed):
        self.solver_id = solver_id
        self.rng = random.Random(rng_seed)
        self.strategy = strategy

    def solve(self, intervals):
        if not intervals:
            return 0
        sorted_ints = sorted(intervals, key=lambda x: x[0])
        target_end = max(e for s, e in intervals)
        count = 0
        current_end = sorted_ints[0][0] - 1
        i = 0
        while current_end < target_end and i < len(sorted_ints):
            best_end = current_end
            while i < len(sorted_ints) and sorted_ints[i][0] <= current_end + 1:
                if self.strategy == 'greedy':
                    if sorted_ints[i][1] > best_end:
                        best_end = sorted_ints[i][1]
                else:
                    best_end = max(best_end, sorted_ints[i][1])
                i += 1
            if best_end == current_end:
                return -1
            current_end = best_end
            count += 1
        return count if current_end >= target_end else -1


class CorrelatedConstraintSolver:
    def __init__(self, solver_id, strategy, rng_seed):
        self.solver_id = solver_id
        self.rng = random.Random(rng_seed)
        self.strategy = strategy

    def solve(self, elements, constraints, k):
        if k == 0:
            return True
        if k > len(elements):
            return False
        selected = set()
        for _ in range(k):
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
                return False
            if self.strategy == 'min_first':
                choice = min(candidates, key=lambda i: elements[i])
            else:
                choice = max(candidates, key=lambda i: elements[i])
            selected.add(choice)
        for a, b in constraints:
            if a in selected and b in selected:
                if elements[a] >= elements[b]:
                    return False
        return True


# ============================================================
# SECTION 3: ORTHOGONAL SOLVER ENSEMBLES
# ============================================================

class OrthogonalEnsembleGenerator:
    """Generate solver ensembles with enforced orthogonality in failure directions."""

    def __init__(self, n_solvers, n_cases, rng_seed):
        self.n_solvers = n_solvers
        self.n_cases = n_cases
        self.rng = random.Random(rng_seed)

    def generate_orthogonal_failure_matrix(self):
        """Generate a failure matrix where rows are maximally orthogonal."""
        matrix = np.zeros((self.n_solvers, self.n_cases), dtype=int)

        # Phase 1: Assign each solver a unique "primary" failure region
        cases_per_solver = self.n_cases // self.n_solvers
        for i in range(self.n_solvers):
            start = i * cases_per_solver
            end = start + cases_per_solver if i < self.n_solvers - 1 else self.n_cases
            # Fail on primary region
            for j in range(start, end):
                matrix[i, j] = 1

        # Phase 2: Add controlled overlap (minimal)
        overlap_budget = self.n_cases // (self.n_solvers * 2)
        for _ in range(overlap_budget):
            i1 = self.rng.randint(0, self.n_solvers - 1)
            i2 = self.rng.randint(0, self.n_solvers - 1)
            if i1 != i2:
                j = self.rng.randint(0, self.n_cases - 1)
                matrix[i1, j] = 1
                matrix[i2, j] = 1

        return matrix

    def orthogonalize_solver_ensemble(self, base_matrix, problem_type, cases):
        """Create solvers whose failure patterns match the orthogonal matrix."""
        solvers = []
        n_solvers = base_matrix.shape[0]

        for i in range(n_solvers):
            target_failures = set(j for j in range(base_matrix.shape[1]) if base_matrix[i, j] == 1)
            solver = OrthogonalSolver(
                solver_id='ortho_' + str(i),
                problem_type=problem_type,
                target_failures=target_failures,
                cases=cases,
                rng_seed=self.rng.randint(0, 2**31)
            )
            solvers.append(solver)

        return solvers


class OrthogonalSolver:
    """Solver designed to fail on specific cases (target_failures)."""

    def __init__(self, solver_id, problem_type, target_failures, cases, rng_seed):
        self.solver_id = solver_id
        self.problem_type = problem_type
        self.target_failures = target_failures
        self.cases = cases
        self.rng = random.Random(rng_seed)

    def solve(self, *args):
        case_idx = self._identify_case(args)
        if case_idx in self.target_failures:
            return self._wrong_answer(*args)
        else:
            return self._correct_answer(*args)

    def _identify_case(self, args):
        """Map input to case index."""
        for i, case in enumerate(self.cases):
            if self._match_case(case, args):
                return i
        return -1

    def _match_case(self, case, args):
        """Check if input matches a known case."""
        try:
            if self.problem_type == 'coin':
                return args[0] == case[0] and args[1] == case[1]
            elif self.problem_type == 'grid':
                return args[0] == case[0] and args[1] == case[1] and args[2] == case[2]
            elif self.problem_type == 'interval':
                return args[0] == case
            elif self.problem_type == 'constraint':
                return args[0] == case[0] and args[1] == case[1] and args[2] == case[2]
        except Exception:
            return False
        return False

    def _correct_answer(self, *args):
        if self.problem_type == 'coin':
            return coin_oracle(args[0], args[1])
        elif self.problem_type == 'grid':
            return grid_oracle(args[0], args[1], args[2])
        elif self.problem_type == 'interval':
            return interval_oracle(args[0])
        elif self.problem_type == 'constraint':
            return constraint_oracle(args[0], args[1], args[2])

    def _wrong_answer(self, *args):
        correct = self._correct_answer(*args)
        if correct == -1:
            return 0
        elif correct == 0:
            return 1
        elif isinstance(correct, bool):
            return not correct
        else:
            return correct + self.rng.choice([-2, -1, 1, 2])


# ============================================================
# SECTION 4: EQUIVALENCE RELATION COMPARISON
# ============================================================

def compute_quotient_signature(matrix):
    """Compute signature of the quotient geometry."""
    n_solvers, n_cases = matrix.shape

    # Spectral signature
    m = matrix.astype(float)
    m_centered = m - m.mean(axis=1, keepdims=True)
    U, s, Vt = np.linalg.svd(m_centered, full_matrices=False)
    total_var = np.sum(s ** 2)
    if total_var == 0:
        spectrum = [0.0] * min(6, n_solvers)
    else:
        spectrum = s.tolist()[:6]

    # Combinatorial signature
    row_degrees = tuple(sorted(matrix.sum(axis=1)))
    col_degrees = tuple(sorted(matrix.sum(axis=0)))
    unique_rows = len(set(tuple(row) for row in matrix))
    unique_cols = len(set(tuple(matrix[:, j]) for j in range(n_cases)))

    # Clustering signature
    row_adj = 0
    for i in range(n_solvers):
        for j in range(i + 1, n_solvers):
            if np.any(np.logical_and(matrix[i], matrix[j])):
                row_adj += 1
    row_adj_fraction = row_adj / (n_solvers * (n_solvers - 1) / 2) if n_solvers > 1 else 0

    # Component count
    visited_rows = set()
    visited_cols = set()
    n_components = 0
    for start_row in range(n_solvers):
        if start_row in visited_rows:
            continue
        n_components += 1
        queue = [('row', start_row)]
        while queue:
            kind, idx = queue.pop()
            if kind == 'row':
                if idx in visited_rows:
                    continue
                visited_rows.add(idx)
                for j in range(n_cases):
                    if matrix[idx, j] == 1 and j not in visited_cols:
                        queue.append(('col', j))
            else:
                if idx in visited_cols:
                    continue
                visited_cols.add(idx)
                for i in range(n_solvers):
                    if matrix[i, idx] == 1 and i not in visited_rows:
                        queue.append(('row', i))

    return {
        'spectrum': tuple(round(x, 4) for x in spectrum),
        'row_degrees': row_degrees,
        'col_degrees': col_degrees,
        'unique_rows': unique_rows,
        'unique_cols': unique_cols,
        'row_adj_fraction': round(row_adj_fraction, 4),
        'n_components': n_components,
    }


def compare_equivalence_relations(sig1, sig2):
    """Compare two quotient signatures."""
    matches = 0
    total = 0
    for key in sig1:
        if key in sig2:
            total += 1
            if sig1[key] == sig2[key]:
                matches += 1
    return matches / total if total > 0 else 0


# ============================================================
# SECTION 5: MAIN EXPERIMENT
# ============================================================

def run_experiment():
    problems = {
        'coin': {
            'cases_fn': gen_coin_cases,
            'oracle_fn': lambda tc: coin_oracle(tc[0], tc[1]),
            'solve_fn': lambda s, tc: s.solve(tc[0], tc[1]),
        },
        'grid': {
            'cases_fn': gen_grid_cases,
            'oracle_fn': lambda tc: grid_oracle(tc[0], tc[1], tc[2]),
            'solve_fn': lambda s, tc: s.solve(tc[0], tc[1], tc[2]),
        },
        'interval': {
            'cases_fn': gen_interval_cases,
            'oracle_fn': lambda tc: interval_oracle(tc),
            'solve_fn': lambda s, tc: s.solve(tc),
        },
        'constraint': {
            'cases_fn': gen_constraint_cases,
            'oracle_fn': lambda tc: constraint_oracle(tc[0], tc[1], tc[2]),
            'solve_fn': lambda s, tc: s.solve(tc[0], tc[1], tc[2]),
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

        # Step 1: Generate correlated ensemble and compute its quotient
        print('  Step 1: Correlated ensemble...')
        correlated_solvers = []
        rng = random.Random(SEED)
        if prob_name == 'coin':
            strategies = ['greedy_largest', 'greedy_smallest', 'dp']
            for s in strategies:
                correlated_solvers.append(CorrelatedCoinSolver('corr_' + s, s, rng.randint(0, 2**31)))
        elif prob_name == 'grid':
            strategies = ['greedy', 'bfs', 'reverse']
            for s in strategies:
                correlated_solvers.append(CorrelatedGridSolver('corr_' + s, s, rng.randint(0, 2**31)))
        elif prob_name == 'interval':
            strategies = ['greedy', 'first']
            for s in strategies:
                correlated_solvers.append(CorrelatedIntervalSolver('corr_' + s, s, rng.randint(0, 2**31)))
        elif prob_name == 'constraint':
            strategies = ['min_first', 'max_first']
            for s in strategies:
                correlated_solvers.append(CorrelatedConstraintSolver('corr_' + s, s, rng.randint(0, 2**31)))

        matrix_corr = np.zeros((len(correlated_solvers), len(cases)), dtype=int)
        for si, s in enumerate(correlated_solvers):
            for ci, tc in enumerate(cases):
                oracle_val = oracle_fn(tc)
                try:
                    solver_val = solve_fn(s, tc)
                    matrix_corr[si, ci] = 0 if solver_val == oracle_val else 1
                except Exception:
                    matrix_corr[si, ci] = 1

        sig_corr = compute_quotient_signature(matrix_corr)
        print('    Correlated signature: ' + str(sig_corr))

        # Step 2: Generate orthogonal ensemble
        print('  Step 2: Orthogonal ensemble...')
        n_solvers = len(correlated_solvers)
        n_cases = len(cases)
        ortho_gen = OrthogonalEnsembleGenerator(n_solvers, n_cases, SEED + 5000)
        ortho_matrix = ortho_gen.generate_orthogonal_failure_matrix()
        ortho_solvers = ortho_gen.orthogonalize_solver_ensemble(ortho_matrix, prob_name, cases)

        matrix_ortho = np.zeros((len(ortho_solvers), len(cases)), dtype=int)
        for si, s in enumerate(ortho_solvers):
            for ci, tc in enumerate(cases):
                oracle_val = oracle_fn(tc)
                try:
                    solver_val = solve_fn(s, tc)
                    matrix_ortho[si, ci] = 0 if solver_val == oracle_val else 1
                except Exception:
                    matrix_ortho[si, ci] = 1

        sig_ortho = compute_quotient_signature(matrix_ortho)
        print('    Orthogonal signature: ' + str(sig_ortho))

        # Step 3: Compare equivalence relations
        print('  Step 3: Comparing equivalence relations...')
        similarity = compare_equivalence_relations(sig_corr, sig_ortho)
        print('    Equivalence relation similarity: ' + str(round(similarity, 4)))

        # Step 4: Classification
        if similarity > 0.8:
            outcome = 'Outcome 1: Structure invariant (robustness class)'
        elif similarity < 0.5:
            outcome = 'Outcome 2: Structure instability (observer-defined geometry)'
        else:
            outcome = 'Mixed: Partial stability'

        print('    Classification: ' + outcome)

        all_results[prob_name] = {
            'correlated_signature': {k: (list(v) if isinstance(v, tuple) else v) for k, v in sig_corr.items()},
            'orthogonal_signature': {k: (list(v) if isinstance(v, tuple) else v) for k, v in sig_ortho.items()},
            'similarity': similarity,
            'outcome': outcome,
            'correlated_failures': int(matrix_corr.sum()),
            'orthogonal_failures': int(matrix_ortho.sum()),
        }
        print()

    # Summary
    print('=' * 60)
    print('  SUMMARY')
    print('=' * 60)
    for prob_name, result in all_results.items():
        print('  ' + prob_name + ':')
        print('    Similarity: ' + str(round(result['similarity'], 4)))
        print('    Outcome: ' + result['outcome'])
        print('    Correlated failures: ' + str(result['correlated_failures']))
        print('    Orthogonal failures: ' + str(result['orthogonal_failures']))
        print()

    with open(OUTPUT_DIR / 'orthogonal_ensemble_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print('  SAVED: ' + str(OUTPUT_DIR / 'orthogonal_ensemble_results.json'))


if __name__ == '__main__':
    run_experiment()
