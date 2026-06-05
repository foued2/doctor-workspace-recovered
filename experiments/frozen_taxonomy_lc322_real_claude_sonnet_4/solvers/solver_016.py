"""Real benchmark solver 016: DP with forward asymmetric transition.
First pass uses all coins, second pass iterates sorted coins with
overwrite (not min). Corrupts transition-axis probes.
Pack source: hand_curated_real.
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
    INF = amount + 1
    dp = [0] + [INF] * amount
    for c in coins:
        for v in range(c, amount + 1):
            if dp[v - c] != INF:
                dp[v] = min(dp[v], dp[v - c] + 1)
    for c in sorted(coins):
        for v in range(c, amount + 1):
            if dp[v - c] != INF:
                dp[v] = dp[v - c] + 1
    return dp[amount] if dp[amount] != INF else -1
