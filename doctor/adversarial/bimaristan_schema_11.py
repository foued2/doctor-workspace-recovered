# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC11 implementation of the Bimaristan Layer 1 synthesizer."""
from __future__ import annotations

import ast
import operator
import random
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from doctor.adversarial.bimaristan_schema import (
    BooleanConstraint,
    GeometryConstraint,
    LC11,
    ManifoldKind,
    RelationConstraint,
    ScaleConstraint,
    TIE_TRANSITION_POLICY,
)
from doctor.adversarial.symbol_registry import LC11_SYMBOL_REGISTRY
from doctor.adversarial.synthesizer_contract import (
    GenerationStrategy,
    GenerationSurface,
    RejectedCandidate,
    SynthesisBatch,
    SynthesizedCandidate,
)


class SynthesisYieldWarning(RuntimeError):
    def __init__(self, generator_id: str, failing_constraint: GeometryConstraint | None, message: str) -> None:
        self.generator_id = generator_id
        self.failing_constraint = failing_constraint
        super().__init__(f"{generator_id}: {message}")


class SchemaInconsistencyError(RuntimeError):
    def __init__(self, manifold_id: str, conflicting_predicate_ids: tuple[str, ...]) -> None:
        self.manifold_id = manifold_id
        self.conflicting_predicate_ids = conflicting_predicate_ids
        super().__init__(f"{manifold_id}: logic-inconsistent validation predicates")


@dataclass(frozen=True)
class SkippedSynthesis:
    generator_id: str
    manifold_id: str
    reason: str


@dataclass(frozen=True)
class _Attempt:
    raw_array: tuple[int, ...]
    strategy: GenerationStrategy


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
}


def _lc11_manifold_index() -> dict[str, tuple[str, ManifoldKind, tuple[str, ...]]]:
    index: dict[str, tuple[str, ManifoldKind, tuple[str, ...]]] = {}
    for family in LC11.invariant_families:
        for manifold in family.failure_manifolds:
            for generator in manifold.geometry_generators:
                predicate_ids = tuple(
                    f"{generator.generator_id}:validation_predicates[{predicate_index}]"
                    for predicate_index, _ in enumerate(generator.validation_predicates)
                )
                index[generator.generator_id] = (manifold.manifold_id, manifold.manifold_type, predicate_ids)
    return index


def _constraint_id(constraint: GeometryConstraint) -> str:
    if isinstance(constraint, RelationConstraint):
        return f"{constraint.left} {constraint.operator} {constraint.right}"
    if isinstance(constraint, ScaleConstraint):
        return f"{constraint.dominant} {constraint.operator} {constraint.dominated}"
    if isinstance(constraint, BooleanConstraint):
        return f"{constraint.name} == {constraint.value}"
    return repr(constraint)


def _eval_expr(expr: str, context: Mapping[str, Any]) -> Any:
    tree = ast.parse(expr, mode="eval")

    def visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            entry = LC11_SYMBOL_REGISTRY.get(node.id)
            if node.id in context:
                return context[node.id]
            return entry.compute(context)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "min":
            return min(visit(arg) for arg in node.args)
        if isinstance(node, ast.Subscript):
            base = visit(node.value)
            index = visit(node.slice)
            return base[index]
        raise ValueError(f"unsupported expression: {expr}")

    return visit(tree)


def _compare(left: Any, operator_name: str, right: Any) -> bool:
    if operator_name == "<":
        return left < right
    if operator_name == "<=":
        return left <= right
    if operator_name == "==":
        return left == right
    if operator_name == ">=":
        return left >= right
    if operator_name == ">":
        return left > right
    if operator_name == "!=":
        return left != right
    if operator_name == "in":
        if isinstance(left, tuple) and len(left) == 2 and isinstance(right, tuple) and len(right) == 2:
            return right[0] <= left[0] <= left[1] <= right[1]
        return left in right
    if operator_name == "not_in":
        return not _compare(left, "in", right)
    raise ValueError(f"unsupported operator: {operator_name}")


def evaluate_constraint(constraint: GeometryConstraint, context: Mapping[str, Any]) -> bool:
    if isinstance(constraint, BooleanConstraint):
        return bool(_eval_expr(constraint.name, context)) is constraint.value
    if isinstance(constraint, ScaleConstraint):
        dominant = _eval_expr(constraint.dominant, context)
        dominated = _eval_expr(constraint.dominated, context)
        if constraint.operator == ">>":
            return dominant > dominated if not isinstance(dominated, tuple) else all(dominant > value for value in dominated)
        if constraint.operator == "<<":
            return dominant < dominated if not isinstance(dominated, tuple) else all(dominant < value for value in dominated)
    if isinstance(constraint, RelationConstraint):
        return _compare(_eval_expr(constraint.left, context), constraint.operator, _eval_expr(constraint.right, context))
    raise TypeError(constraint)


def predicate_values(predicate: RelationConstraint, context: Mapping[str, Any]) -> tuple[Any, Any]:
    return _eval_expr(predicate.left, context), _eval_expr(predicate.right, context)


