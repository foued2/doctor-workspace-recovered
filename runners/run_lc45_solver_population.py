from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc45_bimaristan import LC45
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
from doctor.adversarial.lc45_ground_truth import lc45_brute_force
from doctor.adversarial.experiment_contract import ExperimentInput, SolverClassification
from doctor.adversarial.experiment_runner import (
    ExperimentSolver,
    ExperimentSpec,
    run_experiment,
    write_experiment_artifacts,
)
from runners.run_lc45 import _run_generator


OUTPUT_PATH = PROJECT_ROOT / "data" / "lc45_solver_population.json"
RECORD_OUTPUT_PATH = PROJECT_ROOT / "data" / "experiment_runs" / "lc45_optc_population_record.json"

LOCAL_HORIZON_MANIFOLDS = {
    "naive_max_jump_suboptimal",
    "single_large_jump_decoy",
    "greedy_horizon_collapse",
    "naive_max_jump_dead_landing",
}
CONTROL_MANIFOLDS = {
    "uniform_jump_array",
    "greedy_frontier_valid_no_false_pressure",
}

SOLVERS: tuple[tuple[str, str, Callable[[list[int]], int]], ...] = (
    ("lc45_naive_greedy", "local_max_jump_horizon", lc45_naive_greedy),
    ("lc45_max_landing_value", "local_value_horizon", lc45_max_landing_value),
    ("lc45_farthest_landing_path", "local_reach_horizon", lc45_farthest_landing_path),
    ("lc45_zero_dead_end_panic", "reachability_dead_end_overgeneralization", lc45_zero_dead_end_panic),
    ("lc45_reachable_boolean_confusion", "reachability_boolean_count_confusion", lc45_reachable_boolean_confusion),
    ("lc45_bfs_depth_cutoff", "search_resource_truncation", lc45_bfs_depth_cutoff),
    ("lc45_three_step_window_dp", "bounded_transition_window", lc45_three_step_window_dp),
    ("lc45_frontier_off_by_one", "counting_boundary_error", lc45_frontier_off_by_one),
    ("lc45_uniform_formula_generalizer", "uniform_pattern_overgeneralization", lc45_uniform_formula_generalizer),
    ("lc45_first_window_max_then_greedy", "local_max_jump_horizon", lc45_first_window_max_then_greedy),
)


def _instances() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in LC45.invariant_families:
        for manifold in family.failure_manifolds:
            generator = manifold.geometry_generators[0]
            result = _run_generator(manifold, generator)
            for index, context in enumerate(result["accepted"], start=1):
                nums = list(context["nums"])
                rows.append(
                    {
                        "input_id": f"{manifold.manifold_id}_{index:03d}",
                        "manifold_id": manifold.manifold_id,
                        "generator_id": generator.generator_id,
                        "family_class": (
                            "local_horizon"
                            if manifold.manifold_id in LOCAL_HORIZON_MANIFOLDS
                            else "control"
                        ),
                        "nums": nums,
                        "truth": lc45_brute_force(nums),
                    }
                )
    return rows


def _observed_failure_class(
    *,
    local_fail: int,
    local_total: int,
    control_fail: int,
    control_total: int,
    failed_manifolds: set[str],
    expected_failure_class: str,
) -> str:
    if local_fail == 0 and control_fail == 0:
        return "survivor"
    if local_fail > 0 and control_fail == 0:
        return "local_horizon_only"
    if local_fail == 0 and control_fail > 0:
        return "control_only_misfit"
    if expected_failure_class == "search_resource_truncation":
        return "search_resource_truncation_with_control_collateral"
    if expected_failure_class in {
        "reachability_dead_end_overgeneralization",
        "reachability_boolean_count_confusion",
    }:
        return "reachability_or_count_confusion"
    if expected_failure_class == "counting_boundary_error":
        return "counting_boundary_error"
    if expected_failure_class == "bounded_transition_window":
        return "bounded_transition_window"
    if failed_manifolds >= CONTROL_MANIFOLDS:
        return "broad_count_or_control_misfit"
    if local_total and control_total:
        return "mixed_local_and_control"
    return "unclassified"


