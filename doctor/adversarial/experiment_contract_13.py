from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.experiment_contract import REQUIRED_PROVENANCE_FIELDS
from doctor.adversarial.lc322_ground_truth import lc322_brute_force
from doctor.adversarial.lc322_ingestion_gate import (
    lc322_coin_reordering_perturbations,
    lc322_ingestion_gate,
)
from solvers.lc322_true_case_b_solvers import (
    lc322_amount_outer_equivalent_dp,
    lc322_bfs_shortest_path,
    lc322_recursive_memo_exact,
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "lc322_heldout_validation.json"
EXTERNAL_MANIFEST_PATH = PROJECT_ROOT / "EXTERNAL_VALIDATION_MANIFEST.json"

Solver = Callable[[list[int]], int]


HELDOUT_SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc322_amount_outer_equivalent_dp", lc322_amount_outer_equivalent_dp),
    ("lc322_bfs_shortest_path", lc322_bfs_shortest_path),
    ("lc322_recursive_memo_exact", lc322_recursive_memo_exact),
)

INTERNAL_VALIDATION_CASES: tuple[dict[str, Any], ...] = (
    {"case_id": "lc322_holdout_internal_001", "coins": [1, 3, 4], "amount": 6},
    {"case_id": "lc322_holdout_internal_002", "coins": [2, 5, 10], "amount": 27},
    {"case_id": "lc322_holdout_internal_003", "coins": [3, 7, 12], "amount": 24},
    {"case_id": "lc322_holdout_internal_004", "coins": [6, 10, 14], "amount": 25},
)


def _wrap_solver(solver: Solver) -> Callable[[list[int], int], int]:
    return lambda coins, amount: solver([*coins, amount])


def _reference_tests(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"coins": list(row["coins"]), "amount": int(row["amount"])} for row in rows]


def _perturbation_count(rows: list[dict[str, Any]]) -> int:
    return sum(
        len(lc322_coin_reordering_perturbations({"coins": list(row["coins"]), "amount": int(row["amount"])}, 3))
        for row in rows
    )


def _external_cases() -> list[dict[str, Any]]:
    payload = json.loads(EXTERNAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for case in payload["cases"]:
        row = dict(case["input"])
        row["case_id"] = case["case_id"]
        row["expected_output"] = case["expected_output"]
        rows.append(row)
    return rows


def _validate_expected_outputs(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        expected = lc322_brute_force(list(row["coins"]), int(row["amount"]))
        if "expected_output" in row and row["expected_output"] != expected:
            raise AssertionError(f"{row['case_id']} expected_output mismatch")
        row["expected_output"] = expected


def _complete_provenance(row: dict[str, Any]) -> bool:
    provenance = row.get("k_provenance", {})
    return REQUIRED_PROVENANCE_FIELDS.issubset(provenance)


def _run_suite(suite_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _validate_expected_outputs(rows)
    result_rows: list[dict[str, Any]] = []
    reference_tests = _reference_tests(rows)
    provenance_base_input = reference_tests[0]
    provenance_perturbed_input = lc322_coin_reordering_perturbations(provenance_base_input, 3)[0]
    perturbation_count = _perturbation_count(rows)
    result = lc322_ingestion_gate(
        problem={"id": "LC322", "suite": suite_name},
        solvers=[_wrap_solver(solver) for _, solver in HELDOUT_SOLVERS],
        oracle=lc322_brute_force,
        reference_tests=reference_tests,
        perturbation_samples=3,
        thresholds={
            "min_perturbation_stability": 0.8,
            "max_perturbation_drop": 0.15,
            "min_oracle_alignment": 0.7,
        },
    )
    for solver_index, (solver_name, _solver) in enumerate(HELDOUT_SOLVERS):
        solver_key = f"solver_{solver_index}"
        solver_stability = result["metrics"]["perturbation_stability"]["per_solver"][solver_key]
        result_rows.append(
            {
                "row_unit": "suite_solver_aggregate",
                "suite": suite_name,
                "problem": "LC322",
                "solver_name": solver_name,
                "case_count": len(rows),
                "case_ids": [row["case_id"] for row in rows],
                "solver_case_evaluation_count": len(rows),
                "perturbation_evaluation_count": perturbation_count,
                "scored_solver_output_count": len(rows) + perturbation_count,
                "provenance_base_input": provenance_base_input,
                "provenance_perturbed_input": provenance_perturbed_input,
                "provenance_inputs_identical": provenance_base_input == provenance_perturbed_input,
                "ingest": result["ingest"],
                "reason": result["reason"],
                "metrics": {
                    **result["metrics"],
                    "perturbation_stability": {
                        "per_solver": {solver_key: solver_stability},
                        "max_drop": 1.0 - solver_stability,
                    },
                },
                "k_provenance": result["k_provenance"],
            }
        )
    return result_rows


def main() -> None:
    internal_rows = [dict(row) for row in INTERNAL_VALIDATION_CASES]
    external_rows = _external_cases()
    result_rows = [
        *_run_suite("heldout_internal", internal_rows),
        *_run_suite("external_validation", external_rows),
    ]
    for row in result_rows:
        if not _complete_provenance(row):
            raise AssertionError(f"incomplete k_provenance for {row['solver_name']} {row['suite']}")

    report = {
        "schema_version": "1.0.0",
        "stage": "post-freeze held-out validation",
        "problem": "LC322",
        "result_row_unit": "suite_solver_aggregate",
        "result_row_unit_definition": "Each result row aggregates one held-out solver over one validation suite. It is not a single solver-case row.",
        "heldout_solver_count": len(HELDOUT_SOLVERS),
        "included_solver_count": len(HELDOUT_SOLVERS),
        "excluded_solver_count": 0,
        "internal_validation_case_count": len(internal_rows),
        "external_validation_case_count": len(external_rows),
        "solver_case_evaluation_count": sum(row["solver_case_evaluation_count"] for row in result_rows),
        "external_solver_case_evaluation_count": sum(
            row["solver_case_evaluation_count"] for row in result_rows if row["suite"] == "external_validation"
        ),
        "perturbation_evaluation_count": sum(row["perturbation_evaluation_count"] for row in result_rows),
        "scored_solver_output_count": sum(row["scored_solver_output_count"] for row in result_rows),
        "result_row_count": len(result_rows),
        "result_rows_with_complete_k_provenance": sum(1 for row in result_rows if _complete_provenance(row)),
        "scoring_blocked_count": 0,
        "perturbation_class_counts": _counts(row["k_provenance"]["perturbation_class"] for row in result_rows),
        "comparator_counts": _counts(row["k_provenance"]["comparator_name"] for row in result_rows),
        "proof_card_coverage": sum(1 for row in result_rows if row["k_provenance"]["proof_card_id"]),
        "forbidden_experiments_run": [],
        "result_rows": result_rows,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "heldout_solver_count",
        "external_validation_case_count",
        "result_row_count",
        "result_rows_with_complete_k_provenance",
    )}, indent=2, sort_keys=True))


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))


if __name__ == "__main__":
    main()
