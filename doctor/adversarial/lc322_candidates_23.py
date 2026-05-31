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
from doctor.adversarial.lc322_ground_truth import lc322_brute_force  # noqa: E402
from runners.run_solver_trajectory_dynamics_analysis import (  # noqa: E402
    _lc322_bfs_trace,
    _lc322_dp_trace,
    _lc322_inputs,
    _lc322_memo_trace,
    _lc322_trace,
)
from solvers.lc322_memorizer_solvers import (  # noqa: E402
    lc322_bfs_reference,
    lc322_lookup_table_memorizer,
    lc322_partial_standard_memorizer,
    lc322_recursive_memo_reference,
    lc322_small_input_pattern_memorizer,
)


OUTPUT_JSON = PROJECT_ROOT / "data" / "lc322_memorizer_detection_test.json"
STEPS = tuple(range(1, 9))
PASS_SILHOUETTE_MIN = 0.10
PASS_NN_RATE_MIN = 0.70


Solver = Callable[[list[int]], int]


GENUINE_SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc322_dp", lc322_dp),
    ("lc322_bfs_reference", lc322_bfs_reference),
    ("lc322_recursive_memo_reference", lc322_recursive_memo_reference),
)

FAKE_SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc322_lookup_table_memorizer", lc322_lookup_table_memorizer),
    ("lc322_small_input_pattern_memorizer", lc322_small_input_pattern_memorizer),
    ("lc322_partial_standard_memorizer", lc322_partial_standard_memorizer),
)

REFERENCE_IDS = ("lc322_dp", "lc322_bfs_reference", "lc322_recursive_memo_reference")


def _round(value: float) -> float:
    return round(float(value), 6)


def _split(nums: list[int]) -> tuple[list[int], int]:
    if not nums:
        return [], 0
    return [value for value in nums[:-1] if value > 0], int(nums[-1])


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
    trace = [float(amount), float(len(coins)), float(sum(coins))]
    if amount in {0, 1, 2, 3, 6, 7, 11, 27, 30, 6249}:
        trace.append(float(amount))
    else:
        trace.extend(_greedy_trace(nums)[1:4])
    return trace


def _small_pattern_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    trace = [float(amount), float(min(coins, default=0)), float(max(coins, default=0))]
    if amount <= 12:
        trace.append(float(amount % max(len(coins), 1)))
    else:
        trace.extend(_greedy_trace(nums)[1:4])
    return trace


def _partial_memorizer_trace(nums: list[int]) -> list[float]:
    coins, amount = _split(nums)
    trace = [float(amount), float(1 if 1 in coins else 0), float(len(coins))]
    if amount <= 20 or len(coins) == 1:
        trace.append(float(amount))
    else:
        trace.append(-1.0)
    return trace


def _trace(solver_id: str, nums: list[int]) -> list[float]:
    if solver_id == "lc322_dp":
        return _lc322_trace("lc322_dp", nums)
    if solver_id == "lc322_bfs_reference":
        return _lc322_bfs_trace(nums, cutoff=False)
    if solver_id == "lc322_recursive_memo_reference":
        return _lc322_memo_trace(nums, modulo=False)
    if solver_id == "lc322_lookup_table_memorizer":
        return _lookup_trace(nums)
    if solver_id == "lc322_small_input_pattern_memorizer":
        return _small_pattern_trace(nums)
    if solver_id == "lc322_partial_standard_memorizer":
        return _partial_memorizer_trace(nums)
    return _lc322_dp_trace(nums)


def _standard_cases() -> list[dict[str, Any]]:
    cases = [
        ([1, 2, 5, 11], 3),
        ([2, 3], -1),
        ([1, 0], 0),
        ([1, 1], 1),
        ([1, 2], 2),
        ([2, 5, 10, 1, 27], 4),
        ([1, 3, 4, 6], 2),
        ([2, 3, 5, 7], 2),
        ([1, 5, 10, 25, 30], 2),
    ]
    return [{"nums": nums, "truth": truth} for nums, truth in cases]


def _novel_cases() -> list[dict[str, Any]]:
    rows = {}
    for row in _lc322_inputs():
        nums = tuple(row["nums"])
        rows[nums] = {"nums": list(nums), "truth": int(row["truth"])}
    for coins in ([1, 7, 10], [3, 7, 12], [4, 9, 11], [2, 6, 13], [5, 8, 17], [6, 10, 15]):
        for amount in range(14, 42, 3):
            try:
                truth = lc322_brute_force(list(coins), amount)
            except Exception:
                continue
            rows[tuple([*coins, amount])] = {"nums": [*coins, amount], "truth": int(truth)}
    return list(rows.values())


def _records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    solvers = [*[(sid, "genuine", fn) for sid, fn in GENUINE_SOLVERS], *[(sid, "fake", fn) for sid, fn in FAKE_SOLVERS]]
    for solver_id, group, solver in solvers:
        for index, row in enumerate(rows):
            nums = list(row["nums"])
            truth = int(row["truth"])
            try:
                output = int(solver(nums))
                correct = output == truth
            except Exception:
                output = 10**9
                correct = False
            trace = _trace(solver_id, nums)
            references = {ref_id: _trace(ref_id, nums) for ref_id in REFERENCE_IDS}
            step_divergence = {
                f"n{step}": _round(float(np.mean([_step_distance(trace, ref, step) for ref in references.values()])))
                for step in STEPS
            }
            prefix_vectors = {
                f"n{step}": [_round(_trace_distance(trace, ref, step)) for ref in references.values()]
                for step in STEPS
            }
            records.append(
                {
                    "solver_id": solver_id,
                    "group": group,
                    "input_index": index,
                    "nums": nums,
                    "truth": truth,
                    "output": output,
                    "final_output_correct": correct,
                    "trace_length": len(trace),
                    "step_divergence_from_references": step_divergence,
                    "prefix_distance_vector_by_step": prefix_vectors,
                }
            )
    return records


