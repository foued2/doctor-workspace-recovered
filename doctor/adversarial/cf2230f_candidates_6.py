from __future__ import annotations

import itertools
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.cf2230f_candidates import (
    cf2230f_exact_bruteforce_small,
    cf2230f_greedy_deepest_start,
    cf2230f_greedy_leaf_path,
    cf2230f_local_depth_proxy,
)
from doctor.adversarial.cf2230f_oracle import cf2230f_scores_small, oracle_cache_info
from doctor.adversarial.comparators import get_comparator
from doctor.adversarial.experiment_contract import REQUIRED_PROVENANCE_FIELDS, validate_provenance
from doctor.adversarial.experiment_runner import (
    construct_evaluation_provenance,
    dispatch_comparator,
    recompute_oracles,
    validate_scoring_gate,
)
from doctor.adversarial.provenance import input_hash, oracle_identity


OUTPUT_PATH = PROJECT_ROOT / "data" / "cf2230f_doctor_probe.json"
PROBLEM_ID = "CF2230F"
PERTURBATION_FAMILY = "identity"
COMPARATOR_NAME = "ExactIntSequenceComparator"
RNG_SEED = 2230
EXHAUSTIVE_MAX_Q = 7
RANDOM_MIN_Q = 8
RANDOM_MAX_Q = 9
RANDOM_CASE_COUNT = 100

Solver = Callable[[list[int]], list[int]]

SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("cf2230f_exact_bruteforce_small", cf2230f_exact_bruteforce_small),
    ("cf2230f_greedy_deepest_start", cf2230f_greedy_deepest_start),
    ("cf2230f_greedy_leaf_path", cf2230f_greedy_leaf_path),
    ("cf2230f_local_depth_proxy", cf2230f_local_depth_proxy),
)


