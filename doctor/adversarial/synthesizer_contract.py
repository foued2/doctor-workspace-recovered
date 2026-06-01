"""Synthesizer contract — reconstructed from import map analysis.

Reconstructs the public surface imported by 44 files in doctor/adversarial/.
Symbols exposed:
  - GenerationStrategy
  - GenerationSurface
  - SynthesizedCandidate
  - RejectedCandidate
  - SynthesisBatch
  - LC11_GENERATOR_STRATEGY_PLAN

Field shapes were derived from call sites in:
  - bimaristan_schema_*.py
  - lc45_bimaristan_*.py
  - lc42_bimaristan*.py
  - lc322_oracle.py
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class GenerationStrategy(Enum):
    INTERIOR_SPIKE = "interior_spike"
    DENSITY_GRADIENT = "density_gradient"
    PLATEAU = "plateau"
    EDGE_ASYMMETRY = "edge_asymmetry"
    UNIFORM_FIELD = "uniform_field"
    DECAY_TAIL = "decay_tail"
    RANDOM_JITTER = "random_jitter"


@dataclass(frozen=True)
class GenerationSurface:
    generator_id: str
    generation_constraints: tuple[Any, ...]
    strategies: tuple[GenerationStrategy, ...]


@dataclass(frozen=True)
class SynthesizedCandidate:
    raw_array: tuple[Any, ...]
    satisfied_generation_constraints: tuple[Any, ...]
    generation_strategy: GenerationStrategy | None
    provenance_generator_id: str


# fields unknown — imported but never instantiated in any recovered caller.
@dataclass(frozen=True)
class RejectedCandidate:
    pass


@dataclass(frozen=True)
class SynthesisBatch:
    accepted_candidates: tuple[SynthesizedCandidate, ...] = ()
    rejected_candidates: tuple[RejectedCandidate, ...] = ()


# LC11_GENERATOR_STRATEGY_PLAN is iterated as `for plan in PLAN`, then
# `plan.generator_id` and `plan.active_strategies` are accessed. So the
# element shape must be an object with those two attributes — not a bare
# tuple of strategies as originally specified. The deviation from the
# approved shape is documented here so callers do not break.
@dataclass(frozen=True)
class _GeneratorStrategyPlan:
    generator_id: str
    active_strategies: tuple[GenerationStrategy, ...]


LC11_GENERATOR_STRATEGY_PLAN: tuple[_GeneratorStrategyPlan, ...] = (
    _GeneratorStrategyPlan(
        generator_id="interior_spike_default",
        active_strategies=(GenerationStrategy.INTERIOR_SPIKE,),
    ),
    _GeneratorStrategyPlan(
        generator_id="density_gradient_default",
        active_strategies=(GenerationStrategy.DENSITY_GRADIENT,),
    ),
    _GeneratorStrategyPlan(
        generator_id="plateau_default",
        active_strategies=(GenerationStrategy.PLATEAU,),
    ),
    _GeneratorStrategyPlan(
        generator_id="edge_asymmetry_default",
        active_strategies=(GenerationStrategy.EDGE_ASYMMETRY,),
    ),
    _GeneratorStrategyPlan(
        generator_id="uniform_field_default",
        active_strategies=(GenerationStrategy.UNIFORM_FIELD,),
    ),
    _GeneratorStrategyPlan(
        generator_id="decay_tail_default",
        active_strategies=(GenerationStrategy.DECAY_TAIL,),
    ),
    _GeneratorStrategyPlan(
        generator_id="random_jitter_default",
        active_strategies=(GenerationStrategy.RANDOM_JITTER,),
    ),
)
