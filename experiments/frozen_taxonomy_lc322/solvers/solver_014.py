"""External blind pack solver with memo bucket size 32.
Fails on memo_collision probes (bucket aliasing).
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations

_BUCKET = 32


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = list(nums[:-1])
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
    memo: dict[tuple[int, int], int] = {}

    def _f(v: int, i: int) -> int:
        if v == 0:
            return 0
        if i >= len(coins):
            return amount + 1
        key = (v // _BUCKET, i)
        if key in memo:
            return memo[key]
        skip = _f(v, i + 1)
        take = amount + 1
        c = coins[i]
        if c <= v:
            sub = _f(v - c, i)
            if sub + 1 < take:
                take = sub + 1
        best = skip if skip < take else take
        memo[key] = best
        return best

    r = _f(amount, 0)
    return r if r <= amount else -1
