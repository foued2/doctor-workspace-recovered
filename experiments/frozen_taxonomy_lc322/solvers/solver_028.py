"""External blind pack solver 028: DFS with first-coin priority.
Finds SOME solution, not necessarily the minimum.
Fails on greedy_trap probes (returns a non-minimal count).
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
    counter = [0]
    found = [amount + 1]

    def _dfs(rem: int, count: int) -> None:
        counter[0] += 1
        if counter[0] > 100_000:
            return
        if rem == 0:
            if count < found[0]:
                found[0] = count
            return
        if count >= found[0]:
            return
        # take the first coin that fits, in order (first-coin priority)
        for i, c in enumerate(coins):
            if c > rem:
                continue
            _dfs(rem - c, count + 1)
            if found[0] < amount + 1:
                return  # commit to first path that finds a solution

    _dfs(amount, 0)
    return found[0] if found[0] <= amount else -1
