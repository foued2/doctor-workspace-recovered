"""Projection sensitivity harness for DOCTOR measurement geometry.

Strict scope:
- perturb the measurement layer only;
- do not change solver implementations or perturbation generators;
- test false-pass stability for LC179, LC128, LC56;
- test trajectory-class stability for the existing 8-class LC322 x LC45 axis.
"""
from __future__ import annotations

import copy
import itertools
import json
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import doctor.adversarial.observer.trajectory as trajectory_module
from doctor.adversarial.lc128_ingestion_gate import lc128_nums_reordering_perturbations
from doctor.adversarial.lc179_ingestion_gate import lc179_nums_reordering_perturbations
from doctor.adversarial.lc56_ingestion_gate import lc56_intervals_reordering_perturbations
from doctor.adversarial.observer.trajectory import compare_trajectories, extract_trajectory
from runners.run_lc128_adversarial import lc128_input_order_consecutive_scan
from runners.run_lc128_gate import REFERENCE_TESTS as LC128_TESTS
from runners.run_lc128_gate import lc128_oracle
from runners.run_lc128_gate import solver_return_len as lc128_return_len
from runners.run_lc128_negative_control import lc128_always_zero
from runners.run_lc128_survival_matrix import lc128_distinct_count
from runners.run_lc179_gate import REFERENCE_TESTS as LC179_TESTS
from runners.run_lc179_gate import lc179_oracle
from runners.run_lc56_gate import REFERENCE_TESTS as LC56_TESTS
from runners.run_lc56_gate import lc56_oracle
from runners.run_lc56_gate import solver_bogus as lc56_bogus
from runners.run_lc56_gate import solver_no_merge as lc56_no_merge
from solvers.negative_controls import lc179_numeric_descending

INSTANCES = 100
OUTPUT_PATH = PROJECT_ROOT / "data" / "projection_sensitivity_report.json"
RAW_LOG_PATH = PROJECT_ROOT / "data" / "projection_sensitivity_raw_log.jsonl"
ARTIFACT_ROOT = PROJECT_ROOT / "doctor" / "adversarial" / "observer" / "artifacts"


