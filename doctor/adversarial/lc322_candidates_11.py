from __future__ import annotations

import json
import math
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import (
    lc322_bfs_coin_count_cutoff,
    lc322_dp,
    lc322_greedy,
    lc322_lookahead_one,
    lc322_memo_collision,
    lc322_modulo_memo_alias,
    lc322_ordering_commitment,
    lc322_reachability_lookahead,
    lc322_smallest_first,
    lc322_transition_asymmetric_forward_dp,
)
from doctor.adversarial.lc45_candidates import (
    lc45_bfs_depth_cutoff,
    lc45_farthest_landing_path,
    lc45_first_window_max_then_greedy,
    lc45_frontier_off_by_one,
    lc45_max_landing_value,
    lc45_naive_greedy,
    lc45_reachable_boolean_confusion,
    lc45_three_step_window_dp,
    lc45_uniform_formula_generalizer,
    lc45_zero_dead_end_panic,
)
from runners.run_lc322_density_blindspot_diagnostic import MUTANTS, _dimension_samples, _single_use_dp
from runners.run_lc45_solver_population import _instances


OUTPUT_JSON = PROJECT_ROOT / "data" / "solver_trajectory_dynamics_analysis.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_126.md"

LC322_SAMPLE_CAP = 64


def _round(value: float) -> float:
    return round(float(value), 6)


def _split_lc322(nums: list[int]) -> tuple[list[int], int]:
    return [value for value in nums[:-1] if value > 0], int(nums[-1]) if nums else 0


def _entropy(values: list[float]) -> float:
    if not values:
        return 0.0
    labels = [f"{value:.3f}" for value in values]
    counts = Counter(labels)
    total = len(labels)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _pad(trace: list[float], length: int) -> np.ndarray:
    if not trace:
        return np.zeros(length)
    if len(trace) >= length:
        return np.array(trace[:length], dtype=float)
    return np.array([*trace, *([trace[-1]] * (length - len(trace)))], dtype=float)


def _trace_distance(left: list[float], right: list[float]) -> float:
    length = max(len(left), len(right), 1)
    lvec = _pad(left, length)
    rvec = _pad(right, length)
    scale = max(float(np.max(np.abs(lvec))), float(np.max(np.abs(rvec))), 1.0)
    return float(np.mean(np.abs(lvec - rvec)) / scale)


def _first_divergence(left: list[float], right: list[float]) -> float:
    length = max(len(left), len(right), 1)
    lvec = _pad(left, length)
    rvec = _pad(right, length)
    for index, (lval, rval) in enumerate(zip(lvec, rvec)):
        if round(float(lval), 6) != round(float(rval), 6):
            return index / max(length - 1, 1)
    return 1.0


def _lc322_greedy_trace(nums: list[int], order: str = "desc") -> list[float]:
    coins, amount = _split_lc322(nums)
    if order == "asc":
        ordered = sorted(coins)
    elif order == "given":
        ordered = coins
    elif order == "reverse_given":
        ordered = list(reversed(coins))
    else:
        ordered = sorted(coins, reverse=True)
    remaining = amount
    trace = [float(remaining)]
    for coin in ordered:
        while coin <= remaining:
            remaining -= coin
            trace.append(float(remaining))
    return trace


def _lc322_bfs_trace(nums: list[int], cutoff: bool = True) -> list[float]:
    coins, amount = _split_lc322(nums)
    if amount == 0:
        return [0.0]
    queue = [(0, 0)]
    seen = {0}
    trace = [0.0]
    for value, steps in queue:
        trace.append(float(value))
        for coin in coins:
            nxt = value + coin
            if nxt == amount:
                trace.append(float(nxt))
                return trace
            if nxt < amount and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, steps + 1))
        if cutoff and steps > len(coins):
            break
    return trace


