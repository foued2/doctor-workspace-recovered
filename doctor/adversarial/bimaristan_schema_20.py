# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC20-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Iterable

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc20_bimaristan import LC20, GENERATORS
from doctor.adversarial.lc20_candidates import lc20_last_char_check, lc20_no_empty_check, lc20_reference
from doctor.adversarial.lc20_ground_truth import GroundTruthDomainError, lc20_brute_force
from doctor.adversarial.lc20_oracle import LC20OracleEvaluator, evaluation_surface
from doctor.adversarial.lc20_symbol_registry import LC20_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


CandidateSolver = Callable[[str], bool]


@dataclass(frozen=True)
class LC20SynthesizedInput:
    input_id: str
    s: str
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC20RejectedInput:
    input_id: str
    s: str
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC20SynthesisBatch:
    accepted: tuple[LC20SynthesizedInput, ...]
    rejected: tuple[LC20RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC20CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[str, ...]
    warnings: tuple[str, ...]


class LC20SchemaValidationError(RuntimeError):
    pass


class LC20SynthesisError(RuntimeError):
    pass


class LC20CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc20_reference", lc20_reference, True),
    ("lc20_no_empty_check", lc20_no_empty_check, False),
    ("lc20_last_char_check", lc20_last_char_check, False),
)


def validate_lc20_path() -> None:
    try:
        assert_valid_schema(LC20, registry=LC20_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC20SchemaValidationError(str(exc)) from exc


def synthesize_lc20_inputs() -> LC20SynthesisBatch:
    validate_lc20_path()
    evaluator = LC20OracleEvaluator()
    accepted: list[LC20SynthesizedInput] = []
    rejected: list[LC20RejectedInput] = []
    warnings: list[str] = []

    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, s in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            try:
                result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(s, generator.generator_id),
                        generator.generation_constraints,
                        generator.generator_id,
                        input_id,
                    )
                )
            except Exception as exc:
                raise LC20SynthesisError(f"{input_id}: {_reason(exc)}") from exc
            if result.passed:
                accepted.append(LC20SynthesizedInput(input_id, s, generator.generator_id, tuple(generator.validation_predicates)))
                generator_accepted += 1
            else:
                rejected.append(LC20RejectedInput(input_id, s, generator.generator_id, ",".join(result.violated_predicate_ids)))
                generator_rejected += 1
            if generator_accepted >= _acceptance_limit(generator.generator_id):
                break

        total = generator_accepted + generator_rejected
        rejection_rate = generator_rejected / total if total else 1.0
        if rejection_rate > 0.8:
            warnings.append(f"{generator.generator_id}: rejection rate {rejection_rate:.2%} exceeds 80%")
        if generator_accepted < 5:
            warnings.append(f"{generator.generator_id}: fewer than 5 valid candidates")

    return LC20SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc20_candidates(batch: LC20SynthesisBatch) -> tuple[LC20CandidateEvaluation, ...]:
    evaluator = LC20OracleEvaluator()
    results: list[LC20CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[str] = []

        for synthesized in batch.accepted:
            s = synthesized.s
            try:
                oracle_result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(s, synthesized.generator_id),
                        synthesized.validation_predicates,
                        synthesized.generator_id,
                        synthesized.input_id,
                    )
                )
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc20_brute_force(s)
                try:
                    observed = solver(s)
                except Exception as exc:
                    rejected_count += 1
                    violated.append(f"{candidate_name}:solver_exception:{type(exc).__name__}")
                    continue
            except GroundTruthDomainError as exc:
                raise LC20CandidateExecutionError(f"{candidate_name} {s!r}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC20CandidateExecutionError(f"{candidate_name} {s!r}: {_reason(exc)}") from exc

            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append(s)
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")

        results.append(
            LC20CandidateEvaluation(
                candidate_name,
                accepted_count,
                rejected_count,
                tuple(sorted(set(violated))),
                tuple(false_pass_inputs),
                batch.warnings,
            )
        )

    return tuple(results)


def generator_counts(batch: LC20SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(
        generator
        for family in LC20.invariant_families
        for manifold in family.failure_manifolds
        for generator in manifold.geometry_generators
    )


def _candidate(s: str, generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate(
        raw_array=tuple(s),
        satisfied_generation_constraints=(),
        generation_strategy=GenerationStrategy.INTERIOR_SPIKE,
        provenance_generator_id=generator_id,
    )


def _acceptance_limit(generator_id: str) -> int:
    if generator_id == "lc20_overclosed_matching_outer":
        return 220
    return 12


def _candidate_space(generator_id: str) -> Iterable[str]:
    if generator_id == "lc20_empty_stack_trap":
        yield from GENERATORS["empty_stack_trap"]()
    elif generator_id == "lc20_mismatched_outer":
        yield from _mismatched_outer_candidates()
    elif generator_id == "lc20_overclosed_matching_outer":
        yield from _overclosed_matching_outer_candidates()


def _overclosed_matching_outer_candidates() -> Iterable[str]:
    alphabet = "()[]{}"
    yielded = 0
    for length in range(3, 10):
        for chars in itertools.product(alphabet, repeat=length):
            s = "".join(chars)
            if lc20_brute_force(s):
                continue
            try:
                lc20_no_empty_check(s)
                no_empty_bad = False
            except Exception:
                no_empty_bad = True
            if not no_empty_bad:
                continue
            if lc20_last_char_check(s) == lc20_brute_force(s):
                continue
            yield s
            yielded += 1
            if yielded >= 220:
                return


def _mismatched_outer_candidates() -> Iterable[str]:
    alphabet = "()[]{}"
    yielded = 0
    for length in range(4, 10):
        for chars in itertools.product(alphabet, repeat=length):
            s = "".join(chars)
            if not _outer_brackets_match(s):
                continue
            if lc20_brute_force(s):
                continue
            if not lc20_last_char_check(s):
                continue
            yield s
            yielded += 1
            if yielded >= 12:
                return


def _outer_brackets_match(s: str) -> bool:
    if len(s) < 2:
        return False
    pairs = {"(": ")", "{": "}", "[": "]"}
    return s[0] in pairs and s[-1] == pairs[s[0]]


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
