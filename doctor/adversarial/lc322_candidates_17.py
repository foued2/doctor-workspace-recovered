from __future__ import annotations

import json
import sys
from collections import deque
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import lc322_dp  # noqa: E402
from runners.run_solver_trajectory_dynamics_analysis import _lc322_trace  # noqa: E402
from solvers.lc322_true_case_b_solvers import (  # noqa: E402
    lc322_amount_outer_equivalent_dp,
    lc322_bfs_shortest_path,
    lc322_recursive_memo_exact,
)


OUTPUT_JSON = PROJECT_ROOT / "data" / "lc322_true_case_b_test.json"
STEPS = tuple(range(2, 9))
PASS_SILHOUETTE_MIN = 0.10
PASS_NN_RATE_MIN = 0.70

Solver = Callable[[list[int]], int]

GENUINE_SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc322_canonical_dp", lc322_dp),
    ("lc322_sorted_coin_outer_dp", lambda nums: _coin_outer_dp(nums, "asc")),
    ("lc322_reverse_coin_outer_dp", lambda nums: _coin_outer_dp(nums, "desc")),
)

ATTEMPTED_FAKES: tuple[tuple[str, Solver], ...] = (
    ("lc322_amount_outer_equivalent_dp", lc322_amount_outer_equivalent_dp),
    ("lc322_bfs_shortest_path", lc322_bfs_shortest_path),
    ("lc322_recursive_memo_exact", lc322_recursive_memo_exact),
)

REFERENCE_IDS = ("lc322_canonical_dp", "lc322_sorted_coin_outer_dp", "lc322_reverse_coin_outer_dp")


def _round(value: float) -> float:
    return round(float(value), 6)


def _split(nums: list[int]) -> tuple[list[int], int]:
    if not nums:
        return [], 0
    return [value for value in nums[:-1] if value > 0], int(nums[-1])


def _exact_truth(coins: list[int], amount: int) -> int:
    if amount < 0:
        return -1
    inf = 10**9
    dp = [inf] * (amount + 1)
    dp[0] = 0
    for coin in sorted(set(coin for coin in coins if coin > 0)):
        for value in range(coin, amount + 1):
            dp[value] = min(dp[value], dp[value - coin] + 1)
    return -1 if dp[amount] >= inf else int(dp[amount])


def _coin_outer_dp(nums: list[int], order: str) -> int:
    coins, amount = _split(nums)
    if order == "asc":
        coins = sorted(coins)
    elif order == "desc":
        coins = sorted(coins, reverse=True)
    if amount < 0:
        return -1
    inf = 10**9
    dp = [inf] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        for value in range(coin, amount + 1):
            dp[value] = min(dp[value], dp[value - coin] + 1)
    return -1 if dp[amount] >= inf else int(dp[amount])


def _coin_outer_trace(nums: list[int], order: str) -> list[float]:
    coins, amount = _split(nums)
    if order == "asc":
        coins = sorted(coins)
    elif order == "desc":
        coins = sorted(coins, reverse=True)
    if amount < 0:
        return [-1.0]
    inf = 10**9
    dp = [inf] * (amount + 1)
    dp[0] = 0
    trace = [0.0]
    for coin in coins:
        for value in range(coin, amount + 1):
            candidate = dp[value - coin] + 1
            if candidate < dp[value]:
                dp[value] = candidate
                trace.append(float(value))
    return trace


def _amount_outer_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    if amount < 0:
        return [-1.0]
    inf = 10**9
    dp = [inf] * (amount + 1)
    dp[0] = 0
    trace = [0.0]
    for value in range(1, amount + 1):
        best = inf
        for coin in coins:
            if coin <= value:
                best = min(best, dp[value - coin] + 1)
        dp[value] = best
        trace.append(float(dp[value] if dp[value] < inf else -1))
    return trace


def _bfs_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    if amount == 0:
        return [0.0]
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    seen = {0}
    trace = [0.0]
    while queue:
        value, steps = queue.popleft()
        trace.append(float(value))
        for coin in coins:
            nxt = value + coin
            if nxt == amount:
                trace.append(float(nxt))
                return trace
            if nxt < amount and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, steps + 1))
    return trace


def _memo_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    trace: list[float] = []
    if amount > 300:
        return _amount_outer_trace(nums)
    sys.setrecursionlimit(max(sys.getrecursionlimit(), amount * 20 + 1000, 100000))

    @lru_cache(maxsize=None)
    def solve(remaining: int) -> int:
        trace.append(float(remaining))
        if remaining == 0:
            return 0
        if remaining < 0:
            return 10**9
        return min(solve(remaining - coin) + 1 for coin in coins) if coins else 10**9

    solve(amount)
    return trace


def _trace(solver_id: str, nums: list[int]) -> list[float]:
    if solver_id == "lc322_canonical_dp":
        return _lc322_trace("lc322_dp", nums)
    if solver_id == "lc322_sorted_coin_outer_dp":
        return _coin_outer_trace(nums, "asc")
    if solver_id == "lc322_reverse_coin_outer_dp":
        return _coin_outer_trace(nums, "desc")
    if solver_id == "lc322_amount_outer_equivalent_dp":
        return _amount_outer_trace(nums)
    if solver_id == "lc322_bfs_shortest_path":
        return _bfs_trace(nums)
    if solver_id == "lc322_recursive_memo_exact":
        return _memo_trace(nums)
    return [0.0]