def _select(candidates: list[dict[str, Any]], instance_index: int) -> dict[str, Any]:
    if not candidates:
        raise ValueError("perturbation generator returned no candidates")
    return copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _typed_equal(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right


def _normalized_equal(left: Any, right: Any) -> bool:
    if isinstance(left, list) and isinstance(right, list):
        return _normalize(left) == _normalize(right)
    return _typed_equal(left, right)


def _normalize(value: Any) -> Any:
    if isinstance(value, list):
        if all(isinstance(item, list) for item in value):
            return sorted(tuple(_normalize(item)) for item in value)
        return tuple(value)
    return value


def _coarse_oracle(value: Any) -> Any:
    if isinstance(value, int):
        if value == 0:
            return "zero"
        if value == 1:
            return "one"
        return "many"
    if isinstance(value, str):
        if value == "":
            return "empty"
        if value == "0":
            return "zero"
        return f"digits:{len(value)}"
    if isinstance(value, list):
        return f"rows:{len(value)}"
    return type(value).__name__


def _projection_match(left: Any, right: Any, projection: str) -> bool:
    if projection == "raw_exact":
        return left == right
    if projection == "typed_exact":
        return _typed_equal(left, right)
    if projection == "normalized":
        return _normalized_equal(left, right)
    if projection == "coarse_oracle":
        return _coarse_oracle(left) == _coarse_oracle(right)
    raise ValueError(f"unknown projection: {projection}")


def _lc179_records() -> list[dict[str, Any]]:
    records = []
    for instance_index in range(1, INSTANCES + 1):
        original = copy.deepcopy(LC179_TESTS[(instance_index - 1) % len(LC179_TESTS)])
        perturbed = _select(
            lc179_nums_reordering_perturbations(copy.deepcopy(original), instance_index),
            instance_index,
        )
        oracle_output = lc179_oracle(copy.deepcopy(perturbed["nums"]))
        solver_output = lc179_numeric_descending(copy.deepcopy(perturbed["nums"]))
        records.append(
            {
                "problem_id": "LC179",
                "solver_id": "lc179_numeric_descending",
                "original_input": original,
                "perturbed_input": perturbed,
                "oracle_output": oracle_output,
                "solver_output": solver_output,
            }
        )
    return records


def _lc128_records() -> list[dict[str, Any]]:
    solvers: tuple[tuple[str, Callable[[list[int]], int]], ...] = (
        ("lc128_always_zero", lc128_always_zero),
        ("lc128_return_len", lc128_return_len),
        ("lc128_distinct_count", lc128_distinct_count),
        ("lc128_input_order_consecutive_scan", lc128_input_order_consecutive_scan),
    )
    records = []
    for solver_id, solver in solvers:
        for instance_index in range(1, INSTANCES + 1):
            original = copy.deepcopy(LC128_TESTS[(instance_index - 1) % len(LC128_TESTS)])
            perturbed = _select(
                lc128_nums_reordering_perturbations(copy.deepcopy(original), instance_index),
                instance_index,
            )
            oracle_output = lc128_oracle(copy.deepcopy(perturbed["nums"]))
            solver_output = solver(copy.deepcopy(perturbed["nums"]))
            records.append(
                {
                    "problem_id": "LC128",
                    "solver_id": solver_id,
                    "original_input": original,
                    "perturbed_input": perturbed,
                    "oracle_output": oracle_output,
                    "solver_output": solver_output,
                }
            )
    return records


def _lc56_records() -> list[dict[str, Any]]:
    solvers: tuple[tuple[str, Callable[[list[list[int]]], list[list[int]]]], ...] = (
        ("lc56_no_merge", lc56_no_merge),
        ("lc56_bogus", lc56_bogus),
    )
    records = []
    for solver_id, solver in solvers:
        for instance_index in range(1, INSTANCES + 1):
            original = copy.deepcopy(LC56_TESTS[(instance_index - 1) % len(LC56_TESTS)])
            perturbed = _select(
                lc56_intervals_reordering_perturbations(copy.deepcopy(original), 10),
                instance_index,
            )
            oracle_output = lc56_oracle(copy.deepcopy(perturbed["intervals"]))
            solver_output = solver(copy.deepcopy(perturbed["intervals"]))
            records.append(
                {
                    "problem_id": "LC56",
                    "solver_id": solver_id,
                    "original_input": original,
                    "perturbed_input": perturbed,
                    "oracle_output": oracle_output,
                    "solver_output": solver_output,
                }
            )
    return records


def _false_pass_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    projections = ("raw_exact", "typed_exact", "normalized", "coarse_oracle")
    summary: dict[str, Any] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["problem_id"], record["solver_id"])].append(record)

    for projection in projections:
        rows = []
        for (problem_id, solver_id), group in sorted(grouped.items()):
            false_pass = sum(
                1
                for record in group
                if _projection_match(record["solver_output"], record["oracle_output"], projection)
            )
            rows.append(
                {
                    "problem_id": problem_id,
                    "solver_id": solver_id,
                    "false_pass_rate": false_pass / len(group),
                    "false_pass_count": false_pass,
                    "total": len(group),
                }
            )
        lc179_rate = next(
            row["false_pass_rate"]
            for row in rows
            if row["problem_id"] == "LC179" and row["solver_id"] == "lc179_numeric_descending"
        )
        summary[projection] = {
            "rows": rows,
            "lc179_false_pass_rate": lc179_rate,
            "lc179_ceiling_preserved": abs(lc179_rate - 0.16) < 1e-12,
        }
    return summary


def _load_trajectory_artifacts() -> list[dict[str, Any]]:
    artifacts = []
    for problem in ("lc322", "lc45"):
        for path in sorted((ARTIFACT_ROOT / problem).glob("*.json")):
            artifacts.append(json.loads(path.read_text(encoding="utf-8")))
    return artifacts


