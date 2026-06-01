# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC322-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc322_bimaristan import LC322
from doctor.adversarial.lc322_candidates import (
    lc322_bfs_coin_count_cutoff,
    lc322_dp,
    lc322_greedy,
    lc322_lookahead_one,
    lc322_memo_collision,
    lc322_modulo_memo_alias,
    lc322_ordering_commitment,
    lc322_reachability_lookahead,
    lc322_smallest_first,
    lc322_transition_asymmetric_forward_dp,
)
from doctor.adversarial.lc322_dimension_filters import (
    ordering_variation_sensitivity_filter,
    transition_asymmetry_sensitivity_filter,
)
from doctor.adversarial.lc322_ground_truth import GroundTruthDomainError, lc322_brute_force
from doctor.adversarial.lc322_oracle import LC322OracleEvaluator, evaluation_surface
from doctor.adversarial.lc322_symbol_registry import LC322_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


CandidateSolver = Callable[[list[int]], int]


@dataclass(frozen=True)
class LC322SynthesizedInput:
    input_id: str
    coins: tuple[int, ...]
    amount: int
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC322RejectedInput:
    input_id: str
    coins: tuple[int, ...]
    amount: int
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC322SynthesisBatch:
    accepted: tuple[LC322SynthesizedInput, ...]
    rejected: tuple[LC322RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC322CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[tuple[tuple[int, ...], int], ...]
    warnings: tuple[str, ...]


class LC322SchemaValidationError(RuntimeError):
    pass


class LC322SynthesisError(RuntimeError):
    pass


class LC322CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc322_dp", lc322_dp, True),
    ("lc322_greedy", lc322_greedy, False),
    ("lc322_smallest_first", lc322_smallest_first, False),
    ("lc322_memo_collision", lc322_memo_collision, False),
    ("lc322_lookahead_one", lc322_lookahead_one, False),
    ("lc322_bfs_coin_count_cutoff", lc322_bfs_coin_count_cutoff, False),
    ("lc322_modulo_memo_alias", lc322_modulo_memo_alias, False),
    ("lc322_reachability_lookahead", lc322_reachability_lookahead, False),
    ("lc322_ordering_commitment", lc322_ordering_commitment, False),
    ("lc322_transition_asymmetric_forward_dp", lc322_transition_asymmetric_forward_dp, False),
)


