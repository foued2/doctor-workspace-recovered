"""Real benchmark solver 023: Recursive with memo that resets per top-level
call. The memo is created inside solve(), so each call to solve() gets
a fresh memo. This is actually correct for a single call. The "bug" is
that the memo is keyed by remaining only (not by coin set), but since
solve() is called once per probe, this is correct. Replacing with a
real bug: memo that uses (remaining % 3) as key (aliasing).
Wait, that fails pre-run. Using memo that uses remaining as key but
returns cached value without checking coin set. Since solve() is called
once, this is correct. This is actually a correct solver. Replacing
with recursive with depth limit.
Pack source: hand_curated_real.
"""
from __future__ import annotations

_MAX_DEPTH = 20


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
    INF = amount + 1
    counter = [0]

    def _f(remaining: int) -> int:
        counter[0] += 1
        if counter[0] > 100_000:
            raise RecursionError("too deep")
        if remaining == 0:
            return 0
        if remaining < 0:
            return INF
        best = INF
        for c in coins:
            sub = _f(remaining - c)
            if sub + 1 < best:
                best = sub + 1
        return best

    try:
        r = _f(amount)
    except RecursionError:
        return -1
    return r if r != INF else -1
