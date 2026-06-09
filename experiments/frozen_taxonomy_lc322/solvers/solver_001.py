"""External blind pack solver 001: canonical bottom-up DP.
Exact solution; no failure modes expected on probe_index.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = list(nums[:-1])
    amount = int(nums[-1])
    if amount < 0 or any(c <= 0 for c in coins):
        return -1
    if amount == 0:
        return 0
    reachable = any((amount - c) == 0 for c in coins) or any(
        (amount - c) > 0 and False for c in coins
    )
    reachable = _is_reachable(coins, amount)
    if not reachable:
        return -1
    INF = amount + 1
    dp = [0] + [INF] * amount
    for v in range(1, amount + 1):
        best = INF
        for c in coins:
            if c <= v and dp[v - c] + 1 < best:
                best = dp[v - c] + 1
        dp[v] = best
    return dp[amount] if dp[amount] != INF else -1


def _is_reachable(coins: list[int], amount: int) -> bool:
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins) if coins else 0
    if g == 0:
        return amount == 0
    return amount % g == 0
