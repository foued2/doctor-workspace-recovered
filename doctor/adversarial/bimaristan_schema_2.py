"""LC79-native synthesis/evaluation path for Bimaristan candidates."""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from doctor.adversarial.bimaristan_schema import GeometryGenerator
from doctor.adversarial.lc79_bimaristan import LC79, GENERATORS
from doctor.adversarial.lc79_candidates import lc79_no_restore, lc79_reference, lc79_reuse_cells
from doctor.adversarial.lc79_ground_truth import GroundTruthDomainError, lc79_brute_force
from doctor.adversarial.lc79_oracle import LC79OracleEvaluator, evaluation_surface
from doctor.adversarial.lc79_symbol_registry import LC79_SYMBOL_REGISTRY
from doctor.adversarial.schema_validator import SchemaValidationError, assert_valid_schema
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


Board = tuple[tuple[str, ...], ...]
CandidateSolver = Callable[[list[list[str]], str], bool]


@dataclass(frozen=True)
class LC79SynthesizedInput:
    input_id: str
    board: Board
    word: str
    generator_id: str
    validation_predicates: tuple[object, ...]


@dataclass(frozen=True)
class LC79RejectedInput:
    input_id: str
    board: Board
    word: str
    generator_id: str
    reason: str


@dataclass(frozen=True)
class LC79SynthesisBatch:
    accepted: tuple[LC79SynthesizedInput, ...]
    rejected: tuple[LC79RejectedInput, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LC79CandidateEvaluation:
    candidate_name: str
    accepted_count: int
    rejected_count: int
    violated_predicate_ids: tuple[str, ...]
    false_pass_inputs: tuple[tuple[Board, str], ...]
    warnings: tuple[str, ...]


class LC79SchemaValidationError(RuntimeError):
    pass


class LC79SynthesisError(RuntimeError):
    pass


class LC79CandidateExecutionError(RuntimeError):
    pass


CANDIDATES: tuple[tuple[str, CandidateSolver, bool], ...] = (
    ("lc79_reference", lc79_reference, True),
    ("lc79_no_restore", lc79_no_restore, False),
    ("lc79_reuse_cells", lc79_reuse_cells, False),
)


def validate_lc79_path() -> None:
    try:
        assert_valid_schema(LC79, registry=LC79_SYMBOL_REGISTRY)
    except SchemaValidationError as exc:
        raise LC79SchemaValidationError(str(exc)) from exc


def synthesize_lc79_inputs() -> LC79SynthesisBatch:
    validate_lc79_path()
    evaluator = LC79OracleEvaluator()
    accepted: list[LC79SynthesizedInput] = []
    rejected: list[LC79RejectedInput] = []
    warnings: list[str] = []
    for generator in _generators():
        generator_accepted = 0
        generator_rejected = 0
        for index, (board, word) in enumerate(_candidate_space(generator.generator_id), start=1):
            input_id = f"{generator.generator_id}_{index:03d}"
            try:
                result = evaluator.evaluate(evaluation_surface(_candidate(board, word, generator.generator_id), generator.generation_constraints, generator.generator_id, input_id))
            except Exception as exc:
                raise LC79SynthesisError(f"{input_id}: {_reason(exc)}") from exc
            board_tuple = tuple(tuple(row) for row in board)
            if result.passed:
                accepted.append(LC79SynthesizedInput(input_id, board_tuple, word, generator.generator_id, tuple(generator.validation_predicates)))
                generator_accepted += 1
            else:
                rejected.append(LC79RejectedInput(input_id, board_tuple, word, generator.generator_id, ",".join(result.violated_predicate_ids)))
                generator_rejected += 1
            if generator_accepted >= _acceptance_limit(generator.generator_id):
                break
        total = generator_accepted + generator_rejected
        rejection_rate = generator_rejected / total if total else 1.0
        if rejection_rate > 0.8:
            warnings.append(f"{generator.generator_id}: rejection rate {rejection_rate:.2%} exceeds 80%")
        if generator_accepted < 5:
            warnings.append(f"{generator.generator_id}: fewer than 5 valid candidates")
    return LC79SynthesisBatch(tuple(accepted), tuple(rejected), tuple(warnings))


def evaluate_lc79_candidates(batch: LC79SynthesisBatch) -> tuple[LC79CandidateEvaluation, ...]:
    evaluator = LC79OracleEvaluator()
    results: list[LC79CandidateEvaluation] = []
    for candidate_name, solver, should_pass_all in CANDIDATES:
        accepted_count = 0
        rejected_count = 0
        violated: list[str] = []
        false_pass_inputs: list[tuple[Board, str]] = []
        for synthesized in batch.accepted:
            board = synthesized.board
            word = synthesized.word
            if not should_pass_all:
                if candidate_name == "lc79_no_restore" and synthesized.generator_id != "lc79_backtrack_required":
                    continue
                if candidate_name == "lc79_reuse_cells" and synthesized.generator_id != "lc79_reuse_trap":
                    continue
            try:
                oracle_result = evaluator.evaluate(evaluation_surface(_candidate(board, word, synthesized.generator_id), synthesized.validation_predicates, synthesized.generator_id, synthesized.input_id))
                if not oracle_result.passed:
                    violated.extend(oracle_result.violated_predicate_ids)
                    rejected_count += 1
                    continue
                truth = lc79_brute_force(_board_list(board), word)
                observed = solver(_board_list(board), word)
            except GroundTruthDomainError as exc:
                raise LC79CandidateExecutionError(f"{candidate_name} board={board}, word={word}: {_reason(exc)}") from exc
            except Exception as exc:
                raise LC79CandidateExecutionError(f"{candidate_name} board={board}, word={word}: {_reason(exc)}") from exc
            if observed == truth:
                accepted_count += 1
                if not should_pass_all:
                    false_pass_inputs.append((board, word))
            else:
                rejected_count += 1
                violated.append(f"{candidate_name}:solver_output_mismatch")
        results.append(LC79CandidateEvaluation(candidate_name, accepted_count, rejected_count, tuple(sorted(set(violated))), tuple(false_pass_inputs), batch.warnings))
    return tuple(results)


def generator_counts(batch: LC79SynthesisBatch) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for generator in _generators():
        accepted = sum(1 for item in batch.accepted if item.generator_id == generator.generator_id)
        rejected = sum(1 for item in batch.rejected if item.generator_id == generator.generator_id)
        rows.append((generator.generator_id, accepted, rejected))
    return tuple(rows)


def _generators() -> tuple[GeometryGenerator, ...]:
    return tuple(generator for family in LC79.invariant_families for manifold in family.failure_manifolds for generator in manifold.geometry_generators)


def _candidate(board: Sequence[Sequence[str]], word: str, generator_id: str) -> SynthesizedCandidate:
    return SynthesizedCandidate((tuple(tuple(row) for row in board), word), (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


def _acceptance_limit(generator_id: str) -> int:
    return 120


_MAX_YIELD = 120
_BOARD_CONFIGS = [
    (2, 3, "AB"), (3, 2, "AB"),
    (2, 4, "AB"), (4, 2, "AB"),
    (3, 3, "AB"),
    (4, 3, "AB"), (3, 4, "AB"),
]
_RANDOM_COUNT = 2000


def _board_valid_words(board: list[list[str]], max_len: int) -> set[str]:
    rows, cols = len(board), len(board[0])
    words: set[str] = set()

    def dfs(r: int, c: int, visited: set[tuple[int, int]], chars: list[str]) -> None:
        if len(chars) >= 3:
            words.add("".join(chars))
        if len(chars) >= max_len:
            return
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                visited.add((nr, nc))
                chars.append(board[nr][nc])
                dfs(nr, nc, visited, chars)
                chars.pop()
                visited.discard((nr, nc))

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, {(r, c)}, [board[r][c]])
    return words


def _board_reuse_words(board: list[list[str]], max_len: int) -> set[str]:
    rows, cols = len(board), len(board[0])
    words: set[str] = set()

    def dfs(r: int, c: int, chars: list[str]) -> None:
        if len(chars) >= 3:
            words.add("".join(chars))
        if len(chars) >= max_len:
            return
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                chars.append(board[nr][nc])
                dfs(nr, nc, chars)
                chars.pop()

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, [board[r][c]])
    return words


def _gen_exhaustive_boards(rows: int, cols: int, alphabet: str) -> Iterable[list[list[str]]]:
    for cells in itertools.product(alphabet, repeat=rows * cols):
        yield [list(cells[i * cols:(i + 1) * cols]) for i in range(rows)]


def _gen_random_boards(rows: int, cols: int, alphabet: str, count: int) -> Iterable[list[list[str]]]:
    for _ in range(count):
        yield [[random.choice(alphabet) for _ in range(cols)] for _ in range(rows)]


def _candidate_space(generator_id: str) -> Iterable[tuple[list[list[str]], str]]:
    if generator_id == "lc79_backtrack_required":
        yield from _no_restore_breakers()
    elif generator_id == "lc79_reuse_trap":
        yield from _reuse_breakers()


def _no_restore_breakers() -> Iterable[tuple[list[list[str]], str]]:
    yielded = 0
    for board, word in GENERATORS["backtrack_required"]():
        if _is_no_restore_breaker(board, word):
            yield _board_list(board), word
            yielded += 1
    for rows, cols, alphabet in _BOARD_CONFIGS:
        if rows * cols > 16:
            continue
        max_word_len = min(10, rows * cols)
        exhaustive_max = 300
        board_count = 0
        for board in _gen_exhaustive_boards(rows, cols, alphabet):
            board_count += 1
            if board_count > exhaustive_max:
                break
            if yielded >= _MAX_YIELD:
                return
            found = 0
            for word in _board_valid_words(board, max_word_len):
                if _is_no_restore_breaker(board, word):
                    yield _board_list(board), word
                    yielded += 1
                    found += 1
                    if found >= 5 or yielded >= _MAX_YIELD:
                        break
        if yielded >= _MAX_YIELD:
            return
    for rows, cols, alphabet in _BOARD_CONFIGS:
        if rows * cols > 16:
            continue
        max_word_len = min(10, rows * cols)
        for board in _gen_random_boards(rows, cols, alphabet, _RANDOM_COUNT):
            if yielded >= _MAX_YIELD:
                return
            found = 0
            for word in _board_valid_words(board, max_word_len):
                if _is_no_restore_breaker(board, word):
                    yield _board_list(board), word
                    yielded += 1
                    found += 1
                    if found >= 5 or yielded >= _MAX_YIELD:
                        break
        if yielded >= _MAX_YIELD:
            return


def _reuse_breakers() -> Iterable[tuple[list[list[str]], str]]:
    yielded = 0
    for board, word in GENERATORS["reuse_trap"]():
        if _is_reuse_breaker(board, word):
            yield _board_list(board), word
            yielded += 1
    for rows, cols, alphabet in _BOARD_CONFIGS:
        if rows * cols > 16:
            continue
        max_word_len = 6
        exhaustive_max = 300
        board_count = 0
        for board in _gen_exhaustive_boards(rows, cols, alphabet):
            board_count += 1
            if board_count > exhaustive_max:
                break
            if yielded >= _MAX_YIELD:
                return
            found = 0
            for word in _board_reuse_words(board, max_word_len):
                if _is_reuse_breaker(board, word):
                    yield _board_list(board), word
                    yielded += 1
                    found += 1
                    if found >= 5 or yielded >= _MAX_YIELD:
                        break
        if yielded >= _MAX_YIELD:
            return
    for rows, cols, alphabet in _BOARD_CONFIGS:
        if rows * cols > 16:
            continue
        max_word_len = 6
        for board in _gen_random_boards(rows, cols, alphabet, _RANDOM_COUNT):
            if yielded >= _MAX_YIELD:
                return
            found = 0
            for word in _board_reuse_words(board, max_word_len):
                if _is_reuse_breaker(board, word):
                    yield _board_list(board), word
                    yielded += 1
                    found += 1
                    if found >= 5 or yielded >= _MAX_YIELD:
                        break
        if yielded >= _MAX_YIELD:
            return


def _is_no_restore_breaker(board: Sequence[Sequence[str]], word: str) -> bool:
    return (
        lc79_brute_force(_board_list(board), word)
        and lc79_reference(_board_list(board), word)
        and not lc79_no_restore(_board_list(board), word)
    )


def _is_reuse_breaker(board: Sequence[Sequence[str]], word: str) -> bool:
    return (
        not lc79_brute_force(_board_list(board), word)
        and not lc79_reference(_board_list(board), word)
        and lc79_reuse_cells(_board_list(board), word)
    )


def _board_list(board: Sequence[Sequence[str]]) -> list[list[str]]:
    return [list(row) for row in board]


def _reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
