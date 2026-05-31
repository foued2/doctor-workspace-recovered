from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc45_candidates import lc45_bfs_depth_cutoff, lc45_farthest_landing_path
from runners.run_lc45_solver_population import _instances


OUTPUT_JSON = PROJECT_ROOT / "data" / "lc45_specificity_audit.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_116.md"

SOLVERS: tuple[tuple[str, str, Callable[[list[int]], int]], ...] = (
    ("lc45_farthest_landing_path", "UNKNOWN", lc45_farthest_landing_path),
    ("lc45_bfs_depth_cutoff", "SURVIVOR", lc45_bfs_depth_cutoff),
)

THRESHOLDS = {
    "dominant_removal_min_ratio": 0.80,
    "dominant_removal_min_distance_floor": 0.10,
    "conditional_mi_min": 0.01,
    "jaccard_max": 0.50,
    "nmi_max": 0.50,
}


def _round(value: float) -> float:
    return round(float(value), 6)


def _instances_by_manifold() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for instance in _instances():
        grouped[str(instance["manifold_id"])].append(instance)
    return dict(sorted(grouped.items()))


def _full_activation(instances_by_manifold: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for solver_id, label, solver in SOLVERS:
        activation_by_manifold: dict[str, float] = {}
        counts_by_manifold: dict[str, dict[str, int]] = {}
        for manifold_id, instances in instances_by_manifold.items():
            fail_count = 0
            for instance in instances:
                observed = solver(list(instance["nums"]))
                if observed != int(instance["truth"]):
                    fail_count += 1
            total = len(instances)
            activation_by_manifold[manifold_id] = round(fail_count / total if total else 0.0, 4)
            counts_by_manifold[manifold_id] = {
                "fail_count": fail_count,
                "pass_count": total - fail_count,
                "total": total,
            }
        rows[solver_id] = {
            "label": label,
            "activation_by_manifold": activation_by_manifold,
            "counts_by_manifold": counts_by_manifold,
        }
    return rows


def _matrix(full_activation: dict[str, dict[str, Any]], manifolds: tuple[str, ...]) -> np.ndarray:
    return np.array(
        [
            [full_activation[solver_id]["activation_by_manifold"][manifold] for manifold in manifolds]
            for solver_id, _label, _solver in SOLVERS
        ],
        dtype=float,
    )


def _separation(matrix: np.ndarray, solver_ids: tuple[str, ...]) -> dict[str, Any]:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    if not np.any(centered):
        coords = np.zeros((matrix.shape[0], 2))
    else:
        u, s, _ = np.linalg.svd(centered, full_matrices=False)
        coords = u[:, :2] * s[:2]
        if coords.shape[1] == 1:
            coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    distances: dict[str, float] = {}
    for i, left in enumerate(solver_ids):
        for j, right in enumerate(solver_ids):
            if j <= i:
                continue
            distances[f"{left}:{right}"] = _round(float(np.linalg.norm(coords[i] - coords[j])))
    min_pair = min(distances, key=distances.get) if distances else None
    max_pair = max(distances, key=distances.get) if distances else None
    min_distance = distances[min_pair] if min_pair else 0.0
    max_distance = distances[max_pair] if max_pair else 0.0
    return {
        "pca_min_distance": min_distance,
        "pca_min_pair": min_pair,
        "pca_max_distance": max_distance,
        "pca_max_pair": max_pair,
        "cluster_separation": _round(max_distance - min_distance),
        "signature_count": len({tuple(row.round(4)) for row in matrix}),
        "pairwise_distances": distances,
        "pca_coordinates": {
            solver_id: [_round(value) for value in coords[index]]
            for index, solver_id in enumerate(solver_ids)
        },
    }


def _nearest_neighbor(separation: dict[str, Any], solver_ids: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for solver_id in solver_ids:
        pairs = {}
        for pair, distance in separation["pairwise_distances"].items():
            left, right = pair.split(":")
            if solver_id == left:
                pairs[right] = distance
            elif solver_id == right:
                pairs[left] = distance
        if not pairs:
            result[solver_id] = {"nearest": None, "nearest_distance": 0.0, "margin": 0.0}
            continue
        nearest = min(pairs, key=pairs.get)
        sorted_distances = sorted(pairs.values())
        margin = sorted_distances[1] - sorted_distances[0] if len(sorted_distances) > 1 else 0.0
        result[solver_id] = {
            "nearest": nearest,
            "nearest_distance": pairs[nearest],
            "margin": _round(margin),
        }
    return result


def _classification_delta(full_nn: dict[str, Any], condition_nn: dict[str, Any]) -> dict[str, Any]:
    return {
        solver_id: {
            "full_nearest": full_nn[solver_id]["nearest"],
            "condition_nearest": condition_nn[solver_id]["nearest"],
            "nearest_changed": full_nn[solver_id]["nearest"] != condition_nn[solver_id]["nearest"],
            "nearest_distance_delta": _round(
                condition_nn[solver_id]["nearest_distance"] - full_nn[solver_id]["nearest_distance"]
            ),
            "margin_delta": _round(condition_nn[solver_id]["margin"] - full_nn[solver_id]["margin"]),
        }
        for solver_id, _label, _solver in SOLVERS
    }


def _activation_frequencies(
    full_activation: dict[str, dict[str, Any]],
    manifolds: tuple[str, ...],
) -> dict[str, dict[str, float]]:
    return {
        solver_id: {
            manifold: full_activation[solver_id]["activation_by_manifold"][manifold]
            for manifold in manifolds
        }
        for solver_id, _label, _solver in SOLVERS
    }


def _condition_results(
    full_activation: dict[str, dict[str, Any]],
    conditions: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    solver_ids = tuple(solver_id for solver_id, _label, _solver in SOLVERS)
    separations = {
        condition_id: _separation(_matrix(full_activation, manifolds), solver_ids)
        for condition_id, manifolds in conditions.items()
    }
    full_nn = _nearest_neighbor(separations["full_basis"], solver_ids)
    results = {}
    for condition_id, manifolds in conditions.items():
        condition_nn = _nearest_neighbor(separations[condition_id], solver_ids)
        results[condition_id] = {
            "manifolds": list(manifolds),
            "separation": separations[condition_id],
            "nearest_neighbor": condition_nn,
            "per_solver_classification_delta": _classification_delta(full_nn, condition_nn),
            "activation_frequencies": _activation_frequencies(full_activation, manifolds),
        }
    return results


def _discrete(values: list[float]) -> list[str]:
    return [f"{value:.4f}" for value in values]


def _mutual_information(x: list[str], y: list[str]) -> float:
    n = len(x)
    joint = Counter(zip(x, y))
    cx = Counter(x)
    cy = Counter(y)
    total = 0.0
    for (vx, vy), count in joint.items():
        pxy = count / n
        px = cx[vx] / n
        py = cy[vy] / n
        total += pxy * math.log2(pxy / (px * py))
    return total


def _entropy(values: list[str]) -> float:
    n = len(values)
    counts = Counter(values)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def _conditional_mutual_information(x: list[str], y: list[str], z: list[str]) -> float:
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, value in enumerate(z):
        grouped[value].append(index)
    n = len(x)
    total = 0.0
    for indexes in grouped.values():
        weight = len(indexes) / n
        total += weight * _mutual_information(
            [x[index] for index in indexes],
            [y[index] for index in indexes],
        )
    return total


def _normalized_mutual_information(x: list[str], y: list[str]) -> float:
    hx = _entropy(x)
    hy = _entropy(y)
    if hx == 0.0 or hy == 0.0:
        return 0.0
    return _mutual_information(x, y) / math.sqrt(hx * hy)


def _values_by_manifold(
    full_activation: dict[str, dict[str, Any]],
    manifolds: tuple[str, ...],
) -> dict[str, list[str]]:
    return {
        manifold: _discrete(
            [full_activation[solver_id]["activation_by_manifold"][manifold] for solver_id, _label, _solver in SOLVERS]
        )
        for manifold in manifolds
    }


def _information_metrics(
    full_activation: dict[str, dict[str, Any]],
    manifolds: tuple[str, ...],
    dominant_manifold: str | None,
) -> dict[str, Any]:
    labels = [solver_id for solver_id, _label, _solver in SOLVERS]
    values = _values_by_manifold(full_activation, manifolds)
    cmi = {}
    for manifold in manifolds:
        for conditioned_on in manifolds:
            if manifold == conditioned_on:
                continue
            cmi[f"{manifold}|{conditioned_on}"] = _round(
                _conditional_mutual_information(labels, values[manifold], values[conditioned_on])
            )
    return {
        "mutual_information": {
            manifold: _round(_mutual_information(labels, values[manifold]))
            for manifold in manifolds
        },
        "conditional_mutual_information": cmi,
        "entropy": {
            "solver_label": abs(_round(_entropy(labels))),
            **{manifold: abs(_round(_entropy(values[manifold]))) for manifold in manifolds},
        },
        "dominant_manifold": dominant_manifold,
    }


def _binary(values: list[float]) -> list[int]:
    return [1 if value > 0.0 else 0 for value in values]


def _coactivation_metrics(
    full_activation: dict[str, dict[str, Any]],
    manifolds: tuple[str, ...],
) -> dict[str, Any]:
    by_manifold = {
        manifold: [
            full_activation[solver_id]["activation_by_manifold"][manifold]
            for solver_id, _label, _solver in SOLVERS
        ]
        for manifold in manifolds
    }
    pairwise = {}
    for left, right in combinations(manifolds, 2):
        lb = _binary(by_manifold[left])
        rb = _binary(by_manifold[right])
        counts = {"a0_b0": 0, "a0_b1": 0, "a1_b0": 0, "a1_b1": 0}
        for lval, rval in zip(lb, rb):
            counts[f"a{lval}_b{rval}"] += 1
        intersection = sum(1 for lval, rval in zip(lb, rb) if lval == 1 and rval == 1)
        union = sum(1 for lval, rval in zip(lb, rb) if lval == 1 or rval == 1)
        covariance = float(np.cov(np.array(by_manifold[left]), np.array(by_manifold[right]), ddof=0)[0, 1])
        pairwise[f"{left}:{right}"] = {
            "coactivation_matrix": counts,
            "jaccard_overlap": _round(intersection / union if union else 0.0),
            "normalized_mutual_information": _round(
                _normalized_mutual_information([str(value) for value in lb], [str(value) for value in rb])
            ),
            "activation_covariance": _round(covariance),
        }
    return {"pairwise": pairwise}


def _conditions(manifolds: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    conditions = {"full_basis": manifolds}
    for manifold in manifolds:
        conditions[f"remove_{manifold}"] = tuple(item for item in manifolds if item != manifold)
    for left, right in combinations(manifolds, 2):
        conditions[f"only_{left}__{right}"] = (left, right)
    return conditions


def _dominant_manifold(info: dict[str, Any]) -> str | None:
    mi = info["mutual_information"]
    if max(mi.values(), default=0.0) <= 0.0:
        return None
    return max(sorted(mi), key=lambda manifold: mi[manifold])


def _decision(
    conditions: dict[str, Any],
    info: dict[str, Any],
    coactivation: dict[str, Any],
    dominant_manifold: str | None,
) -> dict[str, Any]:
    full_min = conditions["full_basis"]["separation"]["pca_min_distance"]
    if dominant_manifold is None:
        removed_min = 0.0
        removal_ratio = 0.0
        removal_ok = False
    else:
        removed_key = f"remove_{dominant_manifold}"
        removed_min = conditions[removed_key]["separation"]["pca_min_distance"]
        removal_ratio = removed_min / full_min if full_min else 0.0
        removal_ok = (
            removed_min >= THRESHOLDS["dominant_removal_min_distance_floor"]
            and removal_ratio >= THRESHOLDS["dominant_removal_min_ratio"]
        )
    cmi_values = info["conditional_mutual_information"]
    cmi_ok = bool(cmi_values) and all(value >= THRESHOLDS["conditional_mi_min"] for value in cmi_values.values())
    overlaps = coactivation["pairwise"]
    overlap_ok = bool(overlaps) and all(
        row["jaccard_overlap"] <= THRESHOLDS["jaccard_max"]
        and row["normalized_mutual_information"] <= THRESHOLDS["nmi_max"]
        for row in overlaps.values()
    )
    return {
        "dominant_removal": {
            "dominant_manifold": dominant_manifold,
            "full_min_distance": full_min,
            "removed_min_distance": removed_min,
            "ratio": _round(removal_ratio),
            "pass": removal_ok,
        },
        "conditional_mi": {
            "values": cmi_values,
            "pass": cmi_ok,
        },
        "coactivation_overlap": {
            "max_jaccard_overlap": max((row["jaccard_overlap"] for row in overlaps.values()), default=0.0),
            "max_normalized_mutual_information": max(
                (row["normalized_mutual_information"] for row in overlaps.values()),
                default=0.0,
            ),
            "pass": overlap_ok,
        },
        "thresholds": THRESHOLDS,
        "independence_criterion": "PASS" if removal_ok and cmi_ok and overlap_ok else "FAIL",
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_116: LC45 Specificity Audit",
        "",
        "## Conditional Ablation Matrix",
        "",
        "| Condition | PCA min-distance | Min pair | Cluster separation | Signature count |",
        "|---|---:|---|---:|---:|",
    ]
    for condition_id, row in report["conditions"].items():
        sep = row["separation"]
        lines.append(
            f"| `{condition_id}` | {sep['pca_min_distance']:.6f} | `{sep['pca_min_pair']}` | "
            f"{sep['cluster_separation']:.6f} | {sep['signature_count']} |"
        )
    lines.extend(
        [
            "",
            "## Mutual Information",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
    )
    for manifold, value in report["information_metrics"]["mutual_information"].items():
        lines.append(f"| `I(solver;{manifold})` | {value:.6f} |")
    for key, value in report["information_metrics"]["conditional_mutual_information"].items():
        lines.append(f"| `I(solver;{key})` | {value:.6f} |")
    lines.extend(
        [
            "",
            "## Coactivation",
            "",
            "| Pair | Jaccard | NMI | Covariance |",
            "|---|---:|---:|---:|",
        ]
    )
    for pair, row in report["coactivation_entanglement"]["pairwise"].items():
        lines.append(
            f"| `{pair}` | {row['jaccard_overlap']:.6f} | "
            f"{row['normalized_mutual_information']:.6f} | {row['activation_covariance']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`independence_criterion`: `{report['decision']['independence_criterion']}`",
            "",
            "## Artifacts",
            "",
            "- `data/lc45_specificity_audit.json`",
            "- `runners/run_lc45_specificity_audit.py`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> dict[str, Any]:
    instances_by_manifold = _instances_by_manifold()
    manifolds = tuple(instances_by_manifold)
    full_activation = _full_activation(instances_by_manifold)
    condition_rows = _condition_results(full_activation, _conditions(manifolds))
    preliminary_info = _information_metrics(full_activation, manifolds, None)
    dominant = _dominant_manifold(preliminary_info)
    info = _information_metrics(full_activation, manifolds, dominant)
    coactivation = _coactivation_metrics(full_activation, manifolds)
    decision = _decision(condition_rows, info, coactivation, dominant)
    return {
        "problem_id": "lc45",
        "audited_solver_ids": [solver_id for solver_id, _label, _solver in SOLVERS],
        "audited_solver_labels": {solver_id: label for solver_id, label, _solver in SOLVERS},
        "manifolds": list(manifolds),
        "instance_counts": {manifold: len(instances) for manifold, instances in instances_by_manifold.items()},
        "full_activation": full_activation,
        "conditions": condition_rows,
        "information_metrics": info,
        "coactivation_entanglement": coactivation,
        "decision": decision,
    }


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
