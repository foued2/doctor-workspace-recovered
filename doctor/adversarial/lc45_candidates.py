from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc45_candidates import lc45_bfs_depth_cutoff, lc45_farthest_landing_path
from runners.run_lc45_solver_population import _instances


LC322_AUDIT = PROJECT_ROOT / "data" / "lc322_specificity_audit.json"
LC45_AUDIT = PROJECT_ROOT / "data" / "lc45_specificity_audit.json"
OUTPUT_JSON = PROJECT_ROOT / "data" / "representational_span_test.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_118.md"

LC45_SOLVERS: tuple[tuple[str, Callable[[list[int]], int]], ...] = (
    ("lc45_farthest_landing_path", lc45_farthest_landing_path),
    ("lc45_bfs_depth_cutoff", lc45_bfs_depth_cutoff),
)

MIN_NONZERO = 1e-9


def _round(value: float) -> float:
    return round(float(value), 6)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _instances_by_manifold() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for instance in _instances():
        grouped.setdefault(str(instance["manifold_id"]), []).append(instance)
    return dict(sorted(grouped.items()))


def _lc322_static_matrix(lc322: dict[str, Any]) -> tuple[list[str], np.ndarray]:
    activations = lc322["conditions"]["full_basis"]["activation_frequencies"]
    entity_ids = list(activations)
    dimensions = list(next(iter(activations.values())))
    matrix = np.array([[activations[entity][dimension] for dimension in dimensions] for entity in entity_ids], dtype=float)
    return entity_ids, matrix


def _lc45_static_matrix(lc45: dict[str, Any]) -> tuple[list[str], np.ndarray]:
    activations = {
        solver_id: payload["activation_by_manifold"]
        for solver_id, payload in lc45["full_activation"].items()
    }
    entity_ids = list(activations)
    dimensions = list(next(iter(activations.values())))
    matrix = np.array([[activations[entity][dimension] for dimension in dimensions] for entity in entity_ids], dtype=float)
    return entity_ids, matrix


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe = np.where(norms == 0.0, 1.0, norms)
    return matrix / safe


def _separation(entity_ids: list[str], matrix: np.ndarray) -> dict[str, Any]:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    if not np.any(centered):
        coords = np.zeros((matrix.shape[0], 2))
    else:
        u, s, _ = np.linalg.svd(centered, full_matrices=False)
        coords = u[:, :2] * s[:2]
        if coords.shape[1] == 1:
            coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    distances: dict[str, float] = {}
    for i, left in enumerate(entity_ids):
        for j, right in enumerate(entity_ids):
            if j <= i:
                continue
            distances[f"{left}|{right}"] = _round(float(np.linalg.norm(coords[i] - coords[j])))
    min_pair = min(distances, key=distances.get) if distances else None
    max_pair = max(distances, key=distances.get) if distances else None
    return {
        "pca_min_distance": distances[min_pair] if min_pair else 0.0,
        "pca_min_pair": min_pair,
        "pca_max_distance": distances[max_pair] if max_pair else 0.0,
        "pca_max_pair": max_pair,
        "signature_count": len({tuple(row.round(6)) for row in matrix}),
        "pca_coordinates": {
            entity_id: [_round(value) for value in coords[index]]
            for index, entity_id in enumerate(entity_ids)
        },
        "pairwise_distances": distances,
    }


