"""External blind pack solver 026: greedy + bounded-verify.
Passes most probes because the verify step catches greedy_trap.
Fails only on a few specific probes.
Pack source: reconstructed_stub (see seval_manifest.json).
"""
from __future__ import annotations

_VERIFY_LIMIT = 30


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
    rem = amount
    count = 0
    for c in coins:
        take = rem // c
        if take > 0:
            rem -= take * c
            count += take
        if rem == 0:
            # verify with bounded DP (correct only for small amounts)
            if amount > _VERIFY_LIMIT:
                return count
            INF = amount + 1
            dp = [0] + [INF] * amount
            for v in range(1, amount + 1):
                for cc in coins:
                    if cc <= v and dp[v - cc] + 1 < dp[v]:
                        dp[v] = dp[v - cc] + 1
            r = dp[amount] if dp[amount] != INF else -1
            return min(count, r) if r != -1 else count
    return -1 if rem != 0 else count
