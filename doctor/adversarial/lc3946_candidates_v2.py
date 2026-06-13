"""LC3946 — Second solver population (30 solvers, independent seed).

Generated with different algorithmic strategies than the original population.
Zero overlap with frozen C-4 population.

Strategy families:
  solver_001..solver_005   : Value-density greedy (5 solvers)
  solver_006..solver_010   : Free-item potential (5 solvers)
  solver_011..solver_015   : Budget-ratio threshold (5 solvers)
  solver_016..solver_020   : Randomized beam search (5 solvers)
  solver_021..solver_025   : Divisibility-chain (5 solvers)
  solver_026..solver_030   : Hybrid-v2 (5 solvers)
"""
from __future__ import annotations

import random
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
    item in p_mask and return the resulting total (bought + free)."""
    n = len(items)
    if p_mask == 0:
        return -1
    prices = [p for _, p in items]
    cost = sum(prices[i] for i in range(n) if p_mask & (1 << i))
    if cost > budget:
        return -1
    free = _free_count(items, p_mask)
    bought = bin(p_mask).count("1")
    remaining = budget - cost
    if remaining > 0:
        cheapest = min(prices[i] for i in range(n) if p_mask & (1 << i))
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
# Family 1: Value-density greedy (5 solvers)
# solver_001..solver_005
# ---------------------------------------------------------------------------


def solver_001(solver_input: list) -> int:
    """solver_001: greedy by value-density (items per unit cost)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    # Compute value-density: 1/price (more items per unit cost)
    densities = [(1.0 / p if p > 0 else 0, i) for i, (_, p) in enumerate(items)]
    densities.sort(reverse=True)
    
    # Buy items in density order
    remaining = budget
    bought = 0
    p_mask = 0
    for _, idx in densities:
        price = items[idx][1]
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
            bought += 1
    
    # Add free items
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_002(solver_input: list) -> int:
    """solver_002: greedy by value-density, but skip items that don't trigger frees."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    factors = [f for f, _ in items]
    prices = [p for _, p in items]
    
    # Compute potential free items for each purchase
    potential = []
    for i in range(n):
        # How many items would become free if we buy item i?
        free_count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        density = 1.0 / prices[i] if prices[i] > 0 else 0
        score = density + free_count * 0.5  # Bonus for free items
        potential.append((score, i))
    
    potential.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, idx in potential:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_003(solver_input: list) -> int:
    """solver_003: greedy by value-density with lookahead."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Score = density + expected free items
    scores = []
    for i in range(n):
        density = 1.0 / prices[i] if prices[i] > 0 else 0
        expected_free = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        scores.append((density + expected_free * 0.3, i))
    
    scores.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_004(solver_input: list) -> int:
    """solver_004: greedy by density, but prefer factor=1 items first."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Score: factor=1 gets big bonus
    scores = []
    for i in range(n):
        density = 1.0 / prices[i] if prices[i] > 0 else 0
        uni_bonus = 10.0 if factors[i] == 1 else 0.0
        scores.append((density + uni_bonus, i))
    
    scores.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_005(solver_input: list) -> int:
    """solver_005: greedy by density, budget-aware (stop if <50% budget used after item)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    
    scores = [(1.0 / prices[i] if prices[i] > 0 else 0, i) for i in range(n)]
    scores.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        price = prices[idx]
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
        # Stop if we've used less than 50% and remaining is small
        if remaining < budget * 0.5 and remaining < min(prices):
            break
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


# ---------------------------------------------------------------------------
# Family 2: Free-item potential (5 solvers)
# solver_006..solver_010
# ---------------------------------------------------------------------------


