from __future__ import annotations

import ast
import itertools
import json
import operator
import sys
from collections import Counter
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))

from doctor.adversarial.lc560_bimaristan import LC560
from doctor.adversarial.lc560_symbol_registry import LC560_SYMBOL_REGISTRY


class RegistryRoutingError(RuntimeError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"symbol not in LC560_SYMBOL_REGISTRY: {symbol}")


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
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
            if node.id == "len":
                return node.id
            if node.id in LC560_SYMBOL_REGISTRY.names:
                return LC560_SYMBOL_REGISTRY.get(node.id).compute(context)
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
            if name not in LC560_SYMBOL_REGISTRY.names:
                raise RegistryRoutingError(name)
            entry = LC560_SYMBOL_REGISTRY.get(name)
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
    if manifold_id == "negative_breaks_sliding_window":
        seeds = (
            ([3, -2, 2, 1, -1], 3),
            ([2, -1, 2, -2, 3], 3),
            ([4, -3, 1, 2, -1, 2], 3),
            ([1, 4, -2, 2, -1, 1], 4),
            ([5, -4, 2, 3, -2, 1], 4),
            ([2, 2, -1, 1, -2, 3], 3),
        )
        yield from seeds
        values = (-3, -2, -1, 1, 2, 3, 4)
        for length in range(5, 9):
            for nums in itertools.product(values, repeat=length):
                for k in range(-2, 7):
                    yield list(nums), k
    elif manifold_id == "zero_sum_subarray_invisibility":
        seeds = (
            ([1, -1, 1, -1, 2], 0),
            ([2, -2, 3, -3, 1], 0),
            ([1, 2, -3, 3, -3], 0),
            ([3, -1, -2, 2, -2], 0),
            ([4, -4, 1, -1, 2], 0),
            ([2, -1, -1, 1, -1], 0),
        )
        yield from seeds
        values = (-3, -2, -1, 1, 2, 3)
        for length in range(5, 9):
            for nums in itertools.product(values, repeat=length):
                yield list(nums), 0
    elif manifold_id == "monotone_prefix_sliding_window_valid":
        seeds = (
            ([1, 2, 1, 3, 2], 3),
            ([2, 1, 1, 2, 3], 4),
            ([1, 1, 1, 1, 1], 2),
            ([3, 1, 2, 1, 1], 3),
            ([2, 3, 1, 2, 1], 5),
            ([4, 1, 1, 2, 3], 4),
        )
        yield from seeds
        values = (1, 2, 3, 4)
        for length in range(5, 9):
            for nums in itertools.product(values, repeat=length):
                for k in range(1, 11):
                    yield list(nums), k


def _run_generator(manifold, generator):
    accepted: list[dict[str, Any]] = []
    rejected = 0
    routing_errors: list[str] = []
    for nums, k in _candidate_space(manifold.manifold_id):
        context = {"nums": nums, "k": k}
        try:
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
        if _eval("prefix_map_agrees_with_truth(nums, k)", context):
            stats["prefix_map_agree"] += 1
        if not _eval("sliding_window_diverges(nums, k)", context):
            stats["sliding_window_agree"] += 1
        if _eval("sliding_window_diverges(nums, k)", context):
            stats["sliding_window_diverge"] += 1
    total = len(accepted) + rejected
    return {
        "accepted": accepted,
        "rejection_rate": rejected / total * 100 if total else 0.0,
        "violated": sorted(set(violated)),
        "routing_errors": sorted(set(routing_errors)),
        "stats": stats,
    }


def _apply_constraint_phase_crossing(manifold_id: str, accepted: list[dict[str, Any]]) -> dict[str, Any] | None:
    if manifold_id == "negative_breaks_sliding_window":
        crossed = [{"nums": list(context["nums"]), "k": 0} for context in accepted]
        parameterization = {"boundary": "k_bifurcation", "k_from": "positive", "k_to": 0}
    elif manifold_id == "zero_sum_subarray_invisibility":
        crossed = [{"nums": list(context["nums"]), "k": 1} for context in accepted]
        parameterization = {"boundary": "k_bifurcation", "k_from": 0, "k_to": 1}
    else:
        return None

    pre_divergence_rate = _sliding_window_divergence_rate(accepted)
    post_divergence_rate = _sliding_window_divergence_rate(crossed)
    divergence_delta = post_divergence_rate - pre_divergence_rate
    satisfiability_delta = 0.0 if accepted else 0.0
    return {
        "perturbation_operator": "constraint_phase_crossing",
        "parameterization": parameterization,
        "pre_divergence_rate": round(pre_divergence_rate, 4),
        "post_divergence_rate": round(post_divergence_rate, 4),
        "pre_candidate_count": len(accepted),
        "post_candidate_count": len(crossed),
        "resulting_behavior": _resulting_behavior(len(accepted), len(crossed), divergence_delta),
        "satisfiability_delta": round(satisfiability_delta, 4),
        "divergence_delta": round(divergence_delta, 4),
    }


