from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_ground_truth import GroundTruthDomainError, lc322_brute_force
from doctor.adversarial.lc45_candidates import lc45_bfs_depth_cutoff, lc45_farthest_landing_path
from doctor.adversarial.lc45_ground_truth import GroundTruthDomainError as LC45DomainError
from doctor.adversarial.lc45_ground_truth import lc45_brute_force
from runners.run_lc322_density_blindspot_diagnostic import DIMENSIONS, MUTANTS, _dimension_samples
from runners.run_lc45_solver_population import _instances
from runners.run_representation_selection_oracle import run as run_selector
from runners.run_representational_span_test import _bfs_trace, _farthest_trace


OUTPUT_JSON = PROJECT_ROOT / "data" / "representation_stability_boundary_test.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_121.md"

LC322_SAMPLE_CAP = 192
MAX_K = 6
DISCONTINUITY_RATIO = 0.50
MIN_NONZERO = 1e-9

LC45_SOLVERS: tuple[tuple[str, Callable[[list[int]], int], Callable[[list[int]], dict[str, Any]]], ...] = (
    ("lc45_farthest_landing_path", lc45_farthest_landing_path, _farthest_trace),
    ("lc45_bfs_depth_cutoff", lc45_bfs_depth_cutoff, _bfs_trace),
)


def _round(value: float) -> float:
    return round(float(value), 6)


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
    return {
        "pca_min_distance": distances[min_pair] if min_pair else 0.0,
        "pca_min_pair": min_pair,
        "signature_count": len({tuple(row.round(6)) for row in matrix}),
    }


def _lc322_context(coins: list[int], amount: int) -> dict[str, Any] | None:
    coins = [coin for coin in coins if coin > 0]
    if not coins or amount < 0:
        return None
    try:
        truth = lc322_brute_force(coins, amount)
    except GroundTruthDomainError:
        return None
    return {"coins": coins, "amount": amount, "nums": [*coins, amount], "truth": truth}