def _state_at(trace: list[float], step: int) -> float:
    if not trace:
        return 0.0
    index = step - 1
    if index < len(trace):
        return float(trace[index])
    return float(trace[-1])


def _pad(trace: list[float], length: int) -> np.ndarray:
    if not trace:
        return np.zeros(length)
    if len(trace) >= length:
        return np.array(trace[:length], dtype=float)
    return np.array([*trace, *([trace[-1]] * (length - len(trace)))], dtype=float)


def _trace_distance(left: list[float], right: list[float], length: int) -> float:
    lvec = _pad(left, length)
    rvec = _pad(right, length)
    scale = max(float(np.max(np.abs(lvec))), float(np.max(np.abs(rvec))), 1.0)
    return float(np.mean(np.abs(lvec - rvec)) / scale)


def _step_distance(left: list[float], right: list[float], step: int) -> float:
    lval = _state_at(left, step)
    rval = _state_at(right, step)
    return abs(lval - rval) / max(abs(lval), abs(rval), 1.0)


def _expanded_suite() -> list[dict[str, Any]]:
    cases: list[tuple[list[int], int, str]] = [
        ([1], 0, "edge_amount_zero"),
        ([1], 17, "single_coin"),
        ([2], 3, "unreachable_single_coin"),
        ([7], 49, "single_coin"),
        ([2, 4, 8], 15, "unreachable_gcd"),
        ([6, 10, 14], 25, "unreachable_gcd"),
        ([1, 5, 10, 25], 30, "standard_us"),
        ([1, 5, 10, 25], 63, "standard_us"),
        ([1, 5, 10, 25], 511, "large_standard_us"),
        ([1, 5, 10, 25], 999, "large_standard_us"),
        ([1, 3, 4], 6, "greedy_fails"),
        ([1, 3, 4], 18, "greedy_fails"),
        ([1, 7, 10], 14, "greedy_fails"),
        ([1, 7, 10], 28, "greedy_fails"),
        ([1, 6, 10], 12, "greedy_fails"),
        ([1, 6, 10], 72, "greedy_fails"),
        ([2, 5, 10], 27, "no_clean_divisibility"),
        ([3, 7, 12], 24, "no_clean_divisibility"),
        ([4, 9, 11], 18, "no_clean_divisibility"),
        ([5, 8, 17], 34, "no_clean_divisibility"),
        ([6, 10, 15], 30, "no_clean_divisibility"),
        ([1, 11, 20], 66, "large_irregular"),
        ([1, 12, 25], 74, "large_irregular"),
        ([4, 17, 29], 533, "large_no_clean_divisibility"),
        ([6, 19, 41], 587, "large_no_clean_divisibility"),
        ([9, 28, 43], 611, "large_no_clean_divisibility"),
        ([11, 37, 58], 719, "large_no_clean_divisibility"),
    ]
    generated_sets = [
        ([1, 4, 9], range(31, 91, 7), "generated_irregular"),
        ([2, 7, 13], range(35, 100, 8), "generated_irregular"),
        ([3, 8, 20], range(42, 132, 11), "generated_irregular"),
        ([5, 12, 31], range(65, 170, 13), "generated_irregular"),
        ([1, 17, 43], range(501, 621, 17), "generated_large"),
        ([7, 23, 51], range(502, 650, 19), "generated_large"),
        ([13, 29, 47], range(503, 700, 23), "generated_large"),
    ]
    for coins, amounts, tag in generated_sets:
        for amount in amounts:
            cases.append((coins, amount, tag))
    rows = []
    seen: set[tuple[tuple[int, ...], int]] = set()
    for coins, amount, tag in cases:
        key = (tuple(coins), int(amount))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"nums": [*coins, int(amount)], "truth": _exact_truth(coins, int(amount)), "category": tag})
    return rows


def _records(rows: list[dict[str, Any]], fakes: list[tuple[str, Solver]]) -> list[dict[str, Any]]:
    records = []
    solvers = [*[(sid, "genuine", fn) for sid, fn in GENUINE_SOLVERS], *[(sid, "fake", fn) for sid, fn in fakes]]
    for solver_id, group, solver in solvers:
        for index, row in enumerate(rows):
            nums = list(row["nums"])
            truth = int(row["truth"])
            output = int(solver(nums))
            trace = _trace(solver_id, nums)
            references = {ref_id: _trace(ref_id, nums) for ref_id in REFERENCE_IDS}
            records.append(
                {
                    "solver_id": solver_id,
                    "group": group,
                    "input_index": index,
                    "category": row["category"],
                    "output": output,
                    "truth": truth,
                    "expanded_suite_pass": output == truth,
                    "step_divergence": {
                        f"n{step}": _round(np.mean([_step_distance(trace, ref, step) for ref in references.values()]))
                        for step in STEPS
                    },
                    "prefix_vector": {
                        f"n{step}": [_round(_trace_distance(trace, ref, step)) for ref in references.values()]
                        for step in STEPS
                    },
                }
            )
    return records


