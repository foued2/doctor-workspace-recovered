from __future__ import annotations

import json
import sys
from collections.abc import Callable
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc55_ingestion_gate import generate_minimum_margin_instance  # noqa: E402
from runners.run_failure_time_predictability_analysis import _early_features  # noqa: E402
from runners.run_lc55_gate import (  # noqa: E402
    REFERENCE_TESTS,
    lc55_oracle,
    solver_always_false,
    solver_always_true,
    solver_dp_forward,
    solver_greedy_ltr,
    solver_greedy_rtl,
)
from runners.run_representation_invariant_separation_test import _base_records as _lc322_lc45_records  # noqa: E402
from runners.run_representation_invariant_separation_test import (  # noqa: E402
    _early_prefix_vector,
    _safe_mean,
    _safe_std,
    _static_outcome_vector,
    _trajectory_summary_vector,
    _trajectory_terminal_vector,
)
from runners.run_solver_trajectory_dynamics_analysis import (  # noqa: E402
    _entropy,
    _first_divergence,
    _round,
    _trace_distance,
)
from solvers.negative_controls import lc55_reachability_optimism, lc55_slack_dependent  # noqa: E402


OUTPUT_JSON = PROJECT_ROOT / "data" / "lc55_representation_placement.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_129.md"

LC55_SOLVERS: tuple[tuple[str, Callable[[list[int]], bool]], ...] = (
    ("lc55_greedy_rtl", solver_greedy_rtl),
    ("lc55_greedy_ltr", solver_greedy_ltr),
    ("lc55_dp_forward", solver_dp_forward),
    ("lc55_always_true", solver_always_true),
    ("lc55_always_false", solver_always_false),
    ("lc55_slack_dependent", lc55_slack_dependent),
    ("lc55_reachability_optimism", lc55_reachability_optimism),
)

REPRESENTATIONS = ("static_outcome", "early_prefix", "trajectory_terminal", "trajectory_summary")


def _lc55_rows() -> list[dict[str, Any]]:
    rows: dict[tuple[int, ...], dict[str, Any]] = {}

    def add(nums: list[int]) -> None:
        if not nums:
            return
        key = tuple(nums)
        rows[key] = {"nums": list(nums), "truth": bool(lc55_oracle(list(nums)))}

    for test in REFERENCE_TESTS:
        nums = list(test["nums"])
        add(nums)
        add(generate_minimum_margin_instance(nums))
        add([*nums, 0])
        if nums[-1] != 0:
            shifted = list(nums)
            shifted[-1] = 0
            add(shifted)

    for length in range(2, 8):
        for nums in product(range(4), repeat=length):
            if nums[0] == 0 and length > 1:
                continue
            add(list(nums))

    return list(rows.values())


def _lc55_reference_trace(nums: list[int]) -> list[float]:
    n = len(nums)
    leftmost_good = n - 1
    trace = [float(leftmost_good)]
    for index in range(n - 2, -1, -1):
        if index + nums[index] >= leftmost_good:
            leftmost_good = index
        trace.append(float(leftmost_good))
    return trace


def _lc55_ltr_trace(nums: list[int]) -> list[float]:
    max_reach = 0
    trace = [0.0]
    for index, jump in enumerate(nums):
        if index > max_reach:
            trace.append(float(max_reach))
            return trace
        max_reach = max(max_reach, index + jump)
        trace.append(float(min(max_reach, len(nums) - 1)))
        if max_reach >= len(nums) - 1:
            return trace
    return trace


def _lc55_dp_trace(nums: list[int]) -> list[float]:
    n = len(nums)
    if n <= 1:
        return [1.0]
    dp = [False] * n
    dp[0] = True
    trace = [1.0]
    for index in range(n):
        if dp[index]:
            for step in range(1, nums[index] + 1):
                if index + step < n:
                    dp[index + step] = True
        trace.append(float(sum(dp)))
    return trace