def _farthest_trace(nums: list[int]) -> dict[str, float | int | str]:
    if len(nums) <= 1:
        return {
            "output": 0,
            "states": 1,
            "visited": 1,
            "edges": 0,
            "max_width": 0,
            "mean_width": 0.0,
            "max_depth": 0,
            "terminal": "target",
        }
    target = len(nums) - 1
    index = 0
    jumps = 0
    seen: set[int] = set()
    widths: list[int] = []
    edges = 0
    while index < target:
        if index in seen or nums[index] <= 0:
            return {
                "output": 10**9,
                "states": len(widths) + 1,
                "visited": len(seen),
                "edges": edges,
                "max_width": max(widths) if widths else 0,
                "mean_width": sum(widths) / len(widths) if widths else 0.0,
                "max_depth": jumps,
                "terminal": "dead",
            }
        seen.add(index)
        farthest = min(target, index + nums[index])
        width = max(0, farthest - index)
        widths.append(width)
        edges += width
        if farthest == target:
            return {
                "output": jumps + 1,
                "states": len(widths) + 1,
                "visited": len(seen) + 1,
                "edges": edges,
                "max_width": max(widths),
                "mean_width": sum(widths) / len(widths),
                "max_depth": jumps + 1,
                "terminal": "target",
            }
        candidates = range(index + 1, farthest + 1)
        index = max(candidates, key=lambda next_index: (next_index + nums[next_index], nums[next_index]))
        jumps += 1
    return {
        "output": jumps,
        "states": len(widths) + 1,
        "visited": len(seen),
        "edges": edges,
        "max_width": max(widths) if widths else 0,
        "mean_width": sum(widths) / len(widths) if widths else 0.0,
        "max_depth": jumps,
        "terminal": "target",
    }


def _bfs_trace(nums: list[int]) -> dict[str, float | int | str]:
    if len(nums) <= 1:
        return {
            "output": 0,
            "states": 1,
            "visited": 1,
            "edges": 0,
            "max_width": 0,
            "mean_width": 0.0,
            "max_depth": 0,
            "terminal": "target",
        }
    target = len(nums) - 1
    frontier = [(0, 0)]
    seen = {0}
    cursor = 0
    widths: list[int] = []
    layer_widths: dict[int, int] = {0: 1}
    edges = 0
    max_depth = 0
    while cursor < len(frontier):
        index, jumps = frontier[cursor]
        cursor += 1
        max_depth = max(max_depth, jumps)
        if jumps > 3:
            return {
                "output": -1,
                "states": cursor,
                "visited": len(seen),
                "edges": edges,
                "max_width": max(layer_widths.values()) if layer_widths else 0,
                "mean_width": sum(widths) / len(widths) if widths else 0.0,
                "max_depth": max_depth,
                "terminal": "cutoff",
            }
        farthest = min(target, index + nums[index])
        width = max(0, farthest - index)
        widths.append(width)
        edges += width
        for next_index in range(index + 1, farthest + 1):
            if next_index == target:
                return {
                    "output": jumps + 1,
                    "states": cursor + 1,
                    "visited": len(seen) + 1,
                    "edges": edges,
                    "max_width": max(layer_widths.values()) if layer_widths else 0,
                    "mean_width": sum(widths) / len(widths) if widths else 0.0,
                    "max_depth": jumps + 1,
                    "terminal": "target",
                }
            if next_index not in seen:
                seen.add(next_index)
                frontier.append((next_index, jumps + 1))
                layer_widths[jumps + 1] = layer_widths.get(jumps + 1, 0) + 1
    return {
        "output": -1,
        "states": cursor,
        "visited": len(seen),
        "edges": edges,
        "max_width": max(layer_widths.values()) if layer_widths else 0,
        "mean_width": sum(widths) / len(widths) if widths else 0.0,
        "max_depth": max_depth,
        "terminal": "exhausted",
    }


def _trace(solver_id: str, nums: list[int]) -> dict[str, float | int | str]:
    if solver_id == "lc45_farthest_landing_path":
        return _farthest_trace(nums)
    if solver_id == "lc45_bfs_depth_cutoff":
        return _bfs_trace(nums)
    raise ValueError(solver_id)


def _terminal_code(value: str) -> float:
    return {
        "target": 0.0,
        "dead": 1.0,
        "cutoff": 2.0,
        "exhausted": 3.0,
    }[value]


