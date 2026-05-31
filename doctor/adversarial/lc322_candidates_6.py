from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import (
    lc322_bfs_coin_count_cutoff,
    lc322_dp,
    lc322_greedy,
    lc322_modulo_memo_alias,
    lc322_reachability_lookahead,
)
from doctor.adversarial.experiment_contract import ExperimentInput, SolverClassification
from doctor.adversarial.experiment_runner import (
    ExperimentSolver,
    ExperimentSpec,
    run_experiment,
    write_experiment_artifacts,
)
from doctor.adversarial.lc322_ground_truth import lc322_brute_force
from runners.run_lc322 import _candidate_space


OUTPUT_PATH = PROJECT_ROOT / "data" / "lc322_search_resource_truncation_probe.json"
RECORD_OUTPUT_PATH = PROJECT_ROOT / "data" / "experiment_runs" / "lc322_search_resource_truncation_record.json"
MANIFOLD_ID = "bfs_coin_count_cutoff"
INSTANCE_LIMIT = 12

SOLVERS: tuple[tuple[str, Callable[[list[int], int], int]], ...] = (
    ("lc322_dp", lc322_dp),
    ("lc322_greedy", lc322_greedy),
    ("lc322_bfs_coin_count_cutoff", lc322_bfs_coin_count_cutoff),
    ("lc322_modulo_memo_alias", lc322_modulo_memo_alias),
    ("lc322_reachability_lookahead", lc322_reachability_lookahead),
)


def _instances() -> list[dict[str, object]]:
    buckets: dict[int, list[tuple[list[int], int]]] = defaultdict(list)
    for coins, amount in _candidate_space(MANIFOLD_ID):
        buckets[int(amount)].append((list(coins), int(amount)))

    selected: list[tuple[list[int], int]] = []
    bucket_keys = sorted(buckets)
    offset = 0
    while len(selected) < INSTANCE_LIMIT:
        added = False
        for amount in bucket_keys:
            bucket = buckets[amount]
            if offset < len(bucket):
                selected.append(bucket[offset])
                added = True
                if len(selected) >= INSTANCE_LIMIT:
                    break
        if not added:
            break
        offset += 1

    rows = []
    for index, (coins, amount) in enumerate(selected, start=1):
        truth = lc322_brute_force(list(coins), amount)
        rows.append(
            {
                "input_id": f"lc322_search_resource_truncation_{index:03d}",
                "coins": list(coins),
                "amount": amount,
                "truth": truth,
                "optimal_coin_count": truth,
                "coin_type_count": len(coins),
                "optimal_coin_count_exceeds_coin_type_count": truth > len(coins),
            }
        )
        if len(rows) >= INSTANCE_LIMIT:
            break
    return rows


def _experiment_inputs(instances: list[dict[str, object]]) -> tuple[ExperimentInput, ...]:
    return tuple(
        ExperimentInput(
            input_id=str(instance["input_id"]),
            manifold_id=MANIFOLD_ID,
            payload={
                "nums": [*list(instance["coins"]), int(instance["amount"])],
            },
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
        for solver_id, solver in SOLVERS
    )


def _classify(_inputs, executions) -> tuple[SolverClassification, ...]:
    rows = []
    for solver_id, _solver in SOLVERS:
        solver_executions = [row for row in executions if row.solver_id == solver_id]
        failures = [row for row in solver_executions if not row.passed]
        if solver_id == "lc322_bfs_coin_count_cutoff":
            label = "SURVIVOR"
            failure_class = "search_resource_truncation"
            mechanism = (
                "Inputs require more optimal BFS depth than the bounded solver permits; "
                "target stops after the search depth exceeds the coin-type count."
            )
        else:
            label = "UNKNOWN"
            failure_class = None
            mechanism = None
        rows.append(
            SolverClassification(
                solver_id=solver_id,
                label=label,
                failure_class=failure_class,
                mechanism=mechanism,
                evidence_input_ids=tuple(row.input_id for row in failures[:5]),
            )
        )
    return tuple(rows)


def build_record(instances: list[dict[str, object]]):
    spec = ExperimentSpec(
        problem_id="lc322",
        solver_set_id="lc322-known-llm-population-v1",
        manifold_set_id="lc322-search-resource-truncation-v1",
        probe_set_id="lc322-search-resource-truncation-v1",
        failure_class_version="lc322-closed-failure-classes-v1",
        inputs=_experiment_inputs(instances),
        solvers=_experiment_solvers(),
        classify=_classify,
        status="closed",
        notes="LC322 search/resource truncation probe for closed artifact baseline.",
    )
    return run_experiment(spec)


def _solver_result_from_record(solver_id: str, record, instances_by_id):
    executions = [row for row in record.executions if row.solver_id == solver_id]
    failures = []
    passes = []
    for row in executions:
        instance = instances_by_id[row.input_id]
        result_row = {
            "input_id": row.input_id,
            "coins": list(instance["coins"]),
            "amount": int(instance["amount"]),
            "truth": row.expected,
            "observed": row.observed,
        }
        if row.passed:
            passes.append(result_row)
        else:
            failures.append(result_row)
    total = len(executions)
    return {
        "solver_id": solver_id,
        "pass_count": len(passes),
        "fail_count": len(failures),
        "pass_rate": round(len(passes) / total, 4) if total else 0.0,
        "fail_rate": round(len(failures) / total, 4) if total else 0.0,
        "failure_examples": failures[:5],
        "pass_examples": passes[:5],
    }


def build_report() -> dict[str, object]:
    instances = _instances()
    record = build_record(instances)
    instances_by_id = {str(instance["input_id"]): instance for instance in instances}
    solver_results = [
        _solver_result_from_record(solver_id, record, instances_by_id)
        for solver_id, _solver in SOLVERS
    ]
    by_solver = {result["solver_id"]: result for result in solver_results}

    target_result = by_solver["lc322_bfs_coin_count_cutoff"]
    modulo_result = by_solver["lc322_modulo_memo_alias"]
    reachability_result = by_solver["lc322_reachability_lookahead"]
    target_exposed = int(target_result["fail_count"]) == len(instances)
    no_collateral_degradation = (
        int(modulo_result["fail_count"]) == 0
        and int(reachability_result["fail_count"]) == 0
    )

    return {
        "problem_id": "lc322",
        "family_id": "search_resource_truncation",
        "manifold_id": MANIFOLD_ID,
        "target_solver_id": "lc322_bfs_coin_count_cutoff",
        "non_target_solver_ids_required_unchanged": [
            "lc322_modulo_memo_alias",
            "lc322_reachability_lookahead",
        ],
        "mechanism": (
            "Inputs require more optimal BFS depth than the bounded solver permits. "
            "The target solver stops after the search depth exceeds the coin-type count."
        ),
        "instances": instances,
        "solver_results": solver_results,
        "experiment_run_record_path": str(RECORD_OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "validation": {
            "target_exposed": target_exposed,
            "no_collateral_degradation": no_collateral_degradation,
            "validation_passed": target_exposed and no_collateral_degradation,
        },
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
    if not report["validation"]["validation_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
