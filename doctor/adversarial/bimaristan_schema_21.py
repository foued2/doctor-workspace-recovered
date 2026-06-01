"""LC322 oracle evaluator implementing OracleEvaluatorContract."""
# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Not on paper critical path. See git log for reconstruction history.
from __future__ import annotations

import ast
import operator
from typing import Any

from doctor.adversarial.bimaristan_schema import RelationConstraint
from doctor.adversarial.lc322_bimaristan import LC322
from doctor.adversarial.lc322_symbol_registry import LC322_SYMBOL_REGISTRY
from doctor.adversarial.oracle_contract import (
    LC322_COMPLEXITY_CEILING,
    OracleEvaluationSurface,
    OracleResult,
    OracleSymbolValue,
    PredicateEvaluation,
)
from doctor.adversarial.schema_validator import assert_valid_schema
from doctor.adversarial.symbol_registry import SymbolCategory


class OracleCeilingError(RuntimeError):
    pass


class LC322OracleSymbolResolutionError(RuntimeError):
    def __init__(self, symbol_name: str, original: Exception) -> None:
        self.symbol_name = symbol_name
        self.original = original
        super().__init__(f"{symbol_name}: {type(original).__name__}: {original}")


class LC322OracleExpressionError(ValueError):
    pass


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
}


class LC322OracleEvaluator:
    def __init__(self, max_amount: int = 30, max_coins: int = 6) -> None:
        assert_valid_schema(LC322, registry=LC322_SYMBOL_REGISTRY)
        self.max_amount = max_amount
        self.max_coins = max_coins
        self._registry = LC322_SYMBOL_REGISTRY

    def evaluate(self, surface: OracleEvaluationSurface) -> OracleResult:
        raw = surface.candidate.raw_array
        coins = list(raw[:-1])
        amount = raw[-1]
        input_array = tuple(raw)

        if amount > self.max_amount or len(coins) > self.max_coins:
            raise OracleCeilingError(
                f"LC322 oracle ceiling exceeded: amount={amount} > {self.max_amount}"
                f" or coins={len(coins)} > {self.max_coins}"
            )

        context: dict[str, Any] = {"coins": coins, "amount": amount}
        cache: dict[str, Any] = {}

        oracle_values: list[OracleSymbolValue] = []
        for entry in self._registry.entries:
            if entry.category is SymbolCategory.ORACLE_DEPENDENT:
                try:
                    value = entry.compute(context | cache)
                except Exception as exc:
                    raise LC322OracleSymbolResolutionError(entry.name, exc) from exc
                cache[entry.name] = value
                oracle_values.append(OracleSymbolValue(entry.name, entry.category, value))

        results: list[PredicateEvaluation] = []
        violated: list[str] = []
        for index, predicate in enumerate(surface.validation_predicates):
            predicate_id = f"{surface.provenance_generator_id}:validation_predicates[{index}]"
            if not isinstance(predicate, RelationConstraint):
                results.append(PredicateEvaluation(predicate_id, predicate, False))
                violated.append(predicate_id)
                continue
            eval_context = context | cache
            left = self._eval(predicate.left, eval_context)
            right = self._eval(predicate.right, eval_context)
            passed = self._compare(left, predicate.operator, right)
            results.append(PredicateEvaluation(predicate_id, predicate, passed, left, right))
            if not passed:
                violated.append(predicate_id)

        return OracleResult(
            input_array=input_array,
            oracle_dependent_values=tuple(oracle_values),
            predicate_results=tuple(results),
            passed=not violated,
            violated_predicate_ids=tuple(violated),
            provenance_generator_id=surface.provenance_generator_id,
            provenance_synthesized_input_id=surface.provenance_synthesized_input_id,
        )

    def _eval(self, expression: str, context: dict[str, Any]) -> Any:
        tree = ast.parse(expression, mode="eval")
        return self._visit(tree.body, context)

    def _visit(self, node: ast.AST, context: dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._visit(node.operand, context)
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            if node.id in {"len", "max"}:
                return node.id
            if node.id in self._registry.names:
                return self._registry.get(node.id).compute(context)
            raise LC322OracleExpressionError(f"unknown symbol: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](
                self._visit(node.left, context),
                self._visit(node.right, context),
            )
        if isinstance(node, ast.BoolOp):
            values = [self._visit(value, context) for value in node.values]
            if isinstance(node.op, ast.Or):
                return any(values)
            if isinstance(node.op, ast.And):
                return all(values)
        if isinstance(node, ast.Compare):
            left = self._visit(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._visit(comparator, context)
                if not self._compare(left, self._operator_name(op), right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            args = [self._visit(arg, context) for arg in node.args]
            if name == "len":
                return len(args[0])
            if name == "max":
                return max(args[0])
            if name not in self._registry.names:
                raise LC322OracleExpressionError(f"unknown function: {name}")
            entry = self._registry.get(name)
            call_context = dict(context)
            for signature, value in zip(entry.input_signature, args):
                call_context[signature] = value
            return entry.compute(call_context)
        raise LC322OracleExpressionError(f"unsupported expression: {ast.dump(node)}")

    def _operator_name(self, op: ast.cmpop) -> str:
        if isinstance(op, ast.Lt):
            return "<"
        if isinstance(op, ast.LtE):
            return "<="
        if isinstance(op, ast.Eq):
            return "=="
        if isinstance(op, ast.NotEq):
            return "!="
        if isinstance(op, ast.GtE):
            return ">="
        if isinstance(op, ast.Gt):
            return ">"
        if isinstance(op, ast.In):
            return "in"
        if isinstance(op, ast.NotIn):
            return "not_in"
        raise ValueError(f"unsupported operator: {op}")

    def _compare(self, left: Any, operator_name: str, right: Any) -> bool:
        if operator_name == "<":
            return left < right
        if operator_name == "<=":
            return left <= right
        if operator_name == "==":
            return left == right
        if operator_name == "!=":
            return left != right
        if operator_name == ">=":
            return left >= right
        if operator_name == ">":
            return left > right
        if operator_name == "in":
            return left in right
        if operator_name == "not_in":
            return left not in right
        raise ValueError(f"unsupported operator: {operator_name}")


def evaluation_surface(candidate, validation_predicates, generator_id: str, synthesized_input_id: str | None = None):
    return OracleEvaluationSurface(
        candidate=candidate,
        validation_predicates=tuple(validation_predicates),
        provenance_generator_id=generator_id,
        provenance_synthesized_input_id=synthesized_input_id,
        complexity_ceiling=LC322_COMPLEXITY_CEILING,
    )