def _lc322_dp_trace(nums: list[int], single_use: bool = False, forward_commit: bool = False) -> list[float]:
    coins, amount = _split_lc322(nums)
    if amount < 0:
        return [-1.0]
    inf = 10**9
    dp = [inf] * (amount + 1)
    dp[0] = 0
    trace = [0.0]
    if forward_commit:
        for value in range(1, amount + 1):
            for coin in sorted(coins):
                if coin <= value and dp[value - coin] != inf:
                    dp[value] = dp[value - coin] + 1
                    break
            trace.append(float(dp[value] if dp[value] != inf else -1))
    else:
        for coin in coins:
            iterator = range(amount, coin - 1, -1) if single_use else range(coin, amount + 1)
            for value in iterator:
                if dp[value - coin] + 1 < dp[value]:
                    dp[value] = dp[value - coin] + 1
                    trace.append(float(value))
    return trace


def _lc322_reachability_trace(nums: list[int]) -> list[float]:
    coins, amount = _split_lc322(nums)
    coins = sorted(coins, reverse=True)
    trace = [float(amount)]
    while amount > 0:
        picked = False
        for coin in coins:
            if coin <= amount and (amount - coin == 0 or any(x <= amount - coin for x in coins)):
                amount -= coin
                trace.append(float(amount))
                picked = True
                break
        if not picked:
            break
    return trace


def _lc322_memo_trace(nums: list[int], modulo: bool = False) -> list[float]:
    coins, amount = _split_lc322(nums)
    memo = {}
    trace: list[float] = []

    def solve(rem: int, depth: int = 0) -> int:
        trace.append(float(rem))
        if rem == 0:
            return 0
        if rem < 0 or depth > 40:
            return 10**6
        key = rem % len(coins) if modulo and coins else rem // 2
        if key in memo:
            return memo[key]
        result = min(solve(rem - coin, depth + 1) + 1 for coin in coins) if coins else 10**6
        memo[key] = result
        return result

    solve(amount)
    return trace


def _lc322_trace(solver_id: str, nums: list[int]) -> list[float]:
    if solver_id in {"lc322_dp", "reference", "mut_04_original"}:
        return _lc322_dp_trace(nums)
    if solver_id == "lc322_greedy":
        return _lc322_greedy_trace(nums, "desc")
    if solver_id == "lc322_smallest_first":
        return _lc322_greedy_trace(nums, "asc")
    if solver_id == "lc322_memo_collision":
        return _lc322_memo_trace(nums)
    if solver_id == "lc322_lookahead_one":
        return _lc322_greedy_trace(nums, "desc")
    if solver_id == "lc322_bfs_coin_count_cutoff":
        return _lc322_bfs_trace(nums, cutoff=True)
    if solver_id == "lc322_modulo_memo_alias":
        return _lc322_memo_trace(nums, modulo=True)
    if solver_id == "lc322_reachability_lookahead" or solver_id == "mut_06":
        return _lc322_reachability_trace(nums)
    if solver_id == "lc322_ordering_commitment" or solver_id == "mut_01":
        return _lc322_greedy_trace(nums, "given")
    if solver_id == "mut_02":
        return _lc322_greedy_trace(nums, "reverse_given")
    if solver_id == "mut_03":
        return _lc322_dp_trace(nums, single_use=True)
    if solver_id == "lc322_transition_asymmetric_forward_dp" or solver_id == "mut_04":
        return _lc322_dp_trace(nums, forward_commit=True)
    return [0.0]


def _lc45_greedy_trace(nums: list[int], mode: str) -> list[float]:
    if len(nums) <= 1:
        return [0.0]
    index = 0
    target = len(nums) - 1
    trace = [0.0]
    seen = set()
    while index < target:
        if index in seen or nums[index] <= 0:
            trace.append(float(index))
            return trace
        seen.add(index)
        farthest = min(target, index + nums[index])
        if farthest == target:
            trace.append(float(target))
            return trace
        candidates = range(index + 1, farthest + 1)
        if mode == "max_landing_value":
            index = max(candidates, key=lambda next_index: (nums[next_index], next_index))
        elif mode == "farthest_landing":
            index = max(candidates, key=lambda next_index: (next_index + nums[next_index], nums[next_index]))
        else:
            index = farthest
        trace.append(float(index))
    return trace


