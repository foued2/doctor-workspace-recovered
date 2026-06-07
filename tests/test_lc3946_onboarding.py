"""Tests for the LC3946 (Maximum Number of Items From Sale I) onboarding.

Mirrors the structure of tests/test_lc322_real_benchmark.py and the
LC322 bimaristan tests. Each test isolates one piece of the LC3946
onboarding to keep failures attributable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from doctor.adversarial.lc3946_ground_truth import (
    LC3946DomainError,
    lc3946_brute_force,
)
from doctor.adversarial.lc3946_candidates import (
    LC3946_CANDIDATES,
    _free_count,
    _greedy_fill,
    _unpack,
)
from doctor.adversarial.problem_class_config import get_problem_class_config


# ---------------------------------------------------------------------------
# 1. The 5-case oracle test (mirrors what is in the oracle file, but isolated)
# ---------------------------------------------------------------------------


class TestLC3946Oracle:
    """The LC3946 brute-force oracle. The 5-case manual check is the
    load-bearing test of the oracle (per DOCTOR_EXECUTION_PROTOCOL §3).
    """

    def test_case_1_single_item(self):
        # items=[(2,5)], budget=10. p={0}: cost=5, free=[0], bought=1,
        # remaining=5, cheapest=5, extra=1, total=1+0+1=2.
        assert lc3946_brute_force([(2, 5)], 10) == 2

    def test_case_2_two_items_2div4(self):
        # items=[(2,5),(4,7)], budget=12. p={0,1}: cost=12, free=[0,1],
        # bought=2, remaining=0, total=3. p={0} alone: 1+1+1=3. Max=3.
        assert lc3946_brute_force([(2, 5), (4, 7)], 12) == 3

    def test_case_3_three_items_chain(self):
        # items=[(2,3),(4,5),(8,7)], budget=8. p={0,1}: cost=8, free=[0,1,2],
        # bought=2, remaining=0, total=5.
        assert lc3946_brute_force([(2, 3), (4, 5), (8, 7)], 8) == 5

    def test_case_4_factor1_universal(self):
        # items=[(1,2),(2,3),(3,5)], budget=6. p={0}: cost=2, free=[0,1,1],
        # bought=1, remaining=4, cheapest=2, extra=2, total=5.
        assert lc3946_brute_force([(1, 2), (2, 3), (3, 5)], 6) == 5

    def test_case_5_antichain_no_free(self):
        # items=[(2,1),(3,1),(5,1),(7,1)], budget=4. All primes, free=0.
        # p={0,1,2,3}: cost=4, bought=4. p={0,1,2}: cost=3, extra=1,
        # total=4. Max=4.
        assert lc3946_brute_force([(2, 1), (3, 1), (5, 1), (7, 1)], 4) == 4

    def test_zero_budget(self):
        assert lc3946_brute_force([(2, 5)], 0) == 0

    def test_empty_items(self):
        assert lc3946_brute_force([], 100) == 0

    def test_unaffordable(self):
        # Cheapest item is 5, budget is 4: cannot buy anything.
        assert lc3946_brute_force([(2, 5)], 4) == 0

    def test_negative_budget_raises(self):
        with pytest.raises(LC3946DomainError):
            lc3946_brute_force([(2, 5)], -1)

    def test_invalid_factor_raises(self):
        with pytest.raises(LC3946DomainError):
            lc3946_brute_force([(0, 5)], 10)

    def test_invalid_price_raises(self):
        with pytest.raises(LC3946DomainError):
            lc3946_brute_force([(2, 0)], 10)


# ---------------------------------------------------------------------------
# 2. Helper functions used by the solver pool
# ---------------------------------------------------------------------------


class TestLC3946Helpers:
    def test_unpack_flat_input(self):
        items, budget = _unpack([1, 2, 2, 3, 0, 6])
        assert items == [(1, 2), (2, 3)]
        assert budget == 6

    def test_unpack_single_item(self):
        items, budget = _unpack([2, 5, 0, 10])
        assert items == [(2, 5)]
        assert budget == 10

    def test_unpack_rejects_odd_length(self):
        with pytest.raises(ValueError):
            _unpack([1, 2, 2])

    def test_unpack_rejects_missing_sentinel(self):
        with pytest.raises(ValueError):
            _unpack([1, 2])  # no (0, budget) sentinel

    def test_free_count_chain(self):
        # Chain: 2 | 4 | 8. p = all three.
        items = [(2, 1), (4, 1), (8, 1)]
        free = _free_count(items, 0b111)
        # j=0: 2 has no i in p with factor_i | 2 (4 doesn't divide 2, 8 doesn't) -> 0
        # j=1: 4 has 2 | 4 -> 1
        # j=2: 8 has 2 | 8, 4 | 8 -> 2
        assert free == [0, 1, 2]

    def test_free_count_universal(self):
        # Factor 1 divides everything.
        items = [(1, 1), (5, 1), (10, 1)]
        free = _free_count(items, 0b111)
        # j=0: factor=1 has no divisor in p (only itself excluded) -> 0
        # j=1: factor=5 has 1 | 5 -> 1
        # j=2: factor=10 has 1 | 10 AND 5 | 10 -> 2
        assert free == [0, 1, 2]

    def test_free_count_antichain(self):
        # All primes, no divisibility.
        items = [(2, 1), (3, 1), (5, 1)]
        free = _free_count(items, 0b111)
        assert free == [0, 0, 0]

    def test_greedy_fill_empty_mask_returns_minus_one(self):
        assert _greedy_fill([(2, 5)], 0, 10) == -1

    def test_greedy_fill_over_budget_returns_minus_one(self):
        assert _greedy_fill([(2, 5), (4, 7)], 0b11, 5) == -1

    def test_greedy_fill_extra_copies(self):
        # p={0}, items=[(2,5)], budget=20. cost=5, free=0, bought=1,
        # remaining=15, cheapest=5, extra=3, total=4.
        assert _greedy_fill([(2, 5)], 0b01, 20) == 4


# ---------------------------------------------------------------------------
# 3. The 30-solver pool
# ---------------------------------------------------------------------------


class TestLC3946Candidates:
    def test_n_solvers_is_30(self):
        assert len(LC3946_CANDIDATES) == 30

    def test_solver_ids_consecutive(self):
        ids = [sid for sid, _ in LC3946_CANDIDATES]
        assert ids == [f"solver_{n:03d}" for n in range(1, 31)]

    def test_solvers_callable(self):
        for sid, fn in LC3946_CANDIDATES:
            assert callable(fn), f"{sid} is not callable"

    def test_solvers_handle_unpack(self):
        # Each solver should accept a flat input list.
        flat = [1, 2, 2, 3, 0, 6]
        for sid, fn in LC3946_CANDIDATES:
            result = fn(flat)
            assert isinstance(result, int), f"{sid} returned non-int: {result}"

    def test_dp_survivors_match_oracle_on_chain(self):
        # The 5 DP-survivor solvers should match the oracle on a hard case.
        items = [(2, 3), (4, 5), (8, 7)]
        budget = 8
        truth = lc3946_brute_force(items, budget)
        flat = [2, 3, 4, 5, 8, 7, 0, budget]
        for sid, fn in LC3946_CANDIDATES[:5]:
            assert fn(flat) == truth, f"{sid} failed on chain: {fn(flat)} != {truth}"

    def test_dp_survivors_match_oracle_on_universal(self):
        items = [(1, 2), (2, 3), (3, 5)]
        budget = 6
        truth = lc3946_brute_force(items, budget)
        flat = [1, 2, 2, 3, 3, 5, 0, budget]
        for sid, fn in LC3946_CANDIDATES[:5]:
            assert fn(flat) == truth, f"{sid} failed on universal: {fn(flat)} != {truth}"

    def test_at_least_one_solver_fails_on_each_probe(self):
        # The 30 probes should each cause at least one of the 25 non-survivor
        # solvers to fail. This is the empirical soundness check.
        with open(REPO_ROOT / "data" / "midweather_fingerprint_lc3946_probe_index.json") as f:
            pi = json.load(f)
        for p in pi["probes"]:
            truth = lc3946_brute_force(p["items"], p["budget"])
            flat = []
            for item in p["items"]:
                flat.append(int(item[0]))
                flat.append(int(item[1]))
            flat.append(0)
            flat.append(int(p["budget"]))
            any_fail = any(
                fn(flat) != truth for sid, fn in LC3946_CANDIDATES[5:]
            )
            assert any_fail, f"{p['probe_id']} (truth={truth}): no non-survivor failed"


# ---------------------------------------------------------------------------
# 4. Problem class config wiring
# ---------------------------------------------------------------------------


class TestLC3946ProblemClassConfig:
    def test_factory_returns_lc3946(self):
        cfg = get_problem_class_config("lc3946")
        assert cfg.problem_id == "lc3946"

    def test_axes_match_declaration(self):
        cfg = get_problem_class_config("lc3946")
        assert cfg.fingerprint_axes == [
            "poset_universal_source",
            "poset_chain",
            "poset_antichain",
            "poset_lattice_boolean",
            "poset_lattice_two_prime",
            "poset_isolated",
        ]

    def test_estimator_names_include_b1_and_c_structured(self):
        cfg = get_problem_class_config("lc3946")
        assert "B1_count" in cfg.estimator_names
        assert "C_structured_fingerprint" in cfg.estimator_names

    def test_estimator_policies_have_all_named_estimators(self):
        cfg = get_problem_class_config("lc3946")
        for name in cfg.estimator_names:
            assert name in cfg.estimator_policies, f"missing policy: {name}"

    def test_oracle_matches_brute_force(self):
        cfg = get_problem_class_config("lc3946")
        # Build a flat solver input via the adapter, then call the oracle.
        probe = {
            "items": [[2, 5], [4, 7]],
            "budget": 12,
        }
        flat = cfg.probe_to_solver_input(probe)
        # 2*2 + 2 = 6 elements: [f0,p0,f1,p1,0,budget]
        assert len(flat) == 6
        assert cfg.oracle(flat) == 3  # case_2 expected

    def test_probe_to_solver_input_flattens_correctly(self):
        cfg = get_problem_class_config("lc3946")
        probe = {"items": [[2, 3], [4, 5]], "budget": 8}
        flat = cfg.probe_to_solver_input(probe)
        assert flat == [2, 3, 4, 5, 0, 8]

    def test_solver_entry_point(self):
        cfg = get_problem_class_config("lc3946")
        assert cfg.solver_entry_point == "solve"

    def test_unknown_problem_class_raises(self):
        with pytest.raises(NotImplementedError):
            get_problem_class_config("lc9999")


# ---------------------------------------------------------------------------
# 5. The 6-feature raw tensor encoder
# ---------------------------------------------------------------------------


class TestLC3946RawTensorEncoder:
    def test_encoder_returns_6_dim_per_solver(self):
        from doctor.adversarial.problem_class_config import lc3946_raw_tensor_encoder
        rows = [
            {
                "solver_id": "solver_001",
                "pass_fail": True,
                "probe": {"items": [[2, 3], [4, 5]], "budget": 8},
                "fingerprint_context": {
                    "axis": "poset_chain",
                    "probe_family": "poset_chain",
                    "deformation_level": 0,
                    "paired_probe_id": "p_lc3946_0001",
                    "expected_invariant": "chain_2_4_8",
                },
            },
        ]
        out = lc3946_raw_tensor_encoder(rows)
        assert "solver_001" in out
        assert len(out["solver_001"]) == 6

    def test_encoder_empty_rows(self):
        from doctor.adversarial.problem_class_config import lc3946_raw_tensor_encoder
        assert lc3946_raw_tensor_encoder([]) == {}

    def test_factor_lattice_features_universal(self):
        from doctor.adversarial.problem_class_config import _lc3946_factor_lattice_features
        f = _lc3946_factor_lattice_features([1, 2, 4])
        assert f[0] == 1.0  # has_universal_source
        assert f[3] == 1.0  # boolean_lattice (1, 2, 4 are powers of 2)
        assert f[2] == 0.0  # not antichain

    def test_factor_lattice_features_antichain(self):
        from doctor.adversarial.problem_class_config import _lc3946_factor_lattice_features
        f = _lc3946_factor_lattice_features([2, 3, 5])
        assert f[0] == 0.0  # no universal
        assert f[2] == 1.0  # antichain (all primes)
        assert f[3] == 0.0  # not boolean (3, 5 aren't powers of 2)
        assert f[5] == 1.0  # isolated

    def test_factor_lattice_features_empty(self):
        from doctor.adversarial.problem_class_config import _lc3946_factor_lattice_features
        assert _lc3946_factor_lattice_features([]) == [0.0] * 6

    def test_factor_lattice_features_two_prime(self):
        from doctor.adversarial.problem_class_config import _lc3946_factor_lattice_features
        f = _lc3946_factor_lattice_features([2, 3, 6, 12])
        assert f[4] == 1.0  # all are products of 2 and 3
        assert f[0] == 0.0  # no factor=1


# ---------------------------------------------------------------------------
# 6. The probe index
# ---------------------------------------------------------------------------


class TestLC3946ProbeIndex:
    @pytest.fixture
    def probe_index(self):
        with open(REPO_ROOT / "data" / "midweather_fingerprint_lc3946_probe_index.json") as f:
            return json.load(f)

    def test_30_probes(self, probe_index):
        assert len(probe_index["probes"]) == 30

    def test_5_probes_per_axis(self, probe_index):
        axes = {}
        for p in probe_index["probes"]:
            axes.setdefault(p["axis"], 0)
            axes[p["axis"]] += 1
        assert axes == {
            "poset_universal_source": 5,
            "poset_chain": 5,
            "poset_antichain": 5,
            "poset_lattice_boolean": 5,
            "poset_lattice_two_prime": 5,
            "poset_isolated": 5,
        }

    def test_axis_set_matches_config(self, probe_index):
        cfg = get_problem_class_config("lc3946")
        assert set(probe_index["axis_set"]) == set(cfg.fingerprint_axes)

    def test_probe_ids_consecutive(self, probe_index):
        ids = [p["probe_id"] for p in probe_index["probes"]]
        assert ids == [f"p_lc3946_{n:04d}" for n in range(1, 31)]

    def test_every_probe_has_required_fields(self, probe_index):
        required = {"probe_id", "family", "axis", "items", "budget",
                    "paired_probe_id", "deformation_level", "expected_invariant"}
        for p in probe_index["probes"]:
            missing = required - set(p.keys())
            assert not missing, f"{p.get('probe_id', '?')} missing: {missing}"


# ---------------------------------------------------------------------------
# 7. End-to-end smoke test (mirrors the LC322 midweather fingerprint)
# ---------------------------------------------------------------------------


class TestLC3946MidweatherFingerprint:
    """Smoke test: the LC3946 midweather fingerprint result file exists and
    has the expected shape.
    """

    def test_result_file_exists(self):
        result_path = REPO_ROOT / "data" / "midweather_fingerprint_lc3946.json"
        assert result_path.exists(), f"missing: {result_path}"

    def test_result_has_decision(self):
        result_path = REPO_ROOT / "data" / "midweather_fingerprint_lc3946.json"
        with open(result_path) as f:
            result = json.load(f)
        assert "decision" in result
        assert "decision_reason" in result
        assert "estimator_table" in result
        assert "per_solver_ground_truth" in result
        assert "guard_statuses" in result

    def test_15_good_15_bad_split(self):
        result_path = REPO_ROOT / "data" / "midweather_fingerprint_lc3946.json"
        with open(result_path) as f:
            result = json.load(f)
        gs = result["ground_truth_summary"]
        assert gs["n_good_solvers"] == 15
        assert gs["n_bad_solvers"] == 15

    def test_b1_and_c_structured_tied(self):
        # On the LC3946 default config (C_structured_fingerprint bound to
        # _fail_count_policy), B1 and C should produce identical loss.
        # This is the LC3946 C-1 finding by construction.
        result_path = REPO_ROOT / "data" / "midweather_fingerprint_lc3946.json"
        with open(result_path) as f:
            result = json.load(f)
        table = {row["estimator"]: row for row in result["estimator_table"]}
        assert table["B1_count"]["decision_loss"] == table["C_structured_fingerprint"]["decision_loss"]