def solver_006(solver_input: list) -> int:
    """solver_006: buy item that triggers most free items first."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Score = number of items that become free
    free_potential = []
    for i in range(n):
        count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        free_potential.append((count, -prices[i], i))  # Tie-break by cheaper
    
    free_potential.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, _, idx in free_potential:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_007(solver_input: list) -> int:
    """solver_007: buy universal factor=1 item first, then greedily fill."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Find factor=1 items
    uni_indices = [i for i in range(n) if factors[i] == 1]
    other_indices = [i for i in range(n) if factors[i] != 1]
    
    remaining = budget
    p_mask = 0
    
    # Buy universal items first (sorted by price)
    uni_sorted = sorted(uni_indices, key=lambda i: prices[i])
    for idx in uni_sorted:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    # Then buy other items by free potential
    other_potential = []
    for i in other_indices:
        count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        other_potential.append((count, -prices[i], i))
    other_potential.sort(reverse=True)
    
    for _, _, idx in other_potential:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_008(solver_input: list) -> int:
    """solver_008: buy items in order of free-item chain potential."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Compute chain potential: how many items can become free transitively
    def chain_length(start):
        visited = {start}
        queue = [start]
        while queue:
            node = queue.pop(0)
            for j in range(n):
                if j not in visited and factors[j] % factors[node] == 0:
                    visited.add(j)
                    queue.append(j)
        return len(visited) - 1  # Exclude the starting item
    
    chain_scores = [(chain_length(i), -prices[i], i) for i in range(n)]
    chain_scores.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, _, idx in chain_scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_009(solver_input: list) -> int:
    """solver_009: buy items that are divisors of many others."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Score = number of items this item divides
    divisor_scores = []
    for i in range(n):
        count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        divisor_scores.append((count, -prices[i], i))
    
    divisor_scores.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, _, idx in divisor_scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_010(solver_input: list) -> int:
    """solver_010: buy items with smallest factors first (more likely to divide)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Sort by factor (ascending), then price (ascending)
    indices = sorted(range(n), key=lambda i: (factors[i], prices[i]))
    
    remaining = budget
    p_mask = 0
    for idx in indices:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


# ---------------------------------------------------------------------------
# Family 3: Budget-ratio threshold (5 solvers)
# solver_011..solver_015
# ---------------------------------------------------------------------------


def solver_011(solver_input: list) -> int:
    """solver_011: only buy items where price/budget < 0.3."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    
    # Filter by budget ratio
    affordable = [(prices[i], i) for i in range(n) if prices[i] / budget < 0.3]
    affordable.sort()
    
    remaining = budget
    p_mask = 0
    for price, idx in affordable:
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_012(solver_input: list) -> int:
    """solver_012: buy items where price/budget < 0.2 (stricter)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    
    affordable = [(prices[i], i) for i in range(n) if prices[i] / budget < 0.2]
    affordable.sort()
    
    remaining = budget
    p_mask = 0
    for price, idx in affordable:
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_013(solver_input: list) -> int:
    """solver_013: buy items where price/budget < 0.4 (relaxed)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    
    affordable = [(prices[i], i) for i in range(n) if prices[i] / budget < 0.4]
    affordable.sort()
    
    remaining = budget
    p_mask = 0
    for price, idx in affordable:
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_014(solver_input: list) -> int:
    """solver_014: adaptive threshold based on item count."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    
    # Threshold depends on number of items
    if n <= 3:
        threshold = 0.5
    elif n <= 5:
        threshold = 0.3
    else:
        threshold = 0.2
    
    affordable = [(prices[i], i) for i in range(n) if prices[i] / budget < threshold]
    affordable.sort()
    
    remaining = budget
    p_mask = 0
    for price, idx in affordable:
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_015(solver_input: list) -> int:
    """solver_015: buy items where cumulative cost < 60% of budget."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    
    # Sort by price
    indices = sorted(range(n), key=lambda i: prices[i])
    
    remaining = budget
    p_mask = 0
    total_spent = 0
    for idx in indices:
        if prices[idx] <= remaining and total_spent + prices[idx] < budget * 0.6:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
            total_spent += prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


# ---------------------------------------------------------------------------
# Family 4: Randomized beam search (5 solvers)
# solver_016..solver_020
# ---------------------------------------------------------------------------


