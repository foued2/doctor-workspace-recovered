"""External blind pack solver 010: greedy with quotient-priority ordering.
Fails on greedy_trap_no_subdivision probes.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    coins = list(nums[:-1])
    amount = int(nums[-1])
    if amount < 0:
        return -1
    coins.sort(key=lambda c: -c)
    count = 0
    remaining = amount
    for c in coins:
        take = remaining // c
        if take > 0:
            remaining -= take * c
            count += take
        if remaining == 0:
            return count
    return -1 if remaining != 0 else count
