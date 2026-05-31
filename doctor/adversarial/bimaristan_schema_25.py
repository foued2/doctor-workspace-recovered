"""LC3 Bimaristan manifolds — Longest Substring Without Repeating Characters."""
from __future__ import annotations

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

import random
import string


def generate_repeat_at_boundary():
    inputs = []
    charset = "abcdefghij"
    for length in range(4, 20):
        prefix_len = length // 2
        prefix = list(charset[:prefix_len])
        repeat_char = random.choice(prefix)
        available = [c for c in charset if c not in prefix]
        suffix_len = length - prefix_len - 1
        suffix = random.sample(available, min(suffix_len, len(available)))
        s = "".join(prefix + suffix + [repeat_char])
        if len(s) >= 4:
            inputs.append(s)
    inputs += ["abcdeabcde", "abcdea", "abcbde", "aabcde", "abcdefa", "dvdf", "anviaj", "abcabcbb", "pwwkew", "bbbbb"]
    return inputs


def generate_all_unique():
    alpha = string.ascii_lowercase
    inputs = [alpha[:length] for length in range(4, 27)]
    inputs += ["1234567890", "!@#$%^&*()", "abcdefghij"]
    return inputs


GENERATORS = {
    "repeat_at_boundary": generate_repeat_at_boundary,
    "all_unique": generate_all_unique,
}


LC3 = BimaristanSchema(
    problem_structure=ProblemStructure(
        problem_id="lc3_longest_substring_without_repeating",
        kind="optimization",
        input_symbols=(Symbol("s", "sequence_integer"),),
        output_symbol=Symbol("max_length", "integer"),
        objective_predicate=RelationConstraint("ground_truth_length(s)", ">=", "0"),
    ),
    invariant_families=(
        InvariantFamily(
            family_id="search_space_pruning_failures",
            invariants=(
                Invariant(
                    invariant_id="lc3_sliding_window_preserves_max_length",
                    falsifiable_predicates=(
                        RelationConstraint("reference_agrees_with_truth(s)", "==", "True"),
                    ),
                    violation_predicates=(
                        RelationConstraint("no_shrink_diverges(s)", "==", "True"),
                        RelationConstraint("fixed_window_diverges(s)", "==", "True"),
                    ),
                ),
            ),
            failure_manifolds=(
                FailureManifold(
                    manifold_id="repeat_at_boundary",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc3_sliding_window_preserves_max_length",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc3_repeat_at_boundary",
                            generation_constraints=(
                                RelationConstraint("has_repeating_chars(s)", "==", "True"),
                                RelationConstraint("len(s)", ">=", "4"),
                                RelationConstraint("len(s)", "<=", "30"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(s)", "==", "True"),
                                RelationConstraint("no_shrink_diverges(s)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
                FailureManifold(
                    manifold_id="all_unique",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc3_sliding_window_preserves_max_length",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc3_all_unique",
                            generation_constraints=(
                                RelationConstraint("all_unique(s)", "==", "True"),
                                RelationConstraint("len(s)", ">=", "27"),
                                RelationConstraint("len(s)", "<=", "100"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(s)", "==", "True"),
                                RelationConstraint("fixed_window_diverges(s)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
                FailureManifold(
                    manifold_id="long_repeat_collision_all_broken",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc3_sliding_window_preserves_max_length",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc3_long_repeat_collision_all_broken",
                            generation_constraints=(
                                RelationConstraint("has_repeating_chars(s)", "==", "True"),
                                RelationConstraint("len(s)", ">=", "27"),
                                RelationConstraint("len(s)", "<=", "100"),
                                RelationConstraint("fixed_window_diverges(s)", "==", "True"),
                                RelationConstraint("no_shrink_diverges(s)", "==", "True"),
                                RelationConstraint("reset_all_diverges(s)", "==", "True"),
                                RelationConstraint("count_total_unique_diverges(s)", "==", "True"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(s)", "==", "True"),
                                RelationConstraint("fixed_window_diverges(s)", "==", "True"),
                                RelationConstraint("no_shrink_diverges(s)", "==", "True"),
                                RelationConstraint("reset_all_diverges(s)", "==", "True"),
                                RelationConstraint("count_total_unique_diverges(s)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
