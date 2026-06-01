# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC33 Bimaristan manifolds — Search in Rotated Sorted Array."""
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
from doctor.adversarial.lc33_candidates import lc33_always_left, lc33_inverted_condition, lc33_reference
from doctor.adversarial.lc33_ground_truth import lc33_brute_force


def generate_target_in_rotated_half():
    seeds = [
        ([4,5,6,7,0,1,2], 0),
        ([4,5,6,7,0,1,2], 1),
        ([4,5,6,7,0,1,2], 2),
        ([6,7,0,1,2,4,5], 0),
        ([6,7,0,1,2,4,5], 1),
        ([3,4,5,6,7,0,1,2], 0),
        ([3,4,5,6,7,0,1,2], 1),
        ([5,6,7,8,9,1,2,3], 1),
        ([5,6,7,8,9,1,2,3], 2),
        ([5,6,7,8,9,1,2,3], 3),
        ([10,12,14,1,3,5,7], 1),
        ([10,12,14,1,3,5,7], 3),
        ([10,12,14,1,3,5,7], 5),
        ([2,3,4,5,6,7,0,1], 0),
        ([2,3,4,5,6,7,0,1], 1),
        ([4,5,6,7,0,1,2], 3),
    ]
    yield from _unique_cases(itertools.chain(
        _filtered_unique(seeds, _is_always_left_breaker),
        _search_always_left_breakers(limit=160),
    ))


def generate_target_near_pivot():
    seeds = [
        ([2,3,0,1], 3),
        ([2,3,0,1], 0),
        ([3,4,5,1,2], 5),
        ([3,4,5,1,2], 1),
        ([2,3,4,5,6,1], 1),
        ([2,3,4,5,6,1], 6),
        ([1,2,3,4,5,6], 1),
        ([6,1,2,3,4,5], 1),
        ([6,1,2,3,4,5], 6),
        ([2,1], 1),
        ([2,1], 2),
        ([4,5,6,7,0,1,2], 7),
        ([4,5,6,7,0,1,2], 4),
        ([3,1,2], 1),
        ([3,1,2], 2),
        ([3,1,2], 3),
    ]
    yield from _unique_cases(itertools.chain(
        _filtered_unique(seeds, _is_inverted_condition_breaker),
        _search_inverted_condition_breakers(limit=160),
    ))


def _search_always_left_breakers(limit: int) -> Iterable[tuple[list[int], int]]:
    yielded = 0
    for nums in _rotated_arrays(min_len=4, max_len=20):
        pivot = _rotation_pivot(nums)
        if pivot <= 0:
            continue
        for target in nums[pivot:]:
            if _is_always_left_breaker(nums, target):
                yield list(nums), target
                yielded += 1
                if yielded >= limit:
                    return


def _search_inverted_condition_breakers(limit: int) -> Iterable[tuple[list[int], int]]:
    yielded = 0
    for nums in _rotated_arrays(min_len=2, max_len=20):
        pivot = _rotation_pivot(nums)
        candidate_targets = _near_pivot_targets(nums, pivot)
        for target in candidate_targets:
            if _is_inverted_condition_breaker(nums, target):
                yield list(nums), target
                yielded += 1
                if yielded >= limit:
                    return


def _rotated_arrays(min_len: int, max_len: int) -> Iterable[list[int]]:
    for length in range(min_len, max_len + 1):
        base = list(range(length))
        for pivot in range(1, length):
            yield base[pivot:] + base[:pivot]


def _near_pivot_targets(nums: Sequence[int], pivot: int) -> tuple[int, ...]:
    if not nums:
        return ()
    indexes = {
        0,
        len(nums) - 1,
        max(0, pivot - 2),
        max(0, pivot - 1),
        min(len(nums) - 1, pivot),
        min(len(nums) - 1, pivot + 1),
    }
    return tuple(nums[index] for index in sorted(indexes))


