# STATUS: MODULE UNIMPORTABLE — 3 cascade self-import failures
# (RelationConstraint, LC322OracleEvaluator, SymbolCategory)
# 34 LC322 oracle tests cannot be collected by pytest.
# These tests documented a completed negative result (paper closed).
# Reconstruction deferred — original implementations unrecoverable.
# See git log for reconstruction history.
from __future__ import annotations

import pytest
from dataclasses import dataclass

from doctor.adversarial.lc322_oracle import LC322OracleEvaluator, OracleCeilingError, evaluation_surface
from doctor.adversarial.lc322_symbol_registry import LC322_SYMBOL_REGISTRY
from doctor.adversarial.symbol_registry import SymbolCategory
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


# --- RelationConstraint stub (added to fix self-referential import on line 5) ---


@dataclass(frozen=True)
class RelationConstraint:
    left: str
    operator: str
    right: str


def _candidate(coins: list[int], amount: int, generator_id="test"):
    raw_array = tuple(coins) + (amount,)
    return SynthesizedCandidate(raw_array, (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


# ── Known divergence case ────────────────────────────────────────────────

COINS_DIVERGE = [4, 5, 7]
AMOUNT_DIVERGE = 10
# greedy: 7→remaining=3→stuck, returns -1
# smallest_first: 4→4→remaining=2→stuck, returns -1
# DP: 5+5=2 coins, is_reachable=True


def test_greedy_diverges_known():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    predicates = (
        RelationConstraint("greedy_diverges(coins, amount)", "==", "True"),
        RelationConstraint("is_reachable(coins, amount)", "==", "True"),
        RelationConstraint("dp_agrees_with_truth(coins, amount)", "==", "True"),
    )
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "greedy_trap_no_subdivision"))
    assert result.passed
    assert result.violated_predicate_ids == ()


def test_smallest_first_diverges_on_known_case():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["smallest_first_diverges"] is True
    assert values["smallest_first_output"] == -1


def test_memo_collision_output_is_integer():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert isinstance(values["memo_collision_output"], int)


def test_lookahead_one_output_is_integer():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert isinstance(values["lookahead_one_output"], int)


def test_bfs_coin_count_cutoff_diverges_on_deep_solution():
    candidate = _candidate([1, 2], 8)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 4
    assert values["optimal_coin_count_exceeds_coin_type_count"] is True
    assert values["bfs_coin_count_cutoff_output"] == -1
    assert values["bfs_coin_count_cutoff_diverges"] is True


def test_modulo_memo_alias_diverges_on_remainder_collision():
    candidate = _candidate([1, 3], 6)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 2
    assert values["modulo_remainder_alias_present"] is True
    assert values["modulo_memo_alias_output"] == 4
    assert values["modulo_memo_alias_diverges"] is True


def test_reachability_lookahead_overcounts_on_non_optimal_reachable_step():
    candidate = _candidate([1, 3, 4], 6)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 2
    assert values["reachability_lookahead_output"] == 3
    assert values["reachability_lookahead_overcounts"] is True
    assert values["reachability_lookahead_diverges"] is True


def test_dp_agrees_with_truth_on_known_case():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["dp_agrees_with_truth"] is True
    assert values["min_coins_ground_truth"] == 2


# ── Simple case where all solvers agree ──────────────────────────────────

COINS_SIMPLE = [1, 2]
AMOUNT_SIMPLE = 4
# All solvers should find 1+1+1+1=4 or 2+2=4 → 2 coins minimum


def test_all_solvers_agree_on_simple_case():
    candidate = _candidate(COINS_SIMPLE, AMOUNT_SIMPLE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 2
    assert values["dp_output"] == 2
    assert values["greedy_output"] == 2
    assert values["smallest_first_output"] == 4
    assert values["dp_agrees_with_truth"] is True
    assert values["greedy_agrees_with_truth"] is True
    assert values["smallest_first_agrees_with_truth"] is False


# ── Unit coin — all solvers correct ──────────────────────────────────────

COINS_UNIT = [1, 5, 10]
AMOUNT_UNIT = 7


def test_unit_coin_all_agree():
    candidate = _candidate(COINS_UNIT, AMOUNT_UNIT)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 3
    assert values["dp_output"] == 3
    assert values["greedy_output"] == 3
    assert values["smallest_first_output"] == 7


# ── Dual medium dominance seed ───────────────────────────────────────────

def test_dual_medium_dominance_seed():
    candidate = _candidate([1, 7, 10], 14)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "dual_medium_dominance"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] >= 0
    assert isinstance(values["greedy_output"], int)
    assert isinstance(values["smallest_first_output"], int)
    assert isinstance(values["memo_collision_output"], int)
    assert isinstance(values["lookahead_one_output"], int)


def test_dual_medium_dominance_another_seed():
    candidate = _candidate([2, 7, 10], 14)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "dual_medium_dominance"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 2


# ── Oracle ceiling ───────────────────────────────────────────────────────

def test_oracle_ceiling_error_amount():
    candidate = _candidate([1], 31)
    with pytest.raises(OracleCeilingError):
        LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))


def test_oracle_ceiling_error_boundary():
    candidate = _candidate([1], 30)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == 30


def test_oracle_ceiling_error_too_many_coins():
    candidate = _candidate([1, 2, 3, 4, 5, 6, 7], 10)
    with pytest.raises(OracleCeilingError):
        LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))


