"""External blind pack solver 024: greedy with sum-of-coins sort.
Fails on a different set than family 2: passes some probes, fails on others.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = list(nums[:-1])
    amount = int(nums[-1])
    if amount < 0:
        return -1
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins) if coins else 0
    if g == 0:
        return 0 if amount == 0 else -1
    if amount % g != 0:
        return -1
    # sort by (sum of digits, value) - heuristic
    coins.sort(key=lambda c: (sum(int(d) for d in str(c)), c), reverse=True)
    rem = amount
    count = 0
    for c in coins:
        take = rem // c
        if take > 0:
            rem -= take * c
            count += take
        if rem == 0:
            return count
    return -1 if rem != 0 else count
