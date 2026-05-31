from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import (
    lc322_greedy,
    lc322_lookahead_one,
    lc322_memo_collision,
    lc322_smallest_first,
)
from doctor.adversarial.lc322_ground_truth import GroundTruthDomainError, lc322_brute_force
from doctor.adversarial.lc322_oracle import LC322OracleEvaluator, evaluation_surface
from doctor.adversarial.lc322_synthesizer import _candidate, synthesize_lc322_inputs


LLM_PROMPT = """Write a solution to the coin change problem.

You are given an integer array coins representing coins of different denominations and an integer amount representing a total amount of money.
Return the fewest number of coins that you need to make up that amount.
If that amount of money cannot be made up by any combination of the coins, return -1.
You may assume that you have an infinite number of each kind of coin.
"""


def llm_solver_01(coins: list[int], amount: int) -> int:
    coins.sort(reverse=True)
    count = 0
    for c in coins:
        if amount >= c:
            count += amount // c
            amount %= c
    return count if amount == 0 else -1


def llm_solver_02(coins: list[int], amount: int) -> int:
    coins.sort()
    ans = 0
    for c in coins:
        while amount >= c:
            amount -= c
            ans += 1
    if amount == 0:
        return ans
    return -1


def llm_solver_03(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    coins = sorted(coins, reverse=True)
    best = 0
    for c in coins:
        if c <= amount:
            best = c
            break
    if best == 0:
        return -1
    if amount % best == 0:
        return amount // best
    return -1


def llm_solver_04(coins: list[int], amount: int) -> int:
    dp = [10**9] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for x in range(amount, c - 1, -1):
            dp[x] = min(dp[x], dp[x - c] + 1)
    return dp[amount] if dp[amount] != 10**9 else -1


def llm_solver_05(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    q = [(0, 0)]
    seen = {0}
    for value, steps in q:
        for c in coins:
            nxt = value + c
            if nxt == amount:
                return steps + 1
            if nxt < amount and nxt not in seen:
                seen.add(nxt)
                q.append((nxt, steps + 1))
        if steps > len(coins):
            break
    return -1


def llm_solver_06(coins: list[int], amount: int) -> int:
    coins = [c for c in coins if c <= amount]
    if amount == 0:
        return 0
    if not coins:
        return -1
    m = min(coins)
    if amount % m != 0:
        return -1
    return amount // m


def llm_solver_07(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    coins = sorted(coins)
    total = 0
    used = 0
    for c in coins:
        if total + c <= amount:
            total += c
            used += 1
    return used if total == amount else -1


def llm_solver_08(coins: list[int], amount: int) -> int:
    memo = {}

    def solve(rem: int) -> int:
        if rem == 0:
            return 0
        if rem < 0:
            return 10**6
        key = rem % len(coins)
        if key in memo:
            return memo[key]
        memo[key] = min(solve(rem - c) + 1 for c in coins)
        return memo[key]

    ans = solve(amount)
    return ans if ans < 10**6 else -1


def llm_solver_09(coins: list[int], amount: int) -> int:
    coins = sorted(coins, reverse=True)
    count = 0
    while amount > 0:
        picked = False
        for c in coins:
            if c <= amount and (amount - c == 0 or any(x <= amount - c for x in coins)):
                amount -= c
                count += 1
                picked = True
                break
        if not picked:
            return -1
    return count


def llm_solver_10(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0
    dp = [0] * (amount + 1)
    for i in range(1, amount + 1):
        choices = []
        for c in coins:
            if i - c >= 0 and dp[i - c] != -1:
                choices.append(dp[i - c] + 1)
        dp[i] = min(choices) if choices else 0
    return dp[amount] if dp[amount] != 0 else -1


LLM_SOLVERS: tuple[tuple[str, Callable[[list[int], int], int]], ...] = (
    ("llm_solver_01", llm_solver_01),
    ("llm_solver_02", llm_solver_02),
    ("llm_solver_03", llm_solver_03),
    ("llm_solver_04", llm_solver_04),
    ("llm_solver_05", llm_solver_05),
    ("llm_solver_06", llm_solver_06),
    ("llm_solver_07", llm_solver_07),
    ("llm_solver_08", llm_solver_08),
    ("llm_solver_09", llm_solver_09),
    ("llm_solver_10", llm_solver_10),
)


KNOWN_SOLVERS: tuple[tuple[str, Callable[[list[int], int], int]], ...] = (
    ("lc322_greedy", lc322_greedy),
    ("lc322_smallest_first", lc322_smallest_first),
    ("lc322_memo_collision", lc322_memo_collision),
    ("lc322_lookahead_one", lc322_lookahead_one),
)


@dataclass(frozen=True)
class SolverResult:
    name: str
    accepted_count: int
    rejected_count: int
    total_count: int
    violated_predicates: tuple[str, ...]
    exception_types: tuple[str, ...]
    known_match: str


def main() -> None:
    batch = synthesize_lc322_inputs()
    evaluator = LC322OracleEvaluator()
    cases = tuple(batch.accepted)
    known_outputs = {
        name: tuple(_safe_output(fn, list(item.coins), item.amount) for item in cases)
        for name, fn in KNOWN_SOLVERS
    }
    results = []

    for name, solver in LLM_SOLVERS:
        accepted = 0
        rejected = 0
        violated: list[str] = []
        exception_types: list[str] = []
        outputs = []
        for item in cases:
            try:
                oracle_result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(item.coins, item.amount, item.generator_id),
                        item.validation_predicates,
                        item.generator_id,
                        item.input_id,
                    )
                )
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected += 1
                    outputs.append(("oracle_rejected", tuple(oracle_result.violated_predicate_ids)))
                    continue
                truth = lc322_brute_force(list(item.coins), item.amount)
                observed = solver(list(item.coins), item.amount)
                outputs.append(("ok", observed))
            except GroundTruthDomainError as exc:
                exception_types.append(type(exc).__name__)
                violated.append(f"{name}:truth_exception:{type(exc).__name__}")
                rejected += 1
                outputs.append(("exception", type(exc).__name__))
                continue
            except Exception as exc:
                exception_types.append(type(exc).__name__)
                violated.append(f"{name}:solver_exception:{type(exc).__name__}")
                rejected += 1
                outputs.append(("exception", type(exc).__name__))
                continue

            if observed == truth:
                accepted += 1
            else:
                rejected += 1
                violated.append(f"{name}:solver_output_mismatch")

        exact_matches = [known_name for known_name, known in known_outputs.items() if tuple(outputs) == known]
        known_match = exact_matches[0] if exact_matches else "new_failure_mode"
        results.append(
            SolverResult(
                name=name,
                accepted_count=accepted,
                rejected_count=rejected,
                total_count=accepted + rejected,
                violated_predicates=tuple(sorted(set(violated))),
                exception_types=tuple(sorted(set(exception_types))),
                known_match=known_match,
            )
        )

    print(f"LC322 adaptive LLM solver test")
    print(f"Prompt: {LLM_PROMPT!r}")
    print(f"Validated input count: {len(cases)}")
    print("Results:")
    for result in results:
        rate = result.accepted_count / result.total_count * 100 if result.total_count else 0.0
        flag = "YES" if rate > 20.0 else "NO"
        print(f"  {result.name}:")
        print(f"    Acceptance rate: {rate:.2f}% ({result.accepted_count}/{result.total_count})")
        print(f"    False pass count: {result.accepted_count}")
        print(f"    Violated predicates: {list(result.violated_predicates) if result.violated_predicates else 'none'}")
        print(f"    Exception types: {list(result.exception_types) if result.exception_types else 'none'}")
        print(f"    Known family match: {result.known_match}")
        print(f"    Acceptance >20% flag: {flag}")


def _safe_output(fn: Callable[[list[int], int], int], coins: list[int], amount: int):
    try:
        return ("ok", fn(coins, amount))
    except Exception as exc:
        return ("exception", type(exc).__name__)


if __name__ == "__main__":
    main()
