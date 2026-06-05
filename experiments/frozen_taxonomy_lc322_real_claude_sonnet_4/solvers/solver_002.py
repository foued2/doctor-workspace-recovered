"""Real benchmark solver 002: top-down recursion with full memo (survivor).
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
    INF = amount + 1
    memo: dict[int, int] = {}

    def _f(remaining: int) -> int:
        if remaining == 0:
            return 0
        if remaining < 0:
            return INF
        if remaining in memo:
            return memo[remaining]
        best = INF
        for c in coins:
            sub = _f(remaining - c)
            if sub + 1 < best:
                best = sub + 1
        memo[remaining] = best
        return best

    r = _f(amount)
    return r if r != INF else -1
