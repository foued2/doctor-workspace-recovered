"""External blind pack solver 025: BFS limited to 3 distinct coin types.
Fails on probes with 4+ distinct coin types.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations

_MAX_TYPES = 3


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = sorted(set(nums[:-1]))
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
    if amount == 0:
        return 0
    # use only first _MAX_TYPES distinct coins
    coins = coins[:_MAX_TYPES]
    dist = [-1] * (amount + 1)
    dist[0] = 0
    frontier = [0]
    steps = 0
    while frontier:
        steps += 1
        new_frontier = []
        for v in frontier:
            for c in coins:
                nv = v + c
                if nv > amount:
                    continue
                if dist[nv] == -1:
                    dist[nv] = steps
                    if nv == amount:
                        return dist[nv]
                    new_frontier.append(nv)
        frontier = new_frontier
    return -1
