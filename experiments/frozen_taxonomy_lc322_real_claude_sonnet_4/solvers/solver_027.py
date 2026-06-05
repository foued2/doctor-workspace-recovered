"""Real benchmark solver 027: Greedy with DP verify for amount <= 30.
Pack source: hand_curated_real.
"""
from __future__ import annotations

_VERIFY_LIMIT = 30


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = sorted([c for c in nums[:-1] if c > 0], reverse=True)
    amount = int(nums[-1])
    if amount < 0:
        return -1
    if amount == 0:
        return 0
    if not coins:
        return -1
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins)
    if amount % g != 0:
        return -1
    rem = amount
    greedy_count = 0
    for c in coins:
        take = rem // c
        if take > 0:
            rem -= take * c
            greedy_count += take
    if rem != 0:
        greedy_count = -1
    if amount <= _VERIFY_LIMIT:
        INF = amount + 1
        dp = [0] + [INF] * amount
        for cc in coins:
            for v in range(cc, amount + 1):
                if dp[v - cc] + 1 < dp[v]:
                    dp[v] = dp[v - cc] + 1
        dp_count = dp[amount] if dp[amount] != INF else -1
        return dp_count
    return greedy_count