def solver_016(solver_input: list) -> int:
    """solver_016: beam search with width=3, random tie-breaking."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    rng = random.Random(42)
    n = len(items)
    prices = [p for _, p in items]
    
    # Beam search: maintain top-3 partial solutions
    beam = [(0, 0, budget)]  # (score, p_mask, remaining)
    
    for step in range(n):
        candidates = []
        for score, mask, rem in beam:
            # Option 1: skip item
            candidates.append((score, mask, rem))
            # Option 2: buy item if affordable
            if prices[step] <= rem:
                new_mask = mask | (1 << step)
                new_rem = rem - prices[step]
                # Estimate future potential
                future_free = sum(1 for j in range(step + 1, n) 
                                if items[j][0] % items[step][0] == 0)
                candidates.append((score + 1 + future_free, new_mask, new_rem))
        
        # Keep top 3 by score (with random tie-breaking)
        candidates.sort(key=lambda x: x[0] + rng.random() * 0.1, reverse=True)
        beam = candidates[:3]
    
    # Return best from beam
    best = 0
    for score, mask, _ in beam:
        total = bin(mask).count("1") + sum(_free_count(items, mask))
        best = max(best, total)
    return best


def solver_017(solver_input: list) -> int:
    """solver_017: beam search with width=5."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    rng = random.Random(123)
    n = len(items)
    prices = [p for _, p in items]
    
    beam = [(0, 0, budget)]
    
    for step in range(n):
        candidates = []
        for score, mask, rem in beam:
            candidates.append((score, mask, rem))
            if prices[step] <= rem:
                new_mask = mask | (1 << step)
                new_rem = rem - prices[step]
                candidates.append((score + 1, new_mask, new_rem))
        
        candidates.sort(key=lambda x: x[0] + rng.random() * 0.1, reverse=True)
        beam = candidates[:5]
    
    best = 0
    for score, mask, _ in beam:
        total = bin(mask).count("1") + sum(_free_count(items, mask))
        best = max(best, total)
    return best


def solver_018(solver_input: list) -> int:
    """solver_018: beam search with width=2, greedy scoring."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    beam = [(0, 0, budget)]
    
    for step in range(n):
        candidates = []
        for score, mask, rem in beam:
            candidates.append((score, mask, rem))
            if prices[step] <= rem:
                new_mask = mask | (1 << step)
                new_rem = rem - prices[step]
                # Greedy scoring: free items potential
                free_potential = sum(1 for j in range(step + 1, n) 
                                   if factors[j] % factors[step] == 0)
                candidates.append((score + 1 + free_potential * 0.5, new_mask, new_rem))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        beam = candidates[:2]
    
    best = 0
    for score, mask, _ in beam:
        total = bin(mask).count("1") + sum(_free_count(items, mask))
        best = max(best, total)
    return best


def solver_019(solver_input: list) -> int:
    """solver_019: random beam with budget-bias scoring."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    rng = random.Random(456)
    n = len(items)
    prices = [p for _, p in items]
    
    beam = [(0, 0, budget)]
    
    for step in range(n):
        candidates = []
        for score, mask, rem in beam:
            candidates.append((score, mask, rem))
            if prices[step] <= rem:
                new_mask = mask | (1 << step)
                new_rem = rem - prices[step]
                # Score: prefer items that leave more budget
                budget_score = new_rem / budget
                candidates.append((score + budget_score, new_mask, new_rem))
        
        candidates.sort(key=lambda x: x[0] + rng.random() * 0.2, reverse=True)
        beam = candidates[:3]
    
    best = 0
    for score, mask, _ in beam:
        total = bin(mask).count("1") + sum(_free_count(items, mask))
        best = max(best, total)
    return best


