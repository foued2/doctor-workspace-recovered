"""LC3946 — Solver pool (30 solvers across 6 strategy families).

Mirrors the LC322 solver population structure exactly:
  solver_001..solver_005   : DP-survivor      (5 solvers, correct under reasonable budget)
  solver_006..solver_010   : Greedy-by-price  (5 solvers, fail on non-canonical price)
  solver_011..solver_015   : Greedy-by-density (5 solvers, fail on density-illusions)
  solver_016..solver_020   : BFS-subset       (5 solvers, fail on deep paths)
  solver_021..solver_025   : Recursive        (5 solvers, fail on free-set collapse)
  solver_026..solver_030   : Hybrid           (5 solvers, mix of accept/reject)

Each solver is a function with signature: solve(solver_input: list) -> int
solver_input is the flat list [f0, p0, f1, p1, ..., 0, budget] (matches the
probe_to_solver_input adapter). The solver unpacks pairs and returns the
maximum total items (purchased + free) within the budget.

Solver-file format: each solver is a top-level function. The seval_manifest
references them by module + function name.
"""
from __future__ import annotations

from collections import deque
from math import gcd
from typing import Callable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unpack(solver_input: list) -> tuple[list[tuple[int, int]], int]:
    """Unpack a flat solver input into (items, budget)."""
    flat = [int(x) for x in solver_input]
    if len(flat) < 2 or len(flat) % 2 != 0:
        raise ValueError(f"LC3946 solver input: bad length {len(flat)}")
    pairs = [(flat[2 * k], flat[2 * k + 1]) for k in range(len(flat) // 2)]
    factor_sentinel, budget = pairs[-1]
    if factor_sentinel != 0:
        raise ValueError(
            f"LC3946 solver input: trailing pair factor must be 0, got {factor_sentinel}"
        )
    return pairs[:-1], int(budget)


def _free_count(items: list[tuple[int, int]], p_mask: int) -> list[int]:
    """Compute free counts for each item given the purchased_set mask p_mask."""
    n = len(items)
    factors = [f for f, _ in items]
    free = [0] * n
    for j in range(n):
        for i in range(n):
            if i == j:
                continue
            if not (p_mask & (1 << i)):
                continue
            if factors[j] % factors[i] == 0:
                free[j] += 1
    return free


def _greedy_fill(items: list[tuple[int, int]], p_mask: int, budget: int) -> int:
    """Given purchased_set p_mask, fill the remaining budget on the cheapest
    item in p_mask and return the resulting total (bought + free).

    Cheapest-item fill is optimal because extra copies do not increase free
    counts (per the problem statement). Returns -1 if p_mask is empty or if
    the cost of p_mask exceeds budget.
    """
    n = len(items)
    if p_mask == 0:
        return -1
    prices = [p for _, p in items]
    cost = 0
    for i in range(n):
        if p_mask & (1 << i):
            cost += prices[i]
    if cost > budget:
        return -1
    free = _free_count(items, p_mask)
    bought = bin(p_mask).count("1")
    remaining = budget - cost
    if remaining > 0:
        cheapest = min(
            prices[i] for i in range(n) if p_mask & (1 << i)
        )
        extra = remaining // cheapest
    else:
        extra = 0
    return bought + sum(free) + extra


def _enumerate_best(items: list[tuple[int, int]], budget: int) -> int:
    """Brute force over all 2^n purchased_set masks, with cheapest-fill."""
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    best = 0
    for mask in range(1, 1 << n):
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
    return best


# ---------------------------------------------------------------------------
# Family 1: DP-survivor (5 solvers, all correct for reasonable budget)
# solver_001..solver_005
# ---------------------------------------------------------------------------


def solver_001(solver_input: list) -> int:
    """solver_001: full 2^n enumeration, cheapest-fill (the DP-survivor)."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


def solver_002(solver_input: list) -> int:
    """solver_002: same as solver_001, but with explicit early termination
    on cost > budget (micro-optimization; semantically identical)."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    best = 0
    for mask in range(1, 1 << n):
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
    return best


def solver_003(solver_input: list) -> int:
    """solver_003: same brute force, sorted item order to keep
    cache locality consistent."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


def solver_004(solver_input: list) -> int:
    """solver_004: 2^n brute force with cheapest-fill. Includes a sanity
    pre-check on the universal_source factor=1 item (which always
    triggers all free items)."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0

    # If a factor=1 item exists, the optimal solution always buys it.
    has_universal = any(f == 1 for f, _ in items)
    if has_universal:
        uni_idx = next(i for i, (f, _) in enumerate(items) if f == 1)
        uni_mask = (1 << uni_idx)
        if items[uni_idx][1] > budget:
            return 0
        best = 0
        for mask in range(1 << n):
            if mask & uni_mask:
                continue  # uni bit handled separately
            full_mask = mask | uni_mask
            total = _greedy_fill(items, full_mask, budget)
            if total > best:
                best = total
        return best
    return _enumerate_best(items, budget)


def solver_005(solver_input: list) -> int:
    """solver_005: full 2^n enumeration. Identical to solver_001."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


# ---------------------------------------------------------------------------
# Family 2: Greedy-by-price (5 solvers)
# solver_006..solver_010 (fail on non-canonical price/divisibility alignment)
# ---------------------------------------------------------------------------


def solver_006(solver_input: list) -> int:
    """solver_006: greedy — buy the cheapest item first, repeatedly, never
    triggers free items (treats items independently)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    prices = [p for _, p in items]
    cheapest_idx = min(range(len(items)), key=lambda i: prices[i])
    cheapest_price = prices[cheapest_idx]
    n_bought = budget // cheapest_price
    return n_bought


def solver_007(solver_input: list) -> int:
    """solver_007: greedy — buy the most expensive item first, repeatedly."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    prices = [p for _, p in items]
    expensive_idx = max(range(len(items)), key=lambda i: prices[i])
    expensive_price = prices[expensive_idx]
    n_bought = budget // expensive_price
    return n_bought


def solver_008(solver_input: list) -> int:
    """solver_008: greedy — buy the item with the largest factor first
    (treating factor as 'value'). Ignores price entirely."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    factors = [f for f, _ in items]
    prices = [p for _, p in items]
    big_idx = max(range(len(items)), key=lambda i: factors[i])
    n_bought = budget // prices[big_idx]
    return n_bought


def solver_009(solver_input: list) -> int:
    """solver_009: greedy — buy the item with the smallest factor first."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    factors = [f for f, _ in items]
    prices = [p for _, p in items]
    small_idx = min(range(len(items)), key=lambda i: factors[i])
    n_bought = budget // prices[small_idx]
    return n_bought


def solver_010(solver_input: list) -> int:
    """solver_010: greedy — buy any single item type, no free-item logic."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    prices = [p for _, p in items]
    return max(budget // p for p in prices)


# ---------------------------------------------------------------------------
# Family 3: Greedy-by-density (5 solvers)
# solver_011..solver_015 (fail on density illusions where poset is non-trivial)
# ---------------------------------------------------------------------------


def solver_011(solver_input: list) -> int:
    """solver_011: pick the single item with best (1/price) ratio, then
    fill budget on it. Ignores free items entirely."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    prices = [p for _, p in items]
    best_idx = min(range(len(items)), key=lambda i: prices[i])
    return budget // prices[best_idx]


def solver_012(solver_input: list) -> int:
    """solver_012: pick item with best (factor / price) ratio."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    ratios = [f / p for f, p in items]
    best_idx = max(range(len(items)), key=lambda i: ratios[i])
    return budget // items[best_idx][1]


def solver_013(solver_input: list) -> int:
    """solver_013: pick item with best (free_count / price) ratio, but
    evaluate free_count with respect to all OTHER items as if they were
    all purchased (overestimate)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    n = len(items)
    factors = [f for f, _ in items]
    prices = [p for _, p in items]
    best_total = 0
    for i in range(n):
        if prices[i] > budget:
            continue
        free_i = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        n_bought = budget // prices[i]
        total = n_bought + free_i
        if total > best_total:
            best_total = total
    return best_total


def solver_014(solver_input: list) -> int:
    """solver_014: pick item with best (1 + free_count) / price, then
    fill. Single-purchase-set solver."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    n = len(items)
    factors = [f for f, _ in items]
    prices = [p for _, p in items]
    best_total = 0
    for i in range(n):
        if prices[i] > budget:
            continue
        free_i = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        score = (1 + free_i) / prices[i]
        n_bought = budget // prices[i]
        total = n_bought + free_i
        if score > 0 and total > best_total:
            best_total = total
    return best_total


def solver_015(solver_input: list) -> int:
    """solver_015: top-2 items by price, try both, take max. Ignores poset."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    prices = [p for _, p in items]
    sorted_by_price = sorted(range(len(items)), key=lambda i: prices[i])
    best = 0
    for i in sorted_by_price[:2]:
        if prices[i] <= budget:
            n_bought = budget // prices[i]
            if n_bought > best:
                best = n_bought
    return best


# ---------------------------------------------------------------------------
# Family 4: BFS-subset (5 solvers)
# solver_016..solver_020 (fail on deep poset paths; cheap on small n)
# ---------------------------------------------------------------------------


def solver_016(solver_input: list) -> int:
    """solver_016: BFS over purchased_set, but with a depth cap."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    cap = min(n, 4)  # depth cap
    best = 0
    queue: deque[tuple[int, int, int]] = deque([(0, 0, 0)])  # mask, cost, depth
    while queue:
        mask, cost, depth = queue.popleft()
        if depth > cap:
            continue
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
        # Expand: add item `depth` (if depth < n)
        if depth < n:
            new_mask = mask | (1 << depth)
            new_cost = cost + items[depth][1]
            if new_cost <= budget:
                queue.append((new_mask, new_cost, depth + 1))
            queue.append((mask, cost, depth + 1))
    return best


def solver_017(solver_input: list) -> int:
    """solver_017: BFS but only explores masks containing the factor=1 item
    (when present). Misses cases where factor=1 is not optimal."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    has_universal = any(f == 1 for f, _ in items)
    if not has_universal:
        return _enumerate_best(items, budget)
    uni_idx = next(i for i, (f, _) in enumerate(items) if f == 1)
    uni_mask = 1 << uni_idx
    if items[uni_idx][1] > budget:
        return 0
    best = 0
    for mask in range(1 << n):
        if not (mask & uni_mask):
            continue
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
    return best


def solver_018(solver_input: list) -> int:
    """solver_018: BFS with a budget cap (max cost in p)."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    cost_cap = budget // 2  # heuristic cap
    best = 0
    for mask in range(1, 1 << n):
        cost = sum(items[i][1] for i in range(n) if mask & (1 << i))
        if cost > cost_cap:
            continue
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
    return best


def solver_019(solver_input: list) -> int:
    """solver_019: 2^n enumeration (correct) but uses GCD to pre-prune
    factors that are all multiples of a smaller factor. Still correct."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    # Group by gcd-1: this doesn't change correctness, but checks the
    # universal-source case.
    g = 0
    for f, _ in items:
        g = gcd(g, f)
    return _enumerate_best(items, budget)


def solver_020(solver_input: list) -> int:
    """solver_020: 2^n enumeration. Same as solver_001 (DP-survivor
    parallel), but with a different iteration order."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    best = 0
    for mask in range(1, 1 << n):
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
    return best


# ---------------------------------------------------------------------------
# Family 5: Recursive (5 solvers)
# solver_021..solver_025 (fail on free-set collapse)
# ---------------------------------------------------------------------------


def solver_021(solver_input: list) -> int:
    """solver_021: recursive subset enumeration with a memo on (mask, budget)
    truncated to (mask % 8) — cache collisions cause wrong answers."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    cache: dict[tuple, int] = {}

    def _solve(idx: int, mask: int) -> int:
        if idx == n:
            return _greedy_fill(items, mask, budget)
        key = (idx % 8, mask)
        if key in cache:
            return cache[key]
        # Skip item idx
        best = _solve(idx + 1, mask)
        # Include item idx
        new_mask = mask | (1 << idx)
        with_idx = _solve(idx + 1, new_mask)
        if with_idx > best:
            best = with_idx
        cache[key] = best
        return best

    return _solve(0, 0)


def solver_022(solver_input: list) -> int:
    """solver_022: recursive but with no memo; safe for small n but slow
    on large n. For LC3946's 6-item probes, this is still correct."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    best = 0
    for mask in range(1, 1 << n):
        total = _greedy_fill(items, mask, budget)
        if total > best:
            best = total
    return best


def solver_023(solver_input: list) -> int:
    """solver_023: recursive — picks items in factor-decreasing order, but
    commits to the first valid subset (no backtracking). Greedy by factor."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    sorted_items = sorted(
        range(n), key=lambda i: items[i][0], reverse=True
    )
    cost = 0
    mask = 0
    for i in sorted_items:
        if cost + items[i][1] <= budget:
            cost += items[i][1]
            mask |= (1 << i)
    return _greedy_fill(items, mask, budget)


def solver_024(solver_input: list) -> int:
    """solver_024: recursive — picks items in factor-increasing order."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    sorted_items = sorted(range(n), key=lambda i: items[i][0])
    cost = 0
    mask = 0
    for i in sorted_items:
        if cost + items[i][1] <= budget:
            cost += items[i][1]
            mask |= (1 << i)
    return _greedy_fill(items, mask, budget)


def solver_025(solver_input: list) -> int:
    """solver_025: 2^n enumeration. Identical to solver_001."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


# ---------------------------------------------------------------------------
# Family 6: Hybrid (5 solvers)
# solver_026..solver_030 (mix of accept/reject)
# ---------------------------------------------------------------------------


def solver_026(solver_input: list) -> int:
    """solver_026: full 2^n enumeration (correct). Hybrid survivor."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


def solver_027(solver_input: list) -> int:
    """solver_027: full 2^n enumeration (correct). Hybrid survivor."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


def solver_028(solver_input: list) -> int:
    """solver_028: greedy — buy the item that minimizes (price - free_count).
    If free_count >= price, the item is 'free' and the solver buys it once.
    Otherwise falls back to the cheapest single item."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    factors = [f for f, _ in items]
    prices = [p for _, p in items]
    best = 0
    for i in range(n):
        if prices[i] > budget:
            continue
        free_i = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        n_bought = budget // prices[i]
        total = n_bought + free_i
        if total > best:
            best = total
    return best


def solver_029(solver_input: list) -> int:
    """solver_029: buys ONE copy of every affordable item, then fills the
    remaining budget on the cheapest affordable item. This is a single-p
    strategy and is correct only for some probe geometries."""
    items, budget = _unpack(solver_input)
    n = len(items)
    if n == 0 or budget == 0:
        return 0
    cost = 0
    mask = 0
    for i in range(n):
        if cost + items[i][1] <= budget:
            cost += items[i][1]
            mask |= (1 << i)
    if mask == 0:
        return 0
    return _greedy_fill(items, mask, budget)


def solver_030(solver_input: list) -> int:
    """solver_030: full 2^n enumeration (correct). Hybrid survivor."""
    items, budget = _unpack(solver_input)
    return _enumerate_best(items, budget)


# ---------------------------------------------------------------------------
# Solver registry (mirrors LC322_CANDIDATES shape)
# ---------------------------------------------------------------------------


LC3946_CANDIDATES: tuple[tuple[str, Callable[[list], int]], ...] = (
    ("solver_001", solver_001),
    ("solver_002", solver_002),
    ("solver_003", solver_003),
    ("solver_004", solver_004),
    ("solver_005", solver_005),
    ("solver_006", solver_006),
    ("solver_007", solver_007),
    ("solver_008", solver_008),
    ("solver_009", solver_009),
    ("solver_010", solver_010),
    ("solver_011", solver_011),
    ("solver_012", solver_012),
    ("solver_013", solver_013),
    ("solver_014", solver_014),
    ("solver_015", solver_015),
    ("solver_016", solver_016),
    ("solver_017", solver_017),
    ("solver_018", solver_018),
    ("solver_019", solver_019),
    ("solver_020", solver_020),
    ("solver_021", solver_021),
    ("solver_022", solver_022),
    ("solver_023", solver_023),
    ("solver_024", solver_024),
    ("solver_025", solver_025),
    ("solver_026", solver_026),
    ("solver_027", solver_027),
    ("solver_028", solver_028),
    ("solver_029", solver_029),
    ("solver_030", solver_030),
)
