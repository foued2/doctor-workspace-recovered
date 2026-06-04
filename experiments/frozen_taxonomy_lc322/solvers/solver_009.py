"""External blind pack solver 009: greedy with one-step lookbehind.
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
    i = 0
    while i < len(coins) and remaining > 0:
        c = coins[i]
        take = remaining // c
        if take == 0 and i + 1 < len(coins) and (remaining - coins[i + 1]) >= 0:
            i += 1
            continue
        remaining -= take * c
        count += take
        i += 1
    return -1 if remaining != 0 else count
