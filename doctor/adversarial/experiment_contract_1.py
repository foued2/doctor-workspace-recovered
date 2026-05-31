from __future__ import annotations

from pathlib import Path

import pytest

from doctor.adversarial.experiment_contract import ExperimentInput, SolverClassification
from doctor.adversarial.experiment_runner import (
    ExperimentSolver,
    ExperimentSpec,
    SolverInterfaceContractError,
    _validate_solver_interface,
    run_experiment,
)
from doctor.adversarial.lc322_candidates import (
    lc322_bfs_coin_count_cutoff,
    lc322_dp,
    lc322_greedy,
    lc322_modulo_memo_alias,
    lc322_reachability_lookahead,
)
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


ERD_WRAPPED_RUNNERS = {
    Path("runners/run_lc322_search_resource_truncation_probe.py"),
    Path("runners/run_lc45_solver_population.py"),
}

LEGACY_DIAGNOSTIC_JSON_WRITERS = {
    Path("runners/run_lc128_adversarial.py"),
    Path("runners/run_lc128_negative_control.py"),
    Path("runners/run_lc128_survival_matrix.py"),
    Path("runners/run_lc135_survival_matrix.py"),
    Path("runners/run_lc45_interaction_matrix.py"),
    Path("runners/run_lc56_survival_matrix.py"),
    Path("runners/run_lc322_opt_c_survivor_local_dominance.py"),
}


def test_tracked_experiment_runners_use_erd_wrapper():
    for path in ERD_WRAPPED_RUNNERS:
        text = path.read_text(encoding="utf-8")
        assert "run_experiment" in text
        assert "write_experiment_artifacts" in text
        assert "OUTPUT_PATH.write_text" not in text


def test_new_lc_json_artifact_writers_cannot_bypass_erd_wrapper():
    lc_json_writers = []
    for path in Path("runners").glob("run_lc*.py"):
        text = path.read_text(encoding="utf-8")
        if "OUTPUT_PATH" in text and ".write_text" in text:
            lc_json_writers.append(path)

    allowed = ERD_WRAPPED_RUNNERS | LEGACY_DIAGNOSTIC_JSON_WRITERS
    unexpected = sorted(path.as_posix() for path in lc_json_writers if path not in allowed)
    assert unexpected == []


def test_solver_interface_mismatch_fails_before_execution():
    calls = {"count": 0}

    def bad_solver(nums: list[int], amount: int) -> int:
        calls["count"] += 1
        return amount

    def classify(_inputs, _executions):
        return (SolverClassification(solver_id="bad", label="UNKNOWN"),)

    spec = ExperimentSpec(
        problem_id="lc45",
        solver_set_id="bad-set",
        manifold_set_id="lc45-six-manifold-probe-set-v1",
        probe_set_id="lc45-six-manifold-probe-set-v1",
        failure_class_version="interface-test-v1",
        inputs=(
            ExperimentInput(
                input_id="i1",
                manifold_id="m1",
                payload={"nums": [2, 3, 1, 1, 4]},
                expected=2,
            ),
        ),
        solvers=(ExperimentSolver(solver_id="bad", run=bad_solver),),
        classify=classify,
    )
    with pytest.raises(SolverInterfaceContractError):
        run_experiment(spec)
    assert calls["count"] == 0


def test_lc322_lc45_experiment_solvers_use_universal_interface():
    solvers = {
        "lc322_dp": lc322_dp,
        "lc322_greedy": lc322_greedy,
        "lc322_bfs_coin_count_cutoff": lc322_bfs_coin_count_cutoff,
        "lc322_modulo_memo_alias": lc322_modulo_memo_alias,
        "lc322_reachability_lookahead": lc322_reachability_lookahead,
        "lc45_naive_greedy": lc45_naive_greedy,
        "lc45_max_landing_value": lc45_max_landing_value,
        "lc45_farthest_landing_path": lc45_farthest_landing_path,
        "lc45_zero_dead_end_panic": lc45_zero_dead_end_panic,
        "lc45_reachable_boolean_confusion": lc45_reachable_boolean_confusion,
        "lc45_bfs_depth_cutoff": lc45_bfs_depth_cutoff,
        "lc45_three_step_window_dp": lc45_three_step_window_dp,
        "lc45_frontier_off_by_one": lc45_frontier_off_by_one,
        "lc45_uniform_formula_generalizer": lc45_uniform_formula_generalizer,
        "lc45_first_window_max_then_greedy": lc45_first_window_max_then_greedy,
    }
    for solver_id, solver in solvers.items():
        _validate_solver_interface(ExperimentSolver(solver_id=solver_id, run=solver))
