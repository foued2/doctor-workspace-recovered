# tests/test_collapse_perturbations.py
# Phase C-5: Collapse Analysis (Distribution Shift) — test suite
# TDD: tests written before the perturbation module.

import pytest

from doctor.collapse_perturbations import (
    invert_ground_truth,
    subsample_solvers,
    knockout_probe_family,
    classify_survival,
)


# ---------------------------------------------------------------------------
# Fixtures: LC322-shaped data (30 solvers, 11 ACCEPT / 19 REJECT)
# ---------------------------------------------------------------------------

def make_ground_truth(n_accept: int = 11, n_reject: int = 19) -> list[str]:
    """11 ACCEPT + 19 REJECT, matching LC322."""
    return ["ACCEPT"] * n_accept + ["REJECT"] * n_reject


def make_per_solver_list(ground_truth: list[str]) -> list[dict]:
    """Build per-solver list with solver_id and ground_truth."""
    return [
        {"solver_id": f"solver_{i+1:03d}", "ground_truth": gt, "decisions": {}}
        for i, gt in enumerate(ground_truth)
    ]


LC322_FAMILIES = [
    "reachability_counterfactual",
    "non_canonical_coin_order",
    "large_amount_stress",
    "greedy_dp_threshold",
    "forward_dp_overwrite",
    "memo_cache_aliasing",
]


def make_probe_index(family_counts: dict[str, int] | None = None) -> dict:
    """Build probe_index with 30 probes, 5 per family."""
    if family_counts is None:
        family_counts = {f: 5 for f in LC322_FAMILIES}
    probes = []
    pid = 0
    for fam, count in family_counts.items():
        for _ in range(count):
            pid += 1
            probes.append({
                "probe_id": f"p_{pid:03d}",
                "family": fam,
                "axis": "test_axis",
            })
    return {"probes": probes, "axis_set": ["test_axis"]}


def make_pass_results(n_solvers: int = 30, n_probes: int = 30) -> dict:
    """Build trivial pass_results: all True."""
    return {
        f"solver_{i+1:03d}": {f"p_{j+1:03d}": True for j in range(n_probes)}
        for i in range(n_solvers)
    }


# ---------------------------------------------------------------------------
# 1. P1: invert_ground_truth
# ---------------------------------------------------------------------------

class TestP1RatioShift:

    def test_invert_changes_all_labels(self):
        gt = ["ACCEPT"] * 5 + ["REJECT"] * 5
        inverted = invert_ground_truth(gt)
        assert inverted == ["REJECT"] * 5 + ["ACCEPT"] * 5

    def test_invert_lc322_shaped_produces_19_accept_11_reject(self):
        gt = make_ground_truth(n_accept=11, n_reject=19)
        inverted = invert_ground_truth(gt)
        assert inverted.count("ACCEPT") == 19
        assert inverted.count("REJECT") == 11

    def test_invert_double_application_returns_original(self):
        gt = make_ground_truth()
        assert invert_ground_truth(invert_ground_truth(gt)) == gt

    def test_invert_preserves_length(self):
        gt = make_ground_truth()
        assert len(invert_ground_truth(gt)) == len(gt)

    def test_invert_raises_on_invalid_label(self):
        with pytest.raises(ValueError):
            invert_ground_truth(["ACCEPT", "MAYBE"])

    def test_invert_empty_list(self):
        assert invert_ground_truth([]) == []


# ---------------------------------------------------------------------------
# 2. P2: subsample_solvers
# ---------------------------------------------------------------------------

class TestP2Subsample:

    def test_p2a_first_20_indices(self):
        per_solver = make_per_solver_list(make_ground_truth())
        subsample = subsample_solvers(per_solver, list(range(20)))
        assert len(subsample) == 20
        assert [s["solver_id"] for s in subsample] == [
            f"solver_{i+1:03d}" for i in range(20)
        ]

    def test_p2b_last_20_indices(self):
        per_solver = make_per_solver_list(make_ground_truth())
        indices = list(range(10, 30))
        subsample = subsample_solvers(per_solver, indices)
        assert len(subsample) == 20
        assert [s["solver_id"] for s in subsample] == [
            f"solver_{i+1:03d}" for i in range(10, 30)
        ]

    def test_p2c_first10_last10_indices(self):
        per_solver = make_per_solver_list(make_ground_truth())
        indices = list(range(10)) + list(range(20, 30))
        subsample = subsample_solvers(per_solver, indices)
        assert len(subsample) == 20
        assert [s["solver_id"] for s in subsample] == (
            [f"solver_{i+1:03d}" for i in range(10)]
            + [f"solver_{i+1:03d}" for i in range(20, 30)]
        )

    def test_subsample_preserves_solver_order(self):
        per_solver = make_per_solver_list(make_ground_truth())
        indices = [5, 0, 15, 3]
        subsample = subsample_solvers(per_solver, indices)
        assert [s["solver_id"] for s in subsample] == [
            "solver_006", "solver_001", "solver_016", "solver_004"
        ]

    def test_subsample_preserves_ground_truth(self):
        per_solver = make_per_solver_list(make_ground_truth())
        indices = [0, 11, 20]
        subsample = subsample_solvers(per_solver, indices)
        assert [s["ground_truth"] for s in subsample] == ["ACCEPT", "REJECT", "REJECT"]

    def test_subsample_raises_on_out_of_bounds_index(self):
        per_solver = make_per_solver_list(make_ground_truth())
        with pytest.raises(IndexError):
            subsample_solvers(per_solver, [30])

    def test_subsample_raises_on_negative_index(self):
        per_solver = make_per_solver_list(make_ground_truth())
        with pytest.raises(IndexError):
            subsample_solvers(per_solver, [-1])