def _lc45_frontier_trace(nums: list[int]) -> list[float]:
    if len(nums) <= 1:
        return [0.0]
    farthest = 0
    current_end = 0
    trace = [0.0]
    for index in range(len(nums) - 1):
        farthest = max(farthest, index + nums[index])
        if index == current_end:
            current_end = farthest
            trace.append(float(current_end))
            if current_end >= len(nums) - 1:
                break
    return trace


def _lc45_bfs_trace(nums: list[int], depth_limit: int = 3) -> list[float]:
    if len(nums) <= 1:
        return [0.0]
    target = len(nums) - 1
    frontier = [(0, 0)]
    seen = {0}
    trace = [0.0]
    for index, jumps in frontier:
        trace.append(float(index))
        if jumps > depth_limit:
            break
        farthest = min(target, index + nums[index])
        for next_index in range(index + 1, farthest + 1):
            if next_index == target:
                trace.append(float(target))
                return trace
            if next_index not in seen:
                seen.add(next_index)
                frontier.append((next_index, jumps + 1))
    return trace


def _lc45_trace(solver_id: str, nums: list[int]) -> list[float]:
    if solver_id == "reference":
        return _lc45_frontier_trace(nums)
    if solver_id == "lc45_naive_greedy":
        return _lc45_greedy_trace(nums, "naive")
    if solver_id == "lc45_max_landing_value":
        return _lc45_greedy_trace(nums, "max_landing_value")
    if solver_id == "lc45_farthest_landing_path":
        return _lc45_greedy_trace(nums, "farthest_landing")
    if solver_id == "lc45_zero_dead_end_panic":
        return [-1.0] if any(value == 0 for value in nums[:-1]) else _lc45_frontier_trace(nums)
    if solver_id == "lc45_reachable_boolean_confusion":
        return _lc45_frontier_trace(nums)
    if solver_id == "lc45_bfs_depth_cutoff":
        return _lc45_bfs_trace(nums, 3)
    if solver_id == "lc45_three_step_window_dp":
        return _lc45_bfs_trace([min(value, 3) for value in nums], 100)
    if solver_id == "lc45_frontier_off_by_one":
        return _lc45_frontier_trace(nums)
    if solver_id == "lc45_uniform_formula_generalizer":
        return [float(value) for value in range(0, len(nums), max(nums[0], 1))] if len(set(nums)) == 1 else _lc45_greedy_trace(nums, "naive")
    if solver_id == "lc45_first_window_max_then_greedy":
        if len(nums) <= 1:
            return [0.0]
        first_farthest = min(len(nums) - 1, nums[0])
        if first_farthest <= 0:
            return [0.0]
        first = max(range(1, first_farthest + 1), key=lambda index: nums[index])
        return [0.0, float(first), *[float(first + value) for value in _lc45_greedy_trace(nums[first:], "naive")[1:]]]
    return [0.0]


LC322_SOLVERS: tuple[tuple[str, str, Callable[[list[int]], int]], ...] = (
    ("lc322_dp", "lc322_solver", lc322_dp),
    ("lc322_greedy", "lc322_solver", lc322_greedy),
    ("lc322_smallest_first", "lc322_solver", lc322_smallest_first),
    ("lc322_memo_collision", "lc322_solver", lc322_memo_collision),
    ("lc322_lookahead_one", "lc322_solver", lc322_lookahead_one),
    ("lc322_bfs_coin_count_cutoff", "lc322_solver", lc322_bfs_coin_count_cutoff),
    ("lc322_modulo_memo_alias", "lc322_solver", lc322_modulo_memo_alias),
    ("lc322_reachability_lookahead", "lc322_solver", lc322_reachability_lookahead),
    ("lc322_ordering_commitment", "lc322_solver", lc322_ordering_commitment),
    ("lc322_transition_asymmetric_forward_dp", "lc322_solver", lc322_transition_asymmetric_forward_dp),
    *[(mutant_id, "mutation_solver", solver) for mutant_id, (_label, solver) in MUTANTS.items()],
)

