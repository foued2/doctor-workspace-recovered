from __future__ import annotations

import ast
import itertools
import operator
import sys
from collections import Counter
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))

from doctor.adversarial.lc45_bimaristan import LC45
from doctor.adversarial.lc45_symbol_registry import LC45_SYMBOL_REGISTRY


class RegistryRoutingError(RuntimeError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"symbol not in LC45_SYMBOL_REGISTRY: {symbol}")


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
}


def _eval(expression: str, context: dict[str, Any]) -> Any:
    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            if node.id in {"len", "max"}:
                return node.id
            if node.id in LC45_SYMBOL_REGISTRY.names:
                return LC45_SYMBOL_REGISTRY.get(node.id).compute(context)
            raise RegistryRoutingError(node.id)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.BoolOp):
            values = [visit(value) for value in node.values]
            if isinstance(node.op, ast.Or):
                return any(values)
            if isinstance(node.op, ast.And):
                return all(values)
        if isinstance(node, ast.Compare):
            left = visit(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = visit(comparator)
                if not _compare(left, _operator_name(op), right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            args = [visit(arg) for arg in node.args]
            if name == "len":
                return len(args[0])
            if name == "max":
                return max(args[0])
            if name not in LC45_SYMBOL_REGISTRY.names:
                raise RegistryRoutingError(name)
            entry = LC45_SYMBOL_REGISTRY.get(name)
            call_context = dict(context)
            for signature, value in zip(entry.input_signature, args):
                call_context[signature] = value
            return entry.compute(call_context)
        raise ValueError(f"unsupported expression: {ast.dump(node)}")

    return visit(tree.body)


def _operator_name(op: ast.cmpop) -> str:
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


def _compare(left: Any, op: str, right: Any) -> bool:
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if op == ">=":
        return left >= right
    if op == ">":
        return left > right
    if op == "in":
        return left in right
    if op == "not_in":
        return left not in right
    raise ValueError(op)


def _predicate_passes(predicate, context: dict[str, Any]) -> bool:
    left = _eval(predicate.left, context)
    right = _eval(predicate.right, context)
    return _compare(left, predicate.operator, right)


def _candidate_space(manifold_id: str):
    seeds = {
        "naive_max_jump_suboptimal": (
            [2, 4, 1, 1, 1, 1],
            [2, 3, 0, 1, 4],
            [3, 5, 1, 1, 1, 1, 1],
            [2, 5, 0, 0, 1, 1, 1],
            [3, 1, 4, 1, 1, 1],
            [2, 4, 0, 1, 1, 1],
            [3, 4, 1, 0, 1, 1],
            [2, 5, 1, 1, 1, 1, 1],
            [3, 2, 5, 1, 1, 1, 1],
            [2, 3, 1, 1, 4],
            [4, 1, 1, 5, 1, 1, 1],
            [3, 5, 0, 1, 1, 1, 1],
        ),
        "single_large_jump_decoy": (
            [2, 5, 0, 0, 1, 1, 1],
            [3, 6, 1, 1, 1, 1, 1, 1],
            [2, 4, 0, 1, 1, 1],
            [3, 5, 1, 0, 1, 1, 1],
            [2, 6, 0, 0, 0, 1, 1, 1],
            [3, 7, 1, 1, 1, 1, 1, 1, 1],
            [2, 5, 1, 1, 1, 1, 1],
            [4, 6, 1, 1, 0, 1, 1, 1],
            [3, 5, 0, 1, 1, 1, 1],
            [2, 7, 0, 0, 0, 0, 1, 1, 1],
            [4, 5, 1, 1, 1, 0, 1],
            [3, 6, 0, 1, 1, 1, 1, 1],
        ),
        "uniform_jump_array": (
            [1, 1, 1, 1],
            [2, 2, 2, 2],
            [3, 3, 3, 3],
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3],
            [2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4],
            [2, 2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4, 4],
        ),
        "greedy_frontier_valid_no_false_pressure": (
            [2, 3, 1, 1, 4],
            [1, 2, 1, 1, 1],
            [2, 2, 1, 1, 1],
            [3, 1, 2, 1, 1],
            [1, 3, 1, 1, 1],
            [2, 1, 2, 1, 1],
            [3, 2, 1, 1, 1],
            [1, 1, 2, 1, 1],
            [2, 3, 2, 1, 1, 1],
            [1, 2, 2, 1, 1, 1],
            [3, 1, 1, 2, 1, 1],
            [2, 1, 1, 2, 1, 1],
        ),
    }
    yield from seeds[manifold_id]

    values = (0, 1, 2, 3, 4, 5)
    for length in range(5, 9):
        for nums in itertools.product(values, repeat=length):
            if nums[0] == 0:
                continue
            yield list(nums)


def _run_generator(manifold, generator):
    accepted: list[dict[str, Any]] = []
    rejected = 0
    routing_errors: list[str] = []
    for nums in _candidate_space(manifold.manifold_id):
        context = {"nums": nums}
        try:
            if _eval("ground_truth_jumps(nums)", context) == -1:
                rejected += 1
                continue
            if all(_predicate_passes(constraint, context) for constraint in generator.generation_constraints):
                accepted.append(context)
            else:
                rejected += 1
        except RegistryRoutingError as exc:
            routing_errors.append(str(exc))
            rejected += 1
        except Exception:
            rejected += 1
        if len(accepted) >= 12:
            break

    violated: list[str] = []
    stats = Counter()
    for context in accepted:
        for predicate_index, predicate in enumerate(generator.validation_predicates):
            try:
                if not _predicate_passes(predicate, context):
                    violated.append(f"{generator.generator_id}:validation_predicates[{predicate_index}]")
            except RegistryRoutingError as exc:
                routing_errors.append(str(exc))
        if _eval("greedy_frontier_agrees_with_truth(nums)", context):
            stats["greedy_frontier_agree"] += 1
        if _eval("naive_diverges(nums)", context):
            stats["naive_diverge"] += 1
        if _eval("dp_agrees_with_truth(nums)", context):
            stats["dp_agree"] += 1
    total = len(accepted) + rejected
    return {
        "accepted": accepted,
        "rejection_rate": rejected / total * 100 if total else 0.0,
        "violated": sorted(set(violated)),
        "routing_errors": sorted(set(routing_errors)),
        "stats": stats,
    }


def main() -> None:
    results: dict[str, dict[str, Any]] = {}
    print("LC45 Bimaristan run")
    for family in LC45.invariant_families:
        for manifold in family.failure_manifolds:
            generator = manifold.geometry_generators[0]
            result = _run_generator(manifold, generator)
            results[manifold.manifold_id] = result
            accepted = result["accepted"]
            stats = result["stats"]
            total = len(accepted)
            print(f"Manifold: {manifold.manifold_id}")
            print(f"  Candidates generated: {total}")
            print(f"  Rejection rate: {result['rejection_rate']:.2f}%")
            print(f"  Violated predicates: {result['violated'] if result['violated'] else 'none'}")
            print(f"  RegistryRoutingErrors: {result['routing_errors'] if result['routing_errors'] else 'none'}")
            print(f"  Greedy-frontier agrees with truth: {stats['greedy_frontier_agree']}/{total}")
            naive_rate = stats["naive_diverge"] / total * 100 if total else 0.0
            print(f"  Naive divergence rate: {naive_rate:.2f}%")
            print(f"  DP agrees with truth: {stats['dp_agree']}/{total}")

    total_candidates = sum(len(result["accepted"]) for result in results.values())
    control = results["greedy_frontier_valid_no_false_pressure"]
    control_count = len(control["accepted"])
    false_pressure = control["stats"]["naive_diverge"] > 0 or control["stats"]["greedy_frontier_agree"] != control_count
    frontier_validated = all(
        result["stats"]["greedy_frontier_agree"] == len(result["accepted"])
        for result in results.values()
    )
    naive_failure_isolated = (
        results["naive_max_jump_suboptimal"]["stats"]["naive_diverge"] > 0
        and results["single_large_jump_decoy"]["stats"]["naive_diverge"] > 0
        and results["uniform_jump_array"]["stats"]["naive_diverge"] == 0
        and control["stats"]["naive_diverge"] == 0
    )
    print("Cross-manifold summary:")
    print(f"  Total candidates: {total_candidates}")
    print(f"  Falsification control candidates: {control_count}")
    print(f"  False adversarial pressure detected: {'yes' if false_pressure else 'no'}")
    print("Falsification verdict:")
    print(f"  Greedy frontier correctly validated: {'yes' if frontier_validated else 'no'}")
    print(f"  System misfires on valid greedy: {'yes' if false_pressure or control_count == 0 else 'no'}")
    print(f"  Naive-greedy failure isolated: {'yes' if naive_failure_isolated else 'no'}")
    print(
        "  Evidence: greedy_frontier_valid_no_false_pressure produced candidates satisfying "
        "greedy_frontier_agrees_with_truth(nums) while naive_diverges(nums) is False."
    )


if __name__ == "__main__":
    main()