def solver_020(solver_input: list) -> int:
    """solver_020: random beam with diversity pressure."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    rng = random.Random(789)
    n = len(items)
    prices = [p for _, p in items]
    
    beam = [(0, 0, budget)]
    
    for step in range(n):
        candidates = []
        for score, mask, rem in beam:
            candidates.append((score, mask, rem))
            if prices[step] <= rem:
                new_mask = mask | (1 << step)
                new_rem = rem - prices[step]
                candidates.append((score + 1, new_mask, new_rem))
        
        # Diversity: pick diverse candidates
        if len(candidates) > 3:
            # Sort by score
            candidates.sort(key=lambda x: x[0], reverse=True)
            # Take top, then random from rest
            selected = [candidates[0]]
            rest = candidates[1:]
            rng.shuffle(rest)
            selected.extend(rest[:2])
            beam = selected
        else:
            beam = candidates
    
    best = 0
    for score, mask, _ in beam:
        total = bin(mask).count("1") + sum(_free_count(items, mask))
        best = max(best, total)
    return best


# ---------------------------------------------------------------------------
# Family 5: Divisibility-chain (5 solvers)
# solver_021..solver_025
# ---------------------------------------------------------------------------


def solver_021(solver_input: list) -> int:
    """solver_021: build divisibility chains greedily."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Build chains: start with smallest factor, add items it divides
    chains = []
    used = set()
    
    # Sort by factor
    indices = sorted(range(n), key=lambda i: factors[i])
    
    for start in indices:
        if start in used:
            continue
        chain = [start]
        used.add(start)
        for j in indices:
            if j not in used and factors[j] % factors[start] == 0:
                chain.append(j)
                used.add(j)
        chains.append(chain)
    
    # Buy chains in order of total cost
    chain_costs = [(sum(prices[i] for i in chain), chain) for chain in chains]
    chain_costs.sort()
    
    remaining = budget
    p_mask = 0
    for cost, chain in chain_costs:
        if cost <= remaining:
            for idx in chain:
                p_mask |= (1 << idx)
            remaining -= cost
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_022(solver_input: list) -> int:
    """solver_022: buy chain starters first, then fill."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Find chain starters (items that divide others)
    starters = []
    for i in range(n):
        divides_count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        starters.append((divides_count, -prices[i], i))
    
    starters.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, _, idx in starters:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    # Fill remaining with cheapest items
    for idx in sorted(range(n), key=lambda i: prices[i]):
        if prices[idx] <= remaining and not (p_mask & (1 << idx)):
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_023(solver_input: list) -> int:
    """solver_023: buy items in divisibility order (smallest factor first)."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Sort by factor, then price
    indices = sorted(range(n), key=lambda i: (factors[i], prices[i]))
    
    remaining = budget
    p_mask = 0
    for idx in indices:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_024(solver_input: list) -> int:
    """solver_024: buy items that form complete divisibility chains."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Find complete chains
    complete_chains = []
    for i in range(n):
        chain = [j for j in range(n) if factors[j] % factors[i] == 0]
        chain_cost = sum(prices[j] for j in chain)
        if chain_cost <= budget:
            complete_chains.append((len(chain), -chain_cost, chain))
    
    complete_chains.sort(reverse=True)
    
    # Buy best chain
    if complete_chains:
        _, _, best_chain = complete_chains[0]
        remaining = budget
        p_mask = 0
        for idx in best_chain:
            if prices[idx] <= remaining:
                p_mask |= (1 << idx)
                remaining -= prices[idx]
        
        bought = bin(p_mask).count("1")
        free = _free_count(items, p_mask)
        return bought + sum(free)
    
    # Fallback: greedy
    return _enumerate_best(items, budget)


def solver_025(solver_input: list) -> int:
    """solver_025: buy items with smallest factors, budget-aware."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Score = factor (lower is better) + free potential
    scores = []
    for i in range(n):
        free_count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        scores.append((factors[i] - free_count * 10, prices[i], i))  # Lower factor + more frees = better
    
    scores.sort()
    
    remaining = budget
    p_mask = 0
    for _, price, idx in scores:
        if price <= remaining:
            p_mask |= (1 << idx)
            remaining -= price
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


# ---------------------------------------------------------------------------
# Family 6: Hybrid-v2 (5 solvers)
# solver_026..solver_030
# ---------------------------------------------------------------------------


def solver_026(solver_input: list) -> int:
    """solver_026: try brute-force first, fall back to greedy."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    
    # If small enough, brute force
    if n <= 10:
        return _enumerate_best(items, budget)
    
    # Otherwise, greedy by density
    prices = [p for _, p in items]
    scores = [(1.0 / prices[i] if prices[i] > 0 else 0, i) for i in range(n)]
    scores.sort(reverse=True)
    
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_027(solver_input: list) -> int:
    """solver_027: try all 3 strategies, return best."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Strategy 1: brute force
    s1 = _enumerate_best(items, budget) if n <= 12 else 0
    
    # Strategy 2: greedy by density
    scores = [(1.0 / prices[i] if prices[i] > 0 else 0, i) for i in range(n)]
    scores.sort(reverse=True)
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    s2 = bin(p_mask).count("1") + sum(_free_count(items, p_mask))
    
    # Strategy 3: buy universal items first
    uni_indices = [i for i in range(n) if factors[i] == 1]
    remaining = budget
    p_mask = 0
    for idx in sorted(uni_indices, key=lambda i: prices[i]):
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    for idx in sorted(range(n), key=lambda i: prices[i]):
        if prices[idx] <= remaining and not (p_mask & (1 << idx)):
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    s3 = bin(p_mask).count("1") + sum(_free_count(items, p_mask))
    
    return max(s1, s2, s3)