def _experiment_inputs(instances: list[dict[str, object]]) -> tuple[ExperimentInput, ...]:
    return tuple(
        ExperimentInput(
            input_id=str(instance["input_id"]),
            manifold_id=str(instance["manifold_id"]),
            payload={"nums": list(instance["nums"])},
            expected=int(instance["truth"]),
        )
        for instance in instances
    )


def _experiment_solvers() -> tuple[ExperimentSolver, ...]:
    return tuple(
        ExperimentSolver(
            solver_id=solver_id,
            run=solver,
        )
        for solver_id, _expected_failure_class, solver in SOLVERS
    )


def _classify(inputs, executions) -> tuple[SolverClassification, ...]:
    by_input = {row.input_id: row for row in inputs}
    classifications = []
    for solver_id, expected_failure_class, _solver in SOLVERS:
        solver_executions = [row for row in executions if row.solver_id == solver_id]
        failures = [row for row in solver_executions if not row.passed]
        failed_manifolds = {by_input[row.input_id].manifold_id for row in failures}
        if solver_id == "lc45_farthest_landing_path":
            label = "UNKNOWN"
            failure_class = None
            mechanism = None
        elif solver_id == "lc45_bfs_depth_cutoff":
            label = "SURVIVOR"
            failure_class = "search_resource_truncation"
            mechanism = "Depth-bounded BFS hypothesis survives the current six LC45 manifolds."
        else:
            label = "BROKEN"
            failure_class = _observed_failure_class(
                local_fail=sum(1 for row in failures if by_input[row.input_id].manifold_id in LOCAL_HORIZON_MANIFOLDS),
                local_total=sum(
                    1 for row in solver_executions if by_input[row.input_id].manifold_id in LOCAL_HORIZON_MANIFOLDS
                ),
                control_fail=sum(1 for row in failures if by_input[row.input_id].manifold_id in CONTROL_MANIFOLDS),
                control_total=sum(
                    1 for row in solver_executions if by_input[row.input_id].manifold_id in CONTROL_MANIFOLDS
                ),
                failed_manifolds=failed_manifolds,
                expected_failure_class=expected_failure_class,
            )
            mechanism = failure_class
        classifications.append(
            SolverClassification(
                solver_id=solver_id,
                label=label,
                failure_class=failure_class,
                mechanism=mechanism,
                evidence_input_ids=tuple(row.input_id for row in failures[:8]),
            )
        )
    return tuple(classifications)


def _solver_result_from_record(solver_id: str, expected_failure_class: str, record, instances_by_id):
    executions = [row for row in record.executions if row.solver_id == solver_id]
    failures = [row for row in executions if not row.passed]
    pass_count_by_manifold: dict[str, int] = {}
    fail_count_by_manifold: dict[str, int] = {}
    total_count_by_manifold: dict[str, int] = {}
    failure_records = []
    for row in executions:
        instance = instances_by_id[row.input_id]
        manifold_id = str(instance["manifold_id"])
        total_count_by_manifold[manifold_id] = total_count_by_manifold.get(manifold_id, 0) + 1
        if row.passed:
            pass_count_by_manifold[manifold_id] = pass_count_by_manifold.get(manifold_id, 0) + 1
        else:
            fail_count_by_manifold[manifold_id] = fail_count_by_manifold.get(manifold_id, 0) + 1
            failure_records.append(
                {
                    "input_id": row.input_id,
                    "manifold_id": manifold_id,
                    "family_class": instance["family_class"],
                    "nums": list(instance["nums"]),
                    "truth": row.expected,
                    "observed": row.observed,
                }
            )

    local_total = sum(total_count_by_manifold.get(manifold_id, 0) for manifold_id in LOCAL_HORIZON_MANIFOLDS)
    local_fail = sum(fail_count_by_manifold.get(manifold_id, 0) for manifold_id in LOCAL_HORIZON_MANIFOLDS)
    control_total = sum(total_count_by_manifold.get(manifold_id, 0) for manifold_id in CONTROL_MANIFOLDS)
    control_fail = sum(fail_count_by_manifold.get(manifold_id, 0) for manifold_id in CONTROL_MANIFOLDS)
    classification = next(row for row in record.classifications if row.solver_id == solver_id)
    observed_failure_class = (
        classification.failure_class if classification.label in {"BROKEN", "SURVIVOR"} else "UNKNOWN"
    )
    return {
        "solver_id": solver_id,
        "expected_failure_class": expected_failure_class,
        "observed_failure_class": observed_failure_class,
        "optc_label": classification.label,
        "total_count": len(executions),
        "fail_count": len(failures),
        "fail_rate": round(len(failures) / len(executions), 4) if executions else 0.0,
        "local_horizon_fail_count": local_fail,
        "local_horizon_total": local_total,
        "local_horizon_fail_rate": round(local_fail / local_total, 4) if local_total else 0.0,
        "control_fail_count": control_fail,
        "control_total": control_total,
        "control_fail_rate": round(control_fail / control_total, 4) if control_total else 0.0,
        "pass_count_by_manifold": pass_count_by_manifold,
        "fail_count_by_manifold": fail_count_by_manifold,
        "failure_examples": failure_records[:8],
    }


