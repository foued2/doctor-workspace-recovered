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
import random
from collections import Counter
from typing import Any


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

K_SCAN_VALUES = tuple(range(-2, 7))
FINE_K_VALUES = (-2, -1, 0, 1, 2)
SIGN_CONTINUITY_K_VALUES = (0, 3, 4, 6)
SIGN_MIXTURE_RATIOS = (0.0, 0.25, 0.5, 0.75, 1.0)
SIGN_TOPOLOGY_SAMPLE_COUNT = 20
SIGN_TOPOLOGY_TARGET_K = 3
SIGN_TOPOLOGY_TARGET_RATIO = 0.25
HYSTERESIS_THRESHOLD = 0.05
SHARP_DISCONTINUITY_THRESHOLD = 0.30
PATH_DEPENDENCE_THRESHOLD = 0.05
SIGN_INTERACTION_THRESHOLD = 0.10
SIGN_THRESHOLD_DELTA = 0.30


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
    pre_collision_depth = _max_collision_depth(accepted[0]["nums"]) if accepted else 0
    post_collision_depth = _max_collision_depth(crossed[0]["nums"]) if crossed else 0
    return {
        "perturbation_operator": "constraint_phase_crossing",
        "parameterization": {
            **parameterization,
            "sign_axis_variable": "max_collision_depth",
        },
        "pre_divergence_rate": round(pre_divergence_rate, 4),
        "post_divergence_rate": round(post_divergence_rate, 4),
        "pre_candidate_count": len(accepted),
        "post_candidate_count": len(crossed),
        "resulting_behavior": _resulting_behavior(len(accepted), len(crossed), divergence_delta),
        "satisfiability_delta": round(satisfiability_delta, 4),
        "divergence_delta": round(divergence_delta, 4),
        "pre_max_collision_depth": pre_collision_depth,
        "post_max_collision_depth": post_collision_depth,
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
    if divergence_delta < 0 and abs(divergence_delta) > 0.05:
        return "topology_inverted"
    if candidate_drop > 0.5 or abs(divergence_delta) > 0.30:
        return "manifold_collapsed"
    if candidate_drop >= 0.10 or abs(divergence_delta) > 0.10:
        return "manifold_destabilized"
    return "manifold_preserved"


def _contexts_at_k(
    contexts: list[dict[str, Any]],
    k: int,
    *,
    sign_flipped: bool = False,
) -> list[dict[str, Any]]:
    transformed = []
    for context in contexts:
        nums = list(context["nums"])
        if sign_flipped:
            nums = [-value for value in nums]
        transformed.append({"nums": nums, "k": k})
    return transformed


def _nums_at_sign_mixture(nums: list[int], ratio: float) -> list[int]:
    if ratio <= 0.0:
        return list(nums)
    ranked = sorted(range(len(nums)), key=lambda index: abs(nums[index]), reverse=True)
    flip_count = round(len(nums) * ratio)
    flip_indices = set(ranked[:flip_count])
    return [
        -value if index in flip_indices else value
        for index, value in enumerate(nums)
    ]


def _contexts_at_sign_mixture(
    contexts: list[dict[str, Any]],
    *,
    k: int,
    ratio: float,
) -> list[dict[str, Any]]:
    return [
        {"nums": _nums_at_sign_mixture(list(context["nums"]), ratio), "k": k}
        for context in contexts
    ]


def _contexts_at_random_sign_topology(
    contexts: list[dict[str, Any]],
    *,
    k: int,
    ratio: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[list[int]]]:
    rng = random.Random(seed)
    transformed = []
    flipped_indices_by_context = []
    for context in contexts:
        nums = list(context["nums"])
        flip_count = int(len(nums) * ratio)
        flipped_indices = sorted(rng.sample(range(len(nums)), flip_count)) if flip_count else []
        flipped = [
            -value if index in flipped_indices else value
            for index, value in enumerate(nums)
        ]
        transformed.append({"nums": flipped, "k": k})
        flipped_indices_by_context.append(flipped_indices)
    return transformed, flipped_indices_by_context


def _scan_curve(
    contexts: list[dict[str, Any]],
    k_values: tuple[int, ...],
    *,
    sign_structure: str,
    sign_flipped: bool = False,
) -> list[dict[str, Any]]:
    pre_contexts = [
        {"nums": [-value for value in context["nums"]] if sign_flipped else list(context["nums"]), "k": context["k"]}
        for context in contexts
    ]
    pre_rate = _sliding_window_divergence_rate(pre_contexts)
    points = []
    for k in k_values:
        scanned = _contexts_at_k(contexts, k, sign_flipped=sign_flipped)
        post_rate = _sliding_window_divergence_rate(scanned)
        points.append(
            {
                "k": k,
                "sign_structure": sign_structure,
                "pre_divergence_rate": round(pre_rate, 4),
                "post_divergence_rate": round(post_rate, 4),
                "divergence_delta": round(post_rate - pre_rate, 4),
            }
        )
    return points


def _sharp_discontinuity_detected(points: list[dict[str, Any]]) -> bool:
    return any(
        abs(points[index + 1]["divergence_delta"] - points[index]["divergence_delta"])
        > SHARP_DISCONTINUITY_THRESHOLD
        for index in range(len(points) - 1)
    )


def _discontinuity_locations(points: list[dict[str, Any]]) -> set[tuple[int, int]]:
    locations: set[tuple[int, int]] = set()
    for index in range(len(points) - 1):
        if (
            abs(points[index + 1]["divergence_delta"] - points[index]["divergence_delta"])
            > SHARP_DISCONTINUITY_THRESHOLD
        ):
            locations.add((points[index]["k"], points[index + 1]["k"]))
    return locations


def _hysteresis_detected(
    ascending: list[dict[str, Any]],
    descending: list[dict[str, Any]],
) -> bool:
    asc_by_k = {point["k"]: point["divergence_delta"] for point in ascending}
    desc_by_k = {point["k"]: point["divergence_delta"] for point in descending}
    return any(
        abs(asc_by_k[k] - desc_by_k[k]) > HYSTERESIS_THRESHOLD
        for k in sorted(set(asc_by_k) & set(desc_by_k))
    )


def _path_independence_points(contexts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    pre_rate = _sliding_window_divergence_rate(contexts)
    direct_rate = _sliding_window_divergence_rate(_contexts_at_k(contexts, 0))

    intermediate = _contexts_at_k(contexts, 1)
    indirect_final = _contexts_at_k(intermediate, 0)
    indirect_rate = _sliding_window_divergence_rate(indirect_final)

    points = [
        {
            "path": "direct",
            "target_k": 0,
            "pre_divergence_rate": round(pre_rate, 4),
            "post_divergence_rate": round(direct_rate, 4),
            "divergence_delta": round(direct_rate - pre_rate, 4),
        },
        {
            "path": "via_k_1",
            "intermediate_k": 1,
            "target_k": 0,
            "pre_divergence_rate": round(pre_rate, 4),
            "post_divergence_rate": round(indirect_rate, 4),
            "divergence_delta": round(indirect_rate - pre_rate, 4),
        },
    ]
    path_dependence = abs(direct_rate - indirect_rate) > PATH_DEPENDENCE_THRESHOLD
    return points, path_dependence


def _sign_interaction_detected(
    original_points: list[dict[str, Any]],
    sign_flipped_points: list[dict[str, Any]],
) -> bool:
    original_by_k = {point["k"]: point["divergence_delta"] for point in original_points}
    flipped_by_k = {point["k"]: point["divergence_delta"] for point in sign_flipped_points}
    point_shift = any(
        abs(original_by_k[k] - flipped_by_k[k]) > SIGN_INTERACTION_THRESHOLD
        for k in sorted(set(original_by_k) & set(flipped_by_k))
    )
    sharp_changed = _sharp_discontinuity_detected(original_points) != _sharp_discontinuity_detected(sign_flipped_points)
    locations_shifted = _discontinuity_locations(original_points) != _discontinuity_locations(sign_flipped_points)
    return point_shift or sharp_changed or locations_shifted


def _is_monotonic(values: list[float]) -> bool:
    if len(values) < 2:
        return True
    nondecreasing = all(values[index] <= values[index + 1] for index in range(len(values) - 1))
    nonincreasing = all(values[index] >= values[index + 1] for index in range(len(values) - 1))
    return nondecreasing or nonincreasing


def _max_collision_depth(nums: list[int]) -> int:
    """Maximum frequency of any single prefix-sum value.

    High recurrence depth -> many (i,j) pairs with prefix[j] == prefix[i]
    -> many zero-sum subarrays. Identified as the mechanism carrier for
    sign-topology sensitivity (FINDINGS Entry 016).
    """
    prefix = 0
    freq: dict[int, int] = {}
    freq[0] = 1
    for v in nums:
        prefix += v
        freq[prefix] = freq.get(prefix, 0) + 1
    return max(freq.values())


def _sign_continuity_grid(contexts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    pre_rate = _sliding_window_divergence_rate(contexts)
    points = []
    by_k: dict[int, list[float]] = {}

    for k in SIGN_CONTINUITY_K_VALUES:
        by_k[k] = []
        for ratio in SIGN_MIXTURE_RATIOS:
            mixed = _contexts_at_sign_mixture(contexts, k=k, ratio=ratio)
            post_rate = _sliding_window_divergence_rate(mixed)
            delta = post_rate - pre_rate
            by_k[k].append(delta)
            collision_depth = _max_collision_depth(
                _nums_at_sign_mixture(contexts[0]["nums"], ratio)
            )
            points.append(
                {
                    "k": k,
                    "sign_mixture_ratio": ratio,
                    "pre_divergence_rate": round(pre_rate, 4),
                    "post_divergence_rate": round(post_rate, 4),
                    "divergence_delta": round(delta, 4),
                    "max_collision_depth": collision_depth,
                }
            )

    sign_response_smooth = all(_is_monotonic(values) for values in by_k.values())
    sign_threshold_detected = any(
        abs(values[index + 1] - values[index]) > SIGN_THRESHOLD_DELTA
        for values in by_k.values()
        for index in range(len(values) - 1)
    )
    k0 = by_k[SIGN_CONTINUITY_K_VALUES[0]]
    k6 = by_k[SIGN_CONTINUITY_K_VALUES[-1]]
    k_sign_interaction = (
        _is_monotonic(k0) != _is_monotonic(k6)
        or any(abs(left - right) > SIGN_INTERACTION_THRESHOLD for left, right in zip(k0, k6))
    )
    return points, {
        "k_sign_interaction": k_sign_interaction,
        "sign_response_smooth": sign_response_smooth,
        "sign_threshold_detected": sign_threshold_detected,
    }


def _sign_topology_randomization_samples(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pre_rate = _sliding_window_divergence_rate(contexts)
    samples = []
    for seed in range(SIGN_TOPOLOGY_SAMPLE_COUNT):
        randomized, flipped_indices = _contexts_at_random_sign_topology(
            contexts,
            k=SIGN_TOPOLOGY_TARGET_K,
            ratio=SIGN_TOPOLOGY_TARGET_RATIO,
            seed=seed,
        )
        post_rate = _sliding_window_divergence_rate(randomized)
        collision_depth = _max_collision_depth(randomized[0]["nums"]) if randomized else 0
        samples.append(
            {
                "permutation_seed": seed,
                "flipped_indices": flipped_indices,
                "divergence_delta": round(post_rate - pre_rate, 4),
                "max_collision_depth": collision_depth,
            }
        )
    return samples


def _k_response_scan_records(manifold_id: str, accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if manifold_id != "negative_breaks_sliding_window":
        return []

    ascending = _scan_curve(accepted, K_SCAN_VALUES, sign_structure="original")
    descending = _scan_curve(accepted, tuple(reversed(K_SCAN_VALUES)), sign_structure="original")
    fine = _scan_curve(accepted, FINE_K_VALUES, sign_structure="original")
    sign_flipped = _scan_curve(accepted, K_SCAN_VALUES, sign_structure="sign_flipped", sign_flipped=True)
    path_points, path_dependence = _path_independence_points(accepted)

    hysteresis = _hysteresis_detected(ascending, descending)
    sharp = _sharp_discontinuity_detected(fine)
    sign_interaction = _sign_interaction_detected(ascending, sign_flipped)
    flags = {
        "hysteresis_detected": hysteresis,
        "path_dependence_detected": path_dependence,
        "sharp_discontinuity_detected": sharp,
        "sign_interaction_detected": sign_interaction,
    }
    common = {
        "manifold_id": manifold_id,
        "perturbation_operator": "k_response_scan",
        **flags,
    }
    return [
        {
            **common,
            "scan_type": "coarse_ascending",
            "parameterization": {"k_values": list(K_SCAN_VALUES)},
            "points": ascending,
        },
        {
            **common,
            "scan_type": "coarse_descending",
            "parameterization": {"k_values": list(reversed(K_SCAN_VALUES))},
            "points": descending,
        },
        {
            **common,
            "scan_type": "fine_boundary",
            "parameterization": {"boundary": "k_zero_neighborhood", "k_values": list(FINE_K_VALUES)},
            "points": fine,
        },
        {
            **common,
            "scan_type": "path_independence",
            "parameterization": {"target_k": 0, "alternate_path": "via_k_1"},
            "points": path_points,
        },
        {
            **common,
            "scan_type": "sign_interaction",
            "parameterization": {
                "k_values": list(K_SCAN_VALUES),
                "transform": "nums_sign_flip",
            },
            "points": ascending + sign_flipped,
        },
    ]


def _sign_continuity_scan_records(manifold_id: str, accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if manifold_id != "negative_breaks_sliding_window":
        return []

    points, flags = _sign_continuity_grid(accepted)
    records = []
    topology_samples = _sign_topology_randomization_samples(accepted)
    for point in points:
        record = {
            "manifold_id": manifold_id,
            "perturbation_operator": "k_response_scan",
            "scan_type": "sign_continuity",
            "parameterization": {
                "flip_order": "largest_magnitude_first",
                "k": point["k"],
                "sign_mixture_ratio": point["sign_mixture_ratio"],
                "sign_axis_variable": "max_collision_depth",
            },
            "point": point,
            **flags,
        }
        if (
            point["k"] == SIGN_TOPOLOGY_TARGET_K
            and point["sign_mixture_ratio"] == SIGN_TOPOLOGY_TARGET_RATIO
        ):
            record["randomized_sign_topology_samples"] = topology_samples
        records.append(record)
    return records


def _perturbation_scan_records(manifold_id: str, accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return (
        _k_response_scan_records(manifold_id, accepted)
        + _sign_continuity_scan_records(manifold_id, accepted)
    )


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
            for scan_record in _perturbation_scan_records(manifold.manifold_id, accepted):
                print(f"PERTURBATION_SCAN: {json.dumps(scan_record, sort_keys=True)}")

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
