"""External blind pack solver 006: greedy descending (canonical failure).
Fails on greedy_trap_no_subdivision probes.
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
    count = 0
    remaining = amount
    for c in coins:
        while remaining >= c:
            remaining -= c
            count += 1
        if remaining == 0:
            return count
    return -1 if remaining != 0 else count
