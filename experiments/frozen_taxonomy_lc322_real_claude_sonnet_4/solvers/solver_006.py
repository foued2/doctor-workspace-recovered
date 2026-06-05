"""Real benchmark solver 006: BFS tracking distance array (survivor).
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
    from collections import deque
    dist = [-1] * (amount + 1)
    dist[0] = 0
    queue: deque[int] = deque([0])
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
