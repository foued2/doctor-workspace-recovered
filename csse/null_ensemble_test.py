import json
import random
import numpy as np
from itertools import combinations

def compute_svd_metrics(matrix):
    matrix_float = matrix.astype(float)
    matrix_centered = matrix_float - matrix_float.mean(axis=1, keepdims=True)
    U, s, Vt = np.linalg.svd(matrix_centered, full_matrices=False)
    total_var = np.sum(s ** 2)
    if total_var == 0:
        return {'S': 0.0, 'intrinsic_dimension': matrix.shape[0], 'singular_spectrum': [0.0] * min(6, matrix.shape[0])}
    cumvar = np.cumsum(s ** 2) / total_var
    dim = int(np.searchsorted(cumvar, 0.90) + 1)
    dim = min(dim, len(s))
    return {'S': float(s[0]), 'intrinsic_dimension': dim, 'singular_spectrum': s.tolist()[:6]}


SEED = 20260613

def coin_change_oracle(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        for x in range(coin, amount + 1):
            if dp[x - coin] + 1 < dp[x]:
                dp[x] = dp[x - coin] + 1
    return dp[amount] if dp[amount] != float('inf') else -1

def grid_shortest_path_oracle(grid, start, end):
    from collections import deque
    R, C = len(grid), len(grid[0])
    if grid[start[0]][start[1]] == 1 or grid[end[0]][end[1]] == 1:
        return -1
    q = deque([(start[0], start[1], 0)])
    visited = {(start[0], start[1])}
    while q:
        r, c, d = q.popleft()
        if (r, c) == (end[0], end[1]):
            return d
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and (nr, nc) not in visited and grid[nr][nc] == 0:
                visited.add((nr, nc))
                q.append((nr, nc, d + 1))
    return -1

def interval_cover_oracle(intervals):
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


class NullSolver:
    def __init__(self, solver_id, strategy, rng):
        self.solver_id = solver_id
        self.strategy = strategy
        self.rng = rng

    def solve_coin(self, coins, amount):
        if self.strategy == 'random':
            return self.rng.randint(0, amount + 10)
        elif self.strategy == 'constant':
            return 0
        elif self.strategy == 'shuffled':
            oracle = coin_change_oracle(coins, amount)
            if oracle == -1:
                return -1
            return oracle + self.rng.choice([-1, 0, 0, 0, 1])
        elif self.strategy == 'adversarial':
            oracle = coin_change_oracle(coins, amount)
            if oracle == -1:
                return -1
            if self.rng.random() < 0.5:
                return oracle + self.rng.choice([-2, -1, 1, 2])
            return oracle
        elif self.strategy == 'high_entropy':
            valid = [i for i in range(amount + 1) if i <= amount]
            return self.rng.choice(valid) if valid else 0
        return 0

    def solve_grid(self, grid, start, end):
        R, C = len(grid), len(grid[0])
        if self.strategy == 'random':
            return self.rng.randint(-1, R * C)
        elif self.strategy == 'constant':
            return 0
        elif self.strategy == 'shuffled':
            oracle = grid_shortest_path_oracle(grid, start, end)
            if oracle == -1:
                return -1
            return oracle + self.rng.choice([-1, 0, 0, 0, 1])
        elif self.strategy == 'adversarial':
            oracle = grid_shortest_path_oracle(grid, start, end)
            if oracle == -1:
                return -1
            if self.rng.random() < 0.5:
                return oracle + self.rng.choice([-2, -1, 1, 2])
            return oracle
        elif self.strategy == 'high_entropy':
            return self.rng.randint(-1, R * C)
        return 0

    def solve_interval(self, intervals):
        if self.strategy == 'random':
            return self.rng.randint(0, len(intervals) + 5)
        elif self.strategy == 'constant':
            return 0
        elif self.strategy == 'shuffled':
            oracle = interval_cover_oracle(intervals)
            if oracle == -1:
                return -1
            return oracle + self.rng.choice([-1, 0, 0, 0, 1])
        elif self.strategy == 'adversarial':
            oracle = interval_cover_oracle(intervals)
            if oracle == -1:
                return -1
            if self.rng.random() < 0.5:
                return oracle + self.rng.choice([-2, -1, 1, 2])
            return oracle
        elif self.strategy == 'high_entropy':
            return self.rng.randint(0, len(intervals) + 5)
        return 0

    def solve_constraint(self, elements, constraints, k):
        if self.strategy == 'random':
            return self.rng.choice([True, False])
        elif self.strategy == 'constant':
            return True
        elif self.strategy == 'shuffled':
            oracle = constraint_lattice_oracle(elements, constraints, k)
            if self.rng.random() < 0.3:
                return not oracle
            return oracle
        elif self.strategy == 'adversarial':
            oracle = constraint_lattice_oracle(elements, constraints, k)
            if self.rng.random() < 0.5:
                return not oracle
            return oracle
        elif self.strategy == 'high_entropy':
            return self.rng.choice([True, False])
        return True


def gen_coin_cases(n=100):
    cases = []
    rng = random.Random(SEED)
    for _ in range(85):
        n_coins = rng.randint(1, 5)
        coins = sorted(set(rng.randint(1, 20) for _ in range(n_coins)))
        amount = rng.randint(1, 50)
        cases.append((coins, amount))
    anchors = [
        ([1], 1), ([1], 5), ([1, 5, 10, 25], 30), ([2], 3), ([3], 7),
        ([5, 10], 15), ([1, 2, 5], 11), ([1, 5, 10, 25, 50], 100),
        ([2, 5], 11), ([1, 3, 4], 7), ([1, 5], 4), ([2, 3, 7], 14),
        ([1, 10, 15], 25), ([5], 12), ([1, 2, 5, 10], 39),
    ]
    return cases[:85] + anchors

def gen_grid_cases(n=100):
    cases = []
    rng = random.Random(SEED + 1)
    for _ in range(85):
        R = rng.randint(3, 7)
        C = rng.randint(3, 7)
        grid = [[0] * C for _ in range(R)]
        n_walls = rng.randint(1, R * C // 3)
        for _ in range(n_walls):
            r, c = rng.randint(0, R - 1), rng.randint(0, C - 1)
            grid[r][c] = 1
        start = (rng.randint(0, R - 1), rng.randint(0, C - 1))
        end = (rng.randint(0, R - 1), rng.randint(0, C - 1))
        grid[start[0]][start[1]] = 0
        grid[end[0]][end[1]] = 0
        cases.append((grid, start, end))
    anchors = [
        ([[0, 0], [0, 0]], (0, 0), (1, 1)),
        ([[0, 1], [1, 0]], (0, 0), (1, 1)),
        ([[0, 0, 0], [1, 1, 0], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0] * 5 for _ in range(5)], (0, 0), (4, 4)),
        ([[0, 1, 0], [0, 1, 0], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0, 0], [0, 0]], (0, 0), (0, 1)),
        ([[0, 1], [0, 0]], (0, 0), (1, 0)),
        ([[0, 0, 0], [0, 1, 0], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0] * 4 for _ in range(4)], (0, 0), (3, 3)),
        ([[0, 1, 0, 0], [0, 1, 0, 1], [0, 0, 0, 1]], (0, 0), (2, 2)),
        ([[0, 0], [1, 0]], (0, 0), (1, 1)),
        ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], (0, 0), (2, 2)),
        ([[0, 1], [0, 0]], (1, 0), (0, 1)),
        ([[0, 0, 1], [1, 0, 0], [0, 1, 0]], (0, 0), (2, 2)),
        ([[0] * 3 for _ in range(3)], (0, 0), (2, 2)),
    ]
    return cases[:85] + anchors

