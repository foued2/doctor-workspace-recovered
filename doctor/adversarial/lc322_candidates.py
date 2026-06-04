from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Solver functions for LC322 Coin Change.
# Signature: fn(nums: list[int]) -> int
#   nums = [c1, c2, ..., amount]  (last element is the amount)
#   Returns minimum coin count, or -1 if unreachable.


def lc322_dp(nums: list[int]) -> int:
    """Correct DP."""
    coins = nums[:-1]
    amount = nums[-1]
    if amount < 0:
        return -1
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if c <= 0:
                continue
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return -1 if dp[amount] == float("inf") else dp[amount]


def lc322_greedy(nums: list[int]) -> int:
    """Greedy: largest coin first. Fails on non-canonical coin systems."""
    coins = sorted([c for c in nums[:-1] if c > 0], reverse=True)
    amount = nums[-1]
    count = 0
    for c in coins:
        q = amount // c
        count += q
        amount -= q * c
    return -1 if amount != 0 else count


def lc322_smallest_first(nums: list[int]) -> int:
    """Always pick smallest coin first — pathologically many coins."""
    coins = sorted([c for c in nums[:-1] if c > 0])
    amount = nums[-1]
    count = 0
    for c in coins:
        q = amount // c
        count += q
        amount -= q * c
    return -1 if amount != 0 else count


def lc322_memo_collision(nums: list[int]) -> int:
    """DP with coin-set-independent memo — cache collisions across amounts.
    Cache key is (remaining % 3), causing aliasing between different amounts."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    _cache: dict[int, int] = {}
    MOD = 3

    def _min_coins(remaining: int) -> int:
        if remaining < 0:
            return float("inf")
        if remaining == 0:
            return 0
        key = remaining % MOD
        if key in _cache:
            return _cache[key]
        best = float("inf")
        for c in coins:
            best = min(best, 1 + _min_coins(remaining - c))
        _cache[key] = best
        return best

    result = _min_coins(amount)
    return -1 if result == float("inf") else result


def lc322_lookahead_one(nums: list[int]) -> int:
    """Only considers using one coin per recursive step without exploring all paths."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    steps = 0
    while amount > 0:
        best = max((c for c in coins if c <= amount), default=None)
        if best is None:
            return -1
        amount -= best
        steps += 1
    return steps


def lc322_bfs_coin_count_cutoff(nums: list[int]) -> int:
    """BFS with depth cutoff — stops searching after a fixed depth."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    cutoff = 6
    from collections import deque
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    visited = {0}
    while queue:
        total, depth = queue.popleft()
        if depth >= cutoff:
            continue
        for c in coins:
            nxt = total + c
            if nxt == amount:
                return depth + 1
            if nxt < amount and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, depth + 1))
    return -1


def lc322_modulo_memo_alias(nums: list[int]) -> int:
    """Uses modulo-2 memo key — maximum aliasing causes wrong results."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    _cache: dict[int, int] = {}

    def _solve(remaining: int) -> int:
        if remaining < 0:
            return float("inf")
        if remaining == 0:
            return 0
        key = remaining % 2
        if key in _cache:
            return _cache[key]
        best = float("inf")
        for c in coins:
            best = min(best, 1 + _solve(remaining - c))
        _cache[key] = best
        return best

    result = _solve(amount)
    return -1 if result == float("inf") else result


def lc322_reachability_lookahead(nums: list[int]) -> int:
    """Checks reachability correctly, then uses greedy coin count (wrong for non-canonical)."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    reachable = {0}
    for c in coins:
        for v in range(c, amount + 1):
            if v - c in reachable:
                reachable.add(v)
    if amount not in reachable:
        return -1
    remaining = amount
    count = 0
    for c in sorted(coins, reverse=True):
        q = remaining // c
        count += q
        remaining -= q * c
    return -1 if remaining != 0 else count


def lc322_ordering_commitment(nums: list[int]) -> int:
    """Commits to coin ordering — picks first coin that fits."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    steps = 0
    while amount > 0:
        chosen = None
        for c in coins:
            if c <= amount:
                chosen = c
                break
        if chosen is None:
            return -1
        amount -= chosen
        steps += 1
    return steps


