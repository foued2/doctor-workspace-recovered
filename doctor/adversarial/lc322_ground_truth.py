"""LC322 Coin Change — ground truth (brute force BFS).

RECONSTRUCTED — original unrecoverable from PhotoRec.
Standard LC322 Coin Change BFS: minimum coins to make amount.
Returns -1 if unreachable (LC322 convention).
"""
from __future__ import annotations

from collections import deque


class GroundTruthDomainError(Exception):
    """Raised when input is not in the LC322 Coin Change domain."""


def lc322_brute_force(coins: list[int], amount: int) -> int:
    if amount < 0:
        raise GroundTruthDomainError(f"negative amount: {amount}")
    if amount == 0:
        return 0
    positive = [c for c in coins if c > 0]
    if not positive:
        return -1
    visited = {0}
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    while queue:
        amt, count = queue.popleft()
        for c in positive:
            nxt = amt + c
            if nxt == amount:
                return count + 1
            if nxt < amount and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, count + 1))
    return -1