def _aggregate_traces(
    instances_by_manifold: dict[str, list[dict[str, Any]]],
    feature_names: tuple[str, ...],
) -> tuple[list[str], np.ndarray]:
    rows = []
    entity_ids = []
    for solver_id, solver in LC45_SOLVERS:
        entity_ids.append(solver_id)
        values = []
        for _manifold_id, instances in instances_by_manifold.items():
            traces = [_trace(solver_id, list(instance["nums"])) for instance in instances]
            outputs = [float(solver(list(instance["nums"]))) for instance in instances]
            truths = [float(instance["truth"]) for instance in instances]
            for feature_name in feature_names:
                if feature_name == "output_mean":
                    values.append(float(np.mean(outputs)))
                elif feature_name == "output_std":
                    values.append(float(np.std(outputs)))
                elif feature_name == "abs_error_mean":
                    values.append(float(np.mean([abs(output - truth) for output, truth in zip(outputs, truths)])))
                elif feature_name == "visited_mean":
                    values.append(float(np.mean([float(trace["visited"]) for trace in traces])))
                elif feature_name == "states_mean":
                    values.append(float(np.mean([float(trace["states"]) for trace in traces])))
                elif feature_name == "edges_mean":
                    values.append(float(np.mean([float(trace["edges"]) for trace in traces])))
                elif feature_name == "max_width_mean":
                    values.append(float(np.mean([float(trace["max_width"]) for trace in traces])))
                elif feature_name == "mean_width_mean":
                    values.append(float(np.mean([float(trace["mean_width"]) for trace in traces])))
                elif feature_name == "max_depth_mean":
                    values.append(float(np.mean([float(trace["max_depth"]) for trace in traces])))
                elif feature_name == "terminal_mean":
                    values.append(float(np.mean([_terminal_code(str(trace["terminal"])) for trace in traces])))
                else:
                    raise ValueError(feature_name)
        rows.append(values)
    return entity_ids, np.array(rows, dtype=float)


TRANSFORMS: dict[str, tuple[str, ...]] = {
    "static_activation": (),
    "normalized_static_activation": (),
    "output_value_summary": ("output_mean", "output_std", "abs_error_mean"),
    "temporal_unfolding_minimal": ("visited_mean",),
    "temporal_unfolding": ("visited_mean", "states_mean", "max_depth_mean"),
    "transition_graph_encoding": ("visited_mean", "edges_mean", "max_width_mean", "mean_width_mean"),
    "trajectory_plus_terminal": (
        "visited_mean",
        "states_mean",
        "edges_mean",
        "max_width_mean",
        "mean_width_mean",
        "max_depth_mean",
        "terminal_mean",
    ),
}


def _lc45_transform_matrix(
    transform_id: str,
    lc45: dict[str, Any],
    instances_by_manifold: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], np.ndarray, list[str]]:
    if transform_id == "static_activation":
        entity_ids, matrix = _lc45_static_matrix(lc45)
        return entity_ids, matrix, list(next(iter(lc45["full_activation"].values()))["activation_by_manifold"])
    if transform_id == "normalized_static_activation":
        entity_ids, matrix = _lc45_static_matrix(lc45)
        return entity_ids, _normalize_rows(matrix), list(next(iter(lc45["full_activation"].values()))["activation_by_manifold"])
    feature_names = TRANSFORMS[transform_id]
    entity_ids, matrix = _aggregate_traces(instances_by_manifold, feature_names)
    expanded_names = [
        f"{manifold}:{feature}"
        for manifold in instances_by_manifold
        for feature in feature_names
    ]
    return entity_ids, matrix, expanded_names


def _minimal_feature_subset(
    instances_by_manifold: dict[str, list[dict[str, Any]]],
    candidate_features: tuple[str, ...],
) -> dict[str, Any]:
    for size in range(1, len(candidate_features) + 1):
        passing = []
        for subset in combinations(candidate_features, size):
            entity_ids, matrix = _aggregate_traces(instances_by_manifold, subset)
            sep = _separation(entity_ids, matrix)
            if sep["pca_min_distance"] > MIN_NONZERO and sep["signature_count"] > 1:
                passing.append(
                    {
                        "features": list(subset),
                        "pca_min_distance": sep["pca_min_distance"],
                        "signature_count": sep["signature_count"],
                    }
                )
        if passing:
            return {
                "size": size,
                "passing_subsets": passing,
                "selected": min(passing, key=lambda row: (row["pca_min_distance"], row["features"])),
            }
    return {"size": None, "passing_subsets": [], "selected": None}


