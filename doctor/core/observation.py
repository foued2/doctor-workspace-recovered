"""Canonical observation form for cross-problem measurement.

This module defines `Observation`, a hashable record of a single
projection-classified evaluation. The form is deliberately minimal:
it captures WHAT was observed (problem, candidate, projection, layer,
classification), under WHICH sampling conditions (seed, sample size),
and NOTHING ELSE.

DESIGN INVARIANTS (must hold — verified by tests/test_observation_canonical.py):

  A. Layer coverage. All three evaluation layers in the latent system
     (brute-force / symbol / schema) can populate Observation without
     being forced to be equivalent. The evaluation_layer field makes
     the layer explicit, not implicit.

  B. Layer visibility. The evaluation_layer is a required, visible
     field. Downstream code that wants to compare observations MUST
     inspect the layer; the Observation does not silently homogenize
     layers.

  C. No implicit cross-problem comparability. Observation does NOT
     define a `compares_to` or `equivalent_to` method. Two observations
     from different problem_ids are NOT automatically comparable. Any
     cross-problem claim must be made explicitly by downstream code
     that has declared its equivalence assumptions.

This module does NOT make any cross-problem measurement claim. It is
the substrate on which such claims could be made, with assumptions
declared.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EVALUATION_LAYERS = frozenset({"brute_force", "symbol", "schema"})


@dataclass(frozen=True)
class Observation:
    problem_id: str
    candidate_id: str
    projection_level: int
    evaluation_layer: str
    canonical_form: tuple
    seed: int
    sample_size: int

    def __post_init__(self) -> None:
        if self.projection_level not in (1, 2, 3, 4):
            raise ValueError(
                f"projection_level must be 1..4, got {self.projection_level}"
            )
        if self.evaluation_layer not in EVALUATION_LAYERS:
            raise ValueError(
                f"evaluation_layer must be one of {sorted(EVALUATION_LAYERS)}, "
                f"got {self.evaluation_layer!r}"
            )
        if not isinstance(self.canonical_form, tuple):
            raise TypeError(
                f"canonical_form must be a tuple, got {type(self.canonical_form).__name__}"
            )
        if not self.candidate_id:
            raise ValueError("candidate_id must be non-empty")
        if self.sample_size <= 0:
            raise ValueError(f"sample_size must be > 0, got {self.sample_size}")


def from_brute_force(
    *,
    problem_id: str,
    candidate_id: str,
    projection_level: int,
    classification: str,
    seed: int,
    sample_size: int,
) -> Observation:
    return Observation(
        problem_id=problem_id,
        candidate_id=candidate_id,
        projection_level=projection_level,
        evaluation_layer="brute_force",
        canonical_form=(classification,),
        seed=seed,
        sample_size=sample_size,
    )


def from_symbol(
    *,
    problem_id: str,
    candidate_id: str,
    projection_level: int,
    symbol_name: str,
    symbol_value: Any,
    passed: bool,
    seed: int,
    sample_size: int,
) -> Observation:
    return Observation(
        problem_id=problem_id,
        candidate_id=candidate_id,
        projection_level=projection_level,
        evaluation_layer="symbol",
        canonical_form=(symbol_name, repr(symbol_value), "PASS" if passed else "FAIL"),
        seed=seed,
        sample_size=sample_size,
    )


def from_schema(
    *,
    problem_id: str,
    candidate_id: str,
    projection_level: int,
    schema_id: str,
    violated: tuple,
    seed: int,
    sample_size: int,
) -> Observation:
    return Observation(
        problem_id=problem_id,
        candidate_id=candidate_id,
        projection_level=projection_level,
        evaluation_layer="schema",
        canonical_form=(schema_id, tuple(sorted(violated))),
        seed=seed,
        sample_size=sample_size,
    )
