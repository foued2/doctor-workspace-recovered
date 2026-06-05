"""Real benchmark solver 008: DP over coin index (knapsack-style) (survivor).
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
    n = len(coins)
    INF = amount + 1
    dp = [[0] * (amount + 1) for _ in range(n + 1)]
    for i in range(1, amount + 1):
        dp[0][i] = INF
    for i in range(1, n + 1):
        c = coins[i - 1]
        for v in range(1, amount + 1):
            skip = dp[i - 1][v]
            take = INF
            if c <= v:
                take = dp[i][v - c] + 1
            dp[i][v] = skip if skip < take else take
    return dp[n][amount] if dp[n][amount] != INF else -1
