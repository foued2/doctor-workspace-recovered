# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Not on paper critical path. See git log for reconstruction history.
from __future__ import annotations

import pytest

from doctor.adversarial.bimaristan_schema import RelationConstraint
from doctor.adversarial.oracle_evaluator import LC11OracleEvaluator, OracleCeilingError, evaluation_surface
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


def _candidate(array, generator_id="test"):
    return SynthesizedCandidate(tuple(array), (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


def test_known_good_lc11_array_answer_49():
    candidate = _candidate([1, 8, 6, 2, 5, 4, 8, 3, 7])
    surface = evaluation_surface(candidate, (RelationConstraint("max_area", "==", "49"),), "test")
    result = LC11OracleEvaluator().evaluate(surface)
    values = {value.symbol_name: value.value for value in result.oracle_dependent_values}
    assert values["global_max_pair_area"] == 49
    assert result.passed
    assert result.violated_predicate_ids == ()


def test_known_fail_move_taller_boundary_predicate():
    candidate = _candidate([3, 1, 4, 2, 1], "short_left_tall_right_hidden_left_partner")
    predicate = RelationConstraint("hidden_partner_area", ">", "current_area")
    result = LC11OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), candidate.provenance_generator_id))
    assert not result.passed
    assert result.violated_predicate_ids == ("short_left_tall_right_hidden_left_partner:validation_predicates[0]",)


def test_oracle_ceiling_error_for_large_array():
    candidate = _candidate([1] * 1001)
    with pytest.raises(OracleCeilingError):
        LC11OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))


def test_input_array_is_not_modified_after_evaluation():
    source = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    candidate = _candidate(source)
    LC11OracleEvaluator().evaluate(evaluation_surface(candidate, (RelationConstraint("max_area", "==", "49"),), "test"))
    assert source == [1, 8, 6, 2, 5, 4, 8, 3, 7]
    assert candidate.raw_array == (1, 8, 6, 2, 5, 4, 8, 3, 7)
