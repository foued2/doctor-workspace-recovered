"""Phase 2.0C negative control calibration runner.

Review-only artifact unless invoked directly. The runner checks whether active
perturbation families can expose semantically plausible wrong heuristics.
"""
from __future__ import annotations

import copy
import json
import multiprocessing as mp
import operator
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc36_ingestion_gate import lc36_syntax_only_perturbations
from doctor.adversarial.lc53_ingestion_gate import lc53_syntax_only_perturbations
from doctor.adversarial.lc55_ingestion_gate import lc55_minimum_margin_perturbations
from doctor.adversarial.lc179_ingestion_gate import lc179_nums_reordering_perturbations
from runners.run_lc36_gate import REFERENCE_TESTS as LC36_REFERENCE_TESTS
from runners.run_lc36_gate import lc36_oracle
from runners.run_lc36_gate import solver_check_rows_cols_skip_boxes
from runners.run_lc53_gate import REFERENCE_TESTS as LC53_REFERENCE_TESTS
from runners.run_lc53_gate import lc53_oracle
from runners.run_lc53_gate import solver_always_zero
from runners.run_lc53_gate import solver_max_element
from runners.run_lc55_gate import REFERENCE_TESTS as LC55_REFERENCE_TESTS
from runners.run_lc55_gate import lc55_oracle
from runners.run_lc179_gate import REFERENCE_TESTS as LC179_REFERENCE_TESTS
from runners.run_lc179_gate import lc179_oracle
from solvers.negative_controls import lc36_row_only
from solvers.negative_controls import lc36_rows_cols_only
from solvers.negative_controls import lc55_reachability_optimism
from solvers.negative_controls import lc55_slack_dependent
from solvers.negative_controls import lc179_numeric_descending

INSTANCES_PER_COMBINATION = 100
MIN_VALID_INSTANCES = 50
RAW_LOG_PATH = PROJECT_ROOT / "data" / "negative_control_raw_log.jsonl"
MATRIX_PATH = PROJECT_ROOT / "data" / "negative_control_matrix.json"

OPERATOR_CLASS_BY_FAMILY = {
    "minimum_margin_feasibility": "CLASS_A",
    "syntax_only": "CLASS_B",
    "ordering_invariant": "CLASS_C",
}


@dataclass(frozen=True)
class NegativeControlSpec:
    problem_id: str
    family: str
    input_key: str
    solver_id: str
    solver: Callable[[Any], Any]
    reference_tests: list[dict[str, Any]]
    perturb: Callable[[dict[str, Any], int], list[dict[str, Any]]]
    oracle: Callable[[Any], Any]
    comparator: Callable[[Any, Any], bool] = operator.eq


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _is_list_of_ints(value: Any) -> bool:
    return isinstance(value, list) and all(type(item) is int for item in value)


def _is_sudoku_board(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 9
        and all(isinstance(row, list) and len(row) == 9 for row in value)
        and all(
            cell == "." or (isinstance(cell, str) and cell in "123456789")
            for row in value
            for cell in row
        )
    )


def _is_well_formed(spec: NegativeControlSpec, test: dict[str, Any]) -> bool:
    if not isinstance(test, dict) or spec.input_key not in test:
        return False
    value = test[spec.input_key]
    if spec.problem_id in {"LC55", "LC53", "LC179"}:
        return _is_list_of_ints(value)
    if spec.problem_id == "LC36":
        return _is_sudoku_board(value)
    return False


def _domain_tests(spec: NegativeControlSpec) -> list[dict[str, Any]]:
    tests = [copy.deepcopy(test) for test in spec.reference_tests if _is_well_formed(spec, test)]
    if spec.problem_id == "LC55":
        tests = [test for test in tests if lc55_oracle(copy.deepcopy(test["nums"]))]
    return tests


def _generate_perturbation(
    spec: NegativeControlSpec,
    original: dict[str, Any],
    instance_index: int,
) -> dict[str, Any] | None:
    try:
        candidates = spec.perturb(copy.deepcopy(original), instance_index)
    except Exception:  # noqa: BLE001 - review artifact records invalid perturbations.
        return None
    if not candidates:
        return None
    perturbed = copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])
    if not _is_well_formed(spec, perturbed):
        return None
    return perturbed


def _perturbation_valid(
    spec: NegativeControlSpec,
    original: dict[str, Any],
    perturbed: dict[str, Any],
) -> bool:
    if spec.problem_id == "LC55":
        return lc55_oracle(copy.deepcopy(perturbed["nums"])) is True
    if spec.problem_id in {"LC53", "LC36"}:
        return _stable_json(original[spec.input_key]) == _stable_json(perturbed[spec.input_key])
    if spec.problem_id == "LC179":
        return sorted(original["nums"]) == sorted(perturbed["nums"])
    return False


