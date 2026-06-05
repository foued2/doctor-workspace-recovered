"""Real benchmark solver 030: BFS with visited set, no depth tracking
bug. Uses a list for queue (not deque) - slow but correct. This is
actually correct. Replacing with BFS that has a wrong initial depth.
Starts with depth=1 instead of depth=0. Returns depth+1 (off by one).
Fails pre-run. Replacing with BFS that uses min-heap (Dijkstra-like)
which gives shortest path correctly. This is correct. Replacing with
DP that has overwrite for amount divisible by 3.
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
            if dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    if amount % 3 == 0:
        for c in sorted(coins):
            for v in range(c, amount + 1):
                if dp[v - c] != INF:
                    dp[v] = dp[v - c] + 1
    return dp[amount] if dp[amount] != INF else -1