def _lc55_slack_trace(nums: list[int]) -> list[float]:
    trace = []
    for index, value in enumerate(nums[:-1]):
        trace.append(float(value))
        if value <= 1:
            trace.append(float(index))
            return trace
    trace.append(float(len(nums) - 1))
    return trace


def _lc55_optimism_trace(nums: list[int]) -> list[float]:
    if len(nums) == 1:
        return [1.0]
    return [float(nums[0]), 1.0 if nums[0] > 0 else 0.0]


def _lc55_trace(solver_id: str, nums: list[int]) -> list[float]:
    if solver_id in {"reference", "lc55_greedy_rtl"}:
        return _lc55_reference_trace(nums)
    if solver_id == "lc55_greedy_ltr":
        return _lc55_ltr_trace(nums)
    if solver_id == "lc55_dp_forward":
        return _lc55_dp_trace(nums)
    if solver_id == "lc55_always_true":
        return [1.0 for _ in nums]
    if solver_id == "lc55_always_false":
        return [0.0 for _ in nums]
    if solver_id == "lc55_slack_dependent":
        return _lc55_slack_trace(nums)
    if solver_id == "lc55_reachability_optimism":
        return _lc55_optimism_trace(nums)
    raise ValueError(solver_id)


def _lc55_solver_record(solver_id: str, solver: Callable[[list[int]], bool], rows: list[dict[str, Any]]) -> dict[str, Any]:
    outputs = []
    truths = []
    failed = []
    traces = []
    refs = []
    early_n2 = []
    early_n5 = []
    for row in rows:
        nums = list(row["nums"])
        truth = bool(row["truth"])
        try:
            output = bool(solver(nums))
            is_failed = output != truth
        except Exception:
            output = False
            is_failed = True
        trace = _lc55_trace(solver_id, nums)
        ref = _lc55_trace("reference", nums)
        outputs.append(1.0 if output else 0.0)
        truths.append(1.0 if truth else 0.0)
        failed.append(1.0 if is_failed else 0.0)
        traces.append(trace)
        refs.append(ref)
        early_n2.append(_early_features(trace, ref, 2))
        early_n5.append(_early_features(trace, ref, 5))
    failure_points = [_first_divergence(trace, ref) for trace, ref, is_failed in zip(traces, refs, failed, strict=True) if is_failed]
    return {
        "solver_id": solver_id,
        "problem_id": "lc55",
        "group": "lc55_solver",
        "outputs": outputs,
        "truths": truths,
        "failed": failed,
        "traces": traces,
        "refs": refs,
        "early_n2": early_n2,
        "early_n5": early_n5,
        "failure_points": failure_points,
    }


def _lc55_records() -> tuple[list[dict[str, Any]], int]:
    rows = _lc55_rows()
    return [_lc55_solver_record(solver_id, solver, rows) for solver_id, solver in LC55_SOLVERS], len(rows)


def _vector(record: dict[str, Any], representation: str) -> list[float]:
    if representation == "static_outcome":
        return _static_outcome_vector(record)
    if representation == "early_prefix":
        return _early_prefix_vector(record)
    if representation == "trajectory_terminal":
        return _trajectory_terminal_vector(record)
    if representation == "trajectory_summary":
        return _trajectory_summary_vector(record)
    raise ValueError(representation)


def _matrix(records: list[dict[str, Any]], representation: str) -> np.ndarray:
    matrix = np.array([_vector(row, representation) for row in records], dtype=float)
    scale = np.std(matrix, axis=0, keepdims=True)
    scale = np.where(scale == 0.0, 1.0, scale)
    return (matrix - np.mean(matrix, axis=0, keepdims=True)) / scale


def _silhouette(matrix: np.ndarray, labels: list[str]) -> float:
    if len(set(labels)) < 2 or len(labels) < 3:
        return 0.0
    scores = []
    for index, label in enumerate(labels):
        same = [i for i, other in enumerate(labels) if other == label and i != index]
        other_groups = sorted({other for other in labels if other != label})
        if not same:
            continue
        a_dist = float(np.mean([np.linalg.norm(matrix[index] - matrix[i]) for i in same]))
        b_dist = min(
            float(np.mean([np.linalg.norm(matrix[index] - matrix[i]) for i, other in enumerate(labels) if other == other_group]))
            for other_group in other_groups
        )
        denom = max(a_dist, b_dist)
        scores.append((b_dist - a_dist) / denom if denom else 0.0)
    return _round(_safe_mean(scores))