def lc322_transition_asymmetric_forward_dp(nums: list[int]) -> int:
    """DP with asymmetric transition — correct first pass, then overwrite pass corrupts."""
    coins = [c for c in nums[:-1] if c > 0]
    amount = nums[-1]
    if amount < 0:
        return -1
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for i in range(c, amount + 1):
            if dp[i - c] != float("inf"):
                dp[i] = min(dp[i], dp[i - c] + 1)
    for c in sorted(coins):
        for i in range(c, amount + 1):
            if dp[i - c] != float("inf"):
                dp[i] = dp[i - c] + 1
    return -1 if dp[amount] == float("inf") else dp[amount]


from doctor.adversarial.lc45_candidates import (
    lc45_bfs_depth_cutoff,
    lc45_farthest_landing_path,
    lc45_first_window_max_then_greedy,
    lc45_frontier_off_by_one,
    lc45_max_landing_value,
    lc45_naive_greedy,
    lc45_reachable_boolean_confusion,
    lc45_three_step_window_dp,
    lc45_uniform_formula_generalizer,
    lc45_zero_dead_end_panic,
)


OUTPUT_JSON = PROJECT_ROOT / "data" / "solver_population_projection_test.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_125.md"

AXES = (
    "structural_growth",
    "horizon_extension",
    "recursion_depth_increase",
    "compositional_shift",
)
LC322_SAMPLE_CAP = 96
MAX_K = 4

LC322_CANDIDATES: tuple[tuple[str, Callable[[list[int]], int]], ...] = (
    ("lc322_dp", lc322_dp),
    ("lc322_greedy", lc322_greedy),
    ("lc322_smallest_first", lc322_smallest_first),
    ("lc322_memo_collision", lc322_memo_collision),
    ("lc322_lookahead_one", lc322_lookahead_one),
    ("lc322_bfs_coin_count_cutoff", lc322_bfs_coin_count_cutoff),
    ("lc322_modulo_memo_alias", lc322_modulo_memo_alias),
    ("lc322_reachability_lookahead", lc322_reachability_lookahead),
    ("lc322_ordering_commitment", lc322_ordering_commitment),
    ("lc322_transition_asymmetric_forward_dp", lc322_transition_asymmetric_forward_dp),
)

LC45_SOLVERS: tuple[tuple[str, Callable[[list[int]], int]], ...] = (
    ("lc45_naive_greedy", lc45_naive_greedy),
    ("lc45_max_landing_value", lc45_max_landing_value),
    ("lc45_farthest_landing_path", lc45_farthest_landing_path),
    ("lc45_zero_dead_end_panic", lc45_zero_dead_end_panic),
    ("lc45_reachable_boolean_confusion", lc45_reachable_boolean_confusion),
    ("lc45_bfs_depth_cutoff", lc45_bfs_depth_cutoff),
    ("lc45_three_step_window_dp", lc45_three_step_window_dp),
    ("lc45_frontier_off_by_one", lc45_frontier_off_by_one),
    ("lc45_uniform_formula_generalizer", lc45_uniform_formula_generalizer),
    ("lc45_first_window_max_then_greedy", lc45_first_window_max_then_greedy),
)

def _round(value: float) -> float:
    return round(float(value), 6)


