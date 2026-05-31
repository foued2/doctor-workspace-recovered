"""LC42-native oracle evaluator with isolated registry routing."""
from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from typing import Any, Mapping

from doctor.adversarial.lc42_symbol_registry import LC42_SYMBOL_REGISTRY


class RegistryRoutingError(RuntimeError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"symbol not in LC42_SYMBOL_REGISTRY: {symbol}")


@dataclass(frozen=True)
class ValidationPredicate:
    predicate_id: str
    left: str
    operator: str
    right: str


@dataclass(frozen=True)
class LC42PredicateResult:
    predicate_id: str
    predicate: ValidationPredicate
    passed: bool
    computed_left: object
    computed_right: object


@dataclass(frozen=True)
class LC42OracleResult:
    input_array: tuple[int, ...]
    predicate_results: tuple[LC42PredicateResult, ...]
    passed: bool
    violated_predicate_ids: tuple[str, ...]


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


class LC42OracleEvaluator:
    def __init__(self, registry=LC42_SYMBOL_REGISTRY) -> None:
        self.registry = registry

    def evaluate(self, candidate_array: tuple[int, ...] | list[int], predicates: tuple[ValidationPredicate, ...]) -> LC42OracleResult:
        arr = tuple(candidate_array)
        context: dict[str, Any] = {"arr": arr, "wide_peak_index": self._infer_wide_peak_index(arr)}
        results: list[LC42PredicateResult] = []
        violated: list[str] = []
        for predicate in predicates:
            left = self._eval(predicate.left, context)
            right = self._eval(predicate.right, context)
            passed = self._compare(left, predicate.operator, right)
            results.append(LC42PredicateResult(predicate.predicate_id, predicate, passed, left, right))
            if not passed:
                violated.append(predicate.predicate_id)
        return LC42OracleResult(arr, tuple(results), not violated, tuple(violated))

    def _eval(self, expression: str, context: Mapping[str, Any]) -> Any:
        tree = ast.parse(expression, mode="eval")
        return self._visit(tree.body, dict(context))

    def _visit(self, node: ast.AST, context: dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            if node.id in {"len", "sum", "range"}:
                return node.id
            if node.id in self.registry.names:
                return self.registry.get(node.id).compute(context)
            raise RegistryRoutingError(node.id)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](self._visit(node.left, context), self._visit(node.right, context))
        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("only single comparisons are supported")
            return self._compare(self._visit(node.left, context), self._operator_name(node.ops[0]), self._visit(node.comparators[0], context))
        if isinstance(node, ast.Call):
            return self._call(node, context)
        if isinstance(node, ast.GeneratorExp):
            return tuple(self._eval_generator(node, context))
        raise ValueError(f"unsupported LC42 expression: {ast.dump(node)}")

    def _call(self, node: ast.Call, context: dict[str, Any]) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("only direct function calls are supported")
        name = node.func.id
        if name == "len":
            return len(self._visit(node.args[0], context))
        if name == "sum":
            value = self._visit(node.args[0], context)
            return sum(value)
        if name == "range":
            args = [self._visit(arg, context) for arg in node.args]
            return range(*args)
        if name not in self.registry.names:
            raise RegistryRoutingError(name)
        arg_names = self.registry.get(name).input_signature
        call_context = dict(context)
        for signature, arg in zip(arg_names, node.args):
            call_context[signature] = self._visit(arg, context)
        return self.registry.get(name).compute(call_context)

    def _eval_generator(self, node: ast.GeneratorExp, context: dict[str, Any]):
        if len(node.generators) != 1:
            raise ValueError("only one generator clause is supported")
        generator = node.generators[0]
        if not isinstance(generator.target, ast.Name):
            raise ValueError("only simple generator targets are supported")
        for item in self._visit(generator.iter, context):
            next_context = dict(context)
            next_context[generator.target.id] = item
            if all(self._visit(condition, next_context) for condition in generator.ifs):
                yield self._visit(node.elt, next_context)

    def _compare(self, left: Any, operator_name: str, right: Any) -> bool:
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
        raise ValueError(f"unsupported operator: {operator_name}")

    def _operator_name(self, op: ast.cmpop) -> str:
        if isinstance(op, ast.Lt):
            return "<"
        if isinstance(op, ast.LtE):
            return "<="
        if isinstance(op, ast.Eq):
            return "=="
        if isinstance(op, ast.GtE):
            return ">="
        if isinstance(op, ast.Gt):
            return ">"
        if isinstance(op, ast.NotEq):
            return "!="
        raise ValueError(f"unsupported operator: {op}")

    def _infer_wide_peak_index(self, arr: tuple[int, ...]) -> int:
        trapped = LC42_SYMBOL_REGISTRY.get("trapped_indices").compute({"arr": arr})
        candidates = [
            index
            for index in range(1, len(arr) - 1)
            if index not in trapped and any(left < index for left in trapped) and any(right > index for right in trapped)
        ]
        if not candidates:
            return max(range(len(arr)), key=lambda index: (arr[index], -index))
        return max(candidates, key=lambda index: (arr[index], -index))