def _nearest_same_problem_rate(matrix: np.ndarray, labels: list[str]) -> float:
    hits = 0
    for index, vector in enumerate(matrix):
        distances = np.linalg.norm(matrix - vector, axis=1)
        distances[index] = float("inf")
        nearest = int(np.argmin(distances))
        if labels[nearest] == labels[index]:
            hits += 1
    return _round(hits / len(labels) if labels else 0.0)


def _centroid_distances(matrix: np.ndarray, labels: list[str]) -> dict[str, float]:
    centroids = {
        problem: np.mean(matrix[[label == problem for label in labels]], axis=0)
        for problem in sorted(set(labels))
    }
    distances = {}
    problems = sorted(centroids)
    for i, left in enumerate(problems):
        for right in problems[i + 1:]:
            distances[f"{left}|{right}"] = _round(float(np.linalg.norm(centroids[left] - centroids[right])))
    return distances


def _population_shifts(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    lc55_core = {"lc55_greedy_rtl", "lc55_greedy_ltr", "lc55_dp_forward"}
    lc55_negative = {"lc55_always_true", "lc55_always_false", "lc55_slack_dependent", "lc55_reachability_optimism"}
    lc45_edge = {
        "lc45_naive_greedy",
        "lc45_uniform_formula_generalizer",
        "lc45_reachable_boolean_confusion",
        "lc45_bfs_depth_cutoff",
        "lc45_first_window_max_then_greedy",
    }
    lc322_mutations = {"mut_01", "mut_02", "mut_03", "mut_04", "mut_06"}
    return {
        "full_population": records,
        "lc55_core_only": [row for row in records if row["problem_id"] != "lc55" or row["solver_id"] in lc55_core],
        "lc55_negative_only": [row for row in records if row["problem_id"] != "lc55" or row["solver_id"] in lc55_negative],
        "lc322_no_mutations": [row for row in records if row["problem_id"] != "lc322" or row["solver_id"] not in lc322_mutations],
        "lc322_mutations_only": [row for row in records if row["problem_id"] != "lc322" or row["solver_id"] in lc322_mutations],
        "lc45_edge_only": [row for row in records if row["problem_id"] != "lc45" or row["solver_id"] in lc45_edge],
        "lc45_core_only": [row for row in records if row["problem_id"] != "lc45" or row["solver_id"] not in lc45_edge],
    }


def _evaluate_shift(records: list[dict[str, Any]], representation: str) -> dict[str, Any]:
    labels = [row["problem_id"] for row in records]
    matrix = _matrix(records, representation)
    return {
        "solver_count": len(records),
        "problem_counts": dict(sorted((problem, labels.count(problem)) for problem in set(labels))),
        "problem_silhouette": _silhouette(matrix, labels),
        "same_problem_nearest_rate": _nearest_same_problem_rate(matrix, labels),
        "centroid_distances": _centroid_distances(matrix, labels),
    }


def _summary(shifts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    silhouettes = [row["problem_silhouette"] for row in shifts.values()]
    nn_rates = [row["same_problem_nearest_rate"] for row in shifts.values()]
    lc55_distances = [
        value
        for row in shifts.values()
        for pair, value in row["centroid_distances"].items()
        if "lc55" in pair
    ]
    mean_distance = _safe_mean(lc55_distances)
    cv = _safe_std(lc55_distances) / mean_distance if mean_distance else 0.0
    passed = min(silhouettes) > 0.0 and min(nn_rates) > 0.67 and min(lc55_distances) > 0.0 and cv <= 0.25
    return {
        "min_problem_silhouette": _round(min(silhouettes)),
        "min_same_problem_nearest_rate": _round(min(nn_rates)),
        "min_lc55_centroid_distance": _round(min(lc55_distances)),
        "max_lc55_centroid_distance": _round(max(lc55_distances)),
        "lc55_centroid_distance_cv": _round(cv),
        "stable_lc55_placement": "PASS" if passed else "FAIL",
    }


def _lc55_solver_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = {}
    for record in records:
        if record["problem_id"] != "lc55":
            continue
        rows[record["solver_id"]] = {
            "failure_rate": _round(_safe_mean(record["failed"])),
            "trajectory_entropy": _round(_safe_mean([_entropy(trace) for trace in record["traces"]])),
            "reference_divergence": _round(_safe_mean([_trace_distance(trace, ref) for trace, ref in zip(record["traces"], record["refs"], strict=True)])),
            "failure_point_mean": _round(_safe_mean(record["failure_points"])),
        }
    return rows


def run() -> dict[str, Any]:
    baseline_records = _lc322_lc45_records()
    lc55_records, lc55_input_count = _lc55_records()
    records = [*baseline_records, *lc55_records]
    shifts = _population_shifts(records)
    representations = {}
    for representation in REPRESENTATIONS:
        shift_results = {
            shift_id: _evaluate_shift(shift_records, representation)
            for shift_id, shift_records in shifts.items()
        }
        representations[representation] = {
            "shifts": shift_results,
            "summary": _summary(shift_results),
        }
    return {
        "objective": "Place LC55 under the four FINDING_128 representation classes without adding probes or representation classes.",
        "lc55_input_count": lc55_input_count,
        "solver_counts": dict(sorted((problem, [row["problem_id"] for row in records].count(problem)) for problem in {row["problem_id"] for row in records})),
        "representations": representations,
        "lc55_solver_metrics": _lc55_solver_metrics(records),
        "any_representation_passed": any(payload["summary"]["stable_lc55_placement"] == "PASS" for payload in representations.values()),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_129: LC55 Representation Placement",
        "",
        "## Summary",
        "",
        "| Representation | Min silhouette | Min same-problem NN | Min LC55 centroid | Max LC55 centroid | CV | Stable LC55 placement |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for representation, payload in report["representations"].items():
        row = payload["summary"]
        lines.append(
            f"| `{representation}` | {row['min_problem_silhouette']:.6f} | {row['min_same_problem_nearest_rate']:.6f} | "
            f"{row['min_lc55_centroid_distance']:.6f} | {row['max_lc55_centroid_distance']:.6f} | "
            f"{row['lc55_centroid_distance_cv']:.6f} | `{row['stable_lc55_placement']}` |"
        )
    lines.extend(["", "## LC55 Solver Metrics", "", "| Solver | Failure rate | Entropy | Ref divergence | Failure point |", "|---|---:|---:|---:|---:|"])
    for solver_id, row in report["lc55_solver_metrics"].items():
        lines.append(
            f"| `{solver_id}` | {row['failure_rate']:.6f} | {row['trajectory_entropy']:.6f} | "
            f"{row['reference_divergence']:.6f} | {row['failure_point_mean']:.6f} |"
        )
    lines.extend(["", "## Shift Matrix", ""])
    for representation, payload in report["representations"].items():
        lines.extend(
            [
                f"### {representation}",
                "",
                "| Shift | Counts | Silhouette | Same-problem NN | Centroid distances |",
                "|---|---|---:|---:|---|",
            ]
        )
        for shift_id, row in payload["shifts"].items():
            lines.append(
                f"| `{shift_id}` | `{row['problem_counts']}` | {row['problem_silhouette']:.6f} | "
                f"{row['same_problem_nearest_rate']:.6f} | `{row['centroid_distances']}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Artifacts",
            "",
            "- `data/lc55_representation_placement.json`",
            "- `runners/run_lc55_representation_placement.py`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report)
    print(
        json.dumps(
            {
                "any_representation_passed": report["any_representation_passed"],
                "lc55_input_count": report["lc55_input_count"],
                "summaries": {
                    representation: payload["summary"]
                    for representation, payload in report["representations"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
