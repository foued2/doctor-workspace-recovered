"""External blind pack solver 003: iterative DP with early-exit pruning.
Exact solution; no failure modes expected on probe_index.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = sorted(set(nums[:-1]))
    amount = int(nums[-1])
    if amount < 0 or any(c <= 0 for c in coins):
        return -1
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins) if coins else 0
    if g == 0:
        return 0 if amount == 0 else -1
    if amount % g != 0:
        return -1
    INF = amount + 1
    dp = [0] + [INF] * amount
    for v in range(1, amount + 1):
        for c in coins:
            if c > v:
                break
            cand = dp[v - c] + 1
            if cand < dp[v]:
                dp[v] = cand
    return dp[amount] if dp[amount] != INF else -1