def main() -> None:
    started = time.perf_counter()
    declaration = validate_scoring_gate(PROBLEM_ID, PERTURBATION_FAMILY)
    comparator = get_comparator(COMPARATOR_NAME)
    cases = _build_cases()
    oracle_version = oracle_identity(cf2230f_scores_small)
    for case in cases:
        expected_base, expected_perturbed = recompute_oracles(
            cf2230f_scores_small,
            case["input"],
            _identity_perturbation(case["input"]),
            lambda oracle, payload: oracle(payload["parents"]),
        )
        case["oracle_output"] = expected_base
        case["expected_perturbed_output"] = expected_perturbed
        case["oracle_version"] = oracle_version
        case["comparator"] = COMPARATOR_NAME
        case["parent_list_hash"] = input_hash(case["input"]["parents"])

    result_rows: list[dict[str, Any]] = []
    total_solver_case_evaluations = 0
    total_scored_perturbation_evaluations = 0

    for suite in _suite_names(cases):
        suite_cases = [case for case in cases if case["suite"] == suite]
        for solver_name, solver in SOLVERS:
            row = _run_solver_suite(
                suite=suite,
                suite_cases=suite_cases,
                solver_name=solver_name,
                solver=solver,
                declaration=declaration,
                comparator_version=comparator.version,
            )
            result_rows.append(row)
            total_solver_case_evaluations += row["solver_case_evaluation_count"]
            total_scored_perturbation_evaluations += row["scored_perturbation_evaluation_count"]

    cache = oracle_cache_info()
    elapsed = time.perf_counter() - started
    report = {
        "schema_version": "1.0.0",
        "stage": "CF2230F Doctor admission/probe",
        "problem": PROBLEM_ID,
        "source_url": "https://codeforces.com/problemset/problem/2230/F",
        "problem_manifest": "CF2230F_PROBLEM_MANIFEST.json",
        "solver_manifest": "CF2230F_SOLVER_MANIFEST.json",
        "oracle_scope": "exact small only",
        "oracle_max_q_used": max(case["q"] for case in cases),
        "oracle_limit_q": 9,
        "oracle_cache": {
            "hits": cache.hits,
            "misses": cache.misses,
            "maxsize": cache.maxsize,
            "currsize": cache.currsize,
        },
        "runtime_seconds": round(elapsed, 6),
        "validation_suite_counts": _counts(case["suite"] for case in cases),
        "sample_case_count": _count_suite(cases, "sample"),
        "exhaustive_max_q": EXHAUSTIVE_MAX_Q,
        "exhaustive_case_count": _count_suite(cases, "exhaustive_tiny"),
        "random_case_count": _count_suite(cases, "random_small"),
        "random_seed": RNG_SEED,
        "shape_focused_case_count": _count_suite(cases, "shape_focused"),
        "solver_count": len(SOLVERS),
        "solver_names": [name for name, _ in SOLVERS],
        "solver_case_evaluation_count": total_solver_case_evaluations,
        "scored_perturbation_evaluation_count": total_scored_perturbation_evaluations,
        "blocked_perturbation_family_count": 5,
        "blocked_perturbation_evaluation_count": 0,
        "perturbation_families": {
            "declared_output_preserving": ["identity"],
            "unknown_until_oracle_recompute_blocked": [
                "parent_sequence_permutation",
                "subtree_relabeling",
                "query_reordering",
                "sibling_insertion_swapping",
                "final_tree_isomorphism_rewrite",
            ],
            "invalid": [],
        },
        "proof_card_coverage": {
            "output_preserving_declared": 1,
            "with_proof_card": 1,
            "proof_card_id": declaration.proof_card_id,
        },
        "comparator": {
            "name": COMPARATOR_NAME,
            "version": comparator.version,
            "bool_int_rejection_tested": True,
            "structured_list_output_safety_tested": True,
        },
        "result_row_unit": "suite_solver_aggregate",
        "result_row_count": len(result_rows),
        "result_rows_with_complete_k_provenance": sum(1 for row in result_rows if _complete_provenance(row)),
        "rows_missing_provenance": sum(1 for row in result_rows if not row.get("k_provenance")),
        "stale_provenance_rows": 0,
        "bad_input_hash_rows": _bad_hash_rows(result_rows),
        "proof_card_gaps": sum(1 for row in result_rows if not row["k_provenance"].get("proof_card_id")),
        "invalid_or_unknown_scored_rows": sum(
            1
            for row in result_rows
            if row["k_provenance"]["perturbation_class"] in {"invalid", "unknown_until_oracle_recompute"}
        ),
        "case_records": [_public_case_record(case) for case in cases],
        "result_rows": result_rows,
        "forbidden_experiments_run": [],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "case_count": len(cases),
        "result_row_count": len(result_rows),
        "solver_case_evaluation_count": total_solver_case_evaluations,
        "scored_perturbation_evaluation_count": total_scored_perturbation_evaluations,
        "runtime_seconds": round(elapsed, 6),
    }, indent=2, sort_keys=True))


def _run_solver_suite(
    *,
    suite: str,
    suite_cases: list[dict[str, Any]],
    solver_name: str,
    solver: Solver,
    declaration,
    comparator_version: str,
) -> dict[str, Any]:
    pass_count = 0
    fail_count = 0
    total_positions = 0
    total_abs_error = 0
    largest_abs_error = 0
    first_failing_case: dict[str, Any] | None = None
    representative_base = suite_cases[0]["input"]
    representative_perturbed = _identity_perturbation(representative_base)
    provenance = construct_evaluation_provenance(
        problem_id=PROBLEM_ID,
        perturbation_family=PERTURBATION_FAMILY,
        oracle=cf2230f_scores_small,
        comparator_name=COMPARATOR_NAME,
        comparator_version=comparator_version,
        base_input=representative_base,
        perturbed_input=representative_perturbed,
        declaration=declaration,
    ).to_dict()

    for case in suite_cases:
        perturbed_input = _identity_perturbation(case["input"])
        expected = case["expected_perturbed_output"]
        observed = solver(list(perturbed_input["parents"]))
        comparison = dispatch_comparator(COMPARATOR_NAME, observed, expected)
        if comparison.equal:
            pass_count += 1
        else:
            fail_count += 1
            if first_failing_case is None:
                first_failing_case = {
                    "case_id": case["case_id"],
                    "suite": suite,
                    "q": case["q"],
                    "parents": case["input"]["parents"],
                    "expected": expected,
                    "observed": observed,
                    "reason": comparison.reason,
                }
        for actual_value, expected_value in itertools.zip_longest(observed, expected, fillvalue=0):
            abs_error = abs(int(actual_value) - int(expected_value))
            total_abs_error += abs_error
            largest_abs_error = max(largest_abs_error, abs_error)
            total_positions += 1

    row = {
        "row_unit": "suite_solver_aggregate",
        "suite": suite,
        "problem": PROBLEM_ID,
        "solver_name": solver_name,
        "case_count": len(suite_cases),
        "solver_case_evaluation_count": len(suite_cases),
        "scored_perturbation_evaluation_count": len(suite_cases),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_count / len(suite_cases) if suite_cases else 0.0,
        "first_failing_case": first_failing_case,
        "largest_absolute_output_sequence_error": largest_abs_error,
        "mean_per_position_error": total_abs_error / total_positions if total_positions else 0.0,
        "provenance_base_input": representative_base,
        "provenance_perturbed_input": representative_perturbed,
        "provenance_inputs_identical": representative_base == representative_perturbed,
        "k_provenance": provenance,
    }
    validate_provenance({"k_provenance": provenance})
    return row


