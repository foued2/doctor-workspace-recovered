"""LC45 bimaristan layer tests.

The Week 4 deliverable: tests for the LC45 oracle evaluator, the LC45
symbol registry, and the cross-problem vocabulary. All tests stay
within-problem (no cross-problem comparison logic; no ComparabilityContext).

Coverage:
  - Oracle evaluator returns correct ground truth on all 30 probes
  - Each of the 9 buggy solvers triggers at least 2 registry symbols
  - The BFS survivor triggers zero false-positive symbols
  - Cross-problem symbols flag correctly
  - Registry structural integrity
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

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
from doctor.adversarial.lc45_oracle_evaluator import (
    LC45EvaluationResult,
    LC45OracleEvaluator,
    LC45Probe,
    LC45ProbeResult,
    LC45TraceFeatures,
    LC45TraceSummary,
)
from doctor.adversarial.lc45_symbol_registry import (
    LC45_MANIFOLDS,
    LC45_SYMBOL_REGISTRY,
    SymbolCategory,
    TRANSFER_DIRECT,
    TRANSFER_EXCLUDED,
    TRANSFER_RE_DERIVE,
)
from doctor.adversarial.problem_class_config import get_lc45_bimaristan_components


# ---------------------------------------------------------------------------
# Fixtures: 30 LC45 probes loaded from data/
# ---------------------------------------------------------------------------


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_INDEX_PATH = REPO_ROOT / "data" / "midweather_fingerprint_lc45_probe_index.json"


def _load_probes() -> list[LC45Probe]:
    raw = json.loads(PROBE_INDEX_PATH.read_text(encoding="utf-8"))
    return [
        LC45Probe(
            probe_id=str(p["probe_id"]),
            nums=tuple(int(x) for x in p["nums"]),
            expected_output=int(p["expected_jumps"]),
            manifold_id=str(p["axis"]),
        )
        for p in raw["probes"]
    ]


@pytest.fixture(scope="module")
def probes() -> list[LC45Probe]:
    return _load_probes()


@pytest.fixture(scope="module")
def oracle_evaluator() -> LC45OracleEvaluator:
    return LC45OracleEvaluator()


# ---------------------------------------------------------------------------
# 1. Registry structural integrity
# ---------------------------------------------------------------------------


def test_registry_has_required_minimum_entries():
    """The registry must have >= 20 entries (per spec)."""
    assert len(LC45_SYMBOL_REGISTRY.entries) >= 20


def test_registry_has_5_algorithm_family_entries():
    af = [e for e in LC45_SYMBOL_REGISTRY.entries
          if e.category is SymbolCategory.ALGORITHM_FAMILY]
    assert len(af) == 5
    names = {e.name for e in af}
    assert names == {
        "uses_bfs_with_visited",
        "uses_naive_max_index",
        "uses_max_value_landing",
        "uses_uniform_formula",
        "uses_bounded_lookahead",
    }


def test_registry_has_3_tie_breaker_entries():
    tb = [e for e in LC45_SYMBOL_REGISTRY.entries
          if e.category is SymbolCategory.TIE_BREAKER]
    assert len(tb) == 3
    names = {e.name for e in tb}
    assert names == {
        "picks_max_index_on_tie",
        "picks_max_value_on_tie",
        "picks_closest_on_tie",
    }


def test_registry_has_3_return_semantics_entries():
    rs = [e for e in LC45_SYMBOL_REGISTRY.entries
          if e.category is SymbolCategory.RETURN_SEMANTICS]
    assert len(rs) == 3
    names = {e.name for e in rs}
    assert names == {
        "output_equals_reachable_count",
        "output_off_by_one_in_bfs",
        "returns_minus_one_on_zero",
    }


def test_registry_has_5_cross_problem_entries():
    cp = [e for e in LC45_SYMBOL_REGISTRY.entries
          if e.category is SymbolCategory.CROSS_PROBLEM]
    assert len(cp) == 5
    assert {e.transfer for e in cp} == {TRANSFER_DIRECT, TRANSFER_RE_DERIVE, TRANSFER_EXCLUDED}


def test_registry_has_12_manifold_predicates():
    mp = [e for e in LC45_SYMBOL_REGISTRY.entries
          if e.category is SymbolCategory.ORACLE_DEPENDENT
          and e.manifold_id is not None]
    assert len(mp) == 12
    assert len({e.manifold_id for e in mp}) == 6
    assert {e.manifold_id for e in mp} == set(LC45_MANIFOLDS)


def test_registry_oracle_dependent_count_meets_spec():
    """Oracle-dependent entries must number >= 20 per spec.

    5 basic + 5 derived + 12 manifold = 22.
    """
    od = [e for e in LC45_SYMBOL_REGISTRY.entries
          if e.category is SymbolCategory.ORACLE_DEPENDENT]
    assert len(od) >= 20


def test_registry_uses_memoization_is_excluded():
    """The excluded symbol must be marked EXCLUDED and return False."""
    memo = LC45_SYMBOL_REGISTRY.get("uses_memoization")
    assert memo is not None
    assert memo.transfer == TRANSFER_EXCLUDED
    assert memo.compute({"eval_result": LC45EvaluationResult(
        candidate_id="x", probe_results=(), summary=LC45TraceSummary(
            visited_mean=0.0, max_depth_mean=0.0, edges_mean=0.0,
            max_width_mean=0.0, landing_distribution={},
            output_equals_reachable_count_count=0,
            output_off_by_one_count=0, total_probes=0, correct_count=0))}) is False


def test_registry_state_space_bounded_is_re_derived():
    """The re-derived symbol must be marked RE_DERIVE."""
    ssb = LC45_SYMBOL_REGISTRY.get("state_space_bounded_by_array_length")
    assert ssb is not None
    assert ssb.transfer == TRANSFER_RE_DERIVE


# ---------------------------------------------------------------------------
# 2. Oracle evaluator: ground truth on all 30 probes
# ---------------------------------------------------------------------------


def test_oracle_evaluator_returns_correct_truth_on_all_30_probes(
    oracle_evaluator, probes
):
    """The BFS oracle must return expected_output for every probe."""
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    assert result.summary.correct_count == 30
    assert result.summary.total_probes == 30
    for r in result.probe_results:
        assert r.correct, f"probe {r.probe_id} (nums={r.nums}) was wrong: {r.candidate_output} != {r.oracle_output}"
        assert r.candidate_output == r.oracle_output


def test_oracle_evaluator_per_probe_trace_features_are_populated(
    oracle_evaluator, probes
):
    """Every probe result must have a populated LC45TraceFeatures."""
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    for r in result.probe_results:
        assert isinstance(r.trace_features, LC45TraceFeatures)
        assert r.trace_features.visited >= 1
        assert r.trace_features.max_depth >= 0
        assert r.trace_features.edges >= 0
        assert r.trace_features.max_width >= 1
        assert r.trace_features.landing == r.candidate_output
        assert r.trace_features.output_off_by_one is False  # BFS is correct


def test_oracle_evaluator_summary_aggregates(
    oracle_evaluator, probes
):
    """The summary must aggregate the 30 per-probe results."""
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    s = result.summary
    assert s.total_probes == 30
    assert s.correct_count == 30
    assert s.visited_mean > 0
    assert s.max_depth_mean > 0
    assert s.edges_mean > 0
    assert s.max_width_mean >= 1
    # All landing values are the correct oracle outputs, so landing_distribution
    # has 30 entries distributed across oracle output values.
    assert sum(s.landing_distribution.values()) == 30


def test_oracle_evaluator_catches_exceptions():
    """The evaluator must catch exceptions and record them in the result."""
    def broken_candidate(nums):
        raise ValueError("intentional test failure")
    evalr = LC45OracleEvaluator()
    probes_short = [LC45Probe("p1", (2, 3, 1, 1, 4), 2, "naive_max_jump_suboptimal")]
    result = evalr.evaluate(broken_candidate, probes_short, "broken")
    r = result.probe_results[0]
    assert r.candidate_output is None
    assert r.correct is False
    assert r.exception is not None
    assert "ValueError" in r.exception


def test_oracle_evaluator_empty_probe_set():
    evalr = LC45OracleEvaluator()
    result = evalr.evaluate(lc45_bfs_depth_cutoff, [], "empty")
    assert result.summary.total_probes == 0
    assert result.probe_results == ()


# ---------------------------------------------------------------------------
# 3. Per-solver symbol triggering: 9 buggy solvers >= 2 symbols each
# ---------------------------------------------------------------------------


_BUGGY_SOLVERS = [
    ("lc45_farthest_landing_path", lc45_farthest_landing_path),
    ("lc45_naive_greedy", lc45_naive_greedy),
    ("lc45_max_landing_value", lc45_max_landing_value),
    ("lc45_zero_dead_end_panic", lc45_zero_dead_end_panic),
    ("lc45_reachable_boolean_confusion", lc45_reachable_boolean_confusion),
    ("lc45_three_step_window_dp", lc45_three_step_window_dp),
    ("lc45_frontier_off_by_one", lc45_frontier_off_by_one),
    ("lc45_uniform_formula_generalizer", lc45_uniform_formula_generalizer),
    ("lc45_first_window_max_then_greedy", lc45_first_window_max_then_greedy),
]


def _evaluate_all_symbols(
    eval_result: LC45EvaluationResult,
) -> dict[str, bool]:
    """Evaluate every entry in the registry and return a name->bool map."""
    return {
        e.name: bool(e.compute({"eval_result": eval_result}))
        for e in LC45_SYMBOL_REGISTRY.entries
    }


@pytest.mark.parametrize("solver_id,solver_fn", _BUGGY_SOLVERS, ids=[s for s, _ in _BUGGY_SOLVERS])
def test_buggy_solver_triggers_at_least_2_symbols(
    solver_id, solver_fn, oracle_evaluator, probes
):
    """Each of the 9 buggy solvers must trigger at least 2 registry symbols."""
    result = oracle_evaluator.evaluate(solver_fn, probes, solver_id)
    flags = _evaluate_all_symbols(result)
    triggered = [name for name, on in flags.items() if on]
    assert len(triggered) >= 2, (
        f"{solver_id} triggered only {len(triggered)} symbols: {triggered}"
    )


# ---------------------------------------------------------------------------
# 4. BFS survivor: zero false-positive symbols
# ---------------------------------------------------------------------------


_FALSE_POSITIVE_SYMBOLS = [
    "uses_naive_max_index",
    "uses_max_value_landing",
    "uses_uniform_formula",
    "uses_bounded_lookahead",
    "picks_max_index_on_tie",
    "picks_max_value_on_tie",
    "output_equals_reachable_count",
    "output_off_by_one_in_bfs",
    "returns_minus_one_on_zero",
    "panics_on_dead_end",
]


def test_bfs_survivor_triggers_zero_false_positive_symbols(
    oracle_evaluator, probes
):
    """The BFS survivor must NOT trigger any of the 10 false-positive symbols.

    False-positive = a symbol that, if True, would mean the candidate
    belongs to a buggy family (greedy, uniform, bounded, off-by-one,
    panic-on-dead-end, etc.). The BFS survivor is the canonical
    ground-truth algorithm and must trigger none of these.
    """
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    flags = _evaluate_all_symbols(result)
    triggered = [s for s in _FALSE_POSITIVE_SYMBOLS if flags.get(s, False)]
    assert triggered == [], (
        f"BFS survivor triggered false-positive symbols: {triggered}"
    )


def test_bfs_survivor_triggers_expected_symbols(
    oracle_evaluator, probes
):
    """The BFS survivor must trigger the 4 expected symbols."""
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    flags = _evaluate_all_symbols(result)
    assert flags["uses_bfs_with_visited"] is True
    assert flags["picks_closest_on_tie"] is True
    assert flags["uses_exhaustive_search"] is True
    assert flags["state_space_bounded_by_array_length"] is True


# ---------------------------------------------------------------------------
# 5. Cross-problem symbols
# ---------------------------------------------------------------------------


def test_cross_problem_uses_exhaustive_search_true_for_bfs(
    oracle_evaluator, probes
):
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    flags = _evaluate_all_symbols(result)
    assert flags["uses_exhaustive_search"] is True


def test_cross_problem_uses_greedy_tie_breaker_true_for_greedy_solvers(
    oracle_evaluator, probes
):
    """At least one of the 3 max-step/max-value greedy candidates triggers
    the cross-problem `uses_greedy_tie_breaker` symbol.
    """
    greedy_solvers = [
        lc45_farthest_landing_path,
        lc45_naive_greedy,
        lc45_max_landing_value,
        lc45_first_window_max_then_greedy,
    ]
    found = False
    for solver in greedy_solvers:
        result = oracle_evaluator.evaluate(solver, probes, solver.__name__)
        flags = _evaluate_all_symbols(result)
        if flags["uses_greedy_tie_breaker"]:
            found = True
            break
    assert found, "No greedy solver triggered uses_greedy_tie_breaker"


def test_cross_problem_panics_on_dead_end_true_for_panic_solver(
    oracle_evaluator, probes
):
    result = oracle_evaluator.evaluate(
        lc45_zero_dead_end_panic, probes, "lc45_zero_dead_end_panic"
    )
    flags = _evaluate_all_symbols(result)
    assert flags["panics_on_dead_end"] is True


def test_cross_problem_uses_memoization_false_for_all_solvers(
    oracle_evaluator, probes
):
    """The EXCLUDED symbol must always be False (LC45 has no sub-problem memoization)."""
    all_solvers = [s for _, s in _BUGGY_SOLVERS] + [lc45_bfs_depth_cutoff]
    for solver in all_solvers:
        result = oracle_evaluator.evaluate(solver, probes, solver.__name__)
        flags = _evaluate_all_symbols(result)
        assert flags["uses_memoization"] is False, (
            f"{solver.__name__} triggered the EXCLUDED uses_memoization symbol"
        )


def test_cross_problem_state_space_bounded_true_for_bfs(
    oracle_evaluator, probes
):
    """The re-derived symbol is True for the BFS (state space = n positions)."""
    result = oracle_evaluator.evaluate(lc45_bfs_depth_cutoff, probes, "bfs_survivor")
    flags = _evaluate_all_symbols(result)
    assert flags["state_space_bounded_by_array_length"] is True


# ---------------------------------------------------------------------------
# 6. Adapter slot wiring
# ---------------------------------------------------------------------------


def test_problem_class_config_exposes_lc45_bimaristan_components():
    """The wiring function returns the new oracle evaluator and symbol registry."""
    components = get_lc45_bimaristan_components()
    assert isinstance(components["evaluator"], LC45OracleEvaluator)
    assert components["symbol_registry"] is LC45_SYMBOL_REGISTRY
    assert tuple(components["manifolds"]) == LC45_MANIFOLDS


def test_lc45_raw_tensor_encoder_is_concrete():
    """The LC45 raw tensor encoder must be a concrete (non-stub) implementation.

    A concrete encoder returns non-trivial 6-dim features per solver,
    derived from symbol values (not just padding with zeros).
    """
    from doctor.adversarial.problem_class_config import lc45_raw_tensor_encoder

    obs_rows = [
        {
            "solver_id": "solver_001",
            "pass_fail": True,
            "nums": [2, 3, 1, 1, 4],
            "expected_output": 2,
            "candidate_output": 2,
        },
        {
            "solver_id": "solver_001",
            "pass_fail": True,
            "nums": [10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            "expected_output": 1,
            "candidate_output": 1,
        },
        {
            "solver_id": "solver_002",
            "pass_fail": False,
            "nums": [2, 3, 1, 1, 4],
            "expected_output": 2,
            "candidate_output": 3,
        },
        {
            "solver_id": "solver_002",
            "pass_fail": True,
            "nums": [0, 1, 1],
            "expected_output": -1,
            "candidate_output": -1,
        },
    ]
    out = lc45_raw_tensor_encoder(obs_rows)
    assert set(out.keys()) == {"solver_001", "solver_002"}
    for sid in out:
        assert len(out[sid]) == 6
        # Concrete (non-stub): pass_fail_rate is 1.0 for solver_001, 0.5 for solver_002
        if sid == "solver_001":
            assert out[sid][0] == 1.0
        elif sid == "solver_002":
            assert out[sid][0] == 0.5


# ---------------------------------------------------------------------------
# 7. Symbol registry behavior on individual probe types
# ---------------------------------------------------------------------------


def test_output_off_by_one_in_bfs_triggers_for_off_by_one_solver(
    oracle_evaluator, probes
):
    """lc45_frontier_off_by_one returns oracle + 1 on every reachable probe,
    so `output_off_by_one_in_bfs` must be True on at least one probe.
    """
    result = oracle_evaluator.evaluate(
        lc45_frontier_off_by_one, probes, "lc45_frontier_off_by_one"
    )
    flags = _evaluate_all_symbols(result)
    assert flags["output_off_by_one_in_bfs"] is True


def test_returns_minus_one_on_zero_triggers_for_panic_solver(
    oracle_evaluator, probes
):
    result = oracle_evaluator.evaluate(
        lc45_zero_dead_end_panic, probes, "lc45_zero_dead_end_panic"
    )
    flags = _evaluate_all_symbols(result)
    assert flags["returns_minus_one_on_zero"] is True


def test_uses_uniform_formula_triggers_for_uniform_formula_solver(
    oracle_evaluator, probes
):
    result = oracle_evaluator.evaluate(
        lc45_uniform_formula_generalizer, probes, "lc45_uniform_formula_generalizer"
    )
    flags = _evaluate_all_symbols(result)
    assert flags["uses_uniform_formula"] is True


def test_uses_bounded_lookahead_triggers_for_windowed_dp(
    oracle_evaluator, probes
):
    result = oracle_evaluator.evaluate(
        lc45_three_step_window_dp, probes, "lc45_three_step_window_dp"
    )
    flags = _evaluate_all_symbols(result)
    assert flags["uses_bounded_lookahead"] is True
