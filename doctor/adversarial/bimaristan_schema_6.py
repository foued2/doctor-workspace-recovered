# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC45-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc45_bimaristan import LC45
from doctor.adversarial.lc45_candidates import lc45_dp, lc45_greedy_frontier, lc45_naive_greedy
from doctor.adversarial.lc45_ground_truth import GroundTruthDomainError, lc45_brute_force
from doctor.adversarial.lc45_oracle import LC45OracleEvaluator, evaluation_surface
from doctor.adversarial.lc45_symbol_registry import LC45_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


CandidateSolver = Callable[[list[int]], int]


@dataclass(frozen=True)
class LC45SynthesizedInput:
    input_id: str
    nums: tuple[int, ...]
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC45RejectedInput:
    input_id: str
    nums: tuple[int, ...]
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC45SynthesisBatch:
    accepted: tuple[LC45SynthesizedInput, ...]
    rejected: tuple[LC45RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC45CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[tuple[int, ...], ...]
    warnings: tuple[str, ...]


class LC45SchemaValidationError(RuntimeError):
    pass


class LC45SynthesisError(RuntimeError):
    pass


class LC45CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc45_greedy_frontier", lc45_greedy_frontier, True),
    ("lc45_naive_greedy", lc45_naive_greedy, False),
    ("lc45_dp", lc45_dp, True),
)


