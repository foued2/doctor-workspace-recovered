"""Real benchmark solver 010: BFS with visited and pop-left, no cutoff (survivor).
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
    visited: set[int] = {0}
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    while queue:
        cur, steps = queue.popleft()
        for c in coins:
            nxt = cur + c
            if nxt == amount:
                return steps + 1
            if nxt < amount and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, steps + 1))
    return -1
