"""Phase 2.0B perturbation integrity calibration runner.

Review-only artifact unless invoked directly. The runner verifies only whether
each active perturbation family preserves its claimed invariant.
"""
from __future__ import annotations

import copy
import hashlib
import json
import multiprocessing as mp
import operator
import sys
import traceback
from collections import Counter
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
from runners.run_lc53_gate import REFERENCE_TESTS as LC53_REFERENCE_TESTS
from runners.run_lc53_gate import lc53_oracle
from runners.run_lc55_gate import REFERENCE_TESTS as LC55_REFERENCE_TESTS
from runners.run_lc55_gate import lc55_oracle
from runners.run_lc179_gate import REFERENCE_TESTS as LC179_REFERENCE_TESTS
from runners.run_lc179_gate import lc179_oracle

INVOCATIONS_PER_FAMILY = 100
COMPARATOR_RECHECKS = 5
EXPECTED_RAW_RECORDS = 4 * INVOCATIONS_PER_FAMILY
RAW_LOG_PATH = PROJECT_ROOT / "data" / "perturbation_integrity_raw_log.jsonl"
REPORT_PATH = PROJECT_ROOT / "data" / "perturbation_integrity_report.json"

GENERATION_REASONS = {
    "nearest_good_suffix_empty",
    "construction_contradiction",
    "generator_exception",
    "representation_invalid",
    "comparator_domain_violation",
}
VALIDITY_REASONS = {
    "reachability_broken",
    "semantic_mutation",
    "ordering_illegal",
    "invariant_violated",
}
ORACLE_REASONS = {
    "oracle_mismatch",
    "oracle_exception",
    "oracle_undefined",
}
COMPARATOR_REASONS = {
    "comparator_exception",
    "comparator_undefined_state",
    "comparator_inconsistent",
}
ALL_REASONS = GENERATION_REASONS | VALIDITY_REASONS | ORACLE_REASONS | COMPARATOR_REASONS


@dataclass(frozen=True)
class ProblemSpec:
    problem_id: str
    family: str
    input_key: str
    reference_tests: list[dict[str, Any]]
    perturb: Callable[[dict[str, Any], int], list[dict[str, Any]]]
    oracle: Callable[[Any], Any]
    oracle_type: type
    comparator: Callable[[Any, Any], bool] = operator.eq


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _empty_record(spec: ProblemSpec, index: int, original_hash: str) -> dict[str, Any]:
    return {
        "problem_id": spec.problem_id,
        "family": spec.family,
        "invocation_index": index,
        "original_input_hash": original_hash,
        "perturbed_input_hash": None,
        "generation_success": None,
        "generation_failure_reason": None,
        "validity_pass": None,
        "validity_failure_reason": None,
        "oracle_original": None,
        "oracle_perturbed": None,
        "oracle_stable": None,
        "oracle_failure_reason": None,
        "comparator_defined": None,
        "comparator_consistent": None,
        "comparator_failure_reason": None,
        "failure_layer": None,
        "failure_reason": None,
    }


def _fail(record: dict[str, Any], layer: str, reason: str) -> dict[str, Any]:
    if reason not in ALL_REASONS:
        raise ValueError(f"unregistered failure reason: {reason}")
    record["failure_layer"] = layer
    record["failure_reason"] = reason
    if layer == "generation":
        record["generation_success"] = False
        record["generation_failure_reason"] = reason
        record["validity_pass"] = None
        record["oracle_original"] = None
        record["oracle_perturbed"] = None
        record["oracle_stable"] = None
        record["comparator_defined"] = None
        record["comparator_consistent"] = None
    elif layer == "validity":
        record["validity_pass"] = False
        record["validity_failure_reason"] = reason
        record["oracle_original"] = None
        record["oracle_perturbed"] = None
        record["oracle_stable"] = None
        record["comparator_defined"] = None
        record["comparator_consistent"] = None
    elif layer == "oracle_stability":
        record["oracle_stable"] = False
        record["oracle_failure_reason"] = reason
        record["comparator_defined"] = None
        record["comparator_consistent"] = None
    elif layer == "comparator":
        record["comparator_consistent"] = False
        record["comparator_failure_reason"] = reason
    else:
        raise ValueError(f"unknown failure layer: {layer}")
    return record


def _is_list_of_ints(value: Any) -> bool:
    return isinstance(value, list) and all(type(item) is int for item in value)


def _is_sudoku_board(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 9
        and all(isinstance(row, list) and len(row) == 9 for row in value)
        and all(cell == "." or (isinstance(cell, str) and cell in "123456789") for row in value for cell in row)
    )


def _is_well_formed(spec: ProblemSpec, test: dict[str, Any]) -> bool:
    if not isinstance(test, dict) or spec.input_key not in test:
        return False
    value = test[spec.input_key]
    if spec.problem_id in {"LC55", "LC53", "LC179"}:
        return _is_list_of_ints(value)
    if spec.problem_id == "LC36":
        return _is_sudoku_board(value)
    return False


