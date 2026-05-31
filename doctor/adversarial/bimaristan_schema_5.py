"""LC560-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc560_bimaristan import LC560
from doctor.adversarial.lc560_candidates import lc560_prefix_map, lc560_sliding_window
from doctor.adversarial.lc560_ground_truth import GroundTruthDomainError, lc560_brute_force
from doctor.adversarial.lc560_oracle import LC560OracleEvaluator, evaluation_surface
from doctor.adversarial.lc560_symbol_registry import LC560_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


CandidateSolver = Callable[[list[int], int], int]


@dataclass(frozen=True)
class LC560SynthesizedInput:
    input_id: str
    nums: tuple[int, ...]
    k: int
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC560RejectedInput:
    input_id: str
    nums: tuple[int, ...]
    k: int
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC560SynthesisBatch:
    accepted: tuple[LC560SynthesizedInput, ...]
    rejected: tuple[LC560RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC560CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[tuple[tuple[int, ...], int], ...]
    warnings: tuple[str, ...]


class LC560SchemaValidationError(RuntimeError):
    pass


class LC560SynthesisError(RuntimeError):
    pass


class LC560CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc560_prefix_map", lc560_prefix_map, True),
    ("lc560_sliding_window", lc560_sliding_window, False),
)


def validate_lc560_path() -> None:
    try:
        assert_valid_schema(LC560, registry=LC560_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC560SchemaValidationError(str(exc)) from exc


def synthesize_lc560_inputs() -> LC560SynthesisBatch:
    validate_lc560_path()
    evaluator = LC560OracleEvaluator()
    accepted: list[LC560SynthesizedInput] = []
    rejected: list[LC560RejectedInput] = []
    warnings: list[str] = []

    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, (nums, k) in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            try:
                result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(nums, k, generator.generator_id),
                        generator.generation_constraints,
                        generator.generator_id,
                        input_id,
                    )
                )
            except Exception as exc:
                raise LC560SynthesisError(f"{input_id}: {_reason(exc)}") from exc
            if result.passed:
                accepted.append(
                    LC560SynthesizedInput(input_id, tuple(nums), k, generator.generator_id, tuple(generator.validation_predicates))
                )
                generator_accepted += 1
            else:
                rejected.append(
                    LC560RejectedInput(input_id, tuple(nums), k, generator.generator_id, ",".join(result.violated_predicate_ids))
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

    return LC560SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc560_candidates(batch: LC560SynthesisBatch) -> tuple[LC560CandidateEvaluation, ...]:
    evaluator = LC560OracleEvaluator()
    results: list[LC560CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[tuple[tuple[int, ...], int]] = []

        for synthesized in batch.accepted:
            nums = synthesized.nums
            k = synthesized.k
            try:
                oracle_result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(nums, k, synthesized.generator_id),
                        synthesized.validation_predicates,
                        synthesized.generator_id,
                        synthesized.input_id,
                    )
                )
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc560_brute_force(list(nums), k)
                observed = solver(list(nums), k)
            except GroundTruthDomainError as exc:
                raise LC560CandidateExecutionError(f"{candidate_name} nums={list(nums)}, k={k}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC560CandidateExecutionError(f"{candidate_name} nums={list(nums)}, k={k}: {_reason(exc)}") from exc

            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append((nums, k))
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")

        results.append(
            LC560CandidateEvaluation(
                candidate_name,
                accepted_count,
                rejected_count,
                tuple(sorted(set(violated))),
                tuple(false_pass_inputs),
                batch.warnings,
            )
        )

    return tuple(results)


def generator_counts(batch: LC560SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(
        generator
        for family in LC560.invariant_families
        for manifold in family.failure_manifolds
        for generator in manifold.geometry_generators
    )


def _candidate(nums: Sequence[int], k: int, generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate(
        raw_array=tuple(nums) + (k,),
        satisfied_generation_constraints=(),
        generation_strategy=GenerationStrategy.INTERIOR_SPIKE,
        provenance_generator_id=generator_id,
    )


def _acceptance_limit(generator_id: str) -> int:
    if generator_id in {"lc560_negative_breaks_sliding_window", "lc560_zero_sum_subarray_invisibility"}:
        return 220
    return 12


def _candidate_space(generator_id: str) -> Iterable[tuple[tuple[int, ...], int]]:
    if generator_id == "lc560_negative_breaks_sliding_window":
        yield from _negative_breakers()
    elif generator_id == "lc560_zero_sum_subarray_invisibility":
        yield from _zero_sum_breakers()
    elif generator_id == "lc560_monotone_prefix_sliding_window_valid":
        yield from _monotone_controls()


def _negative_breakers() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for length in range(5, 10):
        for nums in itertools.product(range(-3, 5), repeat=length):
            for k in range(-3, 8):
                truth = lc560_brute_force(list(nums), k)
                if truth < 1:
                    continue
                if lc560_prefix_map(list(nums), k) != truth:
                    continue
                if lc560_sliding_window(list(nums), k) == truth:
                    continue
                yield nums, k
                yielded += 1
                if yielded >= 220:
                    return


def _zero_sum_breakers() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for length in range(5, 10):
        for nums in itertools.product(range(-3, 5), repeat=length):
            k = 0
            truth = lc560_brute_force(list(nums), k)
            if truth < 2:
                continue
            if lc560_prefix_map(list(nums), k) != truth:
                continue
            if lc560_sliding_window(list(nums), k) == truth:
                continue
            yield nums, k
            yielded += 1
            if yielded >= 220:
                return


def _monotone_controls() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for length in range(5, 9):
        for nums in itertools.product(range(1, 5), repeat=length):
            for k in range(1, 10):
                truth = lc560_brute_force(list(nums), k)
                if truth < 1:
                    continue
                if lc560_prefix_map(list(nums), k) != truth:
                    continue
                if lc560_sliding_window(list(nums), k) != truth:
                    continue
                yield nums, k
                yielded += 1
                if yielded >= 12:
                    return


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
