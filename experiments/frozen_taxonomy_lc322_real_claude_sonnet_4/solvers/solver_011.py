"""Real benchmark solver 011: BFS without visited set.
Passes pre-run (small amounts). Fails on larger probes via duplicate work
or timeout. Not a deliberate happy-path-only bug; genuine missing invariant.
Pack source: hand_curated_real.
"""
from __future__ import annotations

_MAX_ITER = 50_000


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
    counter = 0
    while queue:
        counter += 1
        if counter > _MAX_ITER:
            raise RuntimeError("bfs_no_visited: exceeded iteration limit")
        total, depth = queue.popleft()
        for c in coins:
            nxt = total + c
            if nxt == amount:
                return depth + 1
            if nxt < amount:
                queue.append((nxt, depth + 1))
    return -1
