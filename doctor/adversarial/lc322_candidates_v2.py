"""LC322 — Simplified v2 solver population (30 solvers, all fast).

All solvers run in O(amount * n) or faster.
"""
from __future__ import annotations

import random
from typing import Callable


def _parse_input(nums: list[int]) -> tuple[list[int], int]:
    if not nums:
        return [], 0
    return [c for c in nums[:-1] if c > 0], nums[-1]


def _dp_coins(coins, amount):
    if amount < 0:
        return -1
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return -1 if dp[amount] == float("inf") else dp[amount]


def _greedy_largest(coins, amount):
    coins_sorted = sorted(coins, reverse=True)
    count = 0
    remaining = amount
    for c in coins_sorted:
        q = remaining // c
        count += q
        remaining -= q * c
    return -1 if remaining != 0 else count


def _greedy_smallest(coins, amount):
    coins_sorted = sorted(coins)
    count = 0
    remaining = amount
    for c in coins_sorted:
        q = remaining // c
        count += q
        remaining -= q * c
    return -1 if remaining != 0 else count


# Family 1: DP variants (solver_001-005)
def solver_001(nums):
    coins, amount = _parse_input(nums)
    return _dp_coins(coins, amount)

def solver_002(nums):
    coins, amount = _parse_input(nums)
    shuffled = coins.copy()
    random.Random(42).shuffle(shuffled)
    return _dp_coins(shuffled, amount)

def solver_003(nums):
    coins, amount = _parse_input(nums)
    shuffled = coins.copy()
    random.Random(123).shuffle(shuffled)
    return _dp_coins(shuffled, amount)

def solver_004(nums):
    coins, amount = _parse_input(nums)
    valid = [c for c in coins if c <= amount]
    return _dp_coins(valid, amount) if valid else -1

def solver_005(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for i in range(c, amount + 1):
            dp[i] = min(dp[i], dp[i - c] + 1)
    return -1 if dp[amount] == float("inf") else dp[amount]

# Family 2: Greedy variants (solver_006-010)
def solver_006(nums):
    coins, amount = _parse_input(nums)
    return _greedy_largest(coins, amount)

def solver_007(nums):
    coins, amount = _parse_input(nums)
    return _greedy_smallest(coins, amount)

def solver_008(nums):
    coins, amount = _parse_input(nums)
    from math import gcd
    from functools import reduce
    if not coins: return -1
    g = reduce(gcd, coins)
    if amount % g != 0: return -1
    scaled = [c // g for c in coins]
    return _greedy_largest(scaled, amount // g)

def solver_009(nums):
    coins, amount = _parse_input(nums)
    if not coins: return -1
    sorted_c = sorted(coins, key=lambda c: amount / c if c > 0 else 0, reverse=True)
    count = 0
    remaining = amount
    for c in sorted_c:
        q = remaining // c
        count += q
        remaining -= q * c
    return -1 if remaining != 0 else count

def solver_010(nums):
    coins, amount = _parse_input(nums)
    rng = random.Random(456)
    shuffled = coins.copy()
    rng.shuffle(shuffled)
    sorted_c = sorted(shuffled, key=lambda c: c + rng.random() * 0.1, reverse=True)
    count = 0
    remaining = amount
    for c in sorted_c:
        q = remaining // c
        count += q
        remaining -= q * c
    return -1 if remaining != 0 else count

# Family 3: Math shortcuts (solver_011-015)
def solver_011(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    if amount == 0: return 0
    from math import gcd
    from functools import reduce
    if not coins: return -1
    g = reduce(gcd, coins)
    if amount % g != 0: return -1
    return _dp_coins([c // g for c in coins], amount // g)

def solver_012(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    if len(coins) == 1:
        c = coins[0]
        return amount // c if amount % c == 0 else -1
    return _dp_coins(coins, amount)

def solver_013(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    if not coins: return -1
    min_coin = min(coins)
    reachable = [False] * (min_coin + 1)
    reachable[0] = True
    for c in coins:
        for i in range(min_coin + 1):
            if reachable[i]:
                reachable[(i + c) % (min_coin + 1)] = True
    if not reachable[amount % (min_coin + 1)]: return -1
    return _dp_coins(coins, amount)

def solver_014(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    max_coin = max(coins) if coins else 1
    return _dp_coins(coins, amount)

def solver_015(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    return _dp_coins(sorted(coins), amount)

# Family 4: Hybrid (solver_016-020)
def solver_016(nums):
    coins, amount = _parse_input(nums)
    g = _greedy_largest(coins, amount)
    if g != -1: return g
    return _dp_coins(coins, amount)

def solver_017(nums):
    coins, amount = _parse_input(nums)
    g = _greedy_smallest(coins, amount)
    if g != -1: return g
    return _dp_coins(coins, amount)

def solver_018(nums):
    coins, amount = _parse_input(nums)
    g = _greedy_largest(coins, amount)
    d = _dp_coins(coins, amount)
    if g == -1: return d
    if d == -1: return g
    return min(g, d)

def solver_019(nums):
    coins, amount = _parse_input(nums)
    if not coins: return -1
    max_coin = max(coins)
    lower = (amount + max_coin - 1) // max_coin
    d = _dp_coins(coins, amount)
    return d

def solver_020(nums):
    coins, amount = _parse_input(nums)
    rng = random.Random(789)
    coins_r = coins.copy()
    rng.shuffle(coins_r)
    return _dp_coins(coins_r, amount)

# Family 5: Edge case handlers (solver_021-025)
def solver_021(nums):
    coins, amount = _parse_input(nums)
    if amount == 0: return 0
    if amount < 0: return -1
    return _dp_coins(coins, amount)

def solver_022(nums):
    coins, amount = _parse_input(nums)
    if not coins: return -1 if amount > 0 else 0
    return _dp_coins(coins, amount)

def solver_023(nums):
    coins, amount = _parse_input(nums)
    if amount < 0: return -1
    if coins and amount < min(coins) and amount > 0: return -1
    return _dp_coins(coins, amount)

def solver_024(nums):
    coins, amount = _parse_input(nums)
    if len(coins) == 1:
        c = coins[0]
        return amount // c if amount % c == 0 else -1
    return _dp_coins(coins, amount)

def solver_025(nums):
    coins, amount = _parse_input(nums)
    results = []
    for fn in [solver_001, solver_006, solver_011, solver_016]:
        try:
            r = fn(nums)
            if r != -1: results.append(r)
        except: pass
    return min(results) if results else -1

# Family 6: Ensemble (solver_026-030)
def solver_026(nums):
    coins, amount = _parse_input(nums)
    return _dp_coins(coins, amount)

def solver_027(nums):
    coins, amount = _parse_input(nums)
    shuffled = coins.copy()
    random.Random(999).shuffle(shuffled)
    return _dp_coins(shuffled, amount)

def solver_028(nums):
    coins, amount = _parse_input(nums)
    sorted_c = sorted(coins)
    return _dp_coins(sorted_c, amount)

def solver_029(nums):
    coins, amount = _parse_input(nums)
    sorted_c = sorted(coins, reverse=True)
    return _dp_coins(sorted_c, amount)

def solver_030(nums):
    coins, amount = _parse_input(nums)
    return _dp_coins(coins, amount)
