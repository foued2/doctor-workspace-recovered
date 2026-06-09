"""External blind pack solver 004: BFS over remainder states.
Exact solution; no failure modes expected on probe_index.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = list(set(nums[:-1]))
    amount = int(nums[-1])
    if amount < 0 or any(c <= 0 for c in coins):
        return -1
    from collections import deque
    from math import gcd
    from functools import reduce
    g = reduce(gcd, coins) if coins else 0
    if g == 0:
        return 0 if amount == 0 else -1
    if amount % g != 0:
        return -1
    if amount == 0:
        return 0
    dist = [-1] * (amount + 1)
    dist[0] = 0
    queue = deque([0])
    while queue:
        v = queue.popleft()
        for c in coins:
            nv = v + c
            if nv > amount:
                continue
            if dist[nv] == -1:
                dist[nv] = dist[v] + 1
                if nv == amount:
                    return dist[nv]
                queue.append(nv)
    return -1
