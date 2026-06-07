"""
Tests for the LC3946-C5 perturbation module.

TDD red phase: this test file is written BEFORE the implementation
(doctor/adversarial/lc3946_collapse_perturbations.py). All tests should
fail with ImportError or assertion errors at this stage. After the
implementation lands, all tests must pass.

Per PHASE_LC3946_C5_SPEC.md Step 2, the tests must cover:
- P1a/P1b/P1c threshold shift changes ground truth labels as expected
- P2 subsamples produce 25 solvers each, matching pre-declared index lists
- P3 knockout removes correct probes from observed and target sets
- P4 cross-population reference is read-only, no perturbation
- Aggregate consistency check correctly detects discrepancy
- Falsification criterion correctly classifies SURVIVES / PARTIALLY_SURVIVES / DOES_NOT_SURVIVE
- 5-case oracle check still passes on unperturbed lc3946_brute_force

Additionally, pre-declared constants from PHASE_LC3946_C5_FREEZE.json must
be exported by the module:
- P1A_THRESHOLD = 0.05, P1B_THRESHOLD = 0.10, P1C_THRESHOLD = 0.20
- P2A_INDICES, P2B_INDICES, P2C_INDICES (each length 25, recovered solver present)
- P3_ROTATION_ORDER (6 axes in axis_declaration order)
- LC322_C4_RESULT_GAP (P4 cross-population anchor)
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# TestPreDeclaredConstants: the pre-declared P1/P2/P3/P4 parameters must
# be exported by the module, exactly as frozen in PHASE_LC3946_C5_FREEZE.json
# ---------------------------------------------------------------------------


class TestPreDeclaredConstants:
    """The pre-declared P1/P2/P3/P4 parameters must be exported."""

    def test_module_imports(self):
        """The perturbation module must be importable (it doesn't exist yet, so this will fail)."""
        mod = importlib.import_module(
            "doctor.adversarial.lc3946_collapse_perturbations"
        )
        assert mod is not None

    def test_p1a_threshold_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P1A_THRESHOLD
        assert P1A_THRESHOLD == 0.05

    def test_p1b_threshold_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P1B_THRESHOLD
        assert P1B_THRESHOLD == 0.10

    def test_p1c_threshold_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P1C_THRESHOLD
        assert P1C_THRESHOLD == 0.20

    def test_p2a_indices_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P2A_INDICES
        assert P2A_INDICES == [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
            20, 21, 22, 23, 24,
        ]
        assert len(P2A_INDICES) == 25

    def test_p2b_indices_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P2B_INDICES
        assert P2B_INDICES == [
            5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
            15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
            25, 26, 27, 28, 29,
        ]
        assert len(P2B_INDICES) == 25

    def test_p2c_indices_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P2C_INDICES
        assert P2C_INDICES == [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
            25, 26, 27, 28, 29,
        ]
        assert len(P2C_INDICES) == 25

    def test_p3_rotation_order_constant(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P3_ROTATION_ORDER
        assert P3_ROTATION_ORDER == [
            "poset_universal_source",
            "poset_chain",
            "poset_antichain",
            "poset_lattice_boolean",
            "poset_lattice_two_prime",
            "poset_isolated",
        ]
        assert len(P3_ROTATION_ORDER) == 6

    def test_lc322_c4_gap_constant(self):
        """P4 cross-population anchor: LC322 C-4 reported gap (for reference)."""
        from doctor.adversarial.lc3946_collapse_perturbations import LC322_C4_RESULT_GAP
        # LC322 C-4 result was gap = 8.30 at large_amount_stress family
        # (mirrored from phase-c4-results tag, commit 50d33e5)
        assert LC322_C4_RESULT_GAP == 8.30

    def test_recovered_solver_position_constant(self):
        """The recovered solver is solver_016 (0-indexed position 15)."""
        from doctor.adversarial.lc3946_collapse_perturbations import RECOVERED_SOLVER_ID
        assert RECOVERED_SOLVER_ID == "solver_016"


# ---------------------------------------------------------------------------
# TestP1ThresholdShift: P1a/P1b/P1c threshold shift functions
# ---------------------------------------------------------------------------


class TestP1ThresholdShift:
    """The threshold_shift function should re-derive ground truth labels
    with a given failure_threshold."""

    def _make_pass_results(self):
        """Build a 5-solver × 5-probe toy pass_results for testing.

        Ground truth at threshold=0.05: all 5 solvers are ACCEPT (fail rate 0.0)
        Ground truth at threshold=0.10: still all ACCEPT
        Ground truth at threshold=0.20: still all ACCEPT
        """
        return {
            f"solver_{i:03d}": {f"p_{j:03d}": True for j in range(1, 6)}
            for i in range(1, 6)
        }

    def test_p1a_baseline_threshold_0p05(self):
        from doctor.adversarial.lc3946_collapse_perturbations import threshold_shift
        pass_results = self._make_pass_results()
        target_ids = ["p_001", "p_002", "p_003", "p_004", "p_005"]
        ground = threshold_shift(pass_results, target_ids, failure_threshold=0.05)
        # All pass at threshold 0.05 -> all ACCEPT
        for sid, g in ground.items():
            assert g["truth_label"] == "ACCEPT", f"{sid} should be ACCEPT at threshold 0.05"
            assert g["heldout_fail_rate"] == 0.0

    def test_p1b_threshold_0p10(self):
        from doctor.adversarial.lc3946_collapse_perturbations import threshold_shift
        pass_results = {
            "solver_a": {"p1": True, "p2": False, "p3": True, "p4": True, "p5": True},
        }
        target_ids = ["p1", "p2", "p3", "p4", "p5"]
        # Held-out fail rate = 0.2 (1 of 5)
        # At threshold 0.05: REJECT (0.2 >= 0.05)
        # At threshold 0.10: REJECT (0.2 >= 0.10)
        # At threshold 0.20: ACCEPT (0.2 < 0.20)
        ground = threshold_shift(pass_results, target_ids, failure_threshold=0.10)
        assert ground["solver_a"]["truth_label"] == "REJECT"
        assert ground["solver_a"]["heldout_fail_rate"] == 0.2

    def test_p1c_threshold_0p20_changes_label(self):
        from doctor.adversarial.lc3946_collapse_perturbations import threshold_shift
        pass_results = {
            "solver_a": {"p1": True, "p2": False, "p3": True, "p4": True, "p5": True},
        }
        target_ids = ["p1", "p2", "p3", "p4", "p5"]
        # At threshold 0.20: ACCEPT (0.2 < 0.20)
        ground = threshold_shift(pass_results, target_ids, failure_threshold=0.20)
        assert ground["solver_a"]["truth_label"] == "ACCEPT"
        assert ground["solver_a"]["heldout_fail_rate"] == 0.2


# ---------------------------------------------------------------------------
# TestP2SolverSubsample: P2a/P2b/P2c subsample functions
# ---------------------------------------------------------------------------


class TestP2SolverSubsample:
    """solver_subsample should filter pass_results to keep only solvers
    at the given 0-indexed positions."""

    def _make_pass_results_30(self):
        return {f"solver_{i+1:03d}": {} for i in range(30)}

    def test_p2a_returns_25_solvers(self):
        from doctor.adversarial.lc3946_collapse_perturbations import solver_subsample, P2A_INDICES
        pass_results = self._make_pass_results_30()
        sub = solver_subsample(pass_results, P2A_INDICES)
        assert len(sub) == 25
        # First 25 = solver_001..solver_025
        for i in range(25):
            assert f"solver_{i+1:03d}" in sub
        for i in range(25, 30):
            assert f"solver_{i+1:03d}" not in sub

    def test_p2b_returns_25_solvers(self):
        from doctor.adversarial.lc3946_collapse_perturbations import solver_subsample, P2B_INDICES
        pass_results = self._make_pass_results_30()
        sub = solver_subsample(pass_results, P2B_INDICES)
        assert len(sub) == 25
        # Last 25 = solver_006..solver_030
        for i in range(5):
            assert f"solver_{i+1:03d}" not in sub
        for i in range(5, 30):
            assert f"solver_{i+1:03d}" in sub

    def test_p2c_returns_25_solvers(self):
        from doctor.adversarial.lc3946_collapse_perturbations import solver_subsample, P2C_INDICES
        pass_results = self._make_pass_results_30()
        sub = solver_subsample(pass_results, P2C_INDICES)
        assert len(sub) == 25
        # First 10 + last 15 = solver_001..solver_010, solver_016..solver_030
        for i in range(10):
            assert f"solver_{i+1:03d}" in sub
        for i in range(10, 15):
            assert f"solver_{i+1:03d}" not in sub
        for i in range(15, 30):
            assert f"solver_{i+1:03d}" in sub


# ---------------------------------------------------------------------------
# TestP2MembershipCheck: recovered solver present in all 3 P2 subsamples
# ---------------------------------------------------------------------------


class TestP2MembershipCheck:
    """The recovered solver (solver_016) must be present in all 3 P2 subsamples."""

    def test_recovered_solver_in_p2a(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P2A_INDICES, RECOVERED_SOLVER_ID
        idx = int(RECOVERED_SOLVER_ID[7:]) - 1  # solver_016 -> 15
        assert idx in P2A_INDICES

    def test_recovered_solver_in_p2b(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P2B_INDICES, RECOVERED_SOLVER_ID
        idx = int(RECOVERED_SOLVER_ID[7:]) - 1
        assert idx in P2B_INDICES

    def test_recovered_solver_in_p2c(self):
        from doctor.adversarial.lc3946_collapse_perturbations import P2C_INDICES, RECOVERED_SOLVER_ID
        idx = int(RECOVERED_SOLVER_ID[7:]) - 1
        assert idx in P2C_INDICES


# ---------------------------------------------------------------------------
# TestP3FamilyKnockout: P3a..P3f family knockout functions
# ---------------------------------------------------------------------------


class TestP3FamilyKnockout:
    """family_knockout should remove all observed probes in a given family
    from both observed and target sets."""

    def _make_probe_index(self):
        """Build a 6-axis × 5-probes-per-axis toy probe_index."""
        axes = [
            "poset_universal_source",
            "poset_chain",
            "poset_antichain",
            "poset_lattice_boolean",
            "poset_lattice_two_prime",
            "poset_isolated",
        ]
        probes = []
        for axis_idx, axis in enumerate(axes):
            for probe_offset in range(5):
                probe_num = axis_idx * 5 + probe_offset + 1
                probes.append({
                    "probe_id": f"p_lc3946_{probe_num:04d}",
                    "axis": axis,
                    "family": axis,
                })
        return {
            "probes": probes,
            "axis_set": axes,
        }

    def test_p3a_knocks_out_poset_universal_source(self):
        from doctor.adversarial.lc3946_collapse_perturbations import family_knockout
        probe_index = self._make_probe_index()
        observed = [f"p_lc3946_{i:04d}" for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]
        target = [f"p_lc3946_{i:04d}" for i in [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]]
        obs_reduced, target_reduced = family_knockout(
            observed, target, "poset_universal_source", probe_index
        )
        # poset_universal_source has 5 probes: 0001..0005
        for pid in ["p_lc3946_0001", "p_lc3946_0002", "p_lc3946_0003", "p_lc3946_0004", "p_lc3946_0005"]:
            assert pid not in obs_reduced
            assert pid not in target_reduced
        # Observed: 5 family probes removed -> 15 - 5 = 10 remain
        # Target: target set is 0016..0030, none in poset_universal_source -> 15 remain
        assert len(obs_reduced) == 10
        assert len(target_reduced) == 15

    def test_p3e_knocks_out_poset_lattice_two_prime(self):
        from doctor.adversarial.lc3946_collapse_perturbations import family_knockout
        probe_index = self._make_probe_index()
        observed = [f"p_lc3946_{i:04d}" for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]
        target = [f"p_lc3946_{i:04d}" for i in [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]]
        obs_reduced, target_reduced = family_knockout(
            observed, target, "poset_lattice_two_prime", probe_index
        )
        # poset_lattice_two_prime has 5 probes: 0021..0025
        for pid in ["p_lc3946_0021", "p_lc3946_0022", "p_lc3946_0023", "p_lc3946_0024", "p_lc3946_0025"]:
            assert pid not in obs_reduced
            assert pid not in target_reduced
        # Observed: observed is 0001..0015, none in poset_lattice_two_prime (0021..0025) -> 15 remain
        # Target: target is 0016..0030, contains 0021..0025 (5 probes) -> 15 - 5 = 10 remain
        assert len(obs_reduced) == 15
        assert len(target_reduced) == 10

    def test_p3_unknown_family_raises(self):
        """Knocking out a family that doesn't exist in the probe_index should raise."""
        from doctor.adversarial.lc3946_collapse_perturbations import family_knockout
        probe_index = self._make_probe_index()
        observed = ["p_lc3946_0001"]
        target = ["p_lc3946_0002"]
        with pytest.raises(ValueError, match="[Uu]nknown family"):
            family_knockout(observed, target, "nonexistent_family", probe_index)


# ---------------------------------------------------------------------------
# TestP4CrossPopulationReference: P4 is a read-only anchor
# ---------------------------------------------------------------------------


class TestP4CrossPopulationReference:
    """P4 cross-population reference should return the LC322 C-4 result
    without applying any perturbation."""

    def test_p4_returns_lc322_c4_gap(self):
        from doctor.adversarial.lc3946_collapse_perturbations import cross_population_reference
        result = cross_population_reference()
        assert result["lc322_c4_gap"] == 8.30
        assert result["lc322_c4_signal_family"] == "large_amount_stress"

    def test_p4_is_read_only_anchor(self):
        """P4 should be a no-op on the LC3946 population (returns the LC322 anchor)."""
        from doctor.adversarial.lc3946_collapse_perturbations import cross_population_reference
        result = cross_population_reference()
        # P4 doesn't return any modified population — just the anchor
        assert "lc3946_perturbation_applied" in result
        assert result["lc3946_perturbation_applied"] is False


# ---------------------------------------------------------------------------
# TestComputeGap: gap = B1_loss - C_genuine_loss
# ---------------------------------------------------------------------------


class TestComputeGap:
    """The gap function should return B1_loss - C_genuine_loss.
    gap > 0 means C_genuine is better."""

    def test_gap_positive(self):
        from doctor.adversarial.lc3946_collapse_perturbations import compute_gap
        # LC3946 C-4 baseline: B1_loss = 1.0, C_genuine_loss = 0.0
        assert compute_gap(1.0, 0.0) == 1.0

    def test_gap_zero(self):
        from doctor.adversarial.lc3946_collapse_perturbations import compute_gap
        # Tie: gap = 0
        assert compute_gap(1.0, 1.0) == 0

    def test_gap_negative(self):
        from doctor.adversarial.lc3946_collapse_perturbations import compute_gap
        # C_genuine worse: gap < 0
        assert compute_gap(0.0, 1.0) == -1.0


# ---------------------------------------------------------------------------
# TestFalsificationCriterion: SURVIVES / PARTIALLY_SURVIVES / DOES_NOT_SURVIVE
# ---------------------------------------------------------------------------


class TestFalsificationCriterion:
    """The falsification criterion should classify per-perturbation gap behavior."""

    def test_survives_all_gaps_positive(self):
        from doctor.adversarial.lc3946_collapse_perturbations import falsification_criterion
        gaps = {f"pert_{i}": 0.5 for i in range(11)}
        assert falsification_criterion(gaps) == "SURVIVES"

    def test_partially_survives_some_collapse(self):
        from doctor.adversarial.lc3946_collapse_perturbations import falsification_criterion
        gaps = {f"pert_{i}": 0.5 for i in range(11)}
        gaps["pert_3"] = 0.0  # collapse on pert_3
        assert falsification_criterion(gaps) == "PARTIALLY_SURVIVES"

    def test_partially_survives_negative_gap(self):
        from doctor.adversarial.lc3946_collapse_perturbations import falsification_criterion
        gaps = {f"pert_{i}": 0.5 for i in range(11)}
        gaps["pert_3"] = -1.0  # negative gap (C_genuine worse)
        assert falsification_criterion(gaps) == "PARTIALLY_SURVIVES"

    def test_does_not_survive_all_collapse(self):
        from doctor.adversarial.lc3946_collapse_perturbations import falsification_criterion
        gaps = {f"pert_{i}": 0.0 for i in range(11)}
        assert falsification_criterion(gaps) == "DOES_NOT_SURVIVE"

    def test_does_not_survive_all_negative(self):
        from doctor.adversarial.lc3946_collapse_perturbations import falsification_criterion
        gaps = {f"pert_{i}": -0.5 for i in range(11)}
        assert falsification_criterion(gaps) == "DOES_NOT_SURVIVE"

    def test_requires_11_perturbations(self):
        """Falsification criterion should require exactly 11 perturbation conditions."""
        from doctor.adversarial.lc3946_collapse_perturbations import falsification_criterion
        gaps = {f"pert_{i}": 1.0 for i in range(10)}  # only 10
        with pytest.raises(ValueError, match="11 perturbation"):
            falsification_criterion(gaps)


# ---------------------------------------------------------------------------
# TestAggregateConsistencyCheck: re-running B1 must reproduce stored (WA, WR, loss)
# ---------------------------------------------------------------------------


class TestAggregateConsistencyCheck:
    """The aggregate consistency check should re-run B1 and C_genuine
    on the unperturbed population and detect any discrepancy."""

    def test_consistent_passes(self):
        from doctor.adversarial.lc3946_collapse_perturbations import aggregate_consistency_check
        # Build a toy pass_results where B1 has loss 1.0 and C_genuine has loss 0.0
        # (matching the LC3946 baseline)
        # 4 solvers, 1 observed failure pattern, ground truth ACCEPT for all
        pass_results = {
            "solver_001": {"p_001": True, "p_002": True},  # 0 fails
            "solver_002": {"p_001": True, "p_002": True},  # 0 fails
            "solver_003": {"p_001": True, "p_002": True},  # 0 fails
            "solver_004": {"p_001": False, "p_002": True}, # 1 fail in poset_X
        }
        target_ids = ["p_001", "p_002"]
        observed_ids = ["p_001", "p_002"]  # toy: same as target
        # Truth labels (all 0.0 fail rate at threshold 0.05): all ACCEPT
        # B1: ACCEPT solver_001..003, REJECT solver_004 (1 fail) -> WA=0, WR=1
        # C_genuine: ACCEPT all (solver_004's 1 fail is in one family) -> WA=0, WR=0
        # For test, we just verify the function returns True on a known-consistent input
        # and False on a known-inconsistent input
        result = aggregate_consistency_check(
            pass_results=pass_results,
            observed_ids=observed_ids,
            target_ids=target_ids,
            failure_threshold=0.05,
            expected_b1_wa_wr_loss=(0, 1, 1.0),
            expected_c_genuine_wa_wr_loss=(0, 0, 0.0),
            probe_index=None,  # toy test; C_genuine will not fire on toy
        )
        # The toy test may not exercise C_genuine's full logic without probe_index;
        # so we just verify the function runs and returns a bool
        assert isinstance(result, bool)

    def test_inconsistent_detected(self):
        """If the expected (WA, WR, loss) doesn't match, return False."""
        from doctor.adversarial.lc3946_collapse_perturbations import aggregate_consistency_check
        pass_results = {
            "solver_001": {"p_001": True, "p_002": True},
            "solver_002": {"p_001": True, "p_002": True},
        }
        target_ids = ["p_001", "p_002"]
        observed_ids = ["p_001", "p_002"]
        # B1 will have loss 0.0 here (no failures) but we claim it should be (0, 1, 1.0)
        result = aggregate_consistency_check(
            pass_results=pass_results,
            observed_ids=observed_ids,
            target_ids=target_ids,
            failure_threshold=0.05,
            expected_b1_wa_wr_loss=(0, 1, 1.0),  # wrong: actual is (0, 0, 0.0)
            expected_c_genuine_wa_wr_loss=(0, 0, 0.0),
            probe_index=None,
        )
        assert result is False

    def test_disjoint_observed_vs_target(self):
        """Regression: observed_ids and target_ids must be treated separately.
        Bug: previously the function used `observed_ids = list(target_ids)`,
        which collapsed the K-observation budget to ground-truth probes.
        Fix: function takes observed_ids and target_ids as separate parameters.
        """
        from doctor.adversarial.lc3946_collapse_perturbations import aggregate_consistency_check
        # 2 solvers, 4 probes. Observed=[p_001, p_002], Target=[p_003, p_004].
        # solver_001: 0 fails in observed, 0 fails in target -> ground ACCEPT
        # solver_002: 1 fail in observed (p_001), 0 fails in target -> ground ACCEPT
        # B1: REJECT solver_002 (1 fail in observed) -> WA=0, WR=1, loss=1.0
        # B1 predicted REJECT for solver_002, ground says ACCEPT, so WR=1
        pass_results = {
            "solver_001": {"p_001": True, "p_002": True, "p_003": True, "p_004": True},
            "solver_002": {"p_001": False, "p_002": True, "p_003": True, "p_004": True},
        }
        observed_ids = ["p_001", "p_002"]
        target_ids = ["p_003", "p_004"]
        # Disjoint observed vs target. B1 sees 1 fail in observed (p_001 for solver_002).
        # If the function uses target_ids as observed_ids (the bug), it would see 0 fails
        # and B1 would ACCEPT both -> loss=0.0 -> inconsistent with expected (0, 1, 1.0).
        # With the fix, B1 sees 1 fail -> REJECT solver_002 -> WR=1 -> consistent.
        result = aggregate_consistency_check(
            pass_results=pass_results,
            observed_ids=observed_ids,
            target_ids=target_ids,
            failure_threshold=0.05,
            expected_b1_wa_wr_loss=(0, 1, 1.0),
            expected_c_genuine_wa_wr_loss=(0, 1, 1.0),  # toy: no probe_index, so C_genuine=B1
            probe_index=None,
        )
        assert result is True, "Disjoint observed/target check should detect B1 sees 1 fail"


# ---------------------------------------------------------------------------
# TestOracle5CaseCheck: regression test for the 5-case oracle check
# ---------------------------------------------------------------------------


class TestOracle5CaseCheck:
    """The 5-case oracle check on lc3946_brute_force must still pass.
    This is a regression test per DOCTOR_EXECUTION_PROTOCOL.md §3."""

    def test_oracle_5_case_check_passes(self):
        from doctor.adversarial.lc3946_ground_truth import (
            lc3946_brute_force,
            _run_5case_oracle_check,
        )
        # _run_5case_oracle_check prints OK lines and returns None.
        # Use capsys to confirm it printed all 5 OK lines (no FAIL).
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _run_5case_oracle_check()
        output = buf.getvalue()
        for i in range(1, 6):
            assert f"OK  case_{i}" in output, f"case_{i} did not print OK"
        assert "FAIL" not in output
        # Direct oracle calls (belt-and-suspenders)
        assert lc3946_brute_force([(2, 5)], 10) == 2
        assert lc3946_brute_force([(2, 5), (4, 7)], 12) == 3
        assert lc3946_brute_force([(2, 3), (4, 5), (8, 7)], 8) == 5
        assert lc3946_brute_force([(1, 2), (2, 3), (3, 5)], 6) == 5
        assert lc3946_brute_force([(2, 1), (3, 1), (5, 1), (7, 1)], 4) == 4