def gen_interval_cases(n=100):
    cases = []
    rng = random.Random(SEED + 2)
    for _ in range(85):
        n_intervals = rng.randint(3, 8)
        intervals = []
        for _ in range(n_intervals):
            s = rng.randint(0, 20)
            e = s + rng.randint(1, 10)
            intervals.append((s, e))
        cases.append(intervals)
    anchors = [
        [(0, 5), (3, 8), (6, 10)],
        [(0, 10), (1, 3), (5, 7)],
        [(0, 3), (2, 6), (5, 9)],
        [(0, 20), (5, 15), (10, 25)],
        [(1, 5), (2, 8), (6, 12)],
        [(0, 5), (3, 8)],
        [(0, 10), (5, 15), (10, 20)],
        [(0, 3), (2, 5), (4, 7), (6, 10)],
        [(0, 100), (50, 60)],
        [(0, 5), (10, 15), (20, 25)],
        [(0, 10), (5, 15)],
        [(0, 1), (2, 3), (4, 5)],
        [(0, 10), (10, 20)],
        [(0, 10), (5, 15), (10, 20)],
        [(0, 5), (3, 8), (6, 10)],
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


def run_null_experiment(problem_type, n_solvers=10, n_seeds=5):
    results = []

    for seed_offset in range(n_seeds):
        seed = SEED + seed_offset * 1000
        rng = random.Random(seed)

        if problem_type == 'coin':
            cases = gen_coin_cases()
            oracle_fn = lambda tc: coin_change_oracle(tc[0], tc[1])
            solve_fn = lambda s, tc: s.solve_coin(tc[0], tc[1])
        elif problem_type == 'grid':
            cases = gen_grid_cases()
            oracle_fn = lambda tc: grid_shortest_path_oracle(tc[0], tc[1], tc[2])
            solve_fn = lambda s, tc: s.solve_grid(tc[0], tc[1], tc[2])
        elif problem_type == 'interval':
            cases = gen_interval_cases()
            oracle_fn = lambda tc: interval_cover_oracle(tc)
            solve_fn = lambda s, tc: s.solve_interval(tc)
        elif problem_type == 'constraint':
            cases = gen_constraint_cases()
            oracle_fn = lambda tc: constraint_lattice_oracle(tc[0], tc[1], tc[2])
            solve_fn = lambda s, tc: s.solve_constraint(tc[0], tc[1], tc[2])

        strategies = ['random', 'constant', 'shuffled', 'adversarial', 'high_entropy']

        for strategy in strategies:
            solvers = []
            for i in range(n_solvers):
                solver_rng = random.Random(seed + i)
                solvers.append(NullSolver(f'null_{strategy}_{i}', strategy, solver_rng))

            matrix = np.zeros((len(solvers), len(cases)), dtype=int)
            for si, s in enumerate(solvers):
                for ci, tc in enumerate(cases):
                    oracle_val = oracle_fn(tc)
                    try:
                        solver_val = solve_fn(s, tc)
                        if solver_val == oracle_val:
                            matrix[si, ci] = 0
                        else:
                            matrix[si, ci] = 1
                    except Exception:
                        matrix[si, ci] = 1

            total_failures = int(matrix.sum())
            if total_failures == 0:
                S = 0.0
                dim = len(solvers)
                spec = [0.0] * min(6, len(solvers))
            else:
                result = compute_svd_metrics(matrix)
                S = result['S']
                dim = result['intrinsic_dimension']
                spec = result['singular_spectrum'][:6]

            results.append({
                'problem': problem_type,
                'strategy': strategy,
                'seed': seed,
                'n_solvers': len(solvers),
                'n_tests': len(cases),
                'total_failures': total_failures,
                'S': S,
                'intrinsic_dimension': dim,
                'singular_spectrum': spec,
            })

    return results


def main():
    print('=' * 70)
    print('  NULL ENSEMBLE STRESS TEST')
    print('=' * 70)
    print()

    all_results = []

    for problem in ['coin', 'grid', 'interval', 'constraint']:
        print('Testing ' + problem + '...')
        results = run_null_experiment(problem, n_solvers=10, n_seeds=5)
        all_results.extend(results)

        strategies = ['random', 'constant', 'shuffled', 'adversarial', 'high_entropy']
        for strategy in strategies:
            strategy_results = [r for r in results if r['strategy'] == strategy]
            S_values = [r['S'] for r in strategy_results]
            dim_values = [r['intrinsic_dimension'] for r in strategy_results]
            fail_values = [r['total_failures'] for r in strategy_results]
            print('  ' + strategy + ': S=' + str(round(np.mean(S_values), 3)) +
                  ' (std=' + str(round(np.std(S_values), 3)) +
                  '), dim=' + str(round(np.mean(dim_values), 1)) +
                  ', failures=' + str(int(np.mean(fail_values))))
        print()

    with open('results/null_ensemble_results.json', 'w') as f:
        json.dump({'results': all_results, 'metadata': {'n_problems': 4, 'n_strategies': 5, 'n_seeds': 5}}, f, indent=2)

    print('=' * 70)
    print('  SUMMARY')
    print('=' * 70)
    print()

    print('Real Stratum-1 results (for comparison):')
    print('  coin: S=11.13, dim=3')
    print('  grid: S=8.09, dim=2')
    print('  interval: S=9.40, dim=2')
    print('  constraint: S=5.83, dim=1')
    print()

    print('Null ensemble results (averaged across seeds):')
    strategies = ['random', 'constant', 'shuffled', 'adversarial', 'high_entropy']
    for strategy in strategies:
        strategy_all = [r for r in all_results if r['strategy'] == strategy]
        S_mean = np.mean([r['S'] for r in strategy_all])
        S_std = np.std([r['S'] for r in strategy_all])
        dim_mean = np.mean([r['intrinsic_dimension'] for r in strategy_all])
        fail_mean = np.mean([r['total_failures'] for r in strategy_all])
        print('  ' + strategy + ':')
        print('    S = ' + str(round(S_mean, 3)) + ' (std=' + str(round(S_std, 3)) + ')')
        print('    dim = ' + str(round(dim_mean, 1)))
        print('    failures = ' + str(int(fail_mean)))

    print()
    print('Key question: Is low-rank structure an artifact of solver construction?')
    print('If null S >> real S, then structure is real.')
    print('If null S ~ real S, then structure is an artifact.')

if __name__ == '__main__':
    main()