# ---------------------------------------------------------------------------
# 3. P3: knockout_probe_family
# ---------------------------------------------------------------------------

class TestP3Knockout:

    def test_knockout_removes_correct_family(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        filtered, removed = knockout_probe_family(
            pass_results, probe_index, "reachability_counterfactual"
        )
        assert len(removed) == 5
        assert removed == ["p_001", "p_002", "p_003", "p_004", "p_005"]

    def test_knockout_filters_pass_results(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        filtered, removed = knockout_probe_family(
            pass_results, probe_index, "non_canonical_coin_order"
        )
        for sid, probes in filtered.items():
            for pid in probes:
                assert pid not in removed

    def test_knockout_preserves_solver_count(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        filtered, _ = knockout_probe_family(
            pass_results, probe_index, "reachability_counterfactual"
        )
        assert len(filtered) == 30

    def test_knockout_reduces_probe_count_per_solver(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        filtered, _ = knockout_probe_family(
            pass_results, probe_index, "reachability_counterfactual"
        )
        for sid, probes in filtered.items():
            assert len(probes) == 25  # 30 - 5

    def test_knockout_returns_sorted_removed_ids(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        _, removed = knockout_probe_family(
            pass_results, probe_index, "memo_cache_aliasing"
        )
        assert removed == sorted(removed)

    def test_knockout_unknown_family_removes_nothing(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        filtered, removed = knockout_probe_family(
            pass_results, probe_index, "nonexistent_family"
        )
        assert removed == []
        for sid, probes in filtered.items():
            assert len(probes) == 30

    def test_knockout_all_six_families_rotates_correctly(self):
        pass_results = make_pass_results()
        probe_index = make_probe_index()
        all_removed: set[str] = set()
        for fam in LC322_FAMILIES:
            _, removed = knockout_probe_family(pass_results, probe_index, fam)
            assert len(removed) == 5
            all_removed.update(removed)
        assert len(all_removed) == 30  # all 6 families cover all 30 probes


# ---------------------------------------------------------------------------
# 4. classify_survival: falsification criterion
# ---------------------------------------------------------------------------

class TestClassifySurvival:

    def test_all_survive(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.5},
                {"lambda_R": 50, "gap": 8.0},
            ]},
            {"perturbation_id": "P2a", "gaps": [
                {"lambda_R": 1, "gap": 0.3},
                {"lambda_R": 50, "gap": 5.0},
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "SURVIVES"

    def test_all_collapse(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.05},
                {"lambda_R": 50, "gap": -0.5},
            ]},
            {"perturbation_id": "P2a", "gaps": [
                {"lambda_R": 1, "gap": 0.0},
                {"lambda_R": 50, "gap": -1.0},
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "DOES_NOT_SURVIVE"

    def test_partial_survive(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.5},
                {"lambda_R": 50, "gap": 8.0},
            ]},
            {"perturbation_id": "P2a", "gaps": [
                {"lambda_R": 1, "gap": 0.05},  # collapse
                {"lambda_R": 50, "gap": 5.0},
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "PARTIALLY_SURVIVES"

    def test_collapse_at_one_lambda_means_collapse(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.5},
                {"lambda_R": 50, "gap": 0.05},  # collapse at one lambda
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "DOES_NOT_SURVIVE"

    def test_reversal_means_collapse(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.5},
                {"lambda_R": 50, "gap": -1.0},  # reversal
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "DOES_NOT_SURVIVE"

    def test_none_gaps_treated_as_collapse(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": None},  # degenerate, treated as collapse
                {"lambda_R": 50, "gap": 5.0},
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "DOES_NOT_SURVIVE"

    def test_empty_perturbations_list(self):
        assert classify_survival([], delta=0.10) == "SURVIVES"

    def test_single_perturbation_survives(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.5},
                {"lambda_R": 50, "gap": 5.0},
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "SURVIVES"

    def test_single_perturbation_collapses(self):
        perts = [
            {"perturbation_id": "P1", "gaps": [
                {"lambda_R": 1, "gap": 0.05},
                {"lambda_R": 50, "gap": 5.0},
            ]},
        ]
        assert classify_survival(perts, delta=0.10) == "DOES_NOT_SURVIVE"
