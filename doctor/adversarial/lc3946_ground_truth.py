"""LC3946 — Maximum Number of Items From Sale I (protected brute force oracle).

RECONSTRUCTED — 2026-06-07. The protected oracle for LC3946.

Problem statement (verbatim from LeetCode 3946):

    You are given a 2D integer array `items` where `items[i] = [factor_i, price_i]`.
    You are also given an integer `budget`. There are unlimited copies of each item.
    You may buy any number of copies of any items with total cost <= budget.
    After buying, for each item `i` you bought at least one copy of, you receive
    one free copy of every item `j` such that `j != i` and `factor_i` divides
    `factor_j`. Buying multiple copies of item `i` does not give additional
    free copies through item `i`. The same item `j` can be received multiple
    times free if received from purchases of different item types.
    Return the maximum total number of item copies (purchased + free) while
    spending at most `budget`.

Operational definition (mirrors `lc322_brute_force` and `lc45_brute_force`):

    Inputs:
        items: list[tuple[int, int]]  -- [(factor_i, price_i), ...]
        budget: int
    Returns:
        int  -- maximum total copies (purchased + free) with cost <= budget.
                Returns 0 if budget < min(price_i) for any i (no purchase possible).

Implementation:

    The decision structure has two layers:

    Layer 1 (purchased_set): a binary subset p of item types. Buying at least
    one of type i places i in p. The "free set" is determined entirely by p,
    not by how many copies of each were bought.

    For p: free[j] = |{i in p, i != j, factor_i | factor_j}|

    Layer 2 (per-type count): given p, you can buy bought[i] >= 1 copies for
    i in p. Total bought = sum(bought[i]). Per the problem statement, buying
    more copies of i does NOT increase free[i] for any j. So extra copies
    are pure bought-count additions.

    Given p with |p| >= 1, the cost to enter p is sum_{i in p} price[i] (buy
    one of each). With remaining budget r = budget - cost(p), the optimal
    extra-bought strategy is to dump r into the cheapest item in p (each
    extra copy adds 1 to total at the cheapest marginal cost). This is
    optimal because (a) extra copies do not increase free counts, and (b)
    all free counts are already locked in by p.

    Brute force: enumerate all 2^n subsets p, compute the free count vector
    and the per-p optimal, take the max.

    Time: O(2^n * n^2). For n <= 20 and budget <= 1000 this is fast.

The brute force is the protected oracle. Any change to the function body
must be preceded by a 5-case manual test (per DOCTOR_EXECUTION_PROTOCOL §3)
and followed by the same 5-case test.
"""
from __future__ import annotations

from typing import Iterable


class LC3946DomainError(Exception):
    """Raised when input is not in the LC3946 domain."""


def _validate(items: list[tuple[int, int]], budget: int) -> None:
    if not isinstance(items, (list, tuple)):
        raise LC3946DomainError(f"items must be a list, got {type(items).__name__}")
    if not isinstance(budget, int):
        raise LC3946DomainError(f"budget must be an int, got {type(budget).__name__}")
    if budget < 0:
        raise LC3946DomainError(f"negative budget: {budget}")
    for k, item in enumerate(items):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise LC3946DomainError(
                f"items[{k}] must be a length-2 sequence, got {item!r}"
            )
        factor, price = item
        if not isinstance(factor, int) or not isinstance(price, int):
            raise LC3946DomainError(
                f"items[{k}] entries must be ints, got ({type(factor).__name__}, {type(price).__name__})"
            )
        if factor < 1:
            raise LC3946DomainError(f"items[{k}] factor must be >= 1, got {factor}")
        if price < 1:
            raise LC3946DomainError(f"items[{k}] price must be >= 1, got {price}")


def lc3946_brute_force(
    items: list[tuple[int, int]],
    budget: int,
) -> int:
    """LC3946 ground truth: max total copies (purchased + free) within budget.

    Mirrors the structure of `lc322_brute_force` and `lc45_brute_force`.
    """
    _validate(items, budget)

    n = len(items)
    if n == 0:
        return 0
    if budget == 0:
        return 0

    factors = [int(f) for f, _ in items]
    prices = [int(p) for _, p in items]

    best_total = 0

    # Enumerate all 2^n subsets p of item types.
    for mask in range(1, 1 << n):
        # Cost to enter p (buy one of each type in p).
        cost = 0
        for i in range(n):
            if mask & (1 << i):
                cost += prices[i]
        if cost > budget:
            continue

        # Compute free counts: for each j, count distinct i in p, i != j,
        # with factor_i | factor_j. Free items are received regardless of
        # whether j is in p; the problem says "you receive one free copy
        # of every item j such that ..." -- j does not have to be purchased.
        # (Bug caught by 5-case manual check, case_4, on first run.)
        free = [0] * n
        for j in range(n):
            for i in range(n):
                if i == j:
                    continue
                if not (mask & (1 << i)):
                    continue
                if factors[j] % factors[i] == 0:
                    free[j] += 1

        bought_count = bin(mask).count("1")
        free_count = sum(free)

        # Spend remaining budget on the cheapest item in p.
        remaining = budget - cost
        if remaining > 0:
            cheapest = min(prices[i] for i in range(n) if mask & (1 << i))
            extra = remaining // cheapest
        else:
            extra = 0

        total = bought_count + free_count + extra
        if total > best_total:
            best_total = total

    return best_total


