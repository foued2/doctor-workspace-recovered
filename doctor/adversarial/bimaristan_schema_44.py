# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
from __future__ import annotations

import pytest

from doctor.adversarial.bimaristan_schema import LC11, RelationConstraint
from doctor.adversarial.lc42_bimaristan import LC42
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema, validate_schema
from doctor.adversarial.symbol_registry import LC11_SYMBOL_REGISTRY
from doctor.adversarial.synthesizer import ConstraintEvaluationError, LC11Synthesizer, SynthesisProblemMismatchError
from doctor.adversarial.synthesizer_contract import GenerationStrategy, GenerationSurface


def test_lc11_schema_validates_against_lc11_registry():
    assert validate_schema(LC11, registry=LC11_SYMBOL_REGISTRY) == ()


def test_lc42_schema_rejected_by_lc11_registry():
    issues = validate_schema(LC42, registry=LC11_SYMBOL_REGISTRY)
    messages = {issue.message for issue in issues}
    assert any("does not match schema problem_id" in message for message in messages)


def test_schema_assertion_raises_with_problem_id_mismatch():
    with pytest.raises(SchemaValidationError):
        assert_valid_schema(LC42, registry=LC11_SYMBOL_REGISTRY)


def test_synthesizer_raises_on_unroutable_constraint_in_strict_mode():
    surface = GenerationSurface(
        "bad_symbol_surface",
        (RelationConstraint("unknown_symbol", "==", "1"),),
        (GenerationStrategy.PLATEAU, GenerationStrategy.INTERIOR_SPIKE),
    )
    with pytest.raises(ConstraintEvaluationError):
        LC11Synthesizer(seed=42).try_synthesize(surface)


def test_synthesizer_can_preserve_legacy_rejection_for_unroutable_constraint():
    surface = GenerationSurface(
        "bad_symbol_surface",
        (RelationConstraint("unknown_symbol", "==", "1"),),
        (GenerationStrategy.PLATEAU, GenerationStrategy.INTERIOR_SPIKE),
    )
    batch, warning = LC11Synthesizer(seed=42, strict_constraints=False).try_synthesize(surface)
    assert warning is not None
    assert batch.accepted_candidates == ()
    assert batch.rejected_candidates


def test_lc11_synthesizer_rejects_non_lc11_surface():
    surface = GenerationSurface(
        "lc42_hidden_basin",
        (),
        (GenerationStrategy.PLATEAU, GenerationStrategy.INTERIOR_SPIKE),
        problem_id="lc42_trapping_rain_water",
    )
    with pytest.raises(SynthesisProblemMismatchError):
        LC11Synthesizer(seed=42).try_synthesize(surface)