def run() -> dict[str, Any]:
    lc322 = _load_json(LC322_AUDIT)
    lc45 = _load_json(LC45_AUDIT)
    instances_by_manifold = _instances_by_manifold()
    lc322_ids, lc322_matrix = _lc322_static_matrix(lc322)
    lc322_baseline = _separation(lc322_ids, lc322_matrix)
    results = {}
    for transform_id in TRANSFORMS:
        lc45_ids, lc45_matrix, feature_names = _lc45_transform_matrix(transform_id, lc45, instances_by_manifold)
        lc45_sep = _separation(lc45_ids, lc45_matrix)
        lc322_sep = _separation(lc322_ids, lc322_matrix)
        results[transform_id] = {
            "feature_count": len(feature_names),
            "features": feature_names,
            "lc45": lc45_sep,
            "lc322": lc322_sep,
            "lc322_structure_unchanged": (
                lc322_sep["pca_min_distance"] == lc322_baseline["pca_min_distance"]
                and lc322_sep["signature_count"] == lc322_baseline["signature_count"]
                and lc322_sep["pca_min_pair"] == lc322_baseline["pca_min_pair"]
            ),
            "lc45_nonzero_variance": lc45_sep["signature_count"] > 1,
            "lc45_nonzero_min_distance": lc45_sep["pca_min_distance"] > MIN_NONZERO,
            "passes_span_test": (
                lc45_sep["signature_count"] > 1
                and lc45_sep["pca_min_distance"] > MIN_NONZERO
                and lc322_sep["pca_min_distance"] == lc322_baseline["pca_min_distance"]
                and lc322_sep["signature_count"] == lc322_baseline["signature_count"]
                and lc322_sep["pca_min_pair"] == lc322_baseline["pca_min_pair"]
            ),
        }
    passing = [name for name, row in results.items() if row["passes_span_test"]]
    minimal = _minimal_feature_subset(
        instances_by_manifold,
        (
            "visited_mean",
            "states_mean",
            "edges_mean",
            "max_width_mean",
            "mean_width_mean",
            "max_depth_mean",
            "terminal_mean",
        ),
    )
    return {
        "source_artifacts": {
            "lc322": str(LC322_AUDIT.relative_to(PROJECT_ROOT)),
            "lc45": str(LC45_AUDIT.relative_to(PROJECT_ROOT)),
        },
        "lc322_baseline": lc322_baseline,
        "transform_results": results,
        "minimal_feature_subset_search": minimal,
        "decision": {
            "passing_transform_count": len(passing),
            "passing_transforms": passing,
            "minimal_selected_features": minimal["selected"]["features"] if minimal["selected"] else [],
            "representational_span_test": "PASS" if passing else "FAIL",
        },
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_118: Representational Span Test",
        "",
        "## Transform Results",
        "",
        "| Transform | LC45 min-distance | LC45 signatures | LC322 min-distance | LC322 signatures | LC322 unchanged | PASS |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for transform_id, row in report["transform_results"].items():
        lines.append(
            f"| `{transform_id}` | {row['lc45']['pca_min_distance']:.6f} | "
            f"{row['lc45']['signature_count']} | {row['lc322']['pca_min_distance']:.6f} | "
            f"{row['lc322']['signature_count']} | `{str(row['lc322_structure_unchanged']).lower()}` | "
            f"`{str(row['passes_span_test']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Minimal Feature Subset",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| `size` | `{report['minimal_feature_subset_search']['size']}` |",
            f"| `selected_features` | `{report['decision']['minimal_selected_features']}` |",
            "",
            "## Decision",
            "",
            f"`representational_span_test`: `{report['decision']['representational_span_test']}`",
            "",
            "## Artifacts",
            "",
            "- `data/representational_span_test.json`",
            "- `runners/run_representational_span_test.py`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report)
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
