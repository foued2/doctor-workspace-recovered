"""Validation utilities for Bimaristan schemas.

The dataclasses in ``bimaristan_schema`` describe evidence, but they do not by
themselves prove that symbols can be routed to an executable registry. This
module is the explicit contract boundary between passive schema data and
problem-specific synthesizer/oracle code.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterable

from doctor.adversarial.bimaristan_schema import (
    BimaristanSchema,
    BooleanConstraint,
    GeometryConstraint,
    RelationConstraint,
    ScaleConstraint,
)
from doctor.adversarial.symbol_registry import SymbolRegistry


DEFAULT_ALLOWED_CALLS = frozenset({"len", "max", "min", "sum", "range", "all", "any"})
DEFAULT_CONSTANTS = frozenset({"True", "False", "None"})


@dataclass(frozen=True)
class SchemaValidationIssue:
    path: str
    message: str


class SchemaValidationError(ValueError):
    def __init__(self, issues: Iterable[SchemaValidationIssue]) -> None:
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(detail)


def _constraint_expressions(constraint: GeometryConstraint) -> tuple[str, ...]:
    if isinstance(constraint, RelationConstraint):
        return constraint.left, constraint.right
    if isinstance(constraint, ScaleConstraint):
        return constraint.dominant, constraint.dominated
    if isinstance(constraint, BooleanConstraint):
        return (constraint.name,)
    return ()


def _names_and_calls(expression: str) -> tuple[set[str], set[str], str | None]:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        return set(), set(), str(exc)

    names: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.add(node.func.id)
    return names, calls, None


def validate_schema(
    schema: BimaristanSchema,
    *,
    registry: SymbolRegistry | None = None,
    allowed_calls: Iterable[str] = DEFAULT_ALLOWED_CALLS,
    allowed_names: Iterable[str] = DEFAULT_CONSTANTS,
) -> tuple[SchemaValidationIssue, ...]:
    issues: list[SchemaValidationIssue] = []
    allowed_call_names = set(allowed_calls)
    allowed_symbol_names = set(allowed_names)

    declared_symbols = {symbol.name for symbol in schema.problem_structure.input_symbols}
    declared_symbols.add(schema.problem_structure.output_symbol.name)
    allowed_symbol_names.update(declared_symbols)

    if registry is not None:
        if registry.problem_id != schema.problem_structure.problem_id:
            issues.append(
                SchemaValidationIssue(
                    "problem_structure.problem_id",
                    f"registry problem_id {registry.problem_id!r} does not match schema problem_id "
                    f"{schema.problem_structure.problem_id!r}",
                )
            )
        allowed_symbol_names.update(registry.names)

    invariant_ids: set[str] = {
        invariant.invariant_id
        for family in schema.invariant_families
        for invariant in family.invariants
    }
    if len(invariant_ids) != sum(len(family.invariants) for family in schema.invariant_families):
        seen_invariants: set[str] = set()
        for family_index, family in enumerate(schema.invariant_families):
            for invariant in family.invariants:
                if invariant.invariant_id in seen_invariants:
                    issues.append(
                        SchemaValidationIssue(
                            f"invariant_families[{family_index}].{invariant.invariant_id}",
                            "duplicate invariant id",
                        )
                    )
                seen_invariants.add(invariant.invariant_id)

    manifold_ids: set[str] = set()
    generator_ids: set[str] = set()

    for family_index, family in enumerate(schema.invariant_families):
        family_path = f"invariant_families[{family_index}]"
        for invariant in family.invariants:
            _validate_constraints(
                invariant.falsifiable_predicates,
                f"{family_path}.{invariant.invariant_id}.falsifiable_predicates",
                allowed_symbol_names,
                allowed_call_names,
                issues,
            )
            _validate_constraints(
                invariant.violation_predicates,
                f"{family_path}.{invariant.invariant_id}.violation_predicates",
                allowed_symbol_names,
                allowed_call_names,
                issues,
            )
        for manifold in family.failure_manifolds:
            manifold_path = f"{family_path}.{manifold.manifold_id}"
            if manifold.manifold_id in manifold_ids:
                issues.append(SchemaValidationIssue(manifold_path, "duplicate manifold id"))
            manifold_ids.add(manifold.manifold_id)
            for target_id in manifold.target_invariant_ids:
                if target_id not in invariant_ids:
                    issues.append(SchemaValidationIssue(manifold_path, f"unknown target invariant {target_id!r}"))
            for generator in manifold.geometry_generators:
                generator_path = f"{manifold_path}.{generator.generator_id}"
                if generator.generator_id in generator_ids:
                    issues.append(SchemaValidationIssue(generator_path, "duplicate generator id"))
                generator_ids.add(generator.generator_id)
                for synthesized in generator.synthesized_inputs:
                    if synthesized.provenance_manifold_id != manifold.manifold_id:
                        issues.append(
                            SchemaValidationIssue(
                                f"{generator_path}.{synthesized.input_id}",
                                "synthesized input manifold provenance does not match enclosing manifold",
                            )
                        )
                    if synthesized.provenance_generator_id != generator.generator_id:
                        issues.append(
                            SchemaValidationIssue(
                                f"{generator_path}.{synthesized.input_id}",
                                "synthesized input generator provenance does not match enclosing generator",
                            )
                        )
                _validate_constraints(
                    generator.generation_constraints,
                    f"{generator_path}.generation_constraints",
                    allowed_symbol_names,
                    allowed_call_names,
                    issues,
                )
                _validate_constraints(
                    generator.validation_predicates,
                    f"{generator_path}.validation_predicates",
                    allowed_symbol_names,
                    allowed_call_names,
                    issues,
                )

    _validate_constraints(
        (schema.problem_structure.objective_predicate,),
        "problem_structure.objective_predicate",
        allowed_symbol_names,
        allowed_call_names,
        issues,
    )
    return tuple(issues)


def assert_valid_schema(schema: BimaristanSchema, **kwargs) -> None:
    issues = validate_schema(schema, **kwargs)
    if issues:
        raise SchemaValidationError(issues)


def _validate_constraints(
    constraints: tuple[GeometryConstraint, ...],
    path: str,
    allowed_symbol_names: set[str],
    allowed_call_names: set[str],
    issues: list[SchemaValidationIssue],
) -> None:
    for constraint_index, constraint in enumerate(constraints):
        for expression in _constraint_expressions(constraint):
            names, calls, error = _names_and_calls(expression)
            expression_path = f"{path}[{constraint_index}]"
            if error is not None:
                issues.append(SchemaValidationIssue(expression_path, f"invalid expression {expression!r}: {error}"))
                continue
            for call_name in sorted(calls - allowed_call_names - allowed_symbol_names):
                issues.append(SchemaValidationIssue(expression_path, f"unknown callable symbol {call_name!r}"))
            callable_names = calls & allowed_call_names
            for name in sorted(names - allowed_symbol_names - allowed_call_names - callable_names):
                issues.append(SchemaValidationIssue(expression_path, f"unknown symbol {name!r}"))