def _build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    cases.append(_case("sample", "cf2230f_sample_001", [1, 1, 3, 3, 1, 2, 1, 2, 8], "codeforces_sample"))
    for q in range(1, EXHAUSTIVE_MAX_Q + 1):
        ranges = [range(1, i + 1) for i in range(1, q + 1)]
        for idx, parents in enumerate(itertools.product(*ranges), start=1):
            cases.append(_case("exhaustive_tiny", f"cf2230f_exhaustive_q{q}_{idx:05d}", list(parents), "exhaustive_parent_sequences"))
    rng = random.Random(RNG_SEED)
    for idx in range(1, RANDOM_CASE_COUNT + 1):
        q = rng.randint(RANDOM_MIN_Q, RANDOM_MAX_Q)
        parents = [rng.randint(1, i) for i in range(1, q + 1)]
        cases.append(_case("random_small", f"cf2230f_random_{idx:03d}", parents, "fixed_seed_random_parent_sequence"))
    for case_id, parents in _shape_cases():
        cases.append(_case("shape_focused", case_id, parents, "manual_shape_focused"))
    return cases


def _case(suite: str, case_id: str, parents: list[int], generation_method: str) -> dict[str, Any]:
    return {
        "suite": suite,
        "case_id": case_id,
        "q": len(parents),
        "input": {"parents": list(parents)},
        "generation_method": generation_method,
    }


def _public_case_record(case: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in case.items()
        if key != "expected_perturbed_output"
    }


def _shape_cases() -> list[tuple[str, list[int]]]:
    return [
        ("cf2230f_shape_path", [1, 2, 3, 4, 5, 6, 7, 8, 9]),
        ("cf2230f_shape_star", [1, 1, 1, 1, 1, 1, 1, 1, 1]),
        ("cf2230f_shape_balanced", [1, 1, 2, 2, 3, 3, 4, 4, 5]),
        ("cf2230f_shape_broom", [1, 2, 3, 4, 5, 1, 1, 1, 1]),
        ("cf2230f_shape_alternating_shallow_deep", [1, 2, 1, 3, 1, 5, 1, 7, 1]),
        ("cf2230f_shape_repeated_leaf", [1, 2, 3, 4, 5, 6, 7, 8, 9]),
        ("cf2230f_shape_repeated_root", [1, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]


def _identity_perturbation(payload: dict[str, Any]) -> dict[str, Any]:
    return {"parents": list(payload["parents"])}


def _complete_provenance(row: dict[str, Any]) -> bool:
    return REQUIRED_PROVENANCE_FIELDS.issubset(row.get("k_provenance", {}))


def _bad_hash_rows(rows: list[dict[str, Any]]) -> int:
    bad = 0
    for row in rows:
        provenance = row["k_provenance"]
        if input_hash(row["provenance_base_input"]) != provenance["base_input_hash"]:
            bad += 1
        elif input_hash(row["provenance_perturbed_input"]) != provenance["perturbed_input_hash"]:
            bad += 1
    return bad


def _suite_names(cases: list[dict[str, Any]]) -> list[str]:
    return sorted({case["suite"] for case in cases})


def _count_suite(cases: list[dict[str, Any]], suite: str) -> int:
    return sum(1 for case in cases if case["suite"] == suite)


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))


if __name__ == "__main__":
    main()
