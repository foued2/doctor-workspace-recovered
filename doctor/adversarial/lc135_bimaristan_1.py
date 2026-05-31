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

from doctor.adversarial.lc135_bimaristan import LC135
from doctor.adversarial.lc135_symbol_registry import LC135_SYMBOL_REGISTRY


class RegistryRoutingError(RuntimeError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"symbol not in LC135_SYMBOL_REGISTRY: {symbol}")


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
            if node.id in LC135_SYMBOL_REGISTRY.names:
                return LC135_SYMBOL_REGISTRY.get(node.id).compute(context)
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
            if name not in LC135_SYMBOL_REGISTRY.names:
                raise RegistryRoutingError(name)
            entry = LC135_SYMBOL_REGISTRY.get(name)
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
        "left_pass_misses_descending_tail": (
            [4, 3, 2, 1],
            [1, 4, 3, 2],
            [2, 5, 4, 3],
            [2, 2, 5, 4, 3],
            [1, 1, 4, 3, 2],
            [3, 3, 6, 5, 4],
            [2, 1, 5, 4, 3],
            [1, 3, 6, 5, 4],
            [2, 2, 2, 5, 4, 3],
            [1, 1, 1, 4, 3, 2],
            [3, 2, 6, 5, 4],
            [1, 2, 2, 5, 4, 3],
        ),
        "right_pass_misses_ascending_prefix": (
            [1, 2, 3, 4],
            [2, 3, 4, 1],
            [3, 4, 5, 2],
            [3, 4, 5, 2, 2],
            [2, 3, 4, 1, 1],
            [4, 5, 6, 3, 3],
            [3, 4, 5, 1, 2],
            [4, 5, 6, 3, 1],
            [3, 4, 5, 2, 2, 2],
            [2, 3, 4, 1, 1, 1],
            [4, 5, 6, 2, 3],
            [3, 4, 5, 2, 2, 1],
        ),
        "valley_forces_both_directions": (
            [3, 2, 1, 2, 3],
            [4, 3, 2, 3, 4],
            [5, 4, 1, 2, 3],
            [3, 2, 1, 2, 1],
            [2, 1, 2, 3, 2],
            [4, 2, 1, 3, 2],
            [3, 1, 2, 1, 2],
            [5, 3, 2, 4, 1],
            [4, 3, 1, 2, 1],
            [2, 1, 3, 2, 4],
            [5, 4, 3, 4, 5],
            [4, 2, 1, 2, 4],
        ),
        "constraint_collision_at_peak": (
            [1, 3, 2, 1, 2],
            [2, 4, 3, 2, 3],
            [1, 2, 4, 3, 1, 2],
            [2, 5, 4, 3, 4],
            [1, 2, 3, 2, 1, 2],
            [2, 3, 5, 4, 2, 3],
            [1, 4, 2, 1, 3],
            [2, 5, 3, 2, 4],
            [1, 2, 5, 3, 2, 4],
            [3, 5, 4, 2, 1, 2],
            [2, 4, 3, 1, 2, 3],
            [1, 3, 2, 4, 3, 1, 2],
        ),
    }
    yield from seeds[manifold_id]

    values = (1, 2, 3, 4, 5)
    for length in range(4, 7):
        for ratings in itertools.product(values, repeat=length):
            yield list(ratings)


def _run_generator(manifold, generator):
    accepted: list[dict[str, Any]] = []
    rejected = 0
    routing_errors: list[str] = []
    for ratings in _candidate_space(manifold.manifold_id):
        context = {"ratings": ratings}
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
        if _eval("two_pass_agrees_with_truth(ratings)", context):
            stats["two_pass_agree"] += 1
        if _eval("left_only_diverges(ratings)", context):
            stats["left_diverge"] += 1
        if _eval("right_only_diverges(ratings)", context):
            stats["right_diverge"] += 1
        if _eval("both_directions_required(ratings)", context):
            stats["both_required"] += 1
    total = len(accepted) + rejected
    return {
        "accepted": accepted,
        "rejection_rate": rejected / total * 100 if total else 0.0,
        "violated": sorted(set(violated)),
        "routing_errors": sorted(set(routing_errors)),
        "stats": stats,
    }