def _lc322_transform(row: dict[str, Any], transform_id: str, k: int) -> dict[str, Any] | None:
    coins = list(row["coins"])
    amount = int(row["amount"])
    if k == 0:
        return _lc322_context(coins, amount)
    if transform_id == "structural_growth":
        return _lc322_context([*coins, *[amount + max(coins, default=1) + step + 1 for step in range(k)]], amount)
    if transform_id == "compositional_shift":
        shifted = sorted(set([*coins, *[coin + k for coin in coins]]))
        return _lc322_context(shifted, amount + k)
    if transform_id == "recursion_depth_increase":
        return _lc322_context(coins, amount + k)
    if transform_id == "horizon_extension":
        return _lc322_context(sorted(set([*coins, max(1, amount // 2 + k)])), amount + k)
    raise ValueError(transform_id)


def _lc322_matrix(samples: dict[str, list[dict[str, Any]]], transform_id: str, k: int) -> tuple[list[str], np.ndarray]:
    activation: dict[str, dict[str, float]] = {}
    for mutant_id, (_label, solver) in MUTANTS.items():
        rates = {}
        for dimension, rows in samples.items():
            divergent = 0
            observed = 0
            for row in rows:
                context = _lc322_transform(row, transform_id, k)
                if context is None:
                    continue
                observed += 1
                try:
                    if solver(context["nums"]) != context["truth"]:
                        divergent += 1
                except Exception:
                    divergent += 1
            rates[dimension] = divergent / observed if observed else 0.0
        activation[mutant_id] = rates
    entity_ids = list(activation)
    matrix = np.array([[activation[entity][dimension] for dimension in DIMENSIONS] for entity in entity_ids], dtype=float)
    return entity_ids, matrix


def _lc45_instance(nums: list[int], source: dict[str, Any]) -> dict[str, Any] | None:
    if not nums or nums[0] <= 0:
        return None
    try:
        truth = lc45_brute_force(nums)
    except LC45DomainError:
        return None
    if truth < 0:
        return None
    return {**source, "nums": nums, "truth": truth}


def _lc45_transform(row: dict[str, Any], transform_id: str, k: int) -> dict[str, Any] | None:
    nums = list(row["nums"])
    if k == 0:
        return _lc45_instance(nums, row)
    if transform_id == "structural_growth":
        return _lc45_instance([*nums, *([1] * k)], row)
    if transform_id == "compositional_shift":
        merged = [*nums[:-1], max(1, nums[-1]), *nums[:k], 1]
        return _lc45_instance(merged, row)
    if transform_id == "recursion_depth_increase":
        stretched = [nums[0], *([1] * k), *nums[1:]]
        return _lc45_instance(stretched, row)
    if transform_id == "horizon_extension":
        shifted = [*nums]
        shifted[0] += k
        return _lc45_instance(shifted, row)
    raise ValueError(transform_id)


def _lc45_instances_by_manifold(transform_id: str, k: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for instance in _instances():
        transformed = _lc45_transform(instance, transform_id, k)
        if transformed is not None:
            grouped.setdefault(str(transformed["manifold_id"]), []).append(transformed)
    return dict(sorted(grouped.items()))


def _lc45_static_matrix(instances_by_manifold: dict[str, list[dict[str, Any]]]) -> tuple[list[str], np.ndarray]:
    rows = []
    entity_ids = []
    for solver_id, solver, _trace in LC45_SOLVERS:
        entity_ids.append(solver_id)
        values = []
        for _manifold, instances in instances_by_manifold.items():
            fail_count = sum(1 for instance in instances if solver(list(instance["nums"])) != int(instance["truth"]))
            values.append(fail_count / len(instances) if instances else 0.0)
        rows.append(values)
    return entity_ids, np.array(rows, dtype=float)


def _lc45_temporal_matrix(instances_by_manifold: dict[str, list[dict[str, Any]]]) -> tuple[list[str], np.ndarray]:
    rows = []
    entity_ids = []
    for solver_id, _solver, trace in LC45_SOLVERS:
        entity_ids.append(solver_id)
        values = []
        for _manifold, instances in instances_by_manifold.items():
            traces = [trace(list(instance["nums"])) for instance in instances]
            values.append(float(np.mean([float(row["mean_width"]) for row in traces])) if traces else 0.0)
        rows.append(values)
    return entity_ids, np.array(rows, dtype=float)


def _observed_regime(problem_id: str, static_sep: dict[str, Any], temporal_sep: dict[str, Any] | None = None) -> dict[str, str]:
    if problem_id == "lc322":
        if static_sep["pca_min_distance"] > MIN_NONZERO and static_sep["signature_count"] > 2:
            return {"representation_class": "static_activation", "dimensionality_regime": "static_multidimensional"}
        return {"representation_class": "degenerate", "dimensionality_regime": "collapsed"}
    assert temporal_sep is not None
    if temporal_sep["pca_min_distance"] > MIN_NONZERO and temporal_sep["signature_count"] > 1:
        return {"representation_class": "temporal_unfolding_minimal", "dimensionality_regime": "projection_sensitive_1d"}
    if static_sep["pca_min_distance"] > MIN_NONZERO and static_sep["signature_count"] > 1:
        return {"representation_class": "static_activation", "dimensionality_regime": "static_low_dimensional"}
    return {"representation_class": "degenerate", "dimensionality_regime": "collapsed"}


def _is_route_match(problem_id: str, observed: dict[str, str], prediction: dict[str, Any]) -> bool:
    expected_class = prediction["predicted_representation_class"]
    expected_regime = prediction["predicted_dimensionality_regime"]
    if problem_id == "lc45":
        class_match = observed["representation_class"] in {
            "temporal_unfolding_minimal",
            "temporal_unfolding",
            "transition_graph_encoding",
            "trajectory_plus_terminal",
        } and expected_class == "temporal_unfolding_minimal"
    else:
        class_match = observed["representation_class"] == expected_class
    return class_match and observed["dimensionality_regime"] == expected_regime


def _curve_breakpoints(rows: list[dict[str, Any]], predicted_class: str, predicted_regime: str) -> dict[str, Any]:
    baseline_distance = rows[0]["selected_min_distance"]
    breakpoints = {
        "regime_flip_k": None,
        "embedding_collapse_k": None,
        "distance_discontinuity_k": None,
        "oracle_confidence_break_k": None,
    }
    previous_distance = baseline_distance
    for row in rows:
        k = row["k"]
        distance = row["selected_min_distance"]
        if breakpoints["regime_flip_k"] is None and (
            row["representation_class"] != predicted_class or row["dimensionality_regime"] != predicted_regime
        ):
            breakpoints["regime_flip_k"] = k
        if breakpoints["embedding_collapse_k"] is None and (distance <= MIN_NONZERO or row["selected_signature_count"] <= 1):
            breakpoints["embedding_collapse_k"] = k
        if k > 0 and breakpoints["distance_discontinuity_k"] is None:
            denominator = max(abs(previous_distance), MIN_NONZERO)
            if abs(distance - previous_distance) / denominator >= DISCONTINUITY_RATIO:
                breakpoints["distance_discontinuity_k"] = k
        if breakpoints["oracle_confidence_break_k"] is None and not row["route_match"]:
            breakpoints["oracle_confidence_break_k"] = k
        previous_distance = distance
    return breakpoints


def _lc322_curve(samples: dict[str, list[dict[str, Any]]], transform_id: str, prediction: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for k in range(0, MAX_K + 1):
        entity_ids, matrix = _lc322_matrix(samples, transform_id, k)
        static_sep = _separation(entity_ids, matrix)
        regime = _observed_regime("lc322", static_sep)
        route_match = _is_route_match("lc322", regime, prediction)
        rows.append(
            {
                "k": k,
                **regime,
                "selected_min_distance": static_sep["pca_min_distance"],
                "selected_signature_count": static_sep["signature_count"],
                "static_min_distance": static_sep["pca_min_distance"],
                "temporal_min_distance": None,
                "route_match": route_match,
            }
        )
    return {
        "rows": rows,
        "breakpoints": _curve_breakpoints(
            rows,
            prediction["predicted_representation_class"],
            prediction["predicted_dimensionality_regime"],
        ),
    }


def _lc45_curve(transform_id: str, prediction: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for k in range(0, MAX_K + 1):
        instances_by_manifold = _lc45_instances_by_manifold(transform_id, k)
        static_ids, static_matrix = _lc45_static_matrix(instances_by_manifold)
        temporal_ids, temporal_matrix = _lc45_temporal_matrix(instances_by_manifold)
        static_sep = _separation(static_ids, static_matrix)
        temporal_sep = _separation(temporal_ids, temporal_matrix)
        regime = _observed_regime("lc45", static_sep, temporal_sep)
        route_match = _is_route_match("lc45", regime, prediction)
        selected_sep = temporal_sep if regime["representation_class"] == "temporal_unfolding_minimal" else static_sep
        rows.append(
            {
                "k": k,
                **regime,
                "selected_min_distance": selected_sep["pca_min_distance"],
                "selected_signature_count": selected_sep["signature_count"],
                "static_min_distance": static_sep["pca_min_distance"],
                "temporal_min_distance": temporal_sep["pca_min_distance"],
                "route_match": route_match,
            }
        )
    return {
        "rows": rows,
        "breakpoints": _curve_breakpoints(
            rows,
            prediction["predicted_representation_class"],
            prediction["predicted_dimensionality_regime"],
        ),
    }


def run() -> dict[str, Any]:
    selector = run_selector()
    predictions = {
        "lc322": selector["problems"]["lc322"]["prediction"],
        "lc45": selector["problems"]["lc45"]["prediction"],
    }
    samples = _dimension_samples(LC322_SAMPLE_CAP)
    transforms = ("structural_growth", "compositional_shift", "recursion_depth_increase", "horizon_extension")
    curves = {
        "lc322": {transform_id: _lc322_curve(samples, transform_id, predictions["lc322"]) for transform_id in transforms},
        "lc45": {transform_id: _lc45_curve(transform_id, predictions["lc45"]) for transform_id in transforms},
    }
    first_breaks = {}
    for problem_id, problem_curves in curves.items():
        first_breaks[problem_id] = {}
        for transform_id, curve in problem_curves.items():
            first_breaks[problem_id][transform_id] = curve["breakpoints"]
    all_rows = [
        row
        for problem_curves in curves.values()
        for curve in problem_curves.values()
        for row in curve["rows"]
    ]
    return {
        "max_k": MAX_K,
        "discontinuity_ratio": DISCONTINUITY_RATIO,
        "selector_prediction": predictions,
        "curves": curves,
        "first_breakpoints": first_breaks,
        "decision": {
            "route_match_count": sum(1 for row in all_rows if row["route_match"]),
            "point_count": len(all_rows),
            "route_match_rate": _round(sum(1 for row in all_rows if row["route_match"]) / len(all_rows)),
            "representation_stability_boundary_test": (
                "PASS" if all(row["route_match"] for row in all_rows) else "FAIL"
            ),
        },
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_121: Representation Stability Boundary Test",
        "",
        "## First Breakpoints",
        "",
        "| Problem | Transform | Regime flip k | Collapse k | Discontinuity k | Confidence break k |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for problem_id, transforms in report["first_breakpoints"].items():
        for transform_id, row in transforms.items():
            lines.append(
                f"| `{problem_id}` | `{transform_id}` | `{row['regime_flip_k']}` | "
                f"`{row['embedding_collapse_k']}` | `{row['distance_discontinuity_k']}` | "
                f"`{row['oracle_confidence_break_k']}` |"
            )
    lines.extend(
        [
            "",
            "## Curves",
            "",
            "| Problem | Transform | k | Representation | Regime | Selected min | Static min | Temporal min | Signatures | Route match |",
            "|---|---|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for problem_id, transforms in report["curves"].items():
        for transform_id, curve in transforms.items():
            for row in curve["rows"]:
                temporal = row["temporal_min_distance"]
                lines.append(
                    f"| `{problem_id}` | `{transform_id}` | {row['k']} | `{row['representation_class']}` | "
                    f"`{row['dimensionality_regime']}` | {row['selected_min_distance']:.6f} | "
                    f"{row['static_min_distance']:.6f} | "
                    f"{temporal:.6f}" if temporal is not None else
                    f"| `{problem_id}` | `{transform_id}` | {row['k']} | `{row['representation_class']}` | "
                    f"`{row['dimensionality_regime']}` | {row['selected_min_distance']:.6f} | "
                    f"{row['static_min_distance']:.6f} | ``"
                )
                lines[-1] += f" | {row['selected_signature_count']} | `{str(row['route_match']).lower()}` |"
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`representation_stability_boundary_test`: `{report['decision']['representation_stability_boundary_test']}`",
            f"`route_match_rate`: `{report['decision']['route_match_rate']:.6f}`",
            "",
            "## Artifacts",
            "",
            "- `data/representation_stability_boundary_test.json`",
            "- `runners/run_representation_stability_boundary_test.py`",
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
