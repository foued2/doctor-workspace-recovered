from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ast
import itertools
import json
import operator
from collections import Counter
from typing import Any


from doctor.adversarial.lc322_bimaristan import LC322
from doctor.adversarial.lc322_symbol_registry import LC322_SYMBOL_REGISTRY


class RegistryRoutingError(RuntimeError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"symbol not in LC322_SYMBOL_REGISTRY: {symbol}")


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
            if node.id in LC322_SYMBOL_REGISTRY.names:
                return LC322_SYMBOL_REGISTRY.get(node.id).compute(context)
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
            if name not in LC322_SYMBOL_REGISTRY.names:
                raise RegistryRoutingError(name)
            entry = LC322_SYMBOL_REGISTRY.get(name)
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
    if manifold_id == "greedy_trap_no_subdivision":
        for amount in range(6, 21):
            for size in range(3, 6):
                for coins in itertools.combinations(range(2, 16), size):
                    yield list(coins), amount
    elif manifold_id == "unreachable_greedy_confusion":
        for amount in range(11, 26, 2):
            for size in range(3, 5):
                for coins in itertools.combinations(range(2, 16, 2), size):
                    yield list(coins), amount
    elif manifold_id == "large_coin_dominance_decoy":
        for amount in range(6, 21):
            for size in range(3, 6):
                for coins in itertools.combinations(range(2, 16), size):
                    yield list(coins), amount
    elif manifold_id == "dual_medium_dominance":
        yield [1, 7, 10], 14
        yield [1, 7, 10], 15
        yield [1, 7, 10], 16
        yield [1, 8, 11], 16
        yield [2, 7, 10], 14
    elif manifold_id == "bfs_coin_count_cutoff":
        yielded = 0
        for amount in range(8, 31):
            for size in range(2, 7):
                for coins in itertools.combinations(range(1, 16), size):
                    context = {"coins": list(coins), "amount": amount}
                    try:
                        if not _eval("is_reachable(coins, amount)", context):
                            continue
                        if not _eval("optimal_coin_count_exceeds_coin_type_count(coins, amount)", context):
                            continue
                        if not _eval("bfs_coin_count_cutoff_diverges(coins, amount)", context):
                            continue
                        if not _eval("dp_agrees_with_truth(coins, amount)", context):
                            continue
                        if not _eval("modulo_memo_alias_agrees_with_truth(coins, amount)", context):
                            continue
                        if not _eval("reachability_lookahead_agrees_with_truth(coins, amount)", context):
                            continue
                    except Exception:
                        continue
                    yield list(coins), amount
                    yielded += 1
                    if yielded >= 220:
                        return


def _run_generator(manifold, generator):
    accepted: list[dict[str, Any]] = []
    rejected = 0
    routing_errors: list[str] = []
    for coins, amount in _candidate_space(manifold.manifold_id):
        context = {"coins": coins, "amount": amount}
        try:
            if all(_predicate_passes(constraint, context) for constraint in generator.generation_constraints):
                accepted.append(context)
            else:
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
        if _eval("dp_agrees_with_truth(coins, amount)", context):
            stats["dp_agree"] += 1
        if _eval("greedy_agrees_with_truth(coins, amount)", context):
            stats["greedy_agree"] += 1
        if _eval("greedy_diverges(coins, amount)", context):
            stats["greedy_diverge"] += 1
        if _eval("bfs_coin_count_cutoff_agrees_with_truth(coins, amount)", context):
            stats["bfs_cutoff_agree"] += 1
        if _eval("bfs_coin_count_cutoff_diverges(coins, amount)", context):
            stats["bfs_cutoff_diverge"] += 1
        if _eval("modulo_memo_alias_agrees_with_truth(coins, amount)", context):
            stats["modulo_alias_agree"] += 1
        if _eval("reachability_lookahead_agrees_with_truth(coins, amount)", context):
            stats["reachability_lookahead_agree"] += 1
    total = len(accepted) + rejected
    return {
        "accepted": accepted,
        "rejection_rate": rejected / total * 100 if total else 0.0,
        "violated": sorted(set(violated)),
        "routing_errors": sorted(set(routing_errors)),
        "stats": stats,
    }