def _filtered_unique(
    cases: Iterable[tuple[Sequence[int], int]],
    predicate,
) -> Iterable[tuple[list[int], int]]:
    seen: set[tuple[tuple[int, ...], int]] = set()
    for nums, target in cases:
        key = (tuple(nums), target)
        if key in seen or not predicate(nums, target):
            continue
        seen.add(key)
        yield list(nums), target


def _unique_cases(cases: Iterable[tuple[Sequence[int], int]]) -> Iterable[tuple[list[int], int]]:
    seen: set[tuple[tuple[int, ...], int]] = set()
    for nums, target in cases:
        key = (tuple(nums), target)
        if key in seen:
            continue
        seen.add(key)
        yield list(nums), target


def _rotation_pivot(nums: Sequence[int]) -> int:
    for index in range(1, len(nums)):
        if nums[index] < nums[index - 1]:
            return index
    return 0


def _target_in_right_rotated_portion(nums: Sequence[int], target: int) -> bool:
    pivot = _rotation_pivot(nums)
    truth = lc33_brute_force(list(nums), target)
    return pivot > 0 and truth >= pivot


def _is_always_left_breaker(nums: Sequence[int], target: int) -> bool:
    truth = lc33_brute_force(list(nums), target)
    return (
        truth != -1
        and _target_in_right_rotated_portion(nums, target)
        and lc33_reference(list(nums), target) == truth
        and lc33_always_left(list(nums), target) != truth
    )


def _is_inverted_condition_breaker(nums: Sequence[int], target: int) -> bool:
    truth = lc33_brute_force(list(nums), target)
    return (
        truth != -1
        and lc33_reference(list(nums), target) == truth
        and lc33_inverted_condition(list(nums), target) != truth
    )


GENERATORS = {
    "target_in_rotated_half": generate_target_in_rotated_half,
    "target_near_pivot": generate_target_near_pivot,
}


LC33 = BimaristanSchema(
    problem_structure=ProblemStructure(
        problem_id="lc33_search_rotated_sorted_array",
        kind="optimization",
        input_symbols=(Symbol("nums", "sequence_integer"), Symbol("target", "integer")),
        output_symbol=Symbol("index", "integer"),
        objective_predicate=RelationConstraint("ground_truth_index(nums, target)", ">=", "-1"),
    ),
    invariant_families=(
        InvariantFamily(
            family_id="search_space_pruning_failures",
            invariants=(
                Invariant(
                    invariant_id="lc33_binary_search_finds_target_in_rotated_array",
                    falsifiable_predicates=(
                        RelationConstraint("reference_agrees_with_truth(nums, target)", "==", "True"),
                    ),
                    violation_predicates=(
                        RelationConstraint("always_left_diverges(nums, target)", "==", "True"),
                        RelationConstraint("inverted_condition_diverges(nums, target)", "==", "True"),
                    ),
                ),
            ),
            failure_manifolds=(
                FailureManifold(
                    manifold_id="target_in_rotated_half",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc33_binary_search_finds_target_in_rotated_array",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc33_target_in_rotated_half",
                            generation_constraints=(
                                RelationConstraint("target_in_right_rotated_portion(nums, target)", "==", "True"),
                                RelationConstraint("array_len(nums)", ">=", "4"),
                                RelationConstraint("array_len(nums)", "<=", "20"),
                            ),
                            validation_predicates=(
                                RelationConstraint("always_left_diverges(nums, target)", "==", "True"),
                                RelationConstraint("reference_agrees_with_truth(nums, target)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
                FailureManifold(
                    manifold_id="target_near_pivot",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc33_binary_search_finds_target_in_rotated_array",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc33_target_near_pivot",
                            generation_constraints=(
                                RelationConstraint("target_exists(nums, target)", "==", "True"),
                                RelationConstraint("array_len(nums)", ">=", "2"),
                                RelationConstraint("array_len(nums)", "<=", "20"),
                            ),
                            validation_predicates=(
                                RelationConstraint("inverted_condition_diverges(nums, target)", "==", "True"),
                                RelationConstraint("reference_agrees_with_truth(nums, target)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