def solver_028(solver_input: list) -> int:
    """solver_028: adaptive strategy based on problem structure."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    prices = [p for _, p in items]
    factors = [f for f, _ in items]
    
    # Analyze problem
    has_universal = any(f == 1 for f in factors)
    avg_price = sum(prices) / n
    
    if has_universal and n <= 8:
        # Use solver_004 strategy
        uni_idx = next(i for i, f in enumerate(factors) if f == 1)
        if prices[uni_idx] > budget:
            return 0
        remaining = budget - prices[uni_idx]
        p_mask = (1 << uni_idx)
        for idx in sorted(range(n), key=lambda i: 1.0 / prices[i] if prices[i] > 0 else 0, reverse=True):
            if idx != uni_idx and prices[idx] <= remaining:
                p_mask |= (1 << idx)
                remaining -= prices[idx]
        return bin(p_mask).count("1") + sum(_free_count(items, p_mask))
    elif avg_price < budget * 0.3:
        # Many affordable items: greedy density
        scores = [(1.0 / prices[i] if prices[i] > 0 else 0, i) for i in range(n)]
        scores.sort(reverse=True)
        remaining = budget
        p_mask = 0
        for _, idx in scores:
            if prices[idx] <= remaining:
                p_mask |= (1 << idx)
                remaining -= prices[idx]
        return bin(p_mask).count("1") + sum(_free_count(items, p_mask))
    else:
        # Few expensive items: brute force
        return _enumerate_best(items, budget)


def solver_029(solver_input: list) -> int:
    """solver_029: random strategy selection."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    rng = random.Random(999)
    n = len(items)
    prices = [p for _, p in items]
    
    strategy = rng.choice(["density", "cheapest", "expensive"])
    
    if strategy == "density":
        scores = [(1.0 / prices[i] if prices[i] > 0 else 0, i) for i in range(n)]
    elif strategy == "cheapest":
        scores = [(prices[i], i) for i in range(n)]
    else:
        scores = [(-prices[i], i) for i in range(n)]
    
    scores.sort()
    
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    
    bought = bin(p_mask).count("1")
    free = _free_count(items, p_mask)
    return bought + sum(free)


def solver_030(solver_input: list) -> int:
    """solver_030: ensemble of top strategies."""
    items, budget = _unpack(solver_input)
    if not items or budget == 0:
        return 0
    
    n = len(items)
    
    # Get results from multiple strategies
    results = []
    
    # Strategy 1: brute force (if feasible)
    if n <= 12:
        results.append(_enumerate_best(items, budget))
    
    # Strategy 2: density greedy
    prices = [p for _, p in items]
    scores = [(1.0 / prices[i] if prices[i] > 0 else 0, i) for i in range(n)]
    scores.sort(reverse=True)
    remaining = budget
    p_mask = 0
    for _, idx in scores:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    results.append(bin(p_mask).count("1") + sum(_free_count(items, p_mask)))
    
    # Strategy 3: free-item potential
    factors = [f for f, _ in items]
    free_potential = []
    for i in range(n):
        count = sum(1 for j in range(n) if j != i and factors[j] % factors[i] == 0)
        free_potential.append((count, -prices[i], i))
    free_potential.sort(reverse=True)
    remaining = budget
    p_mask = 0
    for _, _, idx in free_potential:
        if prices[idx] <= remaining:
            p_mask |= (1 << idx)
            remaining -= prices[idx]
    results.append(bin(p_mask).count("1") + sum(_free_count(items, p_mask)))
    
    return max(results) if results else 0
