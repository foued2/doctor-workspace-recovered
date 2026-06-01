# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC135-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc135_bimaristan import LC135
from doctor.adversarial.lc135_candidates import lc135_left_pass_only, lc135_right_pass_only, lc135_two_pass
from doctor.adversarial.lc135_ground_truth import GroundTruthDomainError, lc135_brute_force
from doctor.adversarial.lc135_oracle import LC135OracleEvaluator, evaluation_surface
from doctor.adversarial.lc135_symbol_registry import LC135_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


CandidateSolver = Callable[[list[int]], int]


@dataclass(frozen=True)
class LC135SynthesizedInput:
    input_id: str
    ratings: tuple[int, ...]
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC135RejectedInput:
    input_id: str
    ratings: tuple[int, ...]
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC135SynthesisBatch:
    accepted: tuple[LC135SynthesizedInput, ...]
    rejected: tuple[LC135RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC135CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[tuple[int, ...], ...]
    warnings: tuple[str, ...]


class LC135SchemaValidationError(RuntimeError):
    pass


class LC135SynthesisError(RuntimeError):
    pass


class LC135CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc135_two_pass", lc135_two_pass, True),
    ("lc135_left_pass_only", lc135_left_pass_only, False),
    ("lc135_right_pass_only", lc135_right_pass_only, False),
)


