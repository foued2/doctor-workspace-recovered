# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
from __future__ import annotations

import pytest

from doctor.adversarial.bimaristan_schema import RelationConstraint
from doctor.adversarial.synthesizer import LC11Synthesizer, SynthesisYieldWarning, candidate_context, evaluate_constraint
from doctor.adversarial.synthesizer_contract import GenerationStrategy, GenerationSurface


def test_each_strategy_produces_valid_array_for_empty_surface():
    synth = LC11Synthesizer(seed=42, attempts_per_strategy=5)
    for strategy in GenerationStrategy:
        alternate = GenerationStrategy.INTERIOR_SPIKE if strategy is GenerationStrategy.PLATEAU else GenerationStrategy.PLATEAU
        surface = GenerationSurface(f"strategy_{strategy.value}", (), (strategy, alternate))
        batch = synth.synthesize(surface)
        matching = [candidate for candidate in batch.accepted_candidates if candidate.generation_strategy is strategy]
        assert matching
        assert all(candidate.raw_array for candidate in matching)


def test_rejection_tracking_logs_correct_constraint():
    constraint = RelationConstraint("n", ">=", "100")
    surface = GenerationSurface("reject_n", (constraint,), (GenerationStrategy.PLATEAU, GenerationStrategy.INTERIOR_SPIKE))
    batch, warning = LC11Synthesizer(seed=42).try_synthesize(surface)
    assert warning is not None
    assert batch.rejected_candidates
    assert batch.rejected_candidates[0].failed_generation_constraint == constraint


def test_synthesis_yield_warning_fires_when_yield_below_threshold():
    surface = GenerationSurface("single_strategy", (), (GenerationStrategy.INTERIOR_SPIKE,))
    with pytest.raises(SynthesisYieldWarning):
        LC11Synthesizer(seed=42).synthesize(surface)


def test_seed_reproducibility():
    surface = GenerationSurface("seeded", (), (GenerationStrategy.INTERIOR_SPIKE, GenerationStrategy.PLATEAU))
    first = LC11Synthesizer(seed=7).synthesize(surface)
    second = LC11Synthesizer(seed=7).synthesize(surface)
    assert first.accepted_candidates == second.accepted_candidates


def test_short_left_hidden_partner_surface_is_rejected_honestly():
    constraints = (
        RelationConstraint("left_height", "<", "right_height"),
        RelationConstraint("hidden_partner_index", ">", "left_index"),
        RelationConstraint("hidden_partner_index", "<", "right_index"),
        RelationConstraint("hidden_partner_area", ">", "current_area"),
    )
    surface = GenerationSurface(
        "short_left_tall_right_hidden_left_partner",
        constraints,
        (GenerationStrategy.INTERIOR_SPIKE, GenerationStrategy.DENSITY_GRADIENT),
    )
    batch, warning = LC11Synthesizer(seed=42).try_synthesize(surface)
    assert warning is not None
    assert all(
        not evaluate_constraint(constraints[-1], candidate_context(surface.generator_id, rejected.raw_array))
        for rejected in batch.rejected_candidates
    )