def _dedupe_lc322_rows(samples: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = {}
    for dimension_rows in samples.values():
        for row in dimension_rows:
            key = tuple(row["nums"])
            rows[key] = {
                "coins": list(row["coins"]),
                "amount": int(row["amount"]),
                "nums": list(row["nums"]),
                "truth": int(row["truth"]),
            }
    return list(rows.values())


def _fail_rate_lc322(
    rows: list[dict[str, Any]],
    solver: Callable[[list[int]], int],
    axis: str,
    k: int,
) -> float:
    from runners.run_representation_stability_boundary_test import _lc322_transform
    observed = 0
    failed = 0
    for row in rows:
        transformed = _lc322_transform(row, axis, k)
        if transformed is None:
            continue
        observed += 1
        try:
            if solver(list(transformed["nums"])) != int(transformed["truth"]):
                failed += 1
        except Exception:
            failed += 1
    return failed / observed if observed else 0.0


def _fail_rate_lc45(
    rows: list[dict[str, Any]],
    solver: Callable[[list[int]], int],
    axis: str,
    k: int,
) -> float:
    from runners.run_representation_stability_boundary_test import _lc45_transform
    observed = 0
    failed = 0
    for row in rows:
        transformed = _lc45_transform(row, axis, k)
        if transformed is None:
            continue
        observed += 1
        try:
            if solver(list(transformed["nums"])) != int(transformed["truth"]):
                failed += 1
        except Exception:
            failed += 1
    return failed / observed if observed else 0.0


def _axis_coordinate(rates: list[float]) -> dict[str, Any]:
    baseline = rates[0]
    drifts = [abs(rate - baseline) for rate in rates[1:]]
    return {
        "baseline_fail_rate": _round(baseline),
        "rates": [_round(rate) for rate in rates],
        "mean_abs_drift": _round(float(np.mean(drifts)) if drifts else 0.0),
        "max_abs_drift": _round(max(drifts) if drifts else 0.0),
        "final_abs_drift": _round(drifts[-1] if drifts else 0.0),
    }


def _project_lc322(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from runners.run_lc322_density_blindspot_diagnostic import MUTANTS
    projected = []
    solvers = [
        *[(solver_id, "lc322_solver", solver) for solver_id, solver in LC322_CANDIDATES],
        *[(mutant_id, "mutation_solver", solver) for mutant_id, (_label, solver) in MUTANTS.items()],
    ]
    for solver_id, group, solver in solvers:
        axis_details = {}
        coordinates = []
        for axis in AXES:
            rates = [_fail_rate_lc322(rows, solver, axis, k) for k in range(MAX_K + 1)]
            detail = _axis_coordinate(rates)
            axis_details[axis] = detail
            coordinates.append(detail["max_abs_drift"])
        projected.append(
            {
                "solver_id": solver_id,
                "problem_id": "lc322",
                "group": group,
                "coordinates": dict(zip(AXES, coordinates)),
                "axis_details": axis_details,
            }
        )
    return projected


def _project_lc45(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projected = []
    for solver_id, solver in LC45_SOLVERS:
        axis_details = {}
        coordinates = []
        for axis in AXES:
            rates = [_fail_rate_lc45(rows, solver, axis, k) for k in range(MAX_K + 1)]
            detail = _axis_coordinate(rates)
            axis_details[axis] = detail
            coordinates.append(detail["max_abs_drift"])
        projected.append(
            {
                "solver_id": solver_id,
                "problem_id": "lc45",
                "group": "lc45_solver",
                "coordinates": dict(zip(AXES, coordinates)),
                "axis_details": axis_details,
            }
        )
    return projected


def _matrix(rows: list[dict[str, Any]]) -> tuple[list[str], np.ndarray]:
    ids = [f"{row['group']}::{row['solver_id']}" for row in rows]
    matrix = np.array([[row["coordinates"][axis] for axis in AXES] for row in rows], dtype=float)
    return ids, matrix


def _pca(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    if not np.any(centered):
        return np.zeros((matrix.shape[0], 2))
    u, s, _ = np.linalg.svd(centered, full_matrices=False)
    coords = u[:, :2] * s[:2]
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    return coords


def _pairwise(matrix: np.ndarray, ids: list[str]) -> dict[str, float]:
    distances = {}
    for i, left in enumerate(ids):
        for j, right in enumerate(ids):
            if j <= i:
                continue
            distances[f"{left}|{right}"] = _round(float(np.linalg.norm(matrix[i] - matrix[j])))
    return distances


def _centroids(rows: list[dict[str, Any]], matrix: np.ndarray) -> dict[str, list[float]]:
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row["group"]].append(matrix[index])
    return {
        group: [_round(value) for value in np.mean(values, axis=0)]
        for group, values in groups.items()
    }


def _nearest_cluster_labels(rows: list[dict[str, Any]], matrix: np.ndarray) -> dict[str, Any]:
    ids = [f"{row['group']}::{row['solver_id']}" for row in rows]
    result = {}
    same_group = 0
    for i, row in enumerate(rows):
        distances = [
            (j, float(np.linalg.norm(matrix[i] - matrix[j])))
            for j in range(len(rows))
            if j != i
        ]
        nearest_index, nearest_distance = min(distances, key=lambda item: item[1])
        nearest_row = rows[nearest_index]
        same = nearest_row["group"] == row["group"]
        if same:
            same_group += 1
        result[ids[i]] = {
            "nearest": ids[nearest_index],
            "nearest_distance": _round(nearest_distance),
            "same_group": same,
        }
    return {
        "rows": result,
        "same_group_nearest_rate": _round(same_group / len(rows) if rows else 0.0),
    }


def _silhouette(rows: list[dict[str, Any]], matrix: np.ndarray, label_key: str) -> float:
    labels = [row[label_key] for row in rows]
    unique = sorted(set(labels))
    if len(unique) < 2:
        return 0.0
    values = []
    for i, label in enumerate(labels):
        same = [
            float(np.linalg.norm(matrix[i] - matrix[j]))
            for j, other in enumerate(labels)
            if i != j and other == label
        ]
        other_means = []
        for other_label in unique:
            if other_label == label:
                continue
            distances = [
                float(np.linalg.norm(matrix[i] - matrix[j]))
                for j, candidate in enumerate(labels)
                if candidate == other_label
            ]
            if distances:
                other_means.append(sum(distances) / len(distances))
        a = sum(same) / len(same) if same else 0.0
        b = min(other_means) if other_means else 0.0
        denominator = max(a, b)
        values.append((b - a) / denominator if denominator else 0.0)
    return _round(sum(values) / len(values))


def _density_clusters(rows: list[dict[str, Any]], matrix: np.ndarray) -> dict[str, Any]:
    ids = [f"{row['group']}::{row['solver_id']}" for row in rows]
    pairwise_values = [
        float(np.linalg.norm(matrix[i] - matrix[j]))
        for i in range(len(rows))
        for j in range(i + 1, len(rows))
    ]
    threshold = float(np.quantile(pairwise_values, 0.25)) if pairwise_values else 0.0
    adjacency = {index: set() for index in range(len(rows))}
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if float(np.linalg.norm(matrix[i] - matrix[j])) <= threshold:
                adjacency[i].add(j)
                adjacency[j].add(i)
    seen = set()
    clusters = []
    for start in range(len(rows)):
        if start in seen:
            continue
        stack = [start]
        component = []
        seen.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        clusters.append(component)
    cluster_rows = []
    for index, component in enumerate(clusters, start=1):
        groups = Counter(rows[item]["group"] for item in component)
        cluster_rows.append(
            {
                "cluster_id": f"cluster_{index}",
                "size": len(component),
                "members": [ids[item] for item in component],
                "group_counts": dict(groups),
                "mixed_group": len(groups) > 1,
            }
        )
    return {
        "threshold": _round(threshold),
        "cluster_count": len(cluster_rows),
        "clusters": cluster_rows,
    }


def _overlap_ratio(clusters: dict[str, Any]) -> dict[str, Any]:
    mixed_members = sum(row["size"] for row in clusters["clusters"] if row["mixed_group"])
    total = sum(row["size"] for row in clusters["clusters"])
    return {
        "mixed_cluster_member_count": mixed_members,
        "total_member_count": total,
        "overlap_ratio": _round(mixed_members / total if total else 0.0),
    }


def _centroid_distances(centroids: dict[str, list[float]]) -> dict[str, float]:
    result = {}
    items = list(centroids.items())
    for i, (left, left_values) in enumerate(items):
        for j, (right, right_values) in enumerate(items):
            if j <= i:
                continue
            result[f"{left}|{right}"] = _round(float(np.linalg.norm(np.array(left_values) - np.array(right_values))))
    return result


def run() -> dict[str, Any]:
    from runners.run_lc322_density_blindspot_diagnostic import _dimension_samples
    from runners.run_lc45_solver_population import _instances
    lc322_rows = _dedupe_lc322_rows(_dimension_samples(LC322_SAMPLE_CAP))
    lc45_rows = [dict(row) for row in _instances()]
    projections = [*_project_lc322(lc322_rows), *_project_lc45(lc45_rows)]
    ids, matrix = _matrix(projections)
    pca_coords = _pca(matrix)
    centroids = _centroids(projections, matrix)
    clusters = _density_clusters(projections, matrix)
    return {
        "axes": list(AXES),
        "projection_method": "max_abs_failure_rate_drift_over_k_0_to_4",
        "input_counts": {
            "lc322": len(lc322_rows),
            "lc45": len(lc45_rows),
        },
        "solver_count": len(projections),
        "projections": projections,
        "pca_coordinates": {
            ids[index]: [_round(value) for value in pca_coords[index]]
            for index in range(len(ids))
        },
        "pairwise_distances": _pairwise(matrix, ids),
        "centroids": centroids,
        "centroid_distances": _centroid_distances(centroids),
        "density_clusters": clusters,
        "separability": {
            "group_silhouette": _silhouette(projections, matrix, "group"),
            "problem_silhouette": _silhouette(projections, matrix, "problem_id"),
            "nearest": _nearest_cluster_labels(projections, matrix),
        },
        "overlap": _overlap_ratio(clusters),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_125: Solver Population Projection Test",
        "",
        "## 4D Coordinates",
        "",
        "| Solver | Problem | Group | Structural | Horizon | Recursion | Compositional |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in report["projections"]:
        coords = row["coordinates"]
        lines.append(
            f"| `{row['solver_id']}` | `{row['problem_id']}` | `{row['group']}` | "
            f"{coords['structural_growth']:.6f} | {coords['horizon_extension']:.6f} | "
            f"{coords['recursion_depth_increase']:.6f} | {coords['compositional_shift']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Separability",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| `group_silhouette` | {report['separability']['group_silhouette']:.6f} |",
            f"| `problem_silhouette` | {report['separability']['problem_silhouette']:.6f} |",
            f"| `same_group_nearest_rate` | {report['separability']['nearest']['same_group_nearest_rate']:.6f} |",
            f"| `overlap_ratio` | {report['overlap']['overlap_ratio']:.6f} |",
            "",
            "## Centroid Distances",
            "",
            "| Pair | Distance |",
            "|---|---:|",
        ]
    )
    for pair, distance in report["centroid_distances"].items():
        lines.append(f"| `{pair}` | {distance:.6f} |")
    lines.extend(
        [
            "",
            "## Density Clusters",
            "",
            "| Cluster | Size | Mixed group | Group counts |",
            "|---|---:|---|---|",
        ]
    )
    for cluster in report["density_clusters"]["clusters"]:
        lines.append(
            f"| `{cluster['cluster_id']}` | {cluster['size']} | `{str(cluster['mixed_group']).lower()}` | "
            f"`{cluster['group_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `data/solver_population_projection_test.json`",
            "- `runners/run_solver_population_projection_test.py`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report)
    print(
        json.dumps(
            {
                "solver_count": report["solver_count"],
                "group_silhouette": report["separability"]["group_silhouette"],
                "problem_silhouette": report["separability"]["problem_silhouette"],
                "overlap_ratio": report["overlap"]["overlap_ratio"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