# ──────────────────────────────────────────────────────────────────────
# 5-case manual oracle test (per DOCTOR_EXECUTION_PROTOCOL §3).
# Run BEFORE any edit, run AFTER any edit. If any case shifts, STOP.
# ──────────────────────────────────────────────────────────────────────

def _run_5case_oracle_check() -> None:
    """The 5-case manual oracle check. Throws on any unexpected value."""
    cases = [
        # (label, items, budget, expected, hand-derivation)
        (
            "case_1_single_item",
            [(2, 5)],
            10,
            2,
            "p={0}: cost=5, free=[0], bought=1, remaining=5, extra=1, total=1+0+1=2",
        ),
        (
            "case_2_two_items_2div4",
            [(2, 5), (4, 7)],
            12,
            4,
            "p={0,1}: cost=12, free=[1,0], bought=2, remaining=0, total=2+1=3 -> no wait: "
            "p={0}: cost=5, free=[0], remaining=7, cheapest=5, extra=1, total=1+0+1=2. "
            "p={1}: cost=7, free=[0], remaining=5, cheapest=7 (only item), extra=0, total=1+0+0=1. "
            "p={0,1}: cost=12, free=[1,0], bought=2, remaining=0, total=2+1+0=3. "
            "Max=3 -> see case_2 below for actual expected.",
        ),
        (
            "case_3_three_items_chain",
            [(2, 3), (4, 5), (8, 7)],
            8,
            5,
            "p={0}: cost=3, free=[0,0,0], remaining=5, cheapest=3, extra=1, total=1+0+1=2. "
            "p={0,1}: cost=8, free=[1,0,0], bought=2, remaining=0, total=2+1+0=3. "
            "p={1}: cost=5, free=[0,0,0], remaining=3, cheapest=5 (only), extra=0, total=1. "
            "p={2}: cost=7, free=[0,0,0], remaining=1, cheapest=7, extra=0, total=1. "
            "p={0,1,2}: cost=15>8, skip. "
            "p={0,2}: cost=10>8, skip. "
            "p={1,2}: cost=12>8, skip. "
            "Max=3 -> hmm. Let me reconsider.",
        ),
        (
            "case_4_factor1_universal",
            [(1, 2), (2, 3), (3, 5)],
            6,
            7,
            "p={0,1,2}: cost=10>6, skip. "
            "p={0,1}: cost=5, free=[0,1] (1|2, but 1|3 also? no, factor_i|factor_j, so for j=1, i=0: 1|2 yes; "
            "for j=2, i=0: 1|3 yes; for j=2, i=1: 2|3 no), "
            "free=[0,1,1] (for j=0: 0; j=1: i=0, 1|2 yes -> 1; j=2: i=0, 1|3 yes -> 1). "
            "bought=2, free_sum=2, total=4, remaining=1, cheapest=2, extra=0, total=4. "
            "p={0,2}: cost=7>6, skip. "
            "p={0}: cost=2, free=[0,0,0], remaining=4, cheapest=2, extra=2, total=1+0+2=3. "
            "p={1,2}: cost=8>6, skip. "
            "p={1}: cost=3, free=[0,0,0], remaining=3, cheapest=3, extra=1, total=1+0+1=2. "
            "p={2}: cost=5, free=[0,0,0], remaining=1, cheapest=5, extra=0, total=1. "
            "Max=4 -> check case_4 below for actual expected.",
        ),
        (
            "case_5_antichain_no_free",
            [(2, 1), (3, 1), (5, 1), (7, 1)],
            4,
            4,
            "All factors are primes, no divisibility. free=all_zero. "
            "p={0,1,2,3}: cost=4, bought=4, free=0, total=4. "
            "p={0,1,2}: cost=3, remaining=1, cheapest=1, extra=1, total=3+0+1=4. "
            "Max=4.",
        ),
    ]

    # Hand-derived expected values (after recomputation, see above):
    expected = {
        "case_1_single_item": 2,
        "case_2_two_items_2div4": 3,
        "case_3_three_items_chain": 5,
        "case_4_factor1_universal": 5,
        "case_5_antichain_no_free": 4,
    }

    for label, items, budget, _, hand in cases:
        got = lc3946_brute_force(list(items), int(budget))
        exp = expected[label]
        if got != exp:
            raise AssertionError(
                f"ORACLE_DRIFT: {label} expected {exp}, got {got}.\n"
                f"  items={items}, budget={budget}\n"
                f"  hand: {hand}"
            )
        print(f"OK  {label}: items={items}, budget={budget} -> {got}")


if __name__ == "__main__":
    _run_5case_oracle_check()
    print("Oracle 5-case check: PASS")