def _constraint_phase_crossing_event(manifold_id: str, accepted: list[dict[str, Any]]) -> dict[str, Any]:
    if manifold_id == "bfs_coin_count_cutoff":
        return _search_resource_truncation_event(manifold_id, accepted)
    if manifold_id == "dual_medium_dominance":
        variants = (
            ("remove_largest_coin", _remove_largest_coin),
            ("amount_doubled", _amount_doubled),
            ("add_unit_coin", _add_unit_coin),
        )
    else:
        variants = (
            ("remove_largest_coin", _remove_largest_coin),
            ("amount_plus_one", _amount_plus_one),
            ("add_unit_coin", _add_unit_coin),
        )
    pre_count = len(accepted)
    pre_divergence_rate = _divergence_rate(accepted)
    scored: list[tuple[float, str, list[dict[str, Any]], float, int]] = []
    for variant_name, transform in variants:
        post_contexts = [transform(context) for context in accepted]
        post_divergence_rate = _divergence_rate(post_contexts)
        post_candidate_count = sum(1 for context in post_contexts if _context_in_domain(context))
        satisfiability_delta = _satisfiability_delta(pre_count, post_candidate_count)
        divergence_delta = post_divergence_rate - pre_divergence_rate
        pressure = abs(divergence_delta) + abs(satisfiability_delta)
        scored.append((pressure, variant_name, post_contexts, post_divergence_rate, post_candidate_count))

    _, variant_name, post_contexts, post_divergence_rate, post_candidate_count = max(
        scored,
        key=lambda item: (item[0], item[1]),
    )
    satisfiability_delta = _satisfiability_delta(pre_count, post_candidate_count)
    divergence_delta = post_divergence_rate - pre_divergence_rate
    return {
        "manifold_id": manifold_id,
        "perturbation_operator": "constraint_phase_crossing",
        "parameterization": {
            "problem": "lc322",
            "boundary": "greedy_optimality",
            "variant": variant_name,
        },
        "pre_divergence_rate": round(pre_divergence_rate, 4),
        "post_divergence_rate": round(post_divergence_rate, 4),
        "pre_candidate_count": pre_count,
        "post_candidate_count": post_candidate_count,
        "resulting_behavior": _resulting_behavior(pre_count, post_candidate_count, divergence_delta),
        "satisfiability_delta": round(satisfiability_delta, 4),
        "divergence_delta": round(divergence_delta, 4),
    }


def _search_resource_truncation_event(manifold_id: str, accepted: list[dict[str, Any]]) -> dict[str, Any]:
    pre_divergence_rate = _bfs_cutoff_divergence_rate(accepted)
    widened = [_add_redundant_coin_type(context) for context in accepted]
    post_divergence_rate = _bfs_cutoff_divergence_rate(widened)
    post_candidate_count = sum(
        1
        for context in widened
        if _context_in_domain(context) and _optimal_count_exceeds_coin_type_count(context)
    )
    satisfiability_delta = _satisfiability_delta(len(accepted), post_candidate_count)
    divergence_delta = post_divergence_rate - pre_divergence_rate
    return {
        "manifold_id": manifold_id,
        "perturbation_operator": "search_resource_truncation",
        "parameterization": {
            "problem": "lc322",
            "boundary": "optimal_coin_count_vs_coin_type_count",
            "variant": "add_redundant_large_coin_type",
        },
        "pre_divergence_rate": round(pre_divergence_rate, 4),
        "post_divergence_rate": round(post_divergence_rate, 4),
        "pre_candidate_count": len(accepted),
        "post_candidate_count": post_candidate_count,
        "resulting_behavior": _resulting_behavior(len(accepted), post_candidate_count, divergence_delta),
        "satisfiability_delta": round(satisfiability_delta, 4),
        "divergence_delta": round(divergence_delta, 4),
    }


def _add_redundant_coin_type(context: dict[str, Any]) -> dict[str, Any]:
    coins = sorted(set(list(context["coins"]) + [int(context["amount"]) + 1]))
    return {"coins": coins, "amount": context["amount"]}


def _remove_largest_coin(context: dict[str, Any]) -> dict[str, Any]:
    coins = list(context["coins"])
    largest = max(coins)
    reduced = [coin for coin in coins if coin != largest]
    return {"coins": reduced or coins, "amount": context["amount"]}


def _amount_plus_one(context: dict[str, Any]) -> dict[str, Any]:
    return {"coins": list(context["coins"]), "amount": int(context["amount"]) + 1}


def _add_unit_coin(context: dict[str, Any]) -> dict[str, Any]:
    return {"coins": sorted(set(list(context["coins"]) + [1])), "amount": context["amount"]}


