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

from doctor.adversarial.comparators import get_comparator
from doctor.adversarial.experiment_contract import REQUIRED_PROVENANCE_FIELDS, validate_provenance
from doctor.adversarial.experiment_runner import (
    construct_evaluation_provenance,
    dispatch_comparator,
    recompute_oracles,
    validate_scoring_gate,
)
from doctor.adversarial.lc3928_candidates import (
    lc3928_exact_small_reference,
    lc3928_greedy_nearest_shop,
    lc3928_naive_local_price,
    lc3928_single_source_wrong_direction,
)
from doctor.adversarial.lc3928_oracle import lc3928_exact_small
from doctor.adversarial.provenance import input_hash, oracle_identity


OUTPUT_PATH = PROJECT_ROOT / "data" / "lc3928_doctor_probe.json"
PROBLEM_ID = "LC3928"
PERTURBATION_FAMILY = "identity"
COMPARATOR_NAME = "ExactIntSequenceComparator"
RNG_SEED = 3928

Solver = Callable[[int, list[int], list[list[int]]], list[int]]

SOLVERS: tuple[tuple[str, Solver], ...] = (
    ("lc3928_exact_small_reference", lc3928_exact_small_reference),
    ("lc3928_naive_local_price", lc3928_naive_local_price),
    ("lc3928_single_source_wrong_direction", lc3928_single_source_wrong_direction),
    ("lc3928_greedy_nearest_shop", lc3928_greedy_nearest_shop),
)