LC45_SOLVERS: tuple[tuple[str, str, Callable[[list[int]], int]], ...] = (
    ("lc45_naive_greedy", "lc45_solver", lc45_naive_greedy),
    ("lc45_max_landing_value", "lc45_solver", lc45_max_landing_value),
    ("lc45_farthest_landing_path", "lc45_solver", lc45_farthest_landing_path),
    ("lc45_zero_dead_end_panic", "lc45_solver", lc45_zero_dead_end_panic),
    ("lc45_reachable_boolean_confusion", "lc45_solver", lc45_reachable_boolean_confusion),
    ("lc45_bfs_depth_cutoff", "lc45_solver", lc45_bfs_depth_cutoff),
    ("lc45_three_step_window_dp", "lc45_solver", lc45_three_step_window_dp),
    ("lc45_frontier_off_by_one", "lc45_solver", lc45_frontier_off_by_one),
    ("lc45_uniform_formula_generalizer", "lc45_solver", lc45_uniform_formula_generalizer),
    ("lc45_first_window_max_then_greedy", "lc45_solver", lc45_first_window_max_then_greedy),
)


def _lc322_inputs() -> list[dict[str, Any]]:
    rows = {}
    for dimension_rows in _dimension_samples(LC322_SAMPLE_CAP).values():
        for row in dimension_rows:
            rows[tuple(row["nums"])] = row
    return list(rows.values())