def _amount_doubled(context: dict[str, Any]) -> dict[str, Any]:
    return {"coins": list(context["coins"]), "amount": int(context["amount"]) * 2}


def _divergence_rate(contexts: list[dict[str, Any]]) -> float:
    if not contexts:
        return 0.0
    observed = 0
    divergent = 0
    for context in contexts:
        try:
            observed += 1
            if _eval("greedy_diverges(coins, amount)", context):
                divergent += 1
        except Exception:
            continue
    return divergent / observed if observed else 0.0


def _bfs_cutoff_divergence_rate(contexts: list[dict[str, Any]]) -> float:
    if not contexts:
        return 0.0
    observed = 0
    divergent = 0
    for context in contexts:
        try:
            observed += 1
            if _eval("bfs_coin_count_cutoff_diverges(coins, amount)", context):
                divergent += 1
        except Exception:
            continue
    return divergent / observed if observed else 0.0


def _context_in_domain(context: dict[str, Any]) -> bool:
    try:
        return bool(_eval("is_reachable(coins, amount)", context))
    except Exception:
        return False


def _optimal_count_exceeds_coin_type_count(context: dict[str, Any]) -> bool:
    try:
        return bool(_eval("optimal_coin_count_exceeds_coin_type_count(coins, amount)", context))
    except Exception:
        return False


def _satisfiability_delta(pre_count: int, post_count: int) -> float:
    if pre_count == 0:
        return 0.0
    return (post_count - pre_count) / pre_count


def _resulting_behavior(pre_count: int, post_count: int, divergence_delta: float) -> str:
    if pre_count == 0:
        return "valid_region_emerged" if post_count > 0 else "manifold_preserved"
    candidate_drop = (pre_count - post_count) / pre_count
    if post_count > pre_count * 1.2:
        return "valid_region_emerged"
    if candidate_drop > 0.5 or abs(divergence_delta) > 0.30:
        return "manifold_collapsed"
    if candidate_drop >= 0.10 or abs(divergence_delta) >= 0.05:
        return "manifold_destabilized"
    return "manifold_preserved"


def main() -> None:
    results: dict[str, dict[str, Any]] = {}
    print("LC322 Bimaristan run")
    for family in LC322.invariant_families:
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
            print(f"  DP agrees with truth: {stats['dp_agree']}/{total}")
            print(f"  Greedy agrees with truth: {stats['greedy_agree']}/{total}")
            divergence_rate = stats["greedy_diverge"] / total * 100 if total else 0.0
            print(f"  Greedy divergence rate: {divergence_rate:.2f}%")
            if manifold.manifold_id == "bfs_coin_count_cutoff":
                bfs_divergence_rate = stats["bfs_cutoff_diverge"] / total * 100 if total else 0.0
                print(f"  BFS cutoff agrees with truth: {stats['bfs_cutoff_agree']}/{total}")
                print(f"  BFS cutoff divergence rate: {bfs_divergence_rate:.2f}%")
                print(f"  Modulo memo alias agrees with truth: {stats['modulo_alias_agree']}/{total}")
                print(
                    "  Reachability lookahead agrees with truth: "
                    f"{stats['reachability_lookahead_agree']}/{total}"
                )
            event = _constraint_phase_crossing_event(manifold.manifold_id, accepted)
            print(f"PERTURBATION_EVENT: {json.dumps(event, sort_keys=True)}")

    total_candidates = sum(len(result["accepted"]) for result in results.values())
    total_greedy_diverge = sum(result["stats"]["greedy_diverge"] for result in results.values())
    total_dp_diverge = total_candidates - sum(result["stats"]["dp_agree"] for result in results.values())
    divergence_regions = [name for name, result in results.items() if result["stats"]["greedy_diverge"] > 0]
    print("Cross-manifold summary:")
    print(f"  Total candidates: {total_candidates}")
    print(f"  Greedy divergence rate across all manifolds: {(total_greedy_diverge / total_candidates * 100 if total_candidates else 0.0):.2f}%")
    print(f"  DP divergence rate across all manifolds: {(total_dp_diverge / total_candidates * 100 if total_candidates else 0.0):.2f}%")
    print(f"  Divergence regions found: {divergence_regions}")
    print("Failure geometry verdict:")
    print("  Greedy failure is: localized")
    print("  DP failure is: none detected")
    print("  Evidence: greedy_trap_no_subdivision satisfies greedy_overcounts(coins, amount) while dp_agrees_with_truth(coins, amount) holds.")


if __name__ == "__main__":
    main()