def build_record(instances: list[dict[str, object]]):
    spec = ExperimentSpec(
        problem_id="lc45",
        solver_set_id="lc45-llm-population-v1",
        manifold_set_id="lc45-six-manifold-probe-set-v1",
        probe_set_id="lc45-six-manifold-probe-set-v1",
        failure_class_version="lc45-optc-failure-classes-v1",
        inputs=_experiment_inputs(instances),
        solvers=_experiment_solvers(),
        classify=_classify,
        status="experimental",
        notes="Active LC45 OPT-C solver-population run.",
    )
    return run_experiment(spec)


def build_report() -> dict[str, object]:
    instances = _instances()
    record = build_record(instances)
    instances_by_id = {str(instance["input_id"]): instance for instance in instances}
    solver_results = [
        _solver_result_from_record(solver_id, expected_failure_class, record, instances_by_id)
        for solver_id, expected_failure_class, _solver in SOLVERS
    ]
    failure_class_distribution: dict[str, int] = {}
    optc_label_distribution: dict[str, int] = {}
    for row in solver_results:
        observed_class = str(row["observed_failure_class"])
        failure_class_distribution[observed_class] = failure_class_distribution.get(observed_class, 0) + 1
        optc_label = str(row["optc_label"])
        optc_label_distribution[optc_label] = optc_label_distribution.get(optc_label, 0) + 1
    survivors = [
        str(row["solver_id"])
        for row in solver_results
        if row["optc_label"] in {"SURVIVOR", "UNKNOWN"}
    ]
    exposed = [
        str(row["solver_id"])
        for row in solver_results
        if row["optc_label"] == "BROKEN"
    ]
    return {
        "problem_id": "lc45",
        "method": "solver_population_x_existing_six_manifolds",
        "candidate_cap_per_manifold": 12,
        "manifold_count": len({instance["manifold_id"] for instance in instances}),
        "instance_count": len(instances),
        "local_horizon_manifolds": sorted(LOCAL_HORIZON_MANIFOLDS),
        "control_manifolds": sorted(CONTROL_MANIFOLDS),
        "solver_population_size": len(SOLVERS),
        "exposed_solver_ids": exposed,
        "survivor_solver_ids": survivors,
        "failure_class_distribution": failure_class_distribution,
        "optc_label_distribution": optc_label_distribution,
        "instances": instances,
        "solver_results": solver_results,
        "experiment_run_record_path": str(RECORD_OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "_record": record,
    }


def main() -> int:
    report = build_report()
    record = report.pop("_record")
    write_experiment_artifacts(
        report=report,
        report_path=OUTPUT_PATH,
        record=record,
        record_path=RECORD_OUTPUT_PATH,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_PATH}")
    print(f"Wrote: {RECORD_OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
