from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import lc322_dp  # noqa: E402
from runners.run_solver_trajectory_dynamics_analysis import _lc322_bfs_trace, _lc322_memo_trace, _lc322_trace  # noqa: E402
from solvers.lc322_oracle_passing_fakes import (  # noqa: E402
    LIMITED_SUITE_ANSWERS,
    lc322_canonical_greedy_fake,
    lc322_limited_lookup_fake,
    lc322_low_amount_only_fake,
)


OUTPUT_JSON = PROJECT_ROOT / "data" / "lc322_incomplete_oracle_test.json"
STEPS = tuple(range(2, 9))
PASS_SILHOUETTE_MIN = 0.10
PASS_NN_RATE_MIN = 0.70

Solver = Callable[[list[int]], int]

GENUINE_SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc322_dp", lc322_dp),
    ("lc322_bfs_reference", lambda nums: _bfs_answer(nums)),
    ("lc322_recursive_memo_reference", lambda nums: _memo_answer(nums)),
)

FAKE_SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc322_canonical_greedy_fake", lc322_canonical_greedy_fake),
    ("lc322_limited_lookup_fake", lc322_limited_lookup_fake),
    ("lc322_low_amount_only_fake", lc322_low_amount_only_fake),
)

REFERENCE_IDS = ("lc322_dp", "lc322_bfs_reference", "lc322_recursive_memo_reference")


def _round(value: float) -> float:
    return round(float(value), 6)


def _split(nums: list[int]) -> tuple[list[int], int]:
    if not nums:
        return [], 0
    return [value for value in nums[:-1] if value > 0], int(nums[-1])


def _bfs_answer(nums: list[int]) -> int:
    coins, amount = _split(nums)
    if amount == 0:
        return 0
    queue = [(0, 0)]
    seen = {0}
    for value, steps in queue:
        for coin in coins:
            nxt = value + coin
            if nxt == amount:
                return steps + 1
            if nxt < amount and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, steps + 1))
    return -1


def _memo_answer(nums: list[int]) -> int:
    coins, amount = _split(nums)
    memo: dict[int, int] = {}

    def solve(rem: int) -> int:
        if rem == 0:
            return 0
        if rem < 0:
            return 10**9
        if rem in memo:
            return memo[rem]
        memo[rem] = min(solve(rem - coin) + 1 for coin in coins) if coins else 10**9
        return memo[rem]

    answer = solve(amount)
    return -1 if answer >= 10**9 else answer


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


def _greedy_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    remaining = amount
    trace = [float(remaining)]
    for coin in sorted(coins, reverse=True):
        while coin <= remaining:
            remaining -= coin
            trace.append(float(remaining))
    return trace


def _lookup_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    key = (tuple(coins), amount)
    trace = [float(amount), float(len(coins)), float(sum(coins))]
    if key in LIMITED_SUITE_ANSWERS or (tuple(sorted(coins)), amount) in LIMITED_SUITE_ANSWERS:
        trace.extend([float(amount), float(LIMITED_SUITE_ANSWERS.get(key, LIMITED_SUITE_ANSWERS.get((tuple(sorted(coins)), amount), -1)))])
    else:
        trace.extend(_greedy_trace(nums)[1:5])
    return trace


def _low_amount_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    if amount <= 65:
        return [float(amount), float(len(coins)), float(max(coins, default=0)), float(amount), float(amount % max(len(coins), 1))]
    return _greedy_trace(nums)


def _trace(solver_id: str, nums: list[int]) -> list[float]:
    if solver_id == "lc322_dp":
        return _lc322_trace("lc322_dp", nums)
    if solver_id == "lc322_bfs_reference":
        return _lc322_bfs_trace(nums, cutoff=False)
    if solver_id == "lc322_recursive_memo_reference":
        return _lc322_memo_trace(nums, modulo=False)
    if solver_id == "lc322_canonical_greedy_fake":
        return _greedy_trace(nums)
    if solver_id == "lc322_limited_lookup_fake":
        return _lookup_trace(nums)
    if solver_id == "lc322_low_amount_only_fake":
        return _low_amount_trace(nums)
    return [0.0]


def _limited_suite() -> list[dict[str, Any]]:
    return [
        {"nums": [*coins, amount], "truth": truth}
        for (coins, amount), truth in LIMITED_SUITE_ANSWERS.items()
    ]


def _heldout_suite() -> list[dict[str, Any]]:
    cases = [
        ([1, 3, 4], 6),
        ([1, 7, 10], 14),
        ([1, 7, 10], 28),
        ([2, 5, 10], 27),
        ([3, 7, 12], 24),
        ([4, 9, 11], 18),
        ([1, 6, 10], 12),
        ([1, 6, 10], 72),
        ([1, 5, 12, 25], 37),
        ([2, 6, 13], 26),
        ([5, 8, 17], 34),
        ([6, 10, 15], 30),
        ([1, 11, 20], 66),
        ([1, 12, 25], 74),
    ]
    rows = []
    for coins, amount in cases:
        rows.append({"nums": [*coins, amount], "truth": _memo_answer([*coins, amount])})
    return rows


def _records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    solvers = [*[(sid, "genuine", fn) for sid, fn in GENUINE_SOLVERS], *[(sid, "fake", fn) for sid, fn in FAKE_SOLVERS]]
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
                    "output": output,
                    "truth": truth,
                    "limited_oracle_pass": output == truth,
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


def _pass_rate(records: list[dict[str, Any]], group: str) -> float:
    rows = [record for record in records if record["group"] == group]
    return sum(1 for row in rows if row["limited_oracle_pass"]) / len(rows)


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


def _solver_accuracy(records: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for solver_id in sorted({record["solver_id"] for record in records}):
        rows = [record for record in records if record["solver_id"] == solver_id]
        result[solver_id] = {
            "group": rows[0]["group"],
            "pass_rate": _round(sum(1 for row in rows if row["limited_oracle_pass"]) / len(rows)),
        }
    return result


def main() -> None:
    limited_records = _records(_limited_suite())
    heldout_records = _records(_heldout_suite())
    separation = _separation(limited_records)
    pass_steps = [step for step, payload in separation.items() if payload["pass"]]
    report = {
        "objective": "Test whether trajectory separates genuine LC322 solvers from fake solvers when an incomplete oracle accepts both groups.",
        "limited_oracle_definition": "18 curated standard LC322 cases; all fake solvers are constructed to pass this suite.",
        "limited_suite_case_count": len(_limited_suite()),
        "heldout_suite_case_count": len(_heldout_suite()),
        "reference_solvers": list(REFERENCE_IDS),
        "genuine_solvers": [sid for sid, _fn in GENUINE_SOLVERS],
        "fake_solvers": [sid for sid, _fn in FAKE_SOLVERS],
        "limited_oracle_group_pass_rate": {
            "genuine": _round(_pass_rate(limited_records, "genuine")),
            "fake": _round(_pass_rate(limited_records, "fake")),
        },
        "limited_oracle_solver_pass_rate": _solver_accuracy(limited_records),
        "heldout_solver_pass_rate": _solver_accuracy(heldout_records),
        "pass_criterion": {
            "silhouette_min": PASS_SILHOUETTE_MIN,
            "same_group_nearest_rate_min": PASS_NN_RATE_MIN,
        },
        "separation_by_step": separation,
        "trajectory_distinguishes_when_limited_oracle_cannot": bool(pass_steps),
        "pass_steps": pass_steps,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_JSON), "pass_steps": pass_steps}, indent=2))


if __name__ == "__main__":
    main()
