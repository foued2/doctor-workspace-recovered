"""External blind pack solver 002: top-down DP with memoization.
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
    memo: dict[int, int] = {0: 0}

    def _f(v: int) -> int:
        if v in memo:
            return memo[v]
        best = amount + 1
        for c in coins:
            if c <= v:
                sub = _f(v - c)
                if sub + 1 < best:
                    best = sub + 1
        memo[v] = best
        return best

    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins) if coins else 0
    if g == 0:
        return 0 if amount == 0 else -1
    if amount % g != 0:
        return -1
    r = _f(amount)
    return r if r <= amount else -1