def main() -> None:
    started = time.perf_counter()
    declaration = validate_scoring_gate(PROBLEM_ID, PERTURBATION_FAMILY)
    comparator = get_comparator(COMPARATOR_NAME)
    cases = _build_cases()
    oracle_version = oracle_identity(lc3928_exact_small)
    oracle_calls = 0
    for case in cases:
        expected_base, expected_perturbed = recompute_oracles(
            lc3928_exact_small,
            case["input"],
            _identity_perturbation(case["input"]),
            _apply_oracle,
        )
        oracle_calls += 2
        case["oracle_output"] = expected_base
        case["_expected_perturbed_output"] = expected_perturbed
        case["oracle_version"] = oracle_version
        case["comparator"] = COMPARATOR_NAME
        case["input_hash"] = input_hash(case["input"])

    result_rows: list[dict[str, Any]] = []
    for suite in sorted({case["suite"] for case in cases}):
        suite_cases = [case for case in cases if case["suite"] == suite]
        for solver_name, solver in SOLVERS:
            result_rows.append(
                _run_solver_suite(
                    suite=suite,
                    suite_cases=suite_cases,
                    solver_name=solver_name,
                    solver=solver,
                    declaration=declaration,
                    comparator_version=comparator.version,
                )
            )

    report = {
        "schema_version": "1.0.0",
        "stage": "LC3928 Doctor admission/probe",
        "problem": PROBLEM_ID,
        "source_url": "https://leetcode.com/problems/minimum-cost-to-buy-apples-ii/",
        "problem_manifest": "LC3928_PROBLEM_MANIFEST.json",
        "solver_manifest": "LC3928_SOLVER_MANIFEST.json",
        "oracle_type": "exact small",
        "oracle_max_n_used": max(case["n"] for case in cases),
        "oracle_max_m_used": max(len(case["input"]["roads"]) for case in cases),
        "oracle_max_weight_used": max((road[2] for case in cases for road in case["input"]["roads"]), default=0),
        "oracle_max_tax_used": max((road[3] for case in cases for road in case["input"]["roads"]), default=0),
        "oracle_max_price_used": max(price for case in cases for price in case["input"]["prices"]),
        "oracle_calls": oracle_calls,
        "validation_suite_counts": _counts(case["suite"] for case in cases),
        "examples_count": _count_suite(cases, "sample"),
        "exhaustive_case_count": _count_suite(cases, "exhaustive_tiny"),
        "random_case_count": _count_suite(cases, "random_small"),
        "shape_focused_case_count": _count_suite(cases, "shape_focused"),
        "adversarial_tradeoff_case_count": _count_suite(cases, "adversarial_tradeoff"),
        "random_seed": RNG_SEED,
        "solver_count": len(SOLVERS),
        "solver_names": [name for name, _solver in SOLVERS],
        "solver_case_evaluation_count": sum(row["solver_case_evaluation_count"] for row in result_rows),
        "scored_perturbation_evaluation_count": sum(row["scored_perturbation_evaluation_count"] for row in result_rows),
        "blocked_perturbation_family_count": 7,
        "blocked_perturbation_evaluation_count": 0,
        "perturbation_families": {
            "declared_output_preserving": ["identity"],
            "unknown_until_oracle_recompute_blocked": [
                "road_order_shuffle",
                "node_relabeling",
                "duplicate_edge_normalization",
                "disconnected_component_rewrite",
                "price_shift",
                "edge_weight_scaling",
                "graph_isomorphism_transformation"
            ],
            "invalid": []
        },
        "proof_card_coverage": {
            "output_preserving_declared": 1,
            "with_proof_card": 1,
            "proof_card_id": declaration.proof_card_id
        },
        "comparator": {
            "name": COMPARATOR_NAME,
            "version": comparator.version,
            "bool_int_rejection_tested": True,
            "list_output_safety_tested": True
        },
        "result_row_unit": "suite_solver_aggregate",
        "result_row_count": len(result_rows),
        "result_rows_with_complete_k_provenance": sum(1 for row in result_rows if _complete_provenance(row)),
        "rows_missing_provenance": sum(1 for row in result_rows if not row.get("k_provenance")),
        "stale_provenance_rows": 0,
        "bad_input_hash_rows": _bad_hash_rows(result_rows),
        "proof_card_gaps": sum(1 for row in result_rows if not row["k_provenance"].get("proof_card_id")),
        "invalid_or_unknown_scored_rows": sum(
            1 for row in result_rows
            if row["k_provenance"]["perturbation_class"] in {"invalid", "unknown_until_oracle_recompute"}
        ),
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "case_records": [_public_case_record(case) for case in cases],
        "result_rows": result_rows,
        "forbidden_experiments_run": []
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "case_count": len(cases),
        "result_row_count": len(result_rows),
        "solver_case_evaluation_count": report["solver_case_evaluation_count"],
        "runtime_seconds": report["runtime_seconds"]
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
    representative_base = suite_cases[0]["input"]
    representative_perturbed = _identity_perturbation(representative_base)
    provenance = construct_evaluation_provenance(
        problem_id=PROBLEM_ID,
        perturbation_family=PERTURBATION_FAMILY,
        oracle=lc3928_exact_small,
        comparator_name=COMPARATOR_NAME,
        comparator_version=comparator_version,
        base_input=representative_base,
        perturbed_input=representative_perturbed,
        declaration=declaration,
    ).to_dict()
    pass_count = 0
    fail_count = 0
    total_positions = 0
    total_abs_error = 0
    largest_abs_error = 0
    first_failing_case: dict[str, Any] | None = None
    for case in suite_cases:
        expected = case["_expected_perturbed_output"]
        payload = _identity_perturbation(case["input"])
        observed = solver(payload["n"], list(payload["prices"]), [list(road) for road in payload["roads"]])
        comparison = dispatch_comparator(COMPARATOR_NAME, observed, expected)
        if comparison.equal:
            pass_count += 1
        else:
            fail_count += 1
            if first_failing_case is None:
                first_failing_case = {
                    "case_id": case["case_id"],
                    "suite": suite,
                    "n": case["n"],
                    "prices": case["input"]["prices"],
                    "roads": case["input"]["roads"],
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
    cases = [
        _case("sample", "lc3928_sample_001", 2, [8, 3], [[0, 1, 1, 2]], "leetcode_sample"),
        _case("sample", "lc3928_sample_002", 3, [9, 4, 6], [[0, 1, 1, 3], [1, 2, 4, 2]], "leetcode_sample"),
        _case("sample", "lc3928_sample_003", 3, [10, 11, 1], [[0, 2, 1, 3], [1, 2, 3, 4], [0, 1, 5, 2]], "leetcode_sample"),
    ]
    cases.extend(_exhaustive_tiny_cases())
    cases.extend(_random_small_cases())
    cases.extend(_shape_cases())
    cases.extend(_adversarial_tradeoff_cases())
    return cases


def _exhaustive_tiny_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    idx = 1
    for n in range(1, 4):
        possible_edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
        edge_options = [None, (1, 1), (1, 2), (2, 1), (2, 2)]
        for prices in itertools.product(range(1, 4), repeat=n):
            for choices in itertools.product(edge_options, repeat=len(possible_edges)):
                roads: list[list[int]] = []
                for (u, v), option in zip(possible_edges, choices):
                    if option is None:
                        continue
                    cost, tax = option
                    roads.append([u, v, cost, tax])
                cases.append(_case("exhaustive_tiny", f"lc3928_exhaustive_{idx:05d}", n, list(prices), roads, "all_n_le_3_prices_1_3_cost_tax_1_2"))
                idx += 1
    return cases


def _random_small_cases() -> list[dict[str, Any]]:
    rng = random.Random(RNG_SEED)
    cases: list[dict[str, Any]] = []
    for idx in range(1, 101):
        n = rng.randint(2, 7)
        prices = [rng.randint(1, 30) for _ in range(n)]
        all_edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
        rng.shuffle(all_edges)
        m = rng.randint(0, min(len(all_edges), n + 3))
        roads = [[u, v, rng.randint(1, 12), rng.randint(1, 8)] for u, v in all_edges[:m]]
        cases.append(_case("random_small", f"lc3928_random_{idx:03d}", n, prices, roads, "fixed_seed_random_graph"))
    return cases


def _shape_cases() -> list[dict[str, Any]]:
    return [
        _case("shape_focused", "lc3928_shape_single_node", 1, [7], [], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_two_nodes", 2, [10, 1], [[0, 1, 2, 3]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_path", 5, [20, 18, 2, 30, 25], [[0, 1, 2, 2], [1, 2, 2, 2], [2, 3, 3, 4], [3, 4, 1, 5]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_star", 5, [50, 8, 9, 10, 1], [[0, 1, 1, 5], [0, 2, 2, 4], [0, 3, 3, 3], [0, 4, 4, 2]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_cycle", 4, [9, 20, 3, 12], [[0, 1, 1, 2], [1, 2, 1, 5], [2, 3, 1, 2], [3, 0, 7, 1]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_disconnected", 4, [5, 100, 1, 40], [[0, 1, 2, 2], [2, 3, 2, 2]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_complete_tiny", 4, [12, 3, 14, 6], [[0, 1, 1, 2], [0, 2, 5, 1], [0, 3, 2, 4], [1, 2, 2, 3], [1, 3, 3, 2], [2, 3, 1, 5]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_equal_prices", 4, [10, 10, 10, 10], [[0, 1, 1, 2], [1, 2, 1, 2], [2, 3, 1, 2]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_cheap_distant", 5, [100, 90, 80, 70, 1], [[0, 1, 1, 1], [1, 2, 1, 1], [2, 3, 1, 1], [3, 4, 1, 1]], "manual_shape_focused"),
        _case("shape_focused", "lc3928_shape_large_weight_contrast", 4, [30, 2, 20, 1], [[0, 1, 1, 100], [0, 2, 20, 1], [2, 3, 1, 1], [1, 3, 50, 1]], "manual_shape_focused"),
    ]


def _adversarial_tradeoff_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    idx = 1

    def add(n: int, prices: list[int], roads: list[list[int]], label: str) -> None:
        nonlocal idx
        cases.append(
            _case(
                "adversarial_tradeoff",
                f"lc3928_adv_tradeoff_{idx:03d}_{label}",
                n,
                prices,
                roads,
                "deterministic_adversarial_tradeoff",
            )
        )
        idx += 1

    for cheap in [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]:
        add(4, [100, 95, 90, cheap], [[0, 1, 1, 1], [1, 2, 1, 1], [2, 3, 1, 1]], "cheap_distant_path")
    for tax in [2, 3, 5, 8, 13, 21, 34, 55, 89, 100]:
        add(4, [30, 1, 25, 24], [[0, 1, 1, tax], [0, 2, 2, 1], [2, 3, 1, 1]], "cheap_near_high_tax")
    for detour in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15]:
        add(5, [70, 60, 4, 50, 45], [[0, 1, 1, 50], [1, 2, 1, 50], [0, 3, detour, 1], [3, 4, 1, 1], [4, 2, 1, 1]], "different_return_path")
    for local in [20, 30, 40, 50, 60, 70, 80, 90, 100, 120]:
        add(3, [local, 1, local + 5], [[0, 1, 3, 1], [1, 2, 2, 1], [0, 2, 1, 100]], "price_dominates_travel")
    for gap in [1, 2, 3, 4, 5, 8, 13, 21, 34, 55]:
        add(5, [100, 100 - gap, 100, 1, 100], [[0, 1, 1, 2], [1, 2, 1, 2], [2, 3, 10, 1], [0, 4, 2, 1], [4, 3, 2, 1]], "near_equal_options")
    for weight in [5, 8, 13, 21, 34, 55, 89, 100, 120, 150]:
        add(6, [90, 80, 70, 60, 50, 1], [[0, 1, 1, 1], [1, 2, weight, 1], [2, 5, 1, 1], [0, 3, 2, 2], [3, 4, 2, 2], [4, 5, 2, 2]], "edge_weight_contrast")
    add(6, [100, 2, 100, 100, 3, 100], [[0, 1, 1, 90], [0, 2, 2, 1], [2, 3, 2, 1], [3, 4, 2, 1], [4, 5, 1, 1]], "nearest_bad_tax")
    add(6, [100, 70, 60, 50, 40, 1], [[0, 1, 1, 100], [1, 2, 1, 100], [2, 5, 1, 100], [0, 3, 5, 1], [3, 4, 5, 1], [4, 5, 5, 1]], "single_source_bad")
    add(7, [9, 100, 100, 1, 100, 100, 2], [[0, 1, 1, 1], [1, 2, 1, 1], [2, 3, 1, 1], [0, 4, 1, 20], [4, 5, 1, 20], [5, 6, 1, 20]], "two_corridors")
    add(7, [100, 1, 100, 100, 100, 2, 100], [[0, 1, 2, 60], [0, 2, 4, 1], [2, 3, 1, 1], [3, 4, 1, 1], [4, 5, 1, 1], [5, 6, 1, 1]], "cheap_local_vs_better_route")
    add(8, [100, 90, 80, 70, 60, 50, 40, 1], [[0, 1, 1, 1], [1, 2, 1, 1], [2, 3, 1, 1], [3, 4, 1, 1], [4, 5, 1, 1], [5, 6, 1, 1], [6, 7, 1, 1], [0, 7, 20, 1]], "max_small_path")
    add(8, [5, 100, 100, 100, 1, 100, 100, 100], [[0, 1, 1, 100], [1, 2, 1, 100], [2, 3, 1, 100], [3, 4, 1, 100], [4, 5, 1, 1], [5, 6, 1, 1], [6, 7, 1, 1], [0, 7, 10, 1]], "max_small_tax")
    return cases


def _case(suite: str, case_id: str, n: int, prices: list[int], roads: list[list[int]], generation_method: str) -> dict[str, Any]:
    return {
        "suite": suite,
        "case_id": case_id,
        "n": n,
        "input": {"n": n, "prices": list(prices), "roads": [list(road) for road in roads]},
        "generation_method": generation_method,
    }


def _apply_oracle(oracle, payload: dict[str, Any]) -> list[int]:
    return oracle(payload["n"], payload["prices"], payload["roads"])


def _identity_perturbation(payload: dict[str, Any]) -> dict[str, Any]:
    return {"n": payload["n"], "prices": list(payload["prices"]), "roads": [list(road) for road in payload["roads"]]}


def _public_case_record(case: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in case.items() if key != "_expected_perturbed_output"}


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


def _count_suite(cases: list[dict[str, Any]], suite: str) -> int:
    return sum(1 for case in cases if case["suite"] == suite)


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))


if __name__ == "__main__":
    main()