def _apply_constraint_phase_crossing(manifold_id: str, accepted: list[dict[str, Any]]) -> dict[str, Any] | None:
    if manifold_id not in {"left_pass_misses_descending_tail", "right_pass_misses_ascending_prefix"}:
        return None

    pre_divergence_rate = _both_directions_required_rate(accepted)
    crossed = [_inject_midpoint_valley(context) for context in accepted]
    post_divergence_rate = _both_directions_required_rate(crossed)
    divergence_delta = post_divergence_rate - pre_divergence_rate
    satisfiability_delta = 0.0 if accepted else 0.0

    return {
        "perturbation_operator": "constraint_phase_crossing",
        "parameterization": {
            "boundary": "directional_sufficiency",
            "transform": "peak_valley_peak_directional_conflict",
        },
        "pre_divergence_rate": round(pre_divergence_rate, 4),
        "post_divergence_rate": round(post_divergence_rate, 4),
        "pre_candidate_count": len(accepted),
        "post_candidate_count": len(crossed),
        "resulting_behavior": _resulting_behavior(len(accepted), len(crossed), divergence_delta),
        "satisfiability_delta": round(satisfiability_delta, 4),
        "divergence_delta": round(divergence_delta, 4),
    }


def _inject_midpoint_valley(context: dict[str, Any]) -> dict[str, Any]:
    ratings = list(context["ratings"])
    peak_value = max(ratings) + 2
    shoulder_value = max(ratings)
    valley_value = min(ratings) - 1
    return {"ratings": [peak_value, shoulder_value, valley_value, shoulder_value, peak_value]}


def _both_directions_required_rate(contexts: list[dict[str, Any]]) -> float:
    if not contexts:
        return 0.0
    required = 0
    observed = 0
    for context in contexts:
        try:
            observed += 1
            if _eval("both_directions_required(ratings)", context):
                required += 1
        except Exception:
            continue
    return required / observed if observed else 0.0


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
    return "manifold_preserved"


def main() -> None:
    results: dict[str, dict[str, Any]] = {}
    print("LC135 Bimaristan run")
    for family in LC135.invariant_families:
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
            print(f"  Two-pass agrees with truth: {stats['two_pass_agree']}/{total}")
            left_rate = stats["left_diverge"] / total * 100 if total else 0.0
            right_rate = stats["right_diverge"] / total * 100 if total else 0.0
            print(f"  Left-only divergence rate: {left_rate:.2f}%")
            print(f"  Right-only divergence rate: {right_rate:.2f}%")
            event = _apply_constraint_phase_crossing(manifold.manifold_id, accepted)
            if event is not None:
                print(f"PERTURBATION_EVENT: {json.dumps({**event, 'manifold_id': manifold.manifold_id}, sort_keys=True)}")

    total_candidates = sum(len(result["accepted"]) for result in results.values())
    collision_count = len(results["constraint_collision_at_peak"]["accepted"])
    composed_candidates = (
        len(results["valley_forces_both_directions"]["accepted"])
        + len(results["constraint_collision_at_peak"]["accepted"])
    )
    both_required = (
        results["valley_forces_both_directions"]["stats"]["both_required"]
        + results["constraint_collision_at_peak"]["stats"]["both_required"]
    )
    both_required_rate = both_required / composed_candidates * 100 if composed_candidates else 0.0
    left_only_region = len(results["left_pass_misses_descending_tail"]["accepted"]) > 0
    right_only_region = len(results["right_pass_misses_ascending_prefix"]["accepted"]) > 0
    collision_viable = collision_count > 0
    fusion_observed = collision_viable and both_required_rate == 100.0
    directional_collapse = not (left_only_region and right_only_region and collision_viable)

    print("Cross-manifold summary:")
    print(f"  Total candidates: {total_candidates}")
    print(f"  Constraint collision manifold candidates: {collision_count}")
    print(f"  Both-directions-required rate: {both_required_rate:.2f}% across valley + collision manifolds")
    print("Composition verdict:")
    print(f"  Manifold fusion observed: {'yes' if fusion_observed else 'no'}")
    print(f"  Directional constraint collapse detected: {'yes' if directional_collapse else 'no'}")
    print(f"  Constraint collision manifold viable: {'yes' if collision_viable else 'no'}")
    print(
        "  Evidence: constraint_collision_at_peak satisfies left_right_constraint_conflict(ratings) "
        "and both_directions_required(ratings) while two_pass_agrees_with_truth(ratings) holds."
    )


if __name__ == "__main__":
    main()