def validate_lc45_path() -> None:
    try:
        assert_valid_schema(LC45, registry=LC45_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC45SchemaValidationError(str(exc)) from exc


def synthesize_lc45_inputs() -> LC45SynthesisBatch:
    validate_lc45_path()
    evaluator = LC45OracleEvaluator()
    accepted: list[LC45SynthesizedInput] = []
    rejected: list[LC45RejectedInput] = []
    warnings: list[str] = []

    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, nums in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            candidate = _candidate(nums, generator.generator_id)
            surface = evaluation_surface(candidate, generator.generation_constraints, generator.generator_id, input_id)
            try:
                result = evaluator.evaluate(surface)
            except Exception as exc:
                rejected.append(LC45RejectedInput(input_id, tuple(nums), generator.generator_id, _reason(exc)))
                generator_rejected += 1
                continue
            if result.passed:
                accepted.append(
                    LC45SynthesizedInput(
                        input_id,
                        tuple(nums),
                        generator.generator_id,
                        tuple(generator.validation_predicates),
                    )
                )
                generator_accepted += 1
            else:
                rejected.append(
                    LC45RejectedInput(
                        input_id,
                        tuple(nums),
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

    return LC45SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc45_candidates(batch: LC45SynthesisBatch) -> tuple[LC45CandidateEvaluation, ...]:
    evaluator = LC45OracleEvaluator()
    results: list[LC45CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[tuple[int, ...]] = []

        for synthesized in batch.accepted:
            nums = synthesized.nums
            try:
                oracle_result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(nums, synthesized.generator_id),
                        synthesized.validation_predicates,
                        synthesized.generator_id,
                        synthesized.input_id,
                    )
                )
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc45_brute_force(list(nums))
                observed = solver(list(nums))
            except (GroundTruthDomainError, LC45SynthesisError) as exc:
                raise LC45CandidateExecutionError(f"{candidate_name} {list(nums)}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC45CandidateExecutionError(f"{candidate_name} {list(nums)}: {_reason(exc)}") from exc

            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append(nums)
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")

        results.append(
            LC45CandidateEvaluation(
                candidate_name,
                accepted_count,
                rejected_count,
                tuple(sorted(set(violated))),
                tuple(false_pass_inputs),
                batch.warnings,
            )
        )

    return tuple(results)


def generator_counts(batch: LC45SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(
        generator
        for family in LC45.invariant_families
        for manifold in family.failure_manifolds
        for generator in manifold.geometry_generators
    )


def _candidate(nums: Sequence[int], generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate(
        raw_array=tuple(nums),
        satisfied_generation_constraints=(),
        generation_strategy=GenerationStrategy.INTERIOR_SPIKE,
        provenance_generator_id=generator_id,
    )


def _candidate_space(generator_id: str) -> Iterable[tuple[int, ...]]:
    seeds = {
        "lc45_naive_max_jump_suboptimal": (
            (2, 4, 1, 1, 1, 1),
            (2, 3, 0, 1, 4),
            (3, 5, 1, 1, 1, 1, 1),
            (2, 5, 0, 0, 1, 1, 1),
            (3, 1, 4, 1, 1, 1),
            (2, 4, 0, 1, 1, 1),
            (3, 4, 1, 0, 1, 1),
            (2, 5, 1, 1, 1, 1, 1),
            (3, 2, 5, 1, 1, 1, 1),
            (2, 3, 1, 1, 4),
            (4, 1, 1, 5, 1, 1, 1),
            (3, 5, 0, 1, 1, 1, 1),
        ),
        "lc45_single_large_jump_decoy": (
            (2, 5, 0, 0, 1, 1, 1),
            (3, 6, 1, 1, 1, 1, 1, 1),
            (2, 4, 0, 1, 1, 1),
            (3, 5, 1, 0, 1, 1, 1),
            (2, 6, 0, 0, 0, 1, 1, 1),
            (3, 7, 1, 1, 1, 1, 1, 1, 1),
            (2, 5, 1, 1, 1, 1, 1),
            (4, 6, 1, 1, 0, 1, 1, 1),
            (3, 5, 0, 1, 1, 1, 1),
            (2, 7, 0, 0, 0, 0, 1, 1, 1),
            (4, 5, 1, 1, 1, 0, 1),
            (3, 6, 0, 1, 1, 1, 1, 1),
        ),
        "lc45_uniform_jump_array": (
            (1, 1, 1, 1),
            (2, 2, 2, 2),
            (3, 3, 3, 3),
            (1, 1, 1, 1, 1),
            (2, 2, 2, 2, 2),
            (3, 3, 3, 3, 3),
            (2, 2, 2, 2, 2, 2),
            (3, 3, 3, 3, 3, 3),
            (4, 4, 4, 4, 4, 4),
            (2, 2, 2, 2, 2, 2, 2),
            (3, 3, 3, 3, 3, 3, 3),
            (4, 4, 4, 4, 4, 4, 4),
        ),
        "lc45_greedy_frontier_valid_no_false_pressure": (
            (2, 3, 1, 1, 4),
            (1, 2, 1, 1, 1),
            (2, 2, 1, 1, 1),
            (3, 1, 2, 1, 1),
            (1, 3, 1, 1, 1),
            (2, 1, 2, 1, 1),
            (3, 2, 1, 1, 1),
            (1, 1, 2, 1, 1),
            (2, 3, 2, 1, 1, 1),
            (1, 2, 2, 1, 1, 1),
            (3, 1, 1, 2, 1, 1),
            (2, 1, 1, 2, 1, 1),
        ),
        "lc45_greedy_horizon_collapse": (
            (2, 3, 1, 1, 4),
            (3, 1, 5, 1, 1, 1, 1),
            (2, 4, 0, 0, 1, 1),
            (3, 2, 4, 1, 1, 1, 1),
            (2, 5, 0, 0, 0, 1, 1),
            (4, 1, 1, 1, 5, 1, 1, 1),
            (3, 1, 4, 0, 1, 1, 1),
            (2, 3, 0, 1, 4),
            (5, 1, 1, 1, 1, 6, 1, 1, 1, 1, 1),
            (3, 2, 1, 4, 1, 1, 1),
            (2, 4, 1, 0, 1, 1),
            (4, 2, 1, 1, 5, 1, 1, 1),
        ),
    }
    if generator_id == "lc45_naive_max_jump_dead_landing":
        yield from _naive_max_jump_dead_landing_candidates()
    else:
        yield from seeds[generator_id]


def _acceptance_limit(generator_id: str) -> int:
    if generator_id == "lc45_naive_max_jump_dead_landing":
        return 220
    return 12


def _naive_max_jump_dead_landing_candidates() -> Iterable[tuple[int, ...]]:
    yielded = 0
    for length in range(5, 13):
        for tail in itertools.product(range(0, 8), repeat=length - 4):
            nums = (1, 2, 2, 0) + tail
            try:
                truth = lc45_brute_force(list(nums))
            except GroundTruthDomainError:
                continue
            if lc45_greedy_frontier(list(nums)) != truth:
                continue
            if lc45_dp(list(nums)) != truth:
                continue
            if lc45_naive_greedy(list(nums)) == truth:
                continue
            yield nums
            yielded += 1
            if yielded >= 220:
                return


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