def _lc55_generation_reason(original: dict[str, Any], perturbed: dict[str, Any]) -> str | None:
    nums = original["nums"]
    changed = perturbed["nums"]
    if len(changed) != len(nums):
        return "construction_contradiction"
    if nums and len(nums) > 1 and changed[0] == 0:
        return "nearest_good_suffix_empty"
    return None


def _lc179_generation_reason(perturbed: dict[str, Any]) -> str | None:
    nums = perturbed["nums"]
    if any(n < 0 for n in nums):
        return "comparator_domain_violation"
    return None


def _generate_perturbation(
    spec: ProblemSpec,
    original: dict[str, Any],
    invocation_index: int,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        candidates = spec.perturb(copy.deepcopy(original), invocation_index)
    except Exception:  # noqa: BLE001 - mapped to protocol failure reason.
        return None, "generator_exception"
    if not candidates:
        return None, "generator_exception"
    perturbed = copy.deepcopy(candidates[(invocation_index - 1) % len(candidates)])
    if not _is_well_formed(spec, perturbed):
        if spec.problem_id == "LC179":
            return None, "comparator_domain_violation"
        return None, "representation_invalid"
    if spec.problem_id == "LC55":
        return perturbed, _lc55_generation_reason(original, perturbed)
    if spec.problem_id == "LC179":
        return perturbed, _lc179_generation_reason(perturbed)
    return perturbed, None


def _validity_reason(spec: ProblemSpec, original: dict[str, Any], perturbed: dict[str, Any]) -> str | None:
    if spec.problem_id == "LC55":
        if not lc55_oracle(copy.deepcopy(perturbed["nums"])):
            return "reachability_broken"
        return None
    if spec.problem_id in {"LC53", "LC36"}:
        if _stable_json(original[spec.input_key]) != _stable_json(perturbed[spec.input_key]):
            return "semantic_mutation"
        return None
    if spec.problem_id == "LC179":
        if sorted(original["nums"]) != sorted(perturbed["nums"]):
            return "ordering_illegal"
        return None
    return "invariant_violated"


def _oracle_value(spec: ProblemSpec, test: dict[str, Any]) -> tuple[Any, str | None]:
    try:
        value = spec.oracle(copy.deepcopy(test[spec.input_key]))
    except Exception:  # noqa: BLE001 - mapped to protocol failure reason.
        return None, "oracle_exception"
    if type(value) is not spec.oracle_type:
        return value, "oracle_undefined"
    return value, None


def _comparator_consistency(spec: ProblemSpec, original_value: Any, perturbed_value: Any) -> tuple[bool, str | None]:
    decisions: list[bool] = []
    try:
        for _ in range(COMPARATOR_RECHECKS):
            decision = spec.comparator(original_value, perturbed_value)
            if type(decision) is not bool:
                return False, "comparator_undefined_state"
            decisions.append(decision)
    except Exception:  # noqa: BLE001 - mapped to protocol failure reason.
        return False, "comparator_exception"
    if any(decision != decisions[0] for decision in decisions):
        return False, "comparator_inconsistent"
    return True, None


def _domain_tests(spec: ProblemSpec) -> list[dict[str, Any]]:
    tests = [copy.deepcopy(test) for test in spec.reference_tests if _is_well_formed(spec, test)]
    if spec.problem_id == "LC55":
        tests = [test for test in tests if lc55_oracle(copy.deepcopy(test["nums"]))]
    return tests


def _trace_invocation(spec: ProblemSpec, invocation_index: int) -> dict[str, Any]:
    domain = _domain_tests(spec)
    if not domain:
        raise ValueError(f"no canonical inputs available for {spec.problem_id}")
    original = copy.deepcopy(domain[(invocation_index - 1) % len(domain)])
    original_hash_before = _sha256_json(original)
    record = _empty_record(spec, invocation_index, original_hash_before)

    perturbed, generation_reason = _generate_perturbation(spec, original, invocation_index)
    original_hash_after = _sha256_json(original)
    if original_hash_before != original_hash_after:
        record["perturbed_input_hash"] = _sha256_json(perturbed) if perturbed is not None else None
        return _fail(record, "generation", "construction_contradiction")
    if generation_reason is not None or perturbed is None:
        record["perturbed_input_hash"] = _sha256_json(perturbed) if perturbed is not None else None
        return _fail(record, "generation", generation_reason or "generator_exception")

    record["perturbed_input_hash"] = _sha256_json(perturbed)
    record["generation_success"] = True

    validity_reason = _validity_reason(spec, original, perturbed)
    if validity_reason is not None:
        return _fail(record, "validity", validity_reason)
    record["validity_pass"] = True

    original_value, original_reason = _oracle_value(spec, original)
    perturbed_value, perturbed_reason = _oracle_value(spec, perturbed)
    if perturbed_reason is not None:
        record["oracle_original"] = _jsonable(original_value)
        return _fail(record, "oracle_stability", perturbed_reason)
    if original_reason is not None:
        record["oracle_perturbed"] = _jsonable(perturbed_value)
        return _fail(record, "oracle_stability", original_reason)

    record["oracle_original"] = _jsonable(original_value)
    record["oracle_perturbed"] = _jsonable(perturbed_value)
    if original_value != perturbed_value:
        return _fail(record, "oracle_stability", "oracle_mismatch")
    record["oracle_stable"] = True

    record["comparator_defined"] = True
    comparator_consistent, comparator_reason = _comparator_consistency(spec, original_value, perturbed_value)
    if comparator_reason is not None:
        return _fail(record, "comparator", comparator_reason)
    record["comparator_consistent"] = comparator_consistent
    if not comparator_consistent:
        return _fail(record, "comparator", "comparator_inconsistent")
    return record


def _problem_specs() -> tuple[ProblemSpec, ...]:
    return (
        ProblemSpec(
            problem_id="LC55",
            family="minimum_margin_feasibility",
            input_key="nums",
            reference_tests=LC55_REFERENCE_TESTS,
            perturb=lc55_minimum_margin_perturbations,
            oracle=lc55_oracle,
            oracle_type=bool,
        ),
        ProblemSpec(
            problem_id="LC53",
            family="syntax_only",
            input_key="nums",
            reference_tests=LC53_REFERENCE_TESTS,
            perturb=lc53_syntax_only_perturbations,
            oracle=lc53_oracle,
            oracle_type=int,
        ),
        ProblemSpec(
            problem_id="LC36",
            family="syntax_only",
            input_key="board",
            reference_tests=LC36_REFERENCE_TESTS,
            perturb=lc36_syntax_only_perturbations,
            oracle=lc36_oracle,
            oracle_type=bool,
        ),
        ProblemSpec(
            problem_id="LC179",
            family="ordering_invariant",
            input_key="nums",
            reference_tests=LC179_REFERENCE_TESTS,
            perturb=lc179_nums_reordering_perturbations,
            oracle=lc179_oracle,
            oracle_type=str,
        ),
    )


def write_raw_log() -> None:
    RAW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    records_written = 0
    with RAW_LOG_PATH.open("w", encoding="utf-8") as raw_log:
        for spec in _problem_specs():
            for invocation_index in range(1, INVOCATIONS_PER_FAMILY + 1):
                raw_log.write(_stable_json(_trace_invocation(spec, invocation_index)) + "\n")
                records_written += 1
    if records_written != EXPECTED_RAW_RECORDS:
        raise AssertionError(f"expected {EXPECTED_RAW_RECORDS} raw records, wrote {records_written}")


def _rate(records: list[dict[str, Any]], key: str) -> float:
    return sum(1 for record in records if record[key] is True) / len(records)


def _alerts(summary: dict[str, Any]) -> list[str]:
    alerts: list[str] = []
    if summary["generation_success_rate"] < 0.90:
        alerts.append("LOW_GENERATION_SUCCESS")
    if summary["validity_pass_rate"] < 0.90:
        alerts.append("LOW_VALIDITY_RATE")
    if summary["oracle_stability_rate"] < 1.0:
        alerts.append("ORACLE_INSTABILITY")
    if summary["comparator_consistency_rate"] < 1.0:
        alerts.append("COMPARATOR_INSTABILITY")
    for reason, count in summary["failure_reason_histogram"].items():
        if count > 5:
            alerts.append(f"SYSTEMATIC_FAILURE: {reason}")
    return alerts


def aggregate_from_raw_log() -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with RAW_LOG_PATH.open("r", encoding="utf-8") as raw_log:
        for line in raw_log:
            record = json.loads(line)
            groups.setdefault((record["problem_id"], record["family"]), []).append(record)

    report: list[dict[str, Any]] = []
    for problem_id, family in sorted(groups):
        records = groups[(problem_id, family)]
        histogram = Counter(record["failure_reason"] for record in records if record["failure_reason"] is not None)
        summary = {
            "problem_id": problem_id,
            "family": family,
            "total_invocations": len(records),
            "generation_success_rate": _rate(records, "generation_success"),
            "validity_pass_rate": _rate(records, "validity_pass"),
            "oracle_stability_rate": _rate(records, "oracle_stable"),
            "comparator_consistency_rate": _rate(records, "comparator_consistent"),
            "failure_reason_histogram": dict(sorted(histogram.items())),
            "alerts": [],
        }
        summary["alerts"] = _alerts(summary)
        report.append(summary)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    write_raw_log()
    report = aggregate_from_raw_log()
    blocked = any(entry["alerts"] for entry in report)
    print(f"Wrote raw log: {RAW_LOG_PATH}")
    print(f"Wrote report: {REPORT_PATH}")
    print(f"Phase 2.0C gate: {'BLOCKED' if blocked else 'UNLOCKED'}")
    return 1 if blocked else 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
