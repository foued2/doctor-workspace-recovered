"""LC3-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import string
import itertools
from dataclasses import dataclass
from typing import Callable, Iterable

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc3_bimaristan import LC3, GENERATORS
from doctor.adversarial.lc3_candidates import (
    lc3_conservative_window,
    lc3_count_total_unique,
    lc3_no_shrink,
    lc3_reference,
    lc3_reset_all,
)
from doctor.adversarial.lc3_ground_truth import GroundTruthDomainError, lc3_brute_force
from doctor.adversarial.lc3_oracle import LC3OracleEvaluator, evaluation_surface
from doctor.adversarial.lc3_symbol_registry import LC3_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


CandidateSolver = Callable[[str], int]


@dataclass(frozen=True)
class LC3SynthesizedInput:
    input_id: str
    s: str
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC3RejectedInput:
    input_id: str
    s: str
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC3SynthesisBatch:
    accepted: tuple[LC3SynthesizedInput, ...]
    rejected: tuple[LC3RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC3CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[str, ...]
    warnings: tuple[str, ...]


class LC3SchemaValidationError(RuntimeError):
    pass


class LC3SynthesisError(RuntimeError):
    pass


class LC3CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc3_reference", lc3_reference, True),
    ("lc3_conservative_window", lc3_conservative_window, False),
    ("lc3_no_shrink", lc3_no_shrink, False),
    ("lc3_reset_all", lc3_reset_all, False),
    ("lc3_count_total_unique", lc3_count_total_unique, False),
)


def validate_lc3_path() -> None:
    try:
        assert_valid_schema(LC3, registry=LC3_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC3SchemaValidationError(str(exc)) from exc


def synthesize_lc3_inputs() -> LC3SynthesisBatch:
    validate_lc3_path()
    evaluator = LC3OracleEvaluator()
    accepted: list[LC3SynthesizedInput] = []
    rejected: list[LC3RejectedInput] = []
    warnings: list[str] = []
    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, s in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            try:
                result = evaluator.evaluate(evaluation_surface(_candidate(s, generator.generator_id), generator.generation_constraints, generator.generator_id, input_id))
            except Exception as exc:
                raise LC3SynthesisError(f"{input_id}: {_reason(exc)}") from exc
            if result.passed:
                accepted.append(LC3SynthesizedInput(input_id, s, generator.generator_id, tuple(generator.validation_predicates)))
                generator_accepted += 1
            else:
                rejected.append(LC3RejectedInput(input_id, s, generator.generator_id, ",".join(result.violated_predicate_ids)))
                generator_rejected += 1
            if generator_accepted >= _acceptance_limit(generator.generator_id):
                break
        total = generator_accepted + generator_rejected
        rejection_rate = generator_rejected / total if total else 1.0
        if rejection_rate > 0.8:
            warnings.append(f"{generator.generator_id}: rejection rate {rejection_rate:.2%} exceeds 80%")
        if generator_accepted < 5:
            warnings.append(f"{generator.generator_id}: fewer than 5 valid candidates")
    return LC3SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc3_candidates(batch: LC3SynthesisBatch) -> tuple[LC3CandidateEvaluation, ...]:
    evaluator = LC3OracleEvaluator()
    results: list[LC3CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[str] = []
        for synthesized in batch.accepted:
            s = synthesized.s
            try:
                oracle_result = evaluator.evaluate(evaluation_surface(_candidate(s, synthesized.generator_id), synthesized.validation_predicates, synthesized.generator_id, synthesized.input_id))
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc3_brute_force(s)
                observed = solver(s)
            except GroundTruthDomainError as exc:
                raise LC3CandidateExecutionError(f"{candidate_name} {s!r}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC3CandidateExecutionError(f"{candidate_name} {s!r}: {_reason(exc)}") from exc
            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append(s)
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")
        results.append(LC3CandidateEvaluation(candidate_name, accepted_count, rejected_count, tuple(sorted(set(violated))), tuple(false_pass_inputs), batch.warnings))
    return tuple(results)


def generator_counts(batch: LC3SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(generator for family in LC3.invariant_families for manifold in family.failure_manifolds for generator in manifold.geometry_generators)


def _candidate(s: str, generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate(tuple(s), (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


def _acceptance_limit(generator_id: str) -> int:
    if generator_id == "lc3_long_repeat_collision_all_broken":
        return 220
    return 12


def _candidate_space(generator_id: str) -> Iterable[str]:
    if generator_id == "lc3_repeat_at_boundary":
        yield from _repeat_at_boundary_candidates()
    elif generator_id == "lc3_all_unique":
        yield from _all_unique_candidates()
    elif generator_id == "lc3_long_repeat_collision_all_broken":
        yield from _long_repeat_collision_all_broken()


def _long_repeat_collision_all_broken() -> Iterable[str]:
    alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    yielded = 0
    for base_tuple in itertools.product("abcde", repeat=6):
        base = "".join(base_tuple)
        if len(set(base)) == len(base):
            continue
        tail_source = "".join(ch for ch in alphabet if ch not in set(base))
        for tail_len in range(27, min(90, len(tail_source))):
            s = base + tail_source[:tail_len]
            truth = lc3_brute_force(s)
            if lc3_reference(s) != truth:
                continue
            if lc3_conservative_window(s) == truth:
                continue
            if lc3_no_shrink(s) == truth:
                continue
            if lc3_reset_all(s) == truth:
                continue
            if lc3_count_total_unique(s) == truth:
                continue
            yield s
            yielded += 1
            if yielded >= 220:
                return


def _repeat_at_boundary_candidates() -> Iterable[str]:
    seeds = (
        "abbc",
        "abbd",
        "accb",
        "accd",
        "addb",
        "addc",
        "baac",
        "baad",
        "bcca",
        "bccd",
        "bdda",
        "bddc",
    )
    for s in seeds:
        truth = lc3_brute_force(s)
        if lc3_reference(s) != truth:
            continue
        if lc3_no_shrink(s) == truth:
            continue
        yield s


def _all_unique_candidates() -> Iterable[str]:
    alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    for length in range(27, 39):
        yield alphabet[:length]


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