def _classify_failure_mode(perturbation_valid: bool, oracle_value: Any, solver_value: Any) -> str:
    if not perturbation_valid:
        return "invalid_perturbation"
    if oracle_value is True and solver_value is False:
        return "false_negative"
    if oracle_value is False and solver_value is True:
        return "false_positive"
    if oracle_value is True and solver_value is True:
        return "false_pass"
    if oracle_value is False and solver_value is False:
        return "correct_rejection"
    return "false_pass" if oracle_value == solver_value else "correct_rejection"


def _trace_instance(spec: NegativeControlSpec, instance_index: int) -> dict[str, Any]:
    domain = _domain_tests(spec)
    if not domain:
        raise ValueError(f"no canonical inputs available for {spec.problem_id}")

    original = copy.deepcopy(domain[(instance_index - 1) % len(domain)])
    perturbed = _generate_perturbation(spec, original, instance_index)
    perturbation_valid = (
        perturbed is not None and _perturbation_valid(spec, original, perturbed)
    )

    oracle_verdict = None
    solver_verdict = None
    if perturbation_valid and perturbed is not None:
        oracle_verdict = spec.oracle(copy.deepcopy(perturbed[spec.input_key]))
        solver_verdict = spec.solver(copy.deepcopy(perturbed[spec.input_key]))

    comparison = (
        spec.comparator(solver_verdict, oracle_verdict)
        if perturbation_valid
        else False
    )
    rejection = perturbation_valid and not comparison
    false_pass = perturbation_valid and comparison
    failure_mode = _classify_failure_mode(
        perturbation_valid,
        oracle_verdict,
        solver_verdict,
    )

    return {
        "problem_id": spec.problem_id,
        "family": spec.family,
        "solver_id": spec.solver_id,
        "instance_index": instance_index,
        "perturbation_valid": perturbation_valid,
        "oracle_verdict": _jsonable(oracle_verdict),
        "solver_verdict": _jsonable(solver_verdict),
        "rejection": rejection,
        "false_pass": false_pass,
        "failure_mode": failure_mode,
    }


def _negative_control_specs() -> tuple[NegativeControlSpec, ...]:
    return (
        NegativeControlSpec(
            problem_id="LC55",
            family="minimum_margin_feasibility",
            input_key="nums",
            solver_id="lc55_slack_dependent",
            solver=lc55_slack_dependent,
            reference_tests=LC55_REFERENCE_TESTS,
            perturb=lc55_minimum_margin_perturbations,
            oracle=lc55_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC55",
            family="minimum_margin_feasibility",
            input_key="nums",
            solver_id="lc55_reachability_optimism",
            solver=lc55_reachability_optimism,
            reference_tests=LC55_REFERENCE_TESTS,
            perturb=lc55_minimum_margin_perturbations,
            oracle=lc55_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC36",
            family="syntax_only",
            input_key="board",
            solver_id="lc36_row_only",
            solver=lc36_row_only,
            reference_tests=LC36_REFERENCE_TESTS,
            perturb=lc36_syntax_only_perturbations,
            oracle=lc36_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC36",
            family="syntax_only",
            input_key="board",
            solver_id="lc36_rows_cols_only",
            solver=lc36_rows_cols_only,
            reference_tests=LC36_REFERENCE_TESTS,
            perturb=lc36_syntax_only_perturbations,
            oracle=lc36_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC36",
            family="syntax_only",
            input_key="board",
            solver_id="solver_check_rows_cols_skip_boxes",
            solver=solver_check_rows_cols_skip_boxes,
            reference_tests=LC36_REFERENCE_TESTS,
            perturb=lc36_syntax_only_perturbations,
            oracle=lc36_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC179",
            family="ordering_invariant",
            input_key="nums",
            solver_id="lc179_numeric_descending",
            solver=lc179_numeric_descending,
            reference_tests=LC179_REFERENCE_TESTS,
            perturb=lc179_nums_reordering_perturbations,
            oracle=lc179_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC53",
            family="syntax_only",
            input_key="nums",
            solver_id="solver_always_zero",
            solver=solver_always_zero,
            reference_tests=LC53_REFERENCE_TESTS,
            perturb=lc53_syntax_only_perturbations,
            oracle=lc53_oracle,
        ),
        NegativeControlSpec(
            problem_id="LC53",
            family="syntax_only",
            input_key="nums",
            solver_id="solver_max_element",
            solver=solver_max_element,
            reference_tests=LC53_REFERENCE_TESTS,
            perturb=lc53_syntax_only_perturbations,
            oracle=lc53_oracle,
        ),
    )