def validate_lc135_path() -> None:
    try:
        assert_valid_schema(LC135, registry=LC135_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC135SchemaValidationError(str(exc)) from exc


def synthesize_lc135_inputs() -> LC135SynthesisBatch:
    validate_lc135_path()
    evaluator = LC135OracleEvaluator()
    accepted: list[LC135SynthesizedInput] = []
    rejected: list[LC135RejectedInput] = []
    warnings: list[str] = []

    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, ratings in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            try:
                result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(ratings, generator.generator_id),
                        generator.generation_constraints,
                        generator.generator_id,
                        input_id,
                    )
                )
            except Exception as exc:
                raise LC135SynthesisError(f"{input_id}: {_reason(exc)}") from exc
            if result.passed:
                accepted.append(
                    LC135SynthesizedInput(
                        input_id,
                        tuple(ratings),
                        generator.generator_id,
                        tuple(generator.validation_predicates),
                    )
                )
                generator_accepted += 1
            else:
                rejected.append(
                    LC135RejectedInput(
                        input_id,
                        tuple(ratings),
                        generator.generator_id,
                        ",".join(result.violated_predicate_ids),
                    )
                )
                generator_rejected += 1
            if generator_accepted >= _acceptance_limit(generator.generator_id):
                break

        total = generator_accepted + generator_rejected
        rejection_rate = generator_rejected / total if total else 1.0
        if rejection_rate > 0.8:
            warnings.append(f"{generator.generator_id}: rejection rate {rejection_rate:.2%} exceeds 80%")
        if generator_accepted < 5:
            warnings.append(f"{generator.generator_id}: fewer than 5 valid candidates")

    return LC135SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc135_candidates(batch: LC135SynthesisBatch) -> tuple[LC135CandidateEvaluation, ...]:
    evaluator = LC135OracleEvaluator()
    results: list[LC135CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[tuple[int, ...]] = []

        for synthesized in batch.accepted:
            ratings = synthesized.ratings
            try:
                oracle_result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(ratings, synthesized.generator_id),
                        synthesized.validation_predicates,
                        synthesized.generator_id,
                        synthesized.input_id,
                    )
                )
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc135_brute_force(list(ratings))
                observed = solver(list(ratings))
            except GroundTruthDomainError as exc:
                raise LC135CandidateExecutionError(f"{candidate_name} {list(ratings)}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC135CandidateExecutionError(f"{candidate_name} {list(ratings)}: {_reason(exc)}") from exc

            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append(ratings)
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")

        results.append(
            LC135CandidateEvaluation(
                candidate_name,
                accepted_count,
                rejected_count,
                tuple(sorted(set(violated))),
                tuple(false_pass_inputs),
                batch.warnings,
            )
        )

    return tuple(results)


def generator_counts(batch: LC135SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(
        generator
        for family in LC135.invariant_families
        for manifold in family.failure_manifolds
        for generator in manifold.geometry_generators
    )


def _candidate(ratings: Sequence[int], generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate(
        raw_array=tuple(ratings),
        satisfied_generation_constraints=(),
        generation_strategy=GenerationStrategy.INTERIOR_SPIKE,
        provenance_generator_id=generator_id,
    )


def _candidate_space(generator_id: str) -> Iterable[tuple[int, ...]]:
    seeds = {
        "lc135_left_pass_misses_descending_tail": (
            (0, 2, 1, 0),
            (0, 3, 1, 0),
            (0, 3, 2, 0),
            (0, 3, 2, 1),
            (0, 4, 1, 0),
            (0, 4, 2, 0),
            (0, 4, 2, 1),
            (0, 4, 3, 0),
            (0, 4, 3, 1),
            (0, 4, 3, 2),
            (1, 2, 1, 0),
            (1, 3, 1, 0),
        ),
        "lc135_right_pass_misses_ascending_prefix": (
            (0, 1, 2, 0),
            (0, 1, 2, 1),
            (0, 1, 2, 2),
            (0, 1, 2, 3),
            (0, 1, 2, 4),
            (0, 1, 3, 0),
            (0, 1, 3, 1),
            (0, 1, 3, 2),
            (0, 1, 3, 3),
            (0, 1, 3, 4),
            (0, 1, 4, 0),
            (0, 1, 4, 1),
        ),
        "lc135_valley_forces_both_directions": (
            (1, 0, 1, 1),
            (1, 0, 1, 2),
            (1, 0, 1, 3),
            (1, 0, 1, 4),
            (1, 0, 2, 2),
            (1, 0, 2, 3),
            (1, 0, 2, 4),
            (1, 0, 3, 3),
            (1, 0, 3, 4),
            (1, 0, 4, 4),
            (1, 1, 0, 1),
            (1, 1, 0, 2),
        ),
        "lc135_constraint_collision_at_peak": (
            (0, 1, 2, 1, 0),
            (0, 1, 3, 1, 0),
            (0, 1, 3, 2, 0),
            (0, 1, 3, 2, 1),
            (0, 1, 4, 1, 0),
            (0, 1, 4, 2, 0),
            (0, 1, 4, 2, 1),
            (0, 1, 4, 3, 0),
            (0, 1, 4, 3, 1),
            (0, 1, 4, 3, 2),
            (0, 2, 1, 0, 1),
            (0, 2, 1, 0, 2),
        ),
        "lc135_left_pass_plateau_cliff": (
            (0, 0, 2, 1, 0),
            (0, 0, 3, 1, 0),
            (0, 0, 3, 2, 0),
            (0, 0, 3, 2, 1),
            (0, 0, 4, 1, 0),
            (0, 0, 4, 2, 0),
            (0, 0, 4, 2, 1),
            (0, 0, 4, 3, 0),
            (0, 0, 4, 3, 1),
            (0, 0, 4, 3, 2),
            (0, 2, 1, 0, 0),
            (0, 2, 1, 1, 0),
        ),
        "lc135_right_pass_plateau_cliff": (
            (0, 0, 0, 0, 1),
            (0, 0, 0, 0, 2),
            (0, 0, 0, 0, 3),
            (0, 0, 0, 0, 4),
            (0, 0, 0, 1, 1),
            (0, 0, 0, 1, 2),
            (0, 0, 0, 1, 3),
            (0, 0, 0, 1, 4),
            (0, 0, 0, 2, 2),
            (0, 0, 0, 2, 3),
            (0, 0, 0, 2, 4),
            (0, 0, 0, 3, 3),
        ),
    }
    if generator_id in {
        "lc135_left_pass_right_constraint_dominates",
        "lc135_right_pass_left_constraint_dominates",
    }:
        yield from _both_one_sided_solvers_fail_candidates()
    else:
        yield from seeds[generator_id]


def _acceptance_limit(generator_id: str) -> int:
    if generator_id in {
        "lc135_left_pass_right_constraint_dominates",
        "lc135_right_pass_left_constraint_dominates",
    }:
        return 220
    return 12


def _both_one_sided_solvers_fail_candidates() -> Iterable[tuple[int, ...]]:
    yielded = 0
    for length in range(4, 9):
        for ratings in itertools.product(range(0, 8), repeat=length):
            truth = lc135_brute_force(list(ratings))
            if lc135_two_pass(list(ratings)) != truth:
                continue
            if lc135_left_pass_only(list(ratings)) == truth:
                continue
            if lc135_right_pass_only(list(ratings)) == truth:
                continue
            yield ratings
            yielded += 1
            if yielded >= 220:
                return


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
