"""Real benchmark solver 022: Recursive with no memoization.
Works for small amounts (pre-run). Fails on large amounts (magnitude
probes) via exponential time.
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
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins)
    if amount % g != 0:
        return -1
    INF = amount + 1
    counter = [0]

    def _f(remaining: int) -> int:
        counter[0] += 1
        if counter[0] > 100_000:
            raise RecursionError("recursive_no_memo: exceeded call limit")
        if remaining == 0:
            return 0
        if remaining < 0:
            return INF
        best = INF
        for c in coins:
            sub = _f(remaining - c)
            if sub + 1 < best:
                best = sub + 1
        return best

    try:
        r = _f(amount)
    except RecursionError:
        return -1
    return r if r != INF else -1