def write_raw_log() -> None:
    RAW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_LOG_PATH.open("w", encoding="utf-8") as raw_log:
        for spec in _negative_control_specs():
            for instance_index in range(1, INSTANCES_PER_COMBINATION + 1):
                raw_log.write(
                    _stable_json(_trace_instance(spec, instance_index)) + "\n"
                )


def _rate(records: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> float:
    if not records:
        return 0.0
    return sum(1 for record in records if predicate(record)) / len(records)


def _operator_class(family: str) -> str:
    try:
        return OPERATOR_CLASS_BY_FAMILY[family]
    except KeyError as exc:
        raise ValueError(f"unresolved operator class for family: {family}") from exc


def _falsification_power(operator_class: str, correct_rejection_rate: float, false_pass_rate: float) -> str:
    if operator_class != "CLASS_C":
        raise ValueError(f"falsification scoring is only valid for CLASS_C, got {operator_class}")
    if false_pass_rate > 0.30 or correct_rejection_rate < 0.20:
        return "LOW_FALSIFICATION_POWER"
    if correct_rejection_rate >= 0.80 and false_pass_rate <= 0.05:
        return "HIGH"
    if correct_rejection_rate >= 0.50 and false_pass_rate <= 0.15:
        return "MEDIUM"
    if correct_rejection_rate >= 0.20 and false_pass_rate <= 0.30:
        return "LOW"
    return "LOW_FALSIFICATION_POWER"


def _alerts(total_valid_instances: int, correct_rejection_rate: float, false_pass_rate: float) -> list[str]:
    alerts: list[str] = []
    if false_pass_rate > 0.30:
        alerts.append("HIGH_FALSE_PASS_RATE")
    if correct_rejection_rate < 0.20:
        alerts.append("LOW_REJECTION_POWER")
    if total_valid_instances < MIN_VALID_INSTANCES:
        alerts.append("LOW_VALID_INSTANCE_COUNT")
    return alerts


def aggregate_from_raw_log() -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    with RAW_LOG_PATH.open("r", encoding="utf-8") as raw_log:
        for line in raw_log:
            record = json.loads(line)
            key = (record["problem_id"], record["family"], record["solver_id"])
            groups.setdefault(key, []).append(record)

    matrix: list[dict[str, Any]] = []
    for problem_id, family, solver_id in sorted(groups):
        records = groups[(problem_id, family, solver_id)]
        operator_class = _operator_class(family)
        valid_records = [record for record in records if record["perturbation_valid"] is True]
        total_generated_instances = len(records)
        total_valid_instances = len(valid_records)
        invalid_perturbation_count = total_generated_instances - total_valid_instances
        total_oracle_evaluated = total_valid_instances
        correct_rejection_rate = _rate(valid_records, lambda record: record["rejection"] is True)
        false_pass_rate = _rate(valid_records, lambda record: record["false_pass"] is True)
        false_negative_rate = _rate(
            valid_records,
            lambda record: record["failure_mode"] == "false_negative",
        )
        false_positive_rate = _rate(
            valid_records,
            lambda record: record["failure_mode"] == "false_positive",
        )
        power = (
            _falsification_power(operator_class, correct_rejection_rate, false_pass_rate)
            if operator_class == "CLASS_C"
            else "NOT_APPLICABLE"
        )
        matrix.append(
            {
                "problem_id": problem_id,
                "family": family,
                "operator_class": operator_class,
                "solver_id": solver_id,
                "total_generated_instances": total_generated_instances,
                "invalid_perturbation_count": invalid_perturbation_count,
                "total_oracle_evaluated": total_oracle_evaluated,
                "total_valid_instances": total_valid_instances,
                "correct_rejection_rate": correct_rejection_rate,
                "false_pass_rate": false_pass_rate,
                "false_negative_rate": false_negative_rate,
                "false_positive_rate": false_positive_rate,
                "falsification_power": power,
                "alerts": _alerts(
                    total_valid_instances,
                    correct_rejection_rate,
                    false_pass_rate,
                ),
            }
        )

    MATRIX_PATH.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return matrix


def main() -> int:
    write_raw_log()
    matrix = aggregate_from_raw_log()
    for entry in matrix:
        if entry["total_valid_instances"] < MIN_VALID_INSTANCES:
            entry["alerts"] = sorted(set(entry["alerts"] + ["LOW_VALID_INSTANCE_COUNT"]))
    MATRIX_PATH.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    blocked = any(
        entry["operator_class"] == "CLASS_C" and entry["alerts"]
        for entry in matrix
    )
    print(f"Wrote raw log: {RAW_LOG_PATH}")
    print(f"Wrote matrix: {MATRIX_PATH}")
    print(f"Phase 2.0C gate: {'BLOCKED' if blocked else 'UNLOCKED'}")
    return 1 if blocked else 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
