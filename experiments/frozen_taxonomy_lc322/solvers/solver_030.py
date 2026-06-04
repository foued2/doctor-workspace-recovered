"""External blind pack solver 030: greedy with floor-of-half-coin heuristic.
Tries a different greedy: divide amount by 2*largest_coin, then greedy.
Fails on specific probes where the heuristic mispredicts.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = sorted(nums[:-1], reverse=True)
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
    # heuristic: predict coin count = amount // (2 * largest_coin)
    largest = coins[0] if coins else 1
    if largest == 0:
        return -1
    predicted = amount // (2 * largest) if 2 * largest > 0 else amount
    # do greedy with the predicted count as a soft bound
    rem = amount
    count = 0
    for c in coins:
        take = rem // c
        if take > 0:
            rem -= take * c
            count += take
        if rem == 0:
            # if predicted matches, return; else check
            if count <= predicted + 1:
                return count
            return -1
    return -1 if rem != 0 else count
