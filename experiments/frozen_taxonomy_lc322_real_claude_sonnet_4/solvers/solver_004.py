"""Real benchmark solver 004: DP with GCD reachability precheck (survivor).
Pack source: hand_curated_real (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = [c for c in nums[:-1] if c > 0]
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
    INF = amount + 1
    dp = [0] + [INF] * amount
    for v in range(1, amount + 1):
        for c in coins:
            if c <= v and dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    return dp[amount] if dp[amount] != INF else -1
