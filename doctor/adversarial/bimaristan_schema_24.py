# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""LC33 oracle evaluator implementing OracleEvaluatorContract."""
from __future__ import annotations

import ast
import operator
from typing import Any

from doctor.adversarial.bimaristan_schema import RelationConstraint
from doctor.adversarial.lc33_bimaristan import LC33
from doctor.adversarial.lc33_symbol_registry import LC33_SYMBOL_REGISTRY
from doctor.adversarial.oracle_contract import ComplexityCeiling, OracleEvaluationSurface, OracleResult, OracleSymbolValue, PredicateEvaluation
from doctor.adversarial.schema_validator import assert_valid_schema
from doctor.adversarial.symbol_registry import SymbolCategory


LC33_COMPLEXITY_CEILING = ComplexityCeiling(
    problem_id="lc33_search_rotated_sorted_array",
    time_complexity="O(log n)",
    space_complexity="O(1)",
)


class LC33OracleCeilingError(RuntimeError):
    pass


class LC33OracleSymbolResolutionError(RuntimeError):
    def __init__(self, symbol_name: str, original: Exception) -> None:
        self.symbol_name = symbol_name
        self.original = original
        super().__init__(f"{symbol_name}: {type(original).__name__}: {original}")


class LC33OracleExpressionError(ValueError):
    pass


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
}


class LC33OracleEvaluator:
    def __init__(self, max_n: int = 100) -> None:
        assert_valid_schema(LC33, registry=LC33_SYMBOL_REGISTRY)
        self.max_n = max_n
        self._registry = LC33_SYMBOL_REGISTRY

    def evaluate(self, surface: OracleEvaluationSurface) -> OracleResult:
        nums, target = surface.candidate.raw_array
        nums = list(nums)
        target = int(target)
        if len(nums) > self.max_n:
            raise LC33OracleCeilingError(f"LC33 oracle ceiling exceeded: n > {self.max_n}")

        context: dict[str, Any] = {"nums": nums, "target": target}
        cache: dict[str, Any] = {}
        oracle_values: list[OracleSymbolValue] = []
        for entry in self._registry.entries:
            if entry.category is SymbolCategory.ORACLE_DEPENDENT:
                try:
                    value = entry.compute(context | cache)
                except Exception as exc:
                    raise LC33OracleSymbolResolutionError(entry.name, exc) from exc
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
            input_array=(tuple(nums), target),
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
            if node.id in {"len", "max", "min"}:
                return node.id
            if node.id in self._registry.names:
                return self._registry.get(node.id).compute(context)
            raise LC33OracleExpressionError(f"unknown symbol: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](self._visit(node.left, context), self._visit(node.right, context))
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
            if name == "min":
                return min(args[0])
            if name not in self._registry.names:
                raise LC33OracleExpressionError(f"unknown function: {name}")
            entry = self._registry.get(name)
            call_context = dict(context)
            for signature, value in zip(entry.input_signature, args):
                call_context[signature] = value
            return entry.compute(call_context)
        raise LC33OracleExpressionError(f"unsupported expression: {ast.dump(node)}")

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
        raise LC33OracleExpressionError(f"unsupported operator: {op}")

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
        raise LC33OracleExpressionError(f"unsupported operator: {operator_name}")


def evaluation_surface(candidate, validation_predicates, generator_id: str, synthesized_input_id: str | None = None):
    return OracleEvaluationSurface(
        candidate=candidate,
        validation_predicates=tuple(validation_predicates),
        provenance_generator_id=generator_id,
        provenance_synthesized_input_id=synthesized_input_id,
        complexity_ceiling=LC33_COMPLEXITY_CEILING,
    )