def _base_context(generator_id: str, raw_array: tuple[int, ...]) -> dict[str, Any]:
    n = len(raw_array)
    context: dict[str, Any] = {
        "height": raw_array,
        "n": n,
        "TIE_TRANSITION_POLICY": TIE_TRANSITION_POLICY,
        "tie_transition_policy": TIE_TRANSITION_POLICY,
        "left_index": 0,
        "right_index": n - 1,
        "i": 1 if n > 2 else 0,
        "j": n - 1,
        "chosen_left": 0,
        "chosen_right": n - 1,
        "symmetric_boundaries": raw_array[0] == raw_array[-1],
        "boundary_pair_area": min(raw_array[0], raw_array[-1]) * (n - 1),
        "interior_peak_height": max(raw_array[1:-1]) if n > 2 else max(raw_array),
        "interior_pair_area": 0,
        "fixed_shorter_height": min(raw_array[0], raw_array[-1]),
        "moving_taller_height": max(raw_array[0], raw_array[-1]),
        "area_before_moving_taller": min(raw_array[0], raw_array[-1]) * (n - 1),
        "area_after_moving_taller": min(raw_array[0], raw_array[-2]) * (n - 2) if n > 2 else 0,
        "moved_boundary": "right" if raw_array[-1] >= raw_array[0] else "left",
        "taller_boundary": "right" if raw_array[-1] >= raw_array[0] else "left",
        "remaining_search_width": n - 2,
        "previous_width": n - 1,
        "hidden_partner_index": min(2, n - 2),
        "next_max_area": 0,
        "previous_max_area": 0,
        "early_candidate_area": 0,
        "late_candidate_area": 0,
        "late_candidate_seen_after_early": True,
    }
    if n >= 4:
        best = (1, 2, min(raw_array[1], raw_array[2]))
        for i in range(1, n - 1):
            for j in range(i + 1, n - 1):
                area = min(raw_array[i], raw_array[j]) * (j - i)
                if area > best[2]:
                    best = (i, j, area)
        context["interior_pair_area"] = best[2]
    context["wrong_width"] = context["j"] - context["i"] + 1
    context["wrong_area"] = min(raw_array[context["i"]], raw_array[context["j"]]) * context["wrong_width"]
    context["correct_area"] = min(raw_array[context["i"]], raw_array[context["j"]]) * (context["j"] - context["i"])
    if generator_id == "short_left_tall_right_hidden_left_partner":
        context["right_index"] = min(2, n - 2)
        context["hidden_partner_index"] = n - 1
    if generator_id == "early_large_area_late_small_area":
        context["early_candidate_area"] = max(
            min(raw_array[i], raw_array[j]) * (j - i) for i in range(n) for j in range(i + 1, n)
        )
        context["late_candidate_area"] = min(raw_array[-2], raw_array[-1])
    return context


def candidate_context(generator_id: str, raw_array: tuple[int, ...]) -> dict[str, Any]:
    return _base_context(generator_id, raw_array)