def _silhouette(matrix: np.ndarray, labels: list[str]) -> float:
    if len(set(labels)) < 2 or len(labels) <= len(set(labels)):
        return 0.0
    scores = []
    for index, label in enumerate(labels):
        distances = np.linalg.norm(matrix - matrix[index], axis=1)
        same = [distances[j] for j, other in enumerate(labels) if other == label and j != index]
        other_labels = [other for other in sorted(set(labels)) if other != label]
        if not same or not other_labels:
            continue
        a = float(np.mean(same))
        b = min(float(np.mean([distances[j] for j, other in enumerate(labels) if other == other_label])) for other_label in other_labels)
        denom = max(a, b)
        scores.append(0.0 if denom == 0 else (b - a) / denom)
    return float(np.mean(scores)) if scores else 0.0


def _same_group_nearest_rate(matrix: np.ndarray, labels: list[str]) -> float:
    if len(labels) < 2:
        return 0.0
    same = 0
    for index, label in enumerate(labels):
        distances = np.linalg.norm(matrix - matrix[index], axis=1)
        distances[index] = np.inf
        nearest = int(np.argmin(distances))
        if labels[nearest] == label:
            same += 1
    return same / len(labels)


def _distribution(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "median": 0.0, "max": 0.0}
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
    result: dict[str, Any] = {}
    for step in STEPS:
        key = f"n{step}"
        matrix = np.array([record["prefix_distance_vector_by_step"][key] for record in records], dtype=float)
        labels = [record["group"] for record in records]
        genuine = [record["step_divergence_from_references"][key] for record in records if record["group"] == "genuine"]
        fake = [record["step_divergence_from_references"][key] for record in records if record["group"] == "fake"]
        result[key] = {
            "silhouette": _round(_silhouette(matrix, labels)),
            "same_group_nearest_rate": _round(_same_group_nearest_rate(matrix, labels)),
            "genuine_divergence_distribution": _distribution(genuine),
            "fake_divergence_distribution": _distribution(fake),
            "mean_gap_fake_minus_genuine": _round(np.mean(fake) - np.mean(genuine) if fake and genuine else 0.0),
            "pass": bool(_silhouette(matrix, labels) >= PASS_SILHOUETTE_MIN and _same_group_nearest_rate(matrix, labels) >= PASS_NN_RATE_MIN),
        }
    return result


def _solver_summary(records: list[dict[str, Any]], standard_case_count: int) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for solver_id in sorted({record["solver_id"] for record in records}):
        rows = [record for record in records if record["solver_id"] == solver_id]
        standard_rows = [row for row in rows if row["input_index"] < standard_case_count]
        novel_rows = [row for row in rows if row["input_index"] >= standard_case_count]
        summary[solver_id] = {
            "group": rows[0]["group"],
            "execution_count": len(rows),
            "final_output_accuracy": _round(sum(1 for row in rows if row["final_output_correct"]) / len(rows)),
            "standard_case_accuracy": _round(sum(1 for row in standard_rows if row["final_output_correct"]) / len(standard_rows)),
            "novel_case_accuracy": _round(sum(1 for row in novel_rows if row["final_output_correct"]) / len(novel_rows)),
            "mean_step_divergence": {
                f"n{step}": _round(np.mean([row["step_divergence_from_references"][f"n{step}"] for row in rows]))
                for step in STEPS
            },
        }
    return summary


def main() -> None:
    standard_rows = _standard_cases()
    rows = [*standard_rows, *_novel_cases()]
    records = _records(rows)
    separation = _separation(records)
    pass_steps = [step for step, payload in separation.items() if payload["pass"]]
    report = {
        "objective": "LC322 memorizer detection from trajectory divergence only; final output is recorded but not used for separation.",
        "step_semantics": "n1-n8 are 1-based trajectory states using the existing LC322 trajectory-list convention.",
        "reference_solvers": list(REFERENCE_IDS),
        "genuine_solvers": [solver_id for solver_id, _solver in GENUINE_SOLVERS],
        "fake_solvers": [solver_id for solver_id, _solver in FAKE_SOLVERS],
        "input_count": len(rows),
        "standard_case_count": len(standard_rows),
        "execution_count": len(records),
        "pass_criterion": {
            "silhouette_min": PASS_SILHOUETTE_MIN,
            "same_group_nearest_rate_min": PASS_NN_RATE_MIN,
        },
        "separation_by_step": separation,
        "trajectory_distinguishes_genuine_from_fake": bool(pass_steps),
        "pass_steps": pass_steps,
        "solver_summary": _solver_summary(records, len(standard_rows)),
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_JSON), "pass_steps": pass_steps}, indent=2))


if __name__ == "__main__":
    main()