def validate_lc322_path() -> None:
    try:
        assert_valid_schema(LC322, registry=LC322_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC322SchemaValidationError(str(exc)) from exc


def synthesize_lc322_inputs() -> LC322SynthesisBatch:
    validate_lc322_path()
    evaluator = LC322OracleEvaluator()
    accepted: list[LC322SynthesizedInput] = []
    rejected: list[LC322RejectedInput] = []
    warnings: list[str] = []

    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, (coins, amount) in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            surface = evaluation_surface(
                _candidate(coins, amount, generator.generator_id),
                generator.generation_constraints,
                generator.generator_id,
                input_id,
            )
            try:
                result = evaluator.evaluate(surface)
            except Exception as exc:
                raise LC322SynthesisError(f"{input_id}: {_reason(exc)}") from exc
            if result.passed:
                accepted.append(
                    LC322SynthesizedInput(
                        input_id,
                        tuple(coins),
                        amount,
                        generator.generator_id,
                        tuple(generator.validation_predicates),
                    )
                )
                generator_accepted += 1
            else:
                rejected.append(
                    LC322RejectedInput(
                        input_id,
                        tuple(coins),
                        amount,
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

    return LC322SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc322_candidates(batch: LC322SynthesisBatch) -> tuple[LC322CandidateEvaluation, ...]:
    evaluator = LC322OracleEvaluator()
    results: list[LC322CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[tuple[tuple[int, ...], int]] = []

        for synthesized in batch.accepted:
            coins = synthesized.coins
            amount = synthesized.amount
            try:
                oracle_result = evaluator.evaluate(
                    evaluation_surface(
                        _candidate(coins, amount, synthesized.generator_id),
                        synthesized.validation_predicates,
                        synthesized.generator_id,
                        synthesized.input_id,
                    )
                )
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc322_brute_force(list(coins), amount)
                observed = solver([*list(coins), amount])
            except GroundTruthDomainError as exc:
                raise LC322CandidateExecutionError(f"{candidate_name} {list(coins)}, {amount}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC322CandidateExecutionError(f"{candidate_name} {list(coins)}, {amount}: {_reason(exc)}") from exc

            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append((coins, amount))
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")

        results.append(
            LC322CandidateEvaluation(
                candidate_name,
                accepted_count,
                rejected_count,
                tuple(sorted(set(violated))),
                tuple(false_pass_inputs),
                batch.warnings,
            )
        )

    return tuple(results)


def generator_counts(batch: LC322SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(
        generator
        for family in LC322.invariant_families
        for manifold in family.failure_manifolds
        for generator in manifold.geometry_generators
    )


def _candidate(coins: Sequence[int], amount: int, generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate(
        raw_array=tuple(coins) + (amount,),
        satisfied_generation_constraints=(),
        generation_strategy=GenerationStrategy.INTERIOR_SPIKE,
        provenance_generator_id=generator_id,
    )


def _candidate_space(generator_id: str) -> Iterable[tuple[tuple[int, ...], int]]:
    if generator_id == "lc322_greedy_trap_no_subdivision":
        yield from (
            ((3, 7, 8), 14),
            ((3, 7, 8, 17), 14),
            ((3, 7, 8, 19), 14),
            ((3, 7, 8, 20), 14),
            ((3, 7, 8, 17, 19), 14),
            ((3, 7, 8, 17, 20), 14),
            ((3, 7, 8, 19, 20), 14),
            ((3, 8, 10), 16),
            ((3, 7, 8, 10), 16),
            ((3, 8, 10, 17), 16),
            ((3, 8, 10, 19), 16),
            ((3, 7, 8, 10, 17), 16),
        )
    elif generator_id == "lc322_unreachable_greedy_confusion":
        for amount in range(11, 26, 2):
            for size in range(3, 5):
                for coins in itertools.combinations(range(2, 16, 2), size):
                    yield coins, amount
    elif generator_id == "lc322_large_coin_dominance_decoy":
        yield from (
            ((1, 3, 4), 6),
            ((1, 3, 4, 7), 6),
            ((1, 3, 4, 8), 6),
            ((1, 3, 4, 9), 6),
            ((1, 3, 4, 10), 6),
            ((1, 3, 4, 11), 6),
            ((1, 3, 4, 12), 6),
            ((1, 3, 4, 13), 6),
            ((1, 3, 4, 14), 6),
            ((1, 3, 4, 15), 6),
            ((1, 3, 4, 16), 6),
            ((1, 3, 4, 17), 6),
        )
    elif generator_id == "lc322_dual_medium_dominance":
        yield (1, 7, 10), 14
        yield (1, 7, 10), 15
        yield (1, 7, 10), 16
        yield (1, 8, 11), 16
        yield (2, 7, 10), 14
    elif generator_id == "lc322_lookahead_one_horizon_trap":
        yield from _lookahead_one_horizon_candidates()
    elif generator_id == "lc322_memo_collision_bucket_overlap":
        yield from _memo_collision_candidates()
    elif generator_id == "lc322_smallest_first_skip_small_coin":
        yield from _smallest_first_candidates()
    elif generator_id == "lc322_bfs_coin_count_cutoff":
        yield from _bfs_coin_count_cutoff_candidates()
    elif generator_id == "lc322_modulo_memo_key_alias":
        yield from _modulo_memo_key_alias_candidates()
    elif generator_id == "lc322_reachability_only_lookahead":
        yield from _reachability_only_lookahead_candidates()
    elif generator_id == "lc322_ordering_variation_sensitivity":
        yield from _ordering_variation_candidates()
    elif generator_id == "lc322_transition_asymmetry_sensitivity":
        yield from _transition_asymmetry_candidates()


def _acceptance_limit(generator_id: str) -> int:
    if generator_id in {
        "lc322_lookahead_one_horizon_trap",
        "lc322_memo_collision_bucket_overlap",
        "lc322_smallest_first_skip_small_coin",
        "lc322_bfs_coin_count_cutoff",
        "lc322_modulo_memo_key_alias",
        "lc322_reachability_only_lookahead",
        "lc322_ordering_variation_sensitivity",
        "lc322_transition_asymmetry_sensitivity",
    }:
        return 220
    return 12


def _lookahead_one_horizon_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yield from _memo_and_lookahead_collision_candidates()


def _memo_collision_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yield from _memo_and_lookahead_collision_candidates()


def _smallest_first_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yield from _memo_and_lookahead_collision_candidates()


def _bfs_coin_count_cutoff_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for amount in range(8, 31):
        for size in range(2, 7):
            for coins in itertools.combinations(range(1, 16), size):
                truth = lc322_brute_force(list(coins), amount)
                if truth == -1 or truth <= len(coins):
                    continue
                if lc322_bfs_coin_count_cutoff([*list(coins), amount]) == truth:
                    continue
                yield coins, amount
                yielded += 1
                if yielded >= 220:
                    return


def _modulo_memo_key_alias_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for amount in range(4, 31):
        for size in range(2, 7):
            for coins in itertools.combinations(range(1, 16), size):
                truth = lc322_brute_force(list(coins), amount)
                if truth == -1:
                    continue
                if lc322_modulo_memo_alias([*list(coins), amount]) == truth:
                    continue
                yield coins, amount
                yielded += 1
                if yielded >= 220:
                    return


def _reachability_only_lookahead_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for amount in range(6, 31):
        for size in range(3, 7):
            for coins in itertools.combinations(range(1, 16), size):
                truth = lc322_brute_force(list(coins), amount)
                observed = lc322_reachability_lookahead([*list(coins), amount])
                if truth == -1 or observed == -1 or observed <= truth:
                    continue
                yield coins, amount
                yielded += 1
                if yielded >= 220:
                    return


def _ordering_variation_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for amount in range(4, 31):
        for size in range(2, 7):
            for coins in itertools.permutations(range(1, 16), size):
                if len(set(coins)) != len(coins):
                    continue
                context = {"coins": list(coins), "amount": amount}
                try:
                    if not ordering_variation_sensitivity_filter(context):
                        continue
                    if lc322_dp([*list(coins), amount]) != lc322_brute_force(list(coins), amount):
                        continue
                except Exception:
                    continue
                yield coins, amount
                yielded += 1
                if yielded >= 220:
                    return


def _transition_asymmetry_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    amount = 2
    for size in range(2, 7):
        for tail in itertools.combinations(range(3, 16), size - 2):
            coins = tuple(sorted((1, 2, *tail), reverse=True))
            context = {"coins": list(coins), "amount": amount}
            try:
                if not transition_asymmetry_sensitivity_filter(context):
                    continue
                if lc322_dp([*list(coins), amount]) != lc322_brute_force(list(coins), amount):
                    continue
            except Exception:
                continue
            yield coins, amount
            yielded += 1
            if yielded >= 220:
                return


def _memo_and_lookahead_collision_candidates() -> Iterable[tuple[tuple[int, ...], int]]:
    yielded = 0
    for amount in range(6, 31):
        for size in range(2, 6):
            for coins in itertools.combinations(range(1, 16), size):
                truth = lc322_brute_force(list(coins), amount)
                if truth == -1:
                    continue
                if lc322_memo_collision([*list(coins), amount]) == truth:
                    continue
                if lc322_lookahead_one([*list(coins), amount]) == truth:
                    continue
                if lc322_smallest_first([*list(coins), amount]) == truth:
                    continue
                yield coins, amount
                yielded += 1
                if yielded >= 220:
                    return


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