def _pass_rates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for solver_id in sorted({row["solver_id"] for row in rows}):
        subset = [row for row in rows if row["solver_id"] == solver_id]
        result[solver_id] = {
            "group": subset[0]["group"],
            "pass_rate": _round(sum(1 for row in subset if row["expanded_suite_pass"]) / len(subset)),
            "passed": sum(1 for row in subset if row["expanded_suite_pass"]),
            "total": len(subset),
        }
    return result


def _silhouette(matrix: np.ndarray, labels: list[str]) -> float:
    scores = []
    for index, label in enumerate(labels):
        distances = np.linalg.norm(matrix - matrix[index], axis=1)
        same = [distances[j] for j, other in enumerate(labels) if other == label and j != index]
        other = [distances[j] for j, other_label in enumerate(labels) if other_label != label]
        if not same or not other:
            continue
        a = float(np.mean(same))
        b = float(np.mean(other))
        denom = max(a, b)
        scores.append(0.0 if denom == 0 else (b - a) / denom)
    return float(np.mean(scores)) if scores else 0.0


def _same_group_nearest_rate(matrix: np.ndarray, labels: list[str]) -> float:
    same = 0
    for index, label in enumerate(labels):
        distances = np.linalg.norm(matrix - matrix[index], axis=1)
        distances[index] = np.inf
        nearest = int(np.argmin(distances))
        if labels[nearest] == label:
            same += 1
    return same / len(labels) if labels else 0.0


def _distribution(values: list[float]) -> dict[str, float]:
    arr = np.array(values, dtype=float)
    return {
        "count": int(len(values)),
        "mean": _round(np.mean(arr)),
        "std": _round(np.std(arr)),
        "min": _round(np.min(arr)),
        "median": _round(np.median(arr)),
        "max": _round(np.max(arr)),
    }


def _separation(records: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    labels = [record["group"] for record in records]
    for step in STEPS:
        key = f"n{step}"
        matrix = np.array([record["prefix_vector"][key] for record in records], dtype=float)
        genuine = [record["step_divergence"][key] for record in records if record["group"] == "genuine"]
        fake = [record["step_divergence"][key] for record in records if record["group"] == "fake"]
        silhouette = _silhouette(matrix, labels)
        nn_rate = _same_group_nearest_rate(matrix, labels)
        result[key] = {
            "silhouette": _round(silhouette),
            "same_group_nearest_rate": _round(nn_rate),
            "genuine_divergence_distribution": _distribution(genuine),
            "fake_divergence_distribution": _distribution(fake),
            "mean_gap_fake_minus_genuine": _round(np.mean(fake) - np.mean(genuine)),
            "pass": bool(silhouette >= PASS_SILHOUETTE_MIN and nn_rate >= PASS_NN_RATE_MIN),
        }
    return result


def _category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        result[row["category"]] = result.get(row["category"], 0) + 1
    return dict(sorted(result.items()))


def main() -> None:
    suite = _expanded_suite()
    attempt_records = _records(suite, list(ATTEMPTED_FAKES))
    pass_rates = _pass_rates(attempt_records)
    passing_fakes = [
        (solver_id, solver)
        for solver_id, solver in ATTEMPTED_FAKES
        if pass_rates[solver_id]["pass_rate"] == 1.0
    ]
    if not passing_fakes:
        outcome = "C"
        separation = {}
        pass_steps: list[str] = []
        analysis_records = []
    else:
        analysis_records = _records(suite, passing_fakes)
        separation = _separation(analysis_records)
        pass_steps = [step for step, payload in separation.items() if payload["pass"]]
        outcome = "A" if pass_steps else "B"
    report = {
        "objective": "True Case B attempt for LC322: can oracle-passing alternate constructions pass an aggressive expanded suite, and does trajectory separate them from genuine DP-style solvers?",
        "outcome_definitions": {
            "A": "Fake passes expanded suite, trajectory still separates.",
            "B": "Fake passes expanded suite, trajectory cannot separate.",
            "C": "Fake cannot be constructed to pass expanded suite.",
        },
        "outcome": outcome,
        "expanded_suite_case_count": len(suite),
        "expanded_suite_category_counts": _category_counts(suite),
        "large_amount_case_count": sum(1 for row in suite if row["nums"][-1] > 500),
        "attempted_fake_pass_rates": pass_rates,
        "passing_fakes": [solver_id for solver_id, _solver in passing_fakes],
        "reference_solvers": list(REFERENCE_IDS),
        "genuine_solvers": [solver_id for solver_id, _solver in GENUINE_SOLVERS],
        "pass_criterion": {
            "silhouette_min": PASS_SILHOUETTE_MIN,
            "same_group_nearest_rate_min": PASS_NN_RATE_MIN,
        },
        "separation_by_step": separation,
        "pass_steps": pass_steps,
        "analysis_execution_count": len(analysis_records),
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_JSON), "outcome": outcome, "pass_steps": pass_steps}, indent=2))


if __name__ == "__main__":
    main()