class LC11Synthesizer:
    def __init__(
        self,
        seed: int = 42,
        attempts_per_strategy: int = 8,
        manifold_index: Mapping[str, tuple[str, ManifoldKind, tuple[str, ...]]] | None = None,
    ) -> None:
        self.seed = seed
        self.attempts_per_strategy = attempts_per_strategy
        self.manifold_index = dict(manifold_index) if manifold_index is not None else _lc11_manifold_index()
        self.skipped: list[SkippedSynthesis] = []

    def synthesize(self, surface: GenerationSurface) -> SynthesisBatch:
        gated = self._gate(surface)
        if gated is not None:
            return gated
        rng = random.Random(self.seed + sum(ord(char) for char in surface.generator_id))
        attempts = tuple(self._attempts(surface, rng))
        accepted: list[SynthesizedCandidate] = []
        rejected: list[RejectedCandidate] = []

        for attempt in attempts:
            context = candidate_context(surface.generator_id, attempt.raw_array)
            failed = self._first_failed(surface.generation_constraints, context)
            if failed is None:
                accepted.append(
                    SynthesizedCandidate(
                        raw_array=attempt.raw_array,
                        satisfied_generation_constraints=surface.generation_constraints,
                        generation_strategy=attempt.strategy,
                        provenance_generator_id=surface.generator_id,
                    )
                )
            else:
                rejected.append(
                    RejectedCandidate(
                        raw_array=attempt.raw_array,
                        generation_strategy=attempt.strategy,
                        failed_generation_constraint=failed,
                        provenance_generator_id=surface.generator_id,
                    )
                )

        batch = SynthesisBatch(surface, tuple(accepted), tuple(rejected))
        total = len(accepted) + len(rejected)
        rejection_rate = len(rejected) / total if total else 1.0
        failing_constraint = rejected[0].failed_generation_constraint if rejected else None
        if rejection_rate > 0.8:
            raise SynthesisYieldWarning(
                surface.generator_id,
                failing_constraint,
                f"rejection rate {rejection_rate:.2%} exceeds 80%",
            )
        if len(accepted) < 10:
            raise SynthesisYieldWarning(surface.generator_id, failing_constraint, "fewer than 10 valid candidates")
        if len({candidate.generation_strategy for candidate in accepted}) < 2:
            raise SynthesisYieldWarning(surface.generator_id, failing_constraint, "fewer than 2 accepted strategies")
        return batch

    def try_synthesize(self, surface: GenerationSurface) -> tuple[SynthesisBatch, SynthesisYieldWarning | None]:
        try:
            return self.synthesize(surface), None
        except SynthesisYieldWarning as warning:
            attempts = tuple(self._attempts(surface, random.Random(self.seed + sum(ord(char) for char in surface.generator_id))))
            accepted: list[SynthesizedCandidate] = []
            rejected: list[RejectedCandidate] = []
            for attempt in attempts:
                context = candidate_context(surface.generator_id, attempt.raw_array)
                failed = self._first_failed(surface.generation_constraints, context)
                if failed is None:
                    accepted.append(
                        SynthesizedCandidate(attempt.raw_array, surface.generation_constraints, attempt.strategy, surface.generator_id)
                    )
                else:
                    rejected.append(RejectedCandidate(attempt.raw_array, attempt.strategy, failed, surface.generator_id))
            return SynthesisBatch(surface, tuple(accepted), tuple(rejected)), warning

    def _gate(self, surface: GenerationSurface) -> SynthesisBatch | None:
        manifold = self.manifold_index.get(surface.generator_id)
        if manifold is None:
            return None
        manifold_id, manifold_type, predicate_ids = manifold
        if manifold_type == "GENERATABLE":
            return None
        if manifold_type == "NONREALIZABLE":
            self.skipped.append(SkippedSynthesis(surface.generator_id, manifold_id, "NONREALIZABLE"))
            return SynthesisBatch(surface, (), ())
        if manifold_type == "LOGIC_INCONSISTENT":
            raise SchemaInconsistencyError(manifold_id, predicate_ids)
        raise ValueError(f"unknown manifold type: {manifold_type}")

    def _first_failed(self, constraints: tuple[GeometryConstraint, ...], context: Mapping[str, Any]) -> GeometryConstraint | None:
        for constraint in constraints:
            try:
                if not evaluate_constraint(constraint, context):
                    return constraint
            except Exception:
                return constraint
        return None

    def _attempts(self, surface: GenerationSurface, rng: random.Random) -> Iterable[_Attempt]:
        for strategy in surface.active_strategies:
            for index in range(self.attempts_per_strategy):
                yield _Attempt(self._array_for(surface.generator_id, strategy, index, rng), strategy)

    def _array_for(self, generator_id: str, strategy: GenerationStrategy, index: int, rng: random.Random) -> tuple[int, ...]:
        if generator_id == "short_left_tall_right_hidden_left_partner":
            return (3 + index % 2, 1, 5 + index, 2, 8 + index)
        if generator_id == "equal_boundaries_single_interior_optimum":
            return (4, 20 + index, 20 + index, 1, 4)
        if generator_id == "both_endpoints_strictly_suboptimal":
            return (1, 10 + index, 10 + index, 1, 1)
        if generator_id == "tallest_line_width_decoy":
            return (1, 3 + index, 10 + index, 4, 2, 6)
        if generator_id == "off_by_one_width_amplifier":
            height = 10 + index
            return (1, height, 1, 1, height)
        if generator_id == "early_large_area_late_small_area":
            if strategy == GenerationStrategy.MONOTONIC_ASCENDING:
                return tuple(range(1 + index, 8 + index))
            if strategy == GenerationStrategy.MONOTONIC_DESCENDING:
                return tuple(range(8 + index, 1 + index, -1))
            return (2, 9 + index, 4, 8 + index, 3, 1)
        if strategy == GenerationStrategy.SYMMETRIC_BOUNDARY:
            edge = 2 + index % 3
            return (edge, 8 + index, 3, 9 + index, edge)
        if strategy == GenerationStrategy.INTERIOR_SPIKE:
            return (2, 5 + index, 12 + index, 6, 2)
        if strategy == GenerationStrategy.MONOTONIC_ASCENDING:
            return tuple(range(1 + index, 7 + index))
        if strategy == GenerationStrategy.MONOTONIC_DESCENDING:
            return tuple(range(7 + index, 1 + index, -1))
        if strategy == GenerationStrategy.PLATEAU:
            return (3, 7 + index % 4, 7 + index % 4, 7 + index % 4, 3)
        if strategy == GenerationStrategy.DENSITY_GRADIENT:
            base = rng.randint(2, 5)
            return (base, base + 3, base + 8 + index, base + 2, base + 5, base + 1)
        raise ValueError(strategy)


def rejection_rate(batch: SynthesisBatch) -> float:
    total = len(batch.accepted_candidates) + len(batch.rejected_candidates)
    return len(batch.rejected_candidates) / total if total else 0.0


def constraint_text(constraint: GeometryConstraint | None) -> str:
    return "none" if constraint is None else _constraint_id(constraint)
