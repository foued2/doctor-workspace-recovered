"""Real benchmark solver 003: BFS with visited set, depth count (survivor).
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
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    visited = {0}
    while queue:
        total, depth = queue.popleft()
        for c in coins:
            nxt = total + c
            if nxt == amount:
                return depth + 1
            if nxt < amount and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, depth + 1))
    return -1
