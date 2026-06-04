"""External blind pack solver 027: recursive backtracking, depth-limited.
Fails on probes needing > 20 coins (returns -1 prematurely).
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations

_MAX_DEPTH = 20


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

    best = [amount + 1]
    max_coin = max(coins) if coins else 1

    def _bt(rem: int, count: int) -> None:
        if rem == 0:
            if count < best[0]:
                best[0] = count
            return
        if count >= best[0] or count >= _MAX_DEPTH:
            return
        # lower-bound prune: if rem needs more coins than we can afford
        if rem > (best[0] - count - 1) * max_coin:
            return
        for c in coins:
            if c > rem:
                continue
            _bt(rem - c, count + 1)

    _bt(amount, 0)
    return best[0] if best[0] <= amount else -1
