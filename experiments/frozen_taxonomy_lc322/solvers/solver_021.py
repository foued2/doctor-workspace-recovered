"""External blind pack solver 021: recursive coin-first, no memo.
Fails on large amount probes due to recursion depth / time.
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
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins) if coins else 0
    if g == 0:
        return 0 if amount == 0 else -1
    if amount % g != 0:
        return -1

    counter = [0]

    def _f(remaining: int, idx: int) -> int:
        counter[0] += 1
        if counter[0] > 100_000:
            raise RecursionError("too deep")
        if remaining == 0:
            return 0
        if idx >= len(coins):
            return amount + 1
        skip = _f(remaining, idx + 1)
        c = coins[idx]
        take = amount + 1
        if c <= remaining:
            sub = _f(remaining - c, idx)
            if sub + 1 < take:
                take = sub + 1
        return skip if skip < take else take

    try:
        r = _f(amount, 0)
    except RecursionError:
        return -1
    return r if r <= amount else -1
