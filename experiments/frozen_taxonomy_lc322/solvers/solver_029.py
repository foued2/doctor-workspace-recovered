"""External blind pack solver 029: recursive without memo, time-bounded.
Returns -1 if recursion exceeds time limit.
Fails on magnitude probes (large amounts).
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations

_CALL_LIMIT = 50_000


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = list(set(nums[:-1]))
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
    best = [amount + 1]

    def _f(rem: int) -> int:
        counter[0] += 1
        if counter[0] > _CALL_LIMIT:
            return amount + 1
        if rem == 0:
            return 0
        if counter[0] > best[0] + 1:
            return amount + 1
        best_local = amount + 1
        for c in coins:
            if c <= rem:
                sub = _f(rem - c)
                if sub + 1 < best_local:
                    best_local = sub + 1
        if best_local < best[0]:
            best[0] = best_local
        return best_local

    r = _f(amount)
    return r if r <= amount else -1