def _solver_metrics(
    *,
    problem_id: str,
    solver_id: str,
    group: str,
    solver: Callable[[list[int]], int],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    entropies = []
    lengths = []
    ref_distances = []
    failure_points = []
    failures = 0
    for row in rows:
        nums = list(row["nums"])
        truth = int(row["truth"])
        trace = _lc322_trace(solver_id, nums) if problem_id == "lc322" else _lc45_trace(solver_id, nums)
        ref = _lc322_trace("reference", nums) if problem_id == "lc322" else _lc45_trace("reference", nums)
        entropies.append(_entropy(trace))
        lengths.append(len(trace))
        ref_distances.append(_trace_distance(trace, ref))
        try:
            failed = solver(nums) != truth
        except Exception:
            failed = True
        if failed:
            failures += 1
            failure_points.append(_first_divergence(trace, ref))
    return {
        "solver_id": solver_id,
        "problem_id": problem_id,
        "group": group,
        "trajectory_entropy": _round(float(np.mean(entropies)) if entropies else 0.0),
        "mean_trace_length": _round(float(np.mean(lengths)) if lengths else 0.0),
        "reference_divergence": _round(float(np.mean(ref_distances)) if ref_distances else 0.0),
        "fail_rate": _round(failures / len(rows) if rows else 0.0),
        "failure_point_mean": _round(float(np.mean(failure_points)) if failure_points else 0.0),
        "failure_point_count": len(failure_points),
    }


def _pairwise_step_divergence(metrics: list[dict[str, Any]], rows_by_problem: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    solver_lookup = {solver_id: solver for solver_id, _group, solver in [*LC322_SOLVERS, *LC45_SOLVERS]}
    pairs = {}
    for i, left in enumerate(metrics):
        for right in metrics[i + 1:]:
            if left["problem_id"] != right["problem_id"]:
                continue
            rows = rows_by_problem[left["problem_id"]]
            distances = []
            for row in rows[:80]:
                nums = list(row["nums"])
                left_trace = _lc322_trace(left["solver_id"], nums) if left["problem_id"] == "lc322" else _lc45_trace(left["solver_id"], nums)
                right_trace = _lc322_trace(right["solver_id"], nums) if right["problem_id"] == "lc322" else _lc45_trace(right["solver_id"], nums)
                distances.append(_trace_distance(left_trace, right_trace))
            pairs[f"{left['solver_id']}|{right['solver_id']}"] = _round(float(np.mean(distances)) if distances else 0.0)
    return pairs


def _group_summary(metrics: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in metrics:
        grouped.setdefault(row["group"], []).append(row)
    return {
        group: {
            "trajectory_entropy": _round(float(np.mean([row["trajectory_entropy"] for row in rows]))),
            "reference_divergence": _round(float(np.mean([row["reference_divergence"] for row in rows]))),
            "fail_rate": _round(float(np.mean([row["fail_rate"] for row in rows]))),
            "failure_point_mean": _round(float(np.mean([row["failure_point_mean"] for row in rows]))),
        }
        for group, rows in grouped.items()
    }


def _mutation_deviation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = {
        "mut_01|lc322_ordering_commitment": ("mut_01", "lc322_ordering_commitment"),
        "mut_02|mut_01": ("mut_02", "mut_01"),
        "mut_03|lc322_dp": ("mut_03", "lc322_dp"),
        "mut_04|lc322_dp": ("mut_04", "lc322_dp"),
        "mut_06|lc322_lookahead_one": ("mut_06", "lc322_lookahead_one"),
    }
    result = {}
    for pair_id, (left, right) in pairs.items():
        distances = []
        first_points = []
        for row in rows[:120]:
            nums = list(row["nums"])
            left_trace = _lc322_trace(left, nums)
            right_trace = _lc322_trace(right, nums)
            distances.append(_trace_distance(left_trace, right_trace))
            first_points.append(_first_divergence(left_trace, right_trace))
        result[pair_id] = {
            "mean_trace_distance": _round(float(np.mean(distances)) if distances else 0.0),
            "mean_first_deviation": _round(float(np.mean(first_points)) if first_points else 0.0),
        }
    return result


def run() -> dict[str, Any]:
    lc322_rows = _lc322_inputs()
    lc45_rows = [dict(row) for row in _instances()]
    metrics = [
        *[
            _solver_metrics(problem_id="lc322", solver_id=solver_id, group=group, solver=solver, rows=lc322_rows)
            for solver_id, group, solver in LC322_SOLVERS
        ],
        *[
            _solver_metrics(problem_id="lc45", solver_id=solver_id, group=group, solver=solver, rows=lc45_rows)
            for solver_id, group, solver in LC45_SOLVERS
        ],
    ]
    rows_by_problem = {"lc322": lc322_rows, "lc45": lc45_rows}
    return {
        "input_counts": {"lc322": len(lc322_rows), "lc45": len(lc45_rows)},
        "solver_metrics": metrics,
        "group_summary": _group_summary(metrics),
        "step_to_step_divergence": _pairwise_step_divergence(metrics, rows_by_problem),
        "mutation_deviation": _mutation_deviation(lc322_rows),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_126: Solver Trajectory Dynamics Analysis",
        "",
        "## Solver Metrics",
        "",
        "| Solver | Problem | Group | Entropy | Trace length | Ref divergence | Fail rate | Failure point |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["solver_metrics"]:
        lines.append(
            f"| `{row['solver_id']}` | `{row['problem_id']}` | `{row['group']}` | "
            f"{row['trajectory_entropy']:.6f} | {row['mean_trace_length']:.6f} | "
            f"{row['reference_divergence']:.6f} | {row['fail_rate']:.6f} | "
            f"{row['failure_point_mean']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Group Summary",
            "",
            "| Group | Entropy | Ref divergence | Fail rate | Failure point |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for group, row in report["group_summary"].items():
        lines.append(
            f"| `{group}` | {row['trajectory_entropy']:.6f} | {row['reference_divergence']:.6f} | "
            f"{row['fail_rate']:.6f} | {row['failure_point_mean']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Mutation Deviation",
            "",
            "| Pair | Mean trace distance | Mean first deviation |",
            "|---|---:|---:|",
        ]
    )
    for pair, row in report["mutation_deviation"].items():
        lines.append(f"| `{pair}` | {row['mean_trace_distance']:.6f} | {row['mean_first_deviation']:.6f} |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `data/solver_trajectory_dynamics_analysis.json`",
            "- `runners/run_solver_trajectory_dynamics_analysis.py`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report)
    print(json.dumps({"solver_count": len(report["solver_metrics"]), "input_counts": report["input_counts"]}, indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
