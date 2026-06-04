"""LC45 Jump Game II — ground truth (brute force BFS).

RECONSTRUCTED — original unrecoverable from PhotoRec.
Standard LC45 Jump Game II BFS: minimum number of jumps to reach last index.
"""
from __future__ import annotations

from collections import deque


class GroundTruthDomainError(Exception):
    """Raised when input is not in the LC45 Jump Game domain."""


def lc45_brute_force(nums: list[int]) -> int:
    if not nums:
        raise GroundTruthDomainError("empty input")
    if len(nums) == 1:
        return 0
    if nums[0] == 0:
        raise GroundTruthDomainError("cannot move from start")
    visited = {0}
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    while queue:
        pos, jumps = queue.popleft()
        for step in range(1, nums[pos] + 1):
            nxt = pos + step
            if nxt >= len(nums) - 1:
                return jumps + 1
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, jumps + 1))
    raise GroundTruthDomainError("unreachable last index")
