"""LC79 Bimaristan manifolds — Word Search."""
# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Not on paper critical path. See git log for reconstruction history.
from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence

from doctor.adversarial.bimaristan_schema import (
    BimaristanSchema,
    FailureManifold,
    GeometryGenerator,
    Invariant,
    InvariantFamily,
    ProblemStructure,
    RelationConstraint,
    Symbol,
)
from doctor.adversarial.lc79_candidates import lc79_no_restore, lc79_reference, lc79_reuse_cells
from doctor.adversarial.lc79_ground_truth import lc79_brute_force


def generate_backtrack_required():
    seeds = [
        ([["C", "A", "A"], ["A", "A", "A"], ["B", "C", "D"]], "AAB"),
        ([["A", "A", "A"], ["A", "A", "B"]], "AABA"),
        ([["A", "A", "A"], ["A", "A", "B"]], "AAAABA"),
        ([["A", "A", "A"], ["A", "A", "B"]], "AABAA"),
        ([["A", "A", "A"], ["A", "B", "A"]], "AAAB"),
    ]
    yield from _unique_cases(itertools.chain(
        _filtered_unique(seeds, _is_no_restore_breaker),
        _search_no_restore_breakers(limit=160),
    ))


def generate_reuse_trap():
    seeds = [
        ([["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCB"),
        ([["A", "A"]], "AAA"),
        ([["a", "a"]], "aaa"),
        ([["A", "A", "A"], ["A", "A", "B"]], "ABABAA"),
        ([["A", "A", "A"], ["A", "A", "B"]], "ABABA"),
        ([["A", "A", "A"], ["A", "A", "B"]], "ABABAB"),
        ([["A", "A", "A"], ["A", "A", "B"]], "BAB"),
        ([["A", "A", "A"], ["A", "A", "B"]], "BABA"),
    ]
    yield from _unique_cases(itertools.chain(
        _filtered_unique(seeds, _is_reuse_breaker),
        _search_reuse_breakers(limit=160),
    ))


_BOARD_CONFIGS = (
    (1, 2, "AB"),
    (2, 2, "AB"),
    (2, 3, "AB"),
    (3, 2, "AB"),
    (3, 3, "AB"),
)


def _search_no_restore_breakers(limit: int) -> Iterable[tuple[list[list[str]], str]]:
    yielded = 0
    for rows, cols, alphabet in _BOARD_CONFIGS:
        if rows == 1:
            continue
        max_word_len = min(10, rows * cols)
        for board in _gen_exhaustive_boards(rows, cols, alphabet):
            found_for_board = 0
            for word in sorted(_board_valid_words(board, max_word_len), key=lambda item: (len(item), item)):
                if _is_no_restore_breaker(board, word):
                    yield _copy_board(board), word
                    yielded += 1
                    found_for_board += 1
                    if yielded >= limit:
                        return
                    if found_for_board >= 8:
                        break


def _search_reuse_breakers(limit: int) -> Iterable[tuple[list[list[str]], str]]:
    yielded = 0
    for rows, cols, alphabet in _BOARD_CONFIGS:
        max_word_len = min(6, rows * cols + 2)
        for board in _gen_exhaustive_boards(rows, cols, alphabet):
            found_for_board = 0
            reuse_only_words = _board_reuse_words(board, max_word_len) - _board_valid_words(board, max_word_len)
            for word in sorted(reuse_only_words, key=lambda item: (len(item), item)):
                if _is_reuse_breaker(board, word):
                    yield _copy_board(board), word
                    yielded += 1
                    found_for_board += 1
                    if yielded >= limit:
                        return
                    if found_for_board >= 8:
                        break


def _filtered_unique(
    cases: Iterable[tuple[Sequence[Sequence[str]], str]],
    predicate,
) -> Iterable[tuple[list[list[str]], str]]:
    seen: set[tuple[tuple[tuple[str, ...], ...], str]] = set()
    for board, word in cases:
        key = (tuple(tuple(row) for row in board), word)
        if key in seen or not predicate(board, word):
            continue
        seen.add(key)
        yield _copy_board(board), word


def _unique_cases(cases: Iterable[tuple[Sequence[Sequence[str]], str]]) -> Iterable[tuple[list[list[str]], str]]:
    seen: set[tuple[tuple[tuple[str, ...], ...], str]] = set()
    for board, word in cases:
        key = (tuple(tuple(row) for row in board), word)
        if key in seen:
            continue
        seen.add(key)
        yield _copy_board(board), word


def _gen_exhaustive_boards(rows: int, cols: int, alphabet: str) -> Iterable[list[list[str]]]:
    for cells in itertools.product(alphabet, repeat=rows * cols):
        yield [list(cells[i * cols:(i + 1) * cols]) for i in range(rows)]


def _board_valid_words(board: Sequence[Sequence[str]], max_len: int) -> set[str]:
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


def _board_reuse_words(board: Sequence[Sequence[str]], max_len: int) -> set[str]:
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


def _is_no_restore_breaker(board: Sequence[Sequence[str]], word: str) -> bool:
    return (
        lc79_brute_force(_copy_board(board), word)
        and lc79_reference(_copy_board(board), word)
        and not lc79_no_restore(_copy_board(board), word)
    )


def _is_reuse_breaker(board: Sequence[Sequence[str]], word: str) -> bool:
    return (
        not lc79_brute_force(_copy_board(board), word)
        and not lc79_reference(_copy_board(board), word)
        and lc79_reuse_cells(_copy_board(board), word)
    )


def _copy_board(board: Sequence[Sequence[str]]) -> list[list[str]]:
    return [list(row) for row in board]


GENERATORS = {
    "backtrack_required": generate_backtrack_required,
    "reuse_trap": generate_reuse_trap,
}


LC79 = BimaristanSchema(
    problem_structure=ProblemStructure(
        problem_id="lc79_word_search",
        kind="optimization",
        input_symbols=(Symbol("board", "sequence_integer"), Symbol("word", "sequence_integer")),
        output_symbol=Symbol("exists", "boolean"),
        objective_predicate=RelationConstraint("ground_truth_exists(board, word)", "==", "True"),
    ),
    invariant_families=(
        InvariantFamily(
            family_id="search_space_pruning_failures",
            invariants=(
                Invariant(
                    invariant_id="lc79_dfs_backtracking_finds_word_if_exists",
                    falsifiable_predicates=(
                        RelationConstraint("reference_agrees_with_truth(board, word)", "==", "True"),
                    ),
                    violation_predicates=(
                        RelationConstraint("no_restore_diverges(board, word)", "==", "True"),
                        RelationConstraint("reuse_cells_diverges(board, word)", "==", "True"),
                    ),
                ),
            ),
            failure_manifolds=(
                FailureManifold(
                    manifold_id="backtrack_required",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc79_dfs_backtracking_finds_word_if_exists",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc79_backtrack_required",
                            generation_constraints=(
                                RelationConstraint("ground_truth_exists(board, word)", "==", "True"),
                                RelationConstraint("board_rows(board)", ">=", "2"),
                                RelationConstraint("board_rows(board)", "<=", "4"),
                                RelationConstraint("word_len(word)", ">=", "3"),
                                RelationConstraint("word_len(word)", "<=", "10"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(board, word)", "==", "True"),
                                RelationConstraint("no_restore_diverges(board, word)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
                FailureManifold(
                    manifold_id="reuse_trap",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc79_dfs_backtracking_finds_word_if_exists",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc79_reuse_trap",
                            generation_constraints=(
                                RelationConstraint("ground_truth_exists(board, word)", "==", "False"),
                                RelationConstraint("board_rows(board)", ">=", "1"),
                                RelationConstraint("board_rows(board)", "<=", "4"),
                                RelationConstraint("word_len(word)", ">=", "3"),
                                RelationConstraint("word_len(word)", "<=", "6"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(board, word)", "==", "True"),
                                RelationConstraint("reuse_cells_diverges(board, word)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
