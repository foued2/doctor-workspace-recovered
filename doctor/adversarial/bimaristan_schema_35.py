"""LC997 Bimaristan manifolds — Find the Town Judge."""
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


def generate_judge_exists_clear():
    inputs = []
    for n in range(4, 13):
        judge = n
        trust = [[i, judge] for i in range(1, n)]
        for _ in range(min(n - 2, 3)):
            a = random.randint(1, n - 1)
            b = random.randint(1, n - 1)
            if a != b:
                trust.append([a, b])
        inputs.append((n, trust))
    return inputs


def generate_no_judge_exists():
    inputs = []
    for n in range(4, 13):
        judge_candidate = n
        trust = [[i, judge_candidate] for i in range(1, n)]
        trust.append([judge_candidate, 1])
        inputs.append((n, trust))
        trust2 = [[i, (i % (n - 1)) + 1] for i in range(1, n + 1) if i != (i % (n - 1)) + 1]
        inputs.append((n, trust2))
    return inputs


GENERATORS = {
    "judge_exists_clear": generate_judge_exists_clear,
    "no_judge_exists": generate_no_judge_exists,
}


LC997 = BimaristanSchema(
    problem_structure=ProblemStructure(
        problem_id="lc997_find_town_judge",
        kind="optimization",
        input_symbols=(Symbol("n", "integer"), Symbol("trust", "sequence_integer")),
        output_symbol=Symbol("judge", "integer"),
        objective_predicate=RelationConstraint("judge_ground_truth(n, trust)", ">=", "-1"),
    ),
    invariant_families=(
        InvariantFamily(
            family_id="search_space_pruning_failures",
            invariants=(
                Invariant(
                    invariant_id="lc997_judge_requires_indegree_n_minus_1_and_outdegree_0",
                    falsifiable_predicates=(
                        RelationConstraint("reference_agrees_with_truth(n, trust)", "==", "True"),
                    ),
                    violation_predicates=(
                        RelationConstraint("no_outdegree_diverges(n, trust)", "==", "True"),
                        RelationConstraint("wrong_threshold_diverges(n, trust)", "==", "True"),
                    ),
                ),
            ),
            failure_manifolds=(
                FailureManifold(
                    manifold_id="judge_exists_clear",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc997_judge_requires_indegree_n_minus_1_and_outdegree_0",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc997_judge_exists_clear",
                            generation_constraints=(
                                RelationConstraint("judge_exists(n, trust)", "==", "True"),
                                RelationConstraint("max_n(n, trust)", "<=", "20"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(n, trust)", "==", "True"),
                                RelationConstraint("wrong_threshold_diverges(n, trust)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
                FailureManifold(
                    manifold_id="no_judge_exists",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc997_judge_requires_indegree_n_minus_1_and_outdegree_0",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc997_no_judge_exists",
                            generation_constraints=(
                                RelationConstraint("judge_exists(n, trust)", "==", "False"),
                                RelationConstraint("max_n(n, trust)", "<=", "20"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(n, trust)", "==", "True"),
                                RelationConstraint("no_outdegree_diverges(n, trust)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
                FailureManifold(
                    manifold_id="duplicate_indegree_collision_no_judge",
                    manifold_type="GENERATABLE",
                    target_invariant_ids=("lc997_judge_requires_indegree_n_minus_1_and_outdegree_0",),
                    geometry_generators=(
                        GeometryGenerator(
                            generator_id="lc997_duplicate_indegree_collision_no_judge",
                            generation_constraints=(
                                RelationConstraint("judge_exists(n, trust)", "==", "False"),
                                RelationConstraint("max_n(n, trust)", "<=", "20"),
                                RelationConstraint("no_outdegree_diverges(n, trust)", "==", "True"),
                                RelationConstraint("wrong_threshold_diverges(n, trust)", "==", "True"),
                            ),
                            validation_predicates=(
                                RelationConstraint("reference_agrees_with_truth(n, trust)", "==", "True"),
                                RelationConstraint("no_outdegree_diverges(n, trust)", "==", "True"),
                                RelationConstraint("wrong_threshold_diverges(n, trust)", "==", "True"),
                            ),
                            synthesized_inputs=(),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