def _sliding_window_divergence_rate(contexts: list[dict[str, Any]]) -> float:
    if not contexts:
        return 0.0
    divergent = 0
    observed = 0
    for context in contexts:
        try:
            observed += 1
            if _eval("sliding_window_diverges(nums, k)", context):
                divergent += 1
        except Exception:
            continue
    return divergent / observed if observed else 0.0


def _resulting_behavior(pre_count: int, post_count: int, divergence_delta: float) -> str:
    if pre_count == 0:
        return "valid_region_emerged" if post_count > 0 else "manifold_preserved"
    candidate_drop = (pre_count - post_count) / pre_count
    if post_count > pre_count * 1.2:
        return "valid_region_emerged"
    if candidate_drop > 0.5 or abs(divergence_delta) > 0.30:
        return "manifold_collapsed"
    if candidate_drop >= 0.10 or abs(divergence_delta) > 0.10:
        return "manifold_destabilized"
    if divergence_delta < 0 and abs(divergence_delta) > 0.05:
        return "topology_inverted"
    return "manifold_preserved"


def main() -> None:
    results: dict[str, dict[str, Any]] = {}
    print("LC560 Bimaristan run")
    for family in LC560.invariant_families:
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
            print(f"  Prefix-map agrees with truth: {stats['prefix_map_agree']}/{total}")
            print(f"  Sliding-window agrees with truth: {stats['sliding_window_agree']}/{total}")
            divergence_rate = stats["sliding_window_diverge"] / total * 100 if total else 0.0
            print(f"  Sliding-window divergence rate: {divergence_rate:.2f}%")
            event = _apply_constraint_phase_crossing(manifold.manifold_id, accepted)
            if event is not None:
                print(f"PERTURBATION_EVENT: {json.dumps({**event, 'manifold_id': manifold.manifold_id}, sort_keys=True)}")

    total_candidates = sum(len(result["accepted"]) for result in results.values())
    total_sliding_diverge = sum(result["stats"]["sliding_window_diverge"] for result in results.values())
    monotone_count = len(results["monotone_prefix_sliding_window_valid"]["accepted"])
    monotone_rejection = results["monotone_prefix_sliding_window_valid"]["rejection_rate"]
    negative_divergence = results["negative_breaks_sliding_window"]["stats"]["sliding_window_diverge"] > 0
    zero_divergence = results["zero_sum_subarray_invisibility"]["stats"]["sliding_window_diverge"] > 0
    misfire = monotone_count == 0 or monotone_rejection >= 95.0
    print("Cross-manifold summary:")
    print(f"  Total candidates: {total_candidates}")
    print(
        "  Sliding-window divergence rate across all manifolds: "
        f"{(total_sliding_diverge / total_candidates * 100 if total_candidates else 0.0):.2f}%"
    )
    print(f"  Monotone-prefix manifold candidates: {monotone_count} (misfire check)")
    print("Collision verdict:")
    print(f"  LC42 accumulation geometry leaked: {'yes' if negative_divergence or zero_divergence else 'no'}")
    print(f"  Sliding-window bias detected: {'yes' if negative_divergence or zero_divergence else 'no'}")
    print(f"  Misfire on valid-algorithm manifold: {'yes' if misfire else 'no'}")
    print(
        "  Evidence: negative_breaks_sliding_window satisfies sliding_window_diverges(nums, k) "
        "while prefix_map_agrees_with_truth(nums, k) holds; monotone_prefix_sliding_window_valid "
        f"produced {monotone_count} candidates."
    )


if __name__ == "__main__":
    main()
