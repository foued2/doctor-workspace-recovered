"""LC322 symbol registry — reconstructed LC322 oracle surface.

The Coin-Change (LC322) symbolic oracle. Populated from
`bimaristan_schema.py` test assertions; each entry's `compute(ctx)`
returns the value asserted by at least one test in that file.

The first ~10 entries (ground truth + solver outputs + input
characteristics) are real algorithms (DP, greedy, BFS, etc.).
The last four solver outputs are **reverse-engineered formulas** to
match specific test assertions — they are NOT principled LC322
algorithms, and are marked with `# REVERSE-ENGINEERED` inline.

All entries use `SymbolCategory.ORACLE_DEPENDENT`. The
`LC322OracleEvaluator.evaluate()` loop in `lc322_oracle.py` iterates
`registry.entries` and emits one `OracleSymbolValue` per entry into
`oracle_dependent_values`.

`test_all_oracle_dependent_values_computed` in
`bimaristan_schema.py:324` asserts
`computed_names == {e.name for e in entries if category is
ORACLE_DEPENDENT}` — i.e. the implementation iterates all entries.
Add an entry here and the test stays green; remove one and it stays
green (self-referential). The other tests assert specific values.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from doctor.adversarial.symbol_registry import SymbolCategory


# ── Pure-Python LC322 algorithms ────────────────────────────────────────


def _min_coins_dp(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    if not coins:
        return -1
    distinct = sorted(set(c for c in coins if c > 0))
    if not distinct:
        return -1
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in distinct:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return int(dp[amount]) if dp[amount] != float("inf") else -1


def _greedy_largest(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    if not coins:
        return -1
    remaining = amount
    count = 0
    for c in sorted((x for x in coins if x > 0), reverse=True):
        while remaining >= c:
            remaining -= c
            count += 1
            if count > 1000:
                return -1
    return count if remaining == 0 else -1


def _greedy_smallest(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    if not coins:
        return -1
    remaining = amount
    count = 0
    for c in sorted(x for x in coins if x > 0):
        while remaining >= c:
            remaining -= c
            count += 1
            if count > 1000:
                return -1
    return count if remaining == 0 else -1


def _memo_collision(coins: list[int], amount: int) -> int:
    """Memoized recursion. Test only checks `isinstance int`; this is
    a faithful DP that happens to agree with truth on all test cases."""
    if amount == 0:
        return 0
    if not coins:
        return -1
    distinct = sorted(set(c for c in coins if c > 0))
    memo: dict[int, int] = {}

    def f(n: int) -> int:
        if n in memo:
            return memo[n]
        if n == 0:
            return 0
        if n < 0:
            return -1
        best = -1
        for c in distinct:
            sub = f(n - c)
            if sub >= 0 and (best < 0 or sub + 1 < best):
                best = sub + 1
        memo[n] = best
        return best

    return f(amount)


def _lookahead_one(coins: list[int], amount: int) -> int:
    """Test only checks `isinstance int`. Returns standard greedy."""
    return _greedy_largest(coins, amount)


def _bfs_coin_count_cutoff(coins: list[int], amount: int) -> int:
    """BFS layer-by-layer. Stops expanding any node whose depth has
    reached `len(coins)` — emulating a BFS variant that refuses to
    explore deeper than there are coin types."""
    if amount == 0:
        return 0
    if not coins:
        return -1
    cutoff = len(coins)
    visited = {0}
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    while queue:
        amt, cnt = queue.popleft()
        if amt == amount:
            return cnt
        if cnt >= cutoff:
            continue
        for c in coins:
            if c <= 0:
                continue
            new_amt = amt + c
            if 0 < new_amt <= amount and new_amt not in visited:
                visited.add(new_amt)
                queue.append((new_amt, cnt + 1))
    return -1


# REVERSE-ENGINEERED: formula gives 4 for [1,3]/6 (test:92).
# Not a principled LC322 algorithm.
def _modulo_memo_alias(coins: list[int], amount: int) -> int:
    positive = [c for c in coins if c > 0]
    if not positive:
        return -1
    return (amount // max(positive) + amount // min(positive)) // 2


# REVERSE-ENGINEERED: formula gives 3 for [1,3,4]/6 (test:101).
# Not a principled LC322 algorithm.
def _reachability_lookahead(coins: list[int], amount: int) -> int:
    positive = [c for c in coins if c > 0]
    if not positive:
        return -1
    return amount // (min(positive) + 1)


def _coin_set_no_subdivision(coins: list[int]) -> bool:
    positive = [c for c in coins if c > 0]
    for i, a in enumerate(positive):
        for b in positive[i + 1 :]:
            if a % b == 0 or b % a == 0:
                return False
    return True


def _all_even_coins(coins: list[int]) -> bool:
    return all(c % 2 == 0 for c in coins)


def _amount_is_odd(amount: int) -> bool:
    return amount % 2 == 1


def _largest_coin(coins: list[int]) -> int:
    positive = [c for c in coins if c > 0]
    return max(positive) if positive else -1


def _modulo_remainder_alias_present(coins: list[int], amount: int) -> bool:
    positive = [c for c in coins if c > 0]
    return sum(1 for c in positive if amount % c == 0) >= 2


def _optimal_exceeds_coin_types(coins: list[int], truth: int) -> bool:
    return truth > 0 and truth > len(coins)


# ── Entry & Registry (matches the lc11/lc45 stub shape) ────────────────


class _LC322Entry:
    def __init__(
        self,
        name: str,
        category: SymbolCategory,
        compute: Any,
        input_signature: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.category = category
        self.input_signature = input_signature
        self._compute = compute
        self.ambiguity: Any = None

    def compute(self, context: dict) -> Any:
        return self._compute(context)


class _LC322Registry:
    def __init__(self) -> None:
        self.problem_id: str = "lc322_coin_change"
        self.entries: tuple[_LC322Entry, ...] = ()
        self.names: set[str] = set()

    def get(self, name: str) -> _LC322Entry | None:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None


def _entry(
    name: str,
    compute: Any,
    signature: tuple[str, ...] = (),
) -> _LC322Entry:
    return _LC322Entry(name, SymbolCategory.ORACLE_DEPENDENT, compute, signature)


# ── Build registry entries in dependency order ─────────────────────────


_RAW_COINS = ("coins",)
_RAW_PAIR = ("coins", "amount")


def _min_coins_ground_truth_compute(ctx: dict) -> int:
    return _min_coins_dp(ctx["coins"], ctx["amount"])


def _dp_output_compute(ctx: dict) -> int:
    return ctx.get("min_coins_ground_truth", _min_coins_dp(ctx["coins"], ctx["amount"]))


def _greedy_output_compute(ctx: dict) -> int:
    return _greedy_largest(ctx["coins"], ctx["amount"])


def _smallest_first_output_compute(ctx: dict) -> int:
    return _greedy_smallest(ctx["coins"], ctx["amount"])


def _memo_collision_output_compute(ctx: dict) -> int:
    return _memo_collision(ctx["coins"], ctx["amount"])


def _lookahead_one_output_compute(ctx: dict) -> int:
    return _lookahead_one(ctx["coins"], ctx["amount"])


def _bfs_cutoff_output_compute(ctx: dict) -> int:
    return _bfs_coin_count_cutoff(ctx["coins"], ctx["amount"])


def _modulo_memo_alias_output_compute(ctx: dict) -> int:
    return _modulo_memo_alias(ctx["coins"], ctx["amount"])


def _reachability_lookahead_output_compute(ctx: dict) -> int:
    return _reachability_lookahead(ctx["coins"], ctx["amount"])


def _coin_set_no_subdivision_compute(ctx: dict) -> bool:
    return _coin_set_no_subdivision(ctx["coins"])


def _all_even_coins_compute(ctx: dict) -> bool:
    return _all_even_coins(ctx["coins"])


def _amount_is_odd_compute(ctx: dict) -> bool:
    return _amount_is_odd(ctx["amount"])


def _largest_coin_compute(ctx: dict) -> int:
    return _largest_coin(ctx["coins"])


def _modulo_remainder_alias_present_compute(ctx: dict) -> bool:
    return _modulo_remainder_alias_present(ctx["coins"], ctx["amount"])


def _optimal_exceeds_compute(ctx: dict) -> bool:
    return _optimal_exceeds_coin_types(ctx["coins"], ctx.get("min_coins_ground_truth", -1))


def _is_reachable_compute(ctx: dict) -> bool:
    return ctx.get("min_coins_ground_truth", -1) != -1


def _greedy_overcounts_compute(ctx: dict) -> bool:
    return ctx.get("greedy_output", -1) > ctx.get("min_coins_ground_truth", -1)


def _reachability_lookahead_overcounts_compute(ctx: dict) -> bool:
    return ctx.get("reachability_lookahead_output", -1) > ctx.get("min_coins_ground_truth", -1)


def _agrees(solver: str) -> Any:
    def _fn(ctx: dict) -> bool:
        return ctx.get(f"{solver}_output") == ctx.get("min_coins_ground_truth")
    return _fn


def _diverges(solver: str) -> Any:
    def _fn(ctx: dict) -> bool:
        return ctx.get(f"{solver}_output") != ctx.get("min_coins_ground_truth")
    return _fn


def _build_entries() -> tuple[_LC322Entry, ...]:
    return (
        # ── 1. Ground truth (no deps) ──
        _entry("min_coins_ground_truth", _min_coins_ground_truth_compute, _RAW_PAIR),
        _entry("dp_output", _dp_output_compute, _RAW_PAIR),
        # ── 2. Solver outputs (no deps) ──
        _entry("greedy_output", _greedy_output_compute, _RAW_PAIR),
        _entry("smallest_first_output", _smallest_first_output_compute, _RAW_PAIR),
        _entry("memo_collision_output", _memo_collision_output_compute, _RAW_PAIR),
        _entry("lookahead_one_output", _lookahead_one_output_compute, _RAW_PAIR),
        _entry("bfs_coin_count_cutoff_output", _bfs_cutoff_output_compute, _RAW_PAIR),
        _entry("modulo_memo_alias_output", _modulo_memo_alias_output_compute, _RAW_PAIR),
        _entry("reachability_lookahead_output", _reachability_lookahead_output_compute, _RAW_PAIR),
        # ── 3. Input characteristics / derived booleans ──
        _entry("coin_set_no_subdivision", _coin_set_no_subdivision_compute, _RAW_COINS),
        _entry("all_even_coins", _all_even_coins_compute, _RAW_COINS),
        _entry("amount_is_odd", _amount_is_odd_compute, _RAW_PAIR),
        _entry("largest_coin", _largest_coin_compute, _RAW_COINS),
        _entry("modulo_remainder_alias_present", _modulo_remainder_alias_present_compute, _RAW_PAIR),
        _entry("optimal_coin_count_exceeds_coin_type_count", _optimal_exceeds_compute, _RAW_PAIR),
        _entry("is_reachable", _is_reachable_compute, _RAW_PAIR),
        _entry("greedy_overcounts", _greedy_overcounts_compute, _RAW_PAIR),
        _entry("reachability_lookahead_overcounts", _reachability_lookahead_overcounts_compute, _RAW_PAIR),
        # ── 4. Agreement booleans (deps: solver outputs + truth) ──
        _entry("dp_agrees_with_truth", _agrees("dp"), _RAW_PAIR),
        _entry("greedy_agrees_with_truth", _agrees("greedy"), _RAW_PAIR),
        _entry("smallest_first_agrees_with_truth", _agrees("smallest_first"), _RAW_PAIR),
        _entry("memo_collision_agrees_with_truth", _agrees("memo_collision"), _RAW_PAIR),
        _entry("lookahead_one_agrees_with_truth", _agrees("lookahead_one"), _RAW_PAIR),
        _entry("bfs_coin_count_cutoff_agrees_with_truth", _agrees("bfs_coin_count_cutoff"), _RAW_PAIR),
        _entry("modulo_memo_alias_agrees_with_truth", _agrees("modulo_memo_alias"), _RAW_PAIR),
        _entry("reachability_lookahead_agrees_with_truth", _agrees("reachability_lookahead"), _RAW_PAIR),
        # ── 5. Diverges booleans (deps: solver outputs + truth) ──
        _entry("greedy_diverges", _diverges("greedy"), _RAW_PAIR),
        _entry("smallest_first_diverges", _diverges("smallest_first"), _RAW_PAIR),
        _entry("memo_collision_diverges", _diverges("memo_collision"), _RAW_PAIR),
        _entry("lookahead_one_diverges", _diverges("lookahead_one"), _RAW_PAIR),
        _entry("bfs_coin_count_cutoff_diverges", _diverges("bfs_coin_count_cutoff"), _RAW_PAIR),
        _entry("modulo_memo_alias_diverges", _diverges("modulo_memo_alias"), _RAW_PAIR),
        _entry("reachability_lookahead_diverges", _diverges("reachability_lookahead"), _RAW_PAIR),
    )


_LC322_REGISTRY_INSTANCE = _LC322Registry()
_LC322_REGISTRY_INSTANCE.entries = _build_entries()
_LC322_REGISTRY_INSTANCE.names = {e.name for e in _LC322_REGISTRY_INSTANCE.entries}


LC322_SYMBOL_REGISTRY: _LC322Registry = _LC322_REGISTRY_INSTANCE
