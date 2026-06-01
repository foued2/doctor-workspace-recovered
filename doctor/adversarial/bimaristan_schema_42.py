# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
from __future__ import annotations

import pytest

from doctor.adversarial.bimaristan_schema import RelationConstraint
from doctor.adversarial.lc45_oracle import LC45OracleEvaluator, OracleCeilingError, evaluation_surface
from doctor.adversarial.lc45_symbol_registry import LC45_SYMBOL_REGISTRY
from doctor.adversarial.symbol_registry import SymbolCategory
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


def _candidate(array, generator_id="test"):
    return SynthesizedCandidate(tuple(array), (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


def test_known_naive_diverges():
    candidate = _candidate([2, 4, 1, 1, 1, 1])
    predicate = RelationConstraint("naive_diverges(nums)", "==", "True")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["naive_diverges"] is True
    assert values["greedy_frontier_agrees_with_truth"] is True
    assert result.passed
    assert result.violated_predicate_ids == ()


def test_single_large_jump_decoy_diverges():
    candidate = _candidate([2, 5, 0, 0, 1, 1, 1])
    predicate = RelationConstraint("naive_diverges(nums)", "==", "True")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["naive_diverges"] is True
    assert values["greedy_frontier_agrees_with_truth"] is True


def test_uniform_array_no_divergence():
    candidate = _candidate([2, 2, 2, 2])
    predicate = RelationConstraint("greedy_and_naive_agree(nums)", "==", "True")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["all_elements_equal"] is True
    assert values["naive_diverges"] is False
    assert values["greedy_and_naive_agree"] is True


def test_horizon_collapse_detected():
    candidate = _candidate([3, 1, 5, 1, 1, 1, 1])
    predicate = RelationConstraint("horizon_collapse_present(nums)", "==", "True")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_horizon_collapse_naive_diverges():
    candidate = _candidate([3, 1, 5, 1, 1, 1, 1])
    predicates = (
        RelationConstraint("horizon_collapse_present(nums)", "==", "True"),
        RelationConstraint("naive_diverges(nums)", "==", "True"),
        RelationConstraint("greedy_frontier_agrees_with_truth(nums)", "==", "True"),
    )
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "greedy_horizon_collapse"))
    assert result.passed
    assert result.violated_predicate_ids == ()


def test_control_manifold_no_false_pressure():
    candidate = _candidate([2, 3, 1, 1, 4])
    predicates = (
        RelationConstraint("greedy_frontier_agrees_with_truth(nums)", "==", "True"),
        RelationConstraint("naive_diverges(nums)", "==", "False"),
    )
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "greedy_frontier_valid_no_false_pressure"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert values["greedy_frontier_agrees_with_truth"] is True
    assert values["naive_diverges"] is True
    assert not result.passed
    assert "greedy_frontier_valid_no_false_pressure:validation_predicates[1]" in result.violated_predicate_ids


def test_len_expression():
    candidate = _candidate([1, 2, 3, 4, 5])
    predicate = RelationConstraint("len(nums)", "==", "5")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_max_expression():
    candidate = _candidate([1, 9, 3, 2])
    predicate = RelationConstraint("max(nums)", "==", "9")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_floor_div_expression():
    candidate = _candidate([1, 1, 1, 1, 1])
    predicate = RelationConstraint("len(nums) // 2", "==", "2")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_predicate_violation_reported():
    candidate = _candidate([2, 2, 2, 2])
    predicate = RelationConstraint("naive_diverges(nums)", "==", "True")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert not result.passed
    assert result.violated_predicate_ids == ("test:validation_predicates[0]",)


def test_oracle_ceiling_error():
    candidate = _candidate([1] * 16)
    with pytest.raises(OracleCeilingError):
        LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))


def test_all_oracle_dependent_values_computed():
    candidate = _candidate([1, 1, 1, 1])
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    computed_names = {v.symbol_name for v in result.oracle_dependent_values}
    expected = {e.name for e in LC45_SYMBOL_REGISTRY.entries if e.category is SymbolCategory.ORACLE_DEPENDENT}
    skip = {"max_jump_at", "reachable_from"}
    assert computed_names == expected - skip


def test_input_array_is_not_modified():
    source = [2, 3, 1, 1, 4]
    candidate = _candidate(source)
    LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (RelationConstraint("len(nums)", ">=", "1"),), "test"))
    assert source == [2, 3, 1, 1, 4]
    assert candidate.raw_array == (2, 3, 1, 1, 4)


def test_comparison_chain():
    candidate = _candidate([2, 4, 1, 1, 1, 1])
    predicate = RelationConstraint("len(nums)", ">=", "5")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_lt_operator():
    candidate = _candidate([1, 1, 1])
    predicate = RelationConstraint("len(nums)", "<", "5")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_gte_operator():
    candidate = _candidate([1, 1, 1, 1, 1])
    predicate = RelationConstraint("len(nums)", ">=", "5")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_ne_operator():
    candidate = _candidate([1, 1, 1])
    predicate = RelationConstraint("len(nums)", "!=", "5")
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))
    assert result.passed


def test_unknown_symbol_raises_error():
    candidate = _candidate([1, 2, 3])
    predicate = RelationConstraint("nonexistent_symbol(nums)", "==", "True")
    with pytest.raises(ValueError):
        LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), "test"))


def test_oracle_dependent_values_include_ground_truth():
    candidate = _candidate([2, 3, 1, 1, 4])
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))
    values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
    assert "ground_truth_jumps" in values
    assert isinstance(values["ground_truth_jumps"], int)
    assert values["ground_truth_jumps"] >= 0


def test_max_operator_in_generation_constraint():
    source = [3, 6, 1, 1, 1, 1, 1, 1]
    candidate = _candidate(source)
    predicates = (
        RelationConstraint("len(nums)", ">=", "6"),
        RelationConstraint("len(nums)", "<=", "12"),
        RelationConstraint("max(nums)", ">=", "len(nums) // 2"),
        RelationConstraint("array_has_greedy_naive_divergence(nums)", "==", "True"),
    )
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "single_large_jump_decoy"))
    assert result.passed


def test_multiple_predicates_mixed_results():
    candidate = _candidate([2, 2, 2, 2])
    predicates = (
        RelationConstraint("all_elements_equal(nums)", "==", "True"),
        RelationConstraint("naive_diverges(nums)", "==", "True"),
    )
    result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, predicates, "test"))
    assert not result.passed
    passed_ids = [p.predicate_id for p in result.predicate_results if p.passed]
    failed_ids = [p.predicate_id for p in result.predicate_results if not p.passed]
    assert "test:validation_predicates[0]" in passed_ids
    assert "test:validation_predicates[1]" in failed_ids
