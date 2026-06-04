"""Canonical observation form for cross-problem measurement.

TEST-LAYER INSTRUMENTATION OBJECT
=================================

Observation is a test-layer instrumentation object. It exists to make
evaluation assumptions visible during analysis and CI verification.

Production modules MUST NOT rely on Observation as an evaluation
primitive. Observation does not establish cross-problem comparability,
behavioral equivalence, or measurement validity. It records the output
of a particular evaluation procedure under a particular projection.

RATIONALE FOR TEST-LOCALITY
===========================

Prior investigation of the blocked schema files (47 files in the
bimaristan_schema family) surfaced three incompatible notions of
"valid measurement" coexisting in the latent system (brute-force,
symbol, schema layers). The findings are recorded in an external
audit artifact, not in this repository. Observation was introduced to
expose those assumptions, not to resolve them. If it migrates into
production code too early, the repository risks reifying one
particular measurement encoding as if it were the canonical semantic
object — bypassing the very problem the investigation uncovered.

The burden of proof for promoting Observation out of the test layer is
on promotion, not on containment. Any future change to this contract
must be argued explicitly and recorded here.

DESIGN INVARIANTS (what Observation is — verified by tests/test_observation_canonical.py):

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

DECLARED CONVENTIONS (test-layer usage)
======================================

Two conventions govern how tests construct Observations. These are
empirically derived from the existing corpus (113+ tests across
test_pipeline.py, test_agreement_path.py, test_adversarial.py,
test_observation_canonical.py, test_lc322_operator_invariance.py,
test_lc45_solver_population.py) and should be treated as binding
until the corpus expands to a point where they must be re-evaluated.

  1. symbol_name: Exactly two values are used in test-layer
     from_symbol() calls. No other symbol_name values appear in
     evaluation-facing tests.

       "pipeline_verdict"  — pipeline execution correctness
       "agreement_verdict" — solver-to-oracle agreement

     Tests that need domain-specific evaluation symbols (e.g.
     "naive_diverges") belong in test_observation_canonical.py,
     which tests the Observation class itself, not the evaluation
     protocol. Do not introduce new symbol_name values in
     evaluation-facing tests without declaring the addition here.

  2. projection_level: All test-layer Observations use
     projection_level=1. No evaluation-facing test uses levels
     2, 3, or 4. Level 1 means "full projection" — the
     Observation captures the complete evaluation result for a
     given candidate under a given evaluation layer. If a
     future test needs projection_level > 1, the rationale
     must be documented here before the test is merged.
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