def test_oracle_ceiling_error_max_coins_boundary():
    candidate = _candidate([1, 2, 3, 4, 5, 6], 10)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] >= 0


# ── Predicate evaluation ─────────────────────────────────────────────────

def test_predicate_violation_reported():
    candidate = _candidate([2, 3], 5)
    predicate = RelationConstraint("greedy_diverges(coins, amount)", "==", "True")
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert not result.passed
    assert result.violated_predicate_ids == ("test:validation_predicates[0]",)


def test_multiple_predicates_one_violated():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    predicates = (
        RelationConstraint("is_reachable(coins, amount)", "==", "True"),
        RelationConstraint("greedy_diverges(coins, amount)", "==", "False"),
    )
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "test"))
    assert not result.passed
    passed_ids = [p.predicate_id for p in result.predicate_results if p.passed]
    failed_ids = [p.predicate_id for p in result.predicate_results if not p.passed]
    assert "test:validation_predicates[0]" in passed_ids
    assert "test:validation_predicates[1]" in failed_ids


def test_in_operator():
    candidate = _candidate([1, 7, 10], 14)
    predicate = RelationConstraint("1", "in", "coins")
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_not_in_operator():
    candidate = _candidate([4, 5, 7], 10)
    predicate = RelationConstraint("1", "not_in", "coins")
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


# ── Expression evaluation ────────────────────────────────────────────────

def test_amount_div_2_expression():
    candidate = _candidate([1], 10)
    predicate = RelationConstraint("amount / 2", "==", "5")
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_len_expression():
    candidate = _candidate([6, 9, 20], 15)
    predicate = RelationConstraint("len(coins)", "==", "3")
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_comparison_chain():
    candidate = _candidate([6, 9, 20], 15)
    predicates = (
        RelationConstraint("amount", ">=", "6"),
        RelationConstraint("amount", "<=", "20"),
    )
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "test"))
    assert result.passed


# ── Solver divergence patterns ───────────────────────────────────────────

def test_greedy_overcounts():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["greedy_overcounts"] is False


def test_coin_set_no_subdivision():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["coin_set_no_subdivision"] is True


def test_largest_coin_expression():
    candidate = _candidate(COINS_DIVERGE, AMOUNT_DIVERGE)
    predicate = RelationConstraint("largest_coin(coins)", "==", "7")
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_all_even_coins():
    candidate = _candidate([2, 4, 6], 10)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["all_even_coins"] is True


def test_amount_is_odd():
    candidate = _candidate([2, 4, 6], 11)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["amount_is_odd"] is True
    assert values["all_even_coins"] is True


# ── Immutability ─────────────────────────────────────────────────────────

def test_input_array_is_not_modified():
    coins = [4, 5, 7]
    amount = 10
    source = tuple(coins) + (amount,)
    candidate = SynthesizedCandidate(source, (), GenerationStrategy.INTERIOR_SPIKE, "test")
    LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (RelationConstraint("amount", ">=", "1"),), "test"))
    assert list(source[:-1]) == [4, 5, 7]
    assert source[-1] == 10
    assert candidate.raw_array == (4, 5, 7, 10)


# ── Error handling ───────────────────────────────────────────────────────

def test_unknown_symbol_raises_error():
    candidate = _candidate([1], 5)
    predicate = RelationConstraint("nonexistent(coins, amount)", "==", "True")
    with pytest.raises(ValueError):
        LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))


# ── All oracle-dependent values ──────────────────────────────────────────

def test_all_oracle_dependent_values_computed():
    candidate = _candidate([1, 2], 4)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    computed_names = {v.symbol_name for v in result.oracle_dependent_values}
    expected = {e.name for e in LC322_SYMBOL_REGISTRY.entries if e.category is SymbolCategory.ORACLE_DEPENDENT}
    assert computed_names == expected


def test_oracle_dependent_values_include_all_solver_variants():
    candidate = _candidate([1, 5, 10], 12)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}

    assert "dp_output" in values
    assert "greedy_output" in values
    assert "smallest_first_output" in values
    assert "memo_collision_output" in values
    assert "lookahead_one_output" in values
    assert "bfs_coin_count_cutoff_output" in values
    assert "modulo_memo_alias_output" in values
    assert "reachability_lookahead_output" in values

    assert "dp_agrees_with_truth" in values
    assert "greedy_agrees_with_truth" in values
    assert "smallest_first_agrees_with_truth" in values
    assert "memo_collision_agrees_with_truth" in values
    assert "lookahead_one_agrees_with_truth" in values
    assert "bfs_coin_count_cutoff_agrees_with_truth" in values
    assert "modulo_memo_alias_agrees_with_truth" in values
    assert "reachability_lookahead_agrees_with_truth" in values

    assert "greedy_diverges" in values
    assert "smallest_first_diverges" in values
    assert "memo_collision_diverges" in values
    assert "lookahead_one_diverges" in values
    assert "bfs_coin_count_cutoff_diverges" in values
    assert "modulo_memo_alias_diverges" in values
    assert "reachability_lookahead_diverges" in values


def test_ground_truth_included():
    candidate = _candidate([1, 5, 10], 7)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert "min_coins_ground_truth" in values
    assert values["min_coins_ground_truth"] == 3


# ── Edge: unreachable amount ─────────────────────────────────────────────

def test_unreachable_amount():
    candidate = _candidate([5, 7], 11)
    result = LC322OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["min_coins_ground_truth"] == -1
    assert values["is_reachable"] is False
    assert values["dp_output"] == -1