def _trajectory_pairs(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trajectories = {
        f"{artifact['problem_id']}.{artifact['manifold_id']}": extract_trajectory(artifact)
        for artifact in artifacts
    }
    rows = []
    for left, right in itertools.combinations(sorted(trajectories), 2):
        score, matching = compare_trajectories(trajectories[left], trajectories[right])
        rows.append(
            {
                "left": left,
                "right": right,
                "left_problem": left.split(".")[0],
                "right_problem": right.split(".")[0],
                "score": round(score, 4),
                "matching": matching,
            }
        )
    return rows


def _execution_log_record(record: dict[str, Any]) -> dict[str, Any]:
    projections = ("raw_exact", "typed_exact", "normalized", "coarse_oracle")
    enriched = dict(record)
    enriched["record_type"] = "execution"
    enriched["oracle_decisions"] = {
        projection: _projection_match(
            record["solver_output"], record["oracle_output"], projection
        )
        for projection in projections
    }
    return enriched


def _trajectory_log_records() -> list[dict[str, Any]]:
    records = []
    for row in _trajectory_pairs(_load_trajectory_artifacts()):
        enriched = dict(row)
        enriched["record_type"] = "trajectory_pair"
        records.append(enriched)
    return records


def _trajectory_summary() -> dict[str, Any]:
    artifacts = _load_trajectory_artifacts()
    baseline = _trajectory_pairs(artifacts)
    baseline_scores = [row["score"] for row in baseline]

    original_onset = trajectory_module.ONSET_OPERATOR_WEIGHT
    trajectory_module.ONSET_OPERATOR_WEIGHT = original_onset * 1.2
    try:
        onset_shift = _trajectory_pairs(artifacts)
    finally:
        trajectory_module.ONSET_OPERATOR_WEIGHT = original_onset

    bins = {
        "exact": len(set(baseline_scores)),
        "bin_0.5": len({round(score * 2) / 2 for score in baseline_scores}),
        "bin_1.0": len({round(score) for score in baseline_scores}),
    }
    cross = [
        row["score"]
        for row in baseline
        if row["left_problem"] != row["right_problem"]
    ]
    within = [
        row["score"]
        for row in baseline
        if row["left_problem"] == row["right_problem"]
    ]
    onset_scores = [row["score"] for row in onset_shift]
    return {
        "artifact_count": len(artifacts),
        "pair_count": len(baseline),
        "baseline_class_count": len(set(baseline_scores)),
        "onset_weight_plus_20_class_count": len(set(onset_scores)),
        "binned_class_counts": bins,
        "cross_family_mean": sum(cross) / len(cross),
        "within_family_mean": sum(within) / len(within),
        "cross_family_separation": (sum(cross) / len(cross)) - (sum(within) / len(within)),
        "class_count_preserved_under_weight": len(set(baseline_scores)) == len(set(onset_scores)),
        "class_count_preserved_under_binning": bins["exact"] == bins["bin_0.5"] == bins["bin_1.0"],
    }


def _classification(false_pass: dict[str, Any], trajectory: dict[str, Any]) -> str:
    lc179_invariant = all(
        projection["lc179_ceiling_preserved"] for projection in false_pass.values()
    )
    trajectory_invariant = (
        trajectory["class_count_preserved_under_weight"]
        and trajectory["class_count_preserved_under_binning"]
    )
    if lc179_invariant and trajectory_invariant:
        return "Invariant signal"
    if not lc179_invariant and not trajectory_invariant:
        return "Projection artifact"
    return "Mixed regime"


def main() -> int:
    records = _lc179_records() + _lc128_records() + _lc56_records()
    RAW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_LOG_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    _jsonable(_execution_log_record(record)),
                    sort_keys=True,
                    ensure_ascii=True,
                )
                + "\n"
            )
        for record in _trajectory_log_records():
            handle.write(json.dumps(_jsonable(record), sort_keys=True, ensure_ascii=True) + "\n")

    false_pass = _false_pass_summary(records)
    trajectory = _trajectory_summary()
    report = {
        "false_pass_stability": false_pass,
        "trajectory_stability": trajectory,
        "classification": _classification(false_pass, trajectory),
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True))
    print(f"Wrote: {OUTPUT_PATH}")
    print(f"Wrote: {RAW_LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
