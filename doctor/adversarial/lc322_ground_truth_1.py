from __future__ import annotations

import json
import math
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
from runners.run_representational_span_test import (
    _aggregate_traces,
    _bfs_trace,
    _farthest_trace,
    _lc45_static_matrix,
    _load_json,
    _separation,
)


LC45_AUDIT = PROJECT_ROOT / "data" / "lc45_specificity_audit.json"
OUTPUT_JSON = PROJECT_ROOT / "data" / "regime_robustness_stress_test.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_120.md"

LC322_SAMPLE_CAP = 192
MIN_NONZERO = 1e-9


def _round(value: float) -> float:
    return round(float(value), 6)


def _lc322_context(coins: list[int], amount: int) -> dict[str, Any] | None:
    try:
        truth = lc322_brute_force(coins, amount)
    except GroundTruthDomainError:
        return None
    nums = [*coins, amount]
    return {
        "coins": coins,
        "amount": amount,
        "nums": nums,
        "truth": truth,
    }


def _perturb_lc322_context(row: dict[str, Any], perturbation: str) -> dict[str, Any] | None:
    coins = list(row["coins"])
    amount = int(row["amount"])
    if perturbation == "baseline":
        return _lc322_context(coins, amount)
    if perturbation == "coin_order_reverse":
        return _lc322_context(list(reversed(coins)), amount)
    if perturbation == "inert_large_coin":
        return _lc322_context([*coins, amount + max(coins, default=1) + 7], amount)
    if perturbation == "amount_plus_one":
        return _lc322_context(coins, amount + 1)
    raise ValueError(perturbation)


def _lc322_activation(perturbation: str, solver_shift: int = 0) -> dict[str, dict[str, float]]:
    samples = _dimension_samples(LC322_SAMPLE_CAP)
    activation: dict[str, dict[str, float]] = {}
    for mutant_id, (_label, solver) in MUTANTS.items():
        rates = {}
        for dimension, rows in samples.items():
            divergent = 0
            observed = 0
            for row in rows:
                context = _perturb_lc322_context(row, perturbation)
                if context is None:
                    continue
                observed += 1
                try:
                    output = solver(context["nums"]) + solver_shift
                    if output != context["truth"]:
                        divergent += 1
                except Exception:
                    divergent += 1
            rates[dimension] = round(divergent / observed if observed else 0.0, 4)
        activation[mutant_id] = rates
    return activation


def _matrix_from_activation(activation: dict[str, dict[str, float]], dimensions: tuple[str, ...]) -> tuple[list[str], np.ndarray]:
    entity_ids = list(activation)
    matrix = np.array([[activation[entity][dimension] for dimension in dimensions] for entity in entity_ids], dtype=float)
    return entity_ids, matrix


def _lc322_observed_regime(perturbation: str, solver_shift: int = 0) -> dict[str, Any]:
    activation = _lc322_activation(perturbation, solver_shift)
    entity_ids, matrix = _matrix_from_activation(activation, tuple(DIMENSIONS))
    sep = _separation(entity_ids, matrix)
    return {
        "representation_class": "static_activation" if sep["pca_min_distance"] > MIN_NONZERO else "degenerate",
        "dimensionality_regime": "static_multidimensional" if sep["signature_count"] > 2 else "collapsed",
        "pca_min_distance": sep["pca_min_distance"],
        "signature_count": sep["signature_count"],
        "activation": activation,
    }


def _lc45_instance(nums: list[int], source: dict[str, Any]) -> dict[str, Any] | None:
    if not nums or nums[0] <= 0:
        return None
    try:
        truth = lc45_brute_force(nums)
    except LC45DomainError:
        return None
    if truth < 0:
        return None
    return {
        **source,
        "nums": nums,
        "truth": truth,
    }


def _perturb_lc45_instance(row: dict[str, Any], perturbation: str) -> dict[str, Any] | None:
    nums = list(row["nums"])
    if perturbation == "baseline":
        return _lc45_instance(nums, row)
    if perturbation == "append_one_tail":
        return _lc45_instance([*nums, 1], row)
    if perturbation == "increment_start_jump":
        shifted = [*nums]
        shifted[0] += 1
        return _lc45_instance(shifted, row)
    if perturbation == "soften_zero_landings":
        softened = [max(value, 1) for value in nums]
        return _lc45_instance(softened, row)
    raise ValueError(perturbation)


def _instances_by_manifold(perturbation: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for instance in _instances():
        perturbed = _perturb_lc45_instance(instance, perturbation)
        if perturbed is None:
            continue
        grouped.setdefault(str(perturbed["manifold_id"]), []).append(perturbed)
    return dict(sorted(grouped.items()))


def _bfs_depth_trace(nums: list[int], depth_limit: int) -> dict[str, float | int | str]:
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
        if jumps > depth_limit:
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


def _lc45_solvers(solver_mutation: str) -> tuple[tuple[str, Callable[[list[int]], int], Callable[[list[int]], dict[str, Any]]], ...]:
    if solver_mutation == "baseline":
        return (
            ("lc45_farthest_landing_path", lc45_farthest_landing_path, _farthest_trace),
            ("lc45_bfs_depth_cutoff", lc45_bfs_depth_cutoff, _bfs_trace),
        )
    if solver_mutation == "bfs_depth_2":
        return (
            ("lc45_farthest_landing_path", lc45_farthest_landing_path, _farthest_trace),
            ("lc45_bfs_depth_2", lambda nums: int(_bfs_depth_trace(nums, 2)["output"]), lambda nums: _bfs_depth_trace(nums, 2)),
        )
    if solver_mutation == "bfs_depth_4":
        return (
            ("lc45_farthest_landing_path", lc45_farthest_landing_path, _farthest_trace),
            ("lc45_bfs_depth_4", lambda nums: int(_bfs_depth_trace(nums, 4)["output"]), lambda nums: _bfs_depth_trace(nums, 4)),
        )
    raise ValueError(solver_mutation)


def _terminal_code(value: str) -> float:
    return {"target": 0.0, "dead": 1.0, "cutoff": 2.0, "exhausted": 3.0}[value]


def _lc45_static_activation(
    instances_by_manifold: dict[str, list[dict[str, Any]]],
    solver_mutation: str,
) -> tuple[list[str], np.ndarray]:
    solvers = _lc45_solvers(solver_mutation)
    rows = []
    entity_ids = []
    for solver_id, solver, _trace in solvers:
        entity_ids.append(solver_id)
        values = []
        for _manifold, instances in instances_by_manifold.items():
            fail_count = sum(1 for instance in instances if solver(list(instance["nums"])) != int(instance["truth"]))
            values.append(fail_count / len(instances) if instances else 0.0)
        rows.append(values)
    return entity_ids, np.array(rows, dtype=float)


def _lc45_temporal_matrix(
    instances_by_manifold: dict[str, list[dict[str, Any]]],
    solver_mutation: str,
) -> tuple[list[str], np.ndarray]:
    solvers = _lc45_solvers(solver_mutation)
    rows = []
    entity_ids = []
    for solver_id, _solver, trace_func in solvers:
        entity_ids.append(solver_id)
        values = []
        for _manifold, instances in instances_by_manifold.items():
            traces = [trace_func(list(instance["nums"])) for instance in instances]
            values.append(float(np.mean([float(trace["mean_width"]) for trace in traces])) if traces else 0.0)
        rows.append(values)
    return entity_ids, np.array(rows, dtype=float)


def _lc45_observed_regime(perturbation: str, solver_mutation: str) -> dict[str, Any]:
    instances = _instances_by_manifold(perturbation)
    static_ids, static_matrix = _lc45_static_activation(instances, solver_mutation)
    temporal_ids, temporal_matrix = _lc45_temporal_matrix(instances, solver_mutation)
    static_sep = _separation(static_ids, static_matrix)
    temporal_sep = _separation(temporal_ids, temporal_matrix)
    if temporal_sep["pca_min_distance"] > MIN_NONZERO and temporal_sep["signature_count"] > 1:
        representation_class = "temporal_unfolding_minimal"
        dimensionality_regime = "projection_sensitive_1d"
    elif static_sep["pca_min_distance"] > MIN_NONZERO and static_sep["signature_count"] > 1:
        representation_class = "static_activation"
        dimensionality_regime = "static_multidimensional" if static_sep["signature_count"] > 2 else "static_low_dimensional"
    else:
        representation_class = "degenerate"
        dimensionality_regime = "collapsed"
    return {
        "representation_class": representation_class,
        "dimensionality_regime": dimensionality_regime,
        "static": static_sep,
        "temporal": temporal_sep,
        "manifold_count": len(instances),
        "instance_count": sum(len(rows) for rows in instances.values()),
    }


def _matches_prediction(problem_id: str, observed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, bool]:
    predicted_class = prediction["predicted_representation_class"]
    predicted_regime = prediction["predicted_dimensionality_regime"]
    class_match = observed["representation_class"] == predicted_class
    regime_match = observed["dimensionality_regime"] == predicted_regime
    if problem_id == "lc45" and observed["representation_class"] in {
        "temporal_unfolding_minimal",
        "temporal_unfolding",
        "transition_graph_encoding",
        "trajectory_plus_terminal",
    }:
        class_match = predicted_class == "temporal_unfolding_minimal"
    return {
        "class_match": class_match,
        "regime_match": regime_match,
        "route_match": class_match and regime_match,
    }


def run() -> dict[str, Any]:
    selector = run_selector()
    lc322_prediction = selector["problems"]["lc322"]["prediction"]
    lc45_prediction = selector["problems"]["lc45"]["prediction"]
    lc322_scenarios = [
        ("baseline", "baseline", 0),
        ("input_coin_order_reverse", "coin_order_reverse", 0),
        ("input_inert_large_coin", "inert_large_coin", 0),
        ("input_amount_plus_one", "amount_plus_one", 0),
        ("solver_output_plus_one", "baseline", 1),
    ]
    lc45_scenarios = [
        ("baseline", "baseline", "baseline"),
        ("input_append_one_tail", "append_one_tail", "baseline"),
        ("input_increment_start_jump", "increment_start_jump", "baseline"),
        ("input_soften_zero_landings", "soften_zero_landings", "baseline"),
        ("solver_bfs_depth_2", "baseline", "bfs_depth_2"),
        ("solver_bfs_depth_4", "baseline", "bfs_depth_4"),
    ]
    lc322_rows = {}
    for scenario_id, input_perturbation, solver_shift in lc322_scenarios:
        observed = _lc322_observed_regime(input_perturbation, solver_shift)
        lc322_rows[scenario_id] = {
            "input_perturbation": input_perturbation,
            "solver_shift": solver_shift,
            "observed": observed,
            "match": _matches_prediction("lc322", observed, lc322_prediction),
        }
    lc45_rows = {}
    for scenario_id, input_perturbation, solver_mutation in lc45_scenarios:
        observed = _lc45_observed_regime(input_perturbation, solver_mutation)
        lc45_rows[scenario_id] = {
            "input_perturbation": input_perturbation,
            "solver_mutation": solver_mutation,
            "observed": observed,
            "match": _matches_prediction("lc45", observed, lc45_prediction),
        }
    all_rows = [*lc322_rows.values(), *lc45_rows.values()]
    route_matches = sum(1 for row in all_rows if row["match"]["route_match"])
    return {
        "selector_prediction": {
            "lc322": lc322_prediction,
            "lc45": lc45_prediction,
        },
        "scenarios": {
            "lc322": lc322_rows,
            "lc45": lc45_rows,
        },
        "decision": {
            "route_match_count": route_matches,
            "scenario_count": len(all_rows),
            "route_match_rate": _round(route_matches / len(all_rows) if all_rows else 0.0),
            "regime_robustness_stress_test": "PASS" if route_matches == len(all_rows) else "FAIL",
        },
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_120: Regime Robustness Stress Test",
        "",
        "## LC322",
        "",
        "| Scenario | Representation | Regime | Min distance | Signatures | Route match |",
        "|---|---|---|---:|---:|---|",
    ]
    for scenario_id, row in report["scenarios"]["lc322"].items():
        observed = row["observed"]
        lines.append(
            f"| `{scenario_id}` | `{observed['representation_class']}` | `{observed['dimensionality_regime']}` | "
            f"{observed['pca_min_distance']:.6f} | {observed['signature_count']} | "
            f"`{str(row['match']['route_match']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## LC45",
            "",
            "| Scenario | Representation | Regime | Static min | Temporal min | Temporal signatures | Route match |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for scenario_id, row in report["scenarios"]["lc45"].items():
        observed = row["observed"]
        lines.append(
            f"| `{scenario_id}` | `{observed['representation_class']}` | `{observed['dimensionality_regime']}` | "
            f"{observed['static']['pca_min_distance']:.6f} | {observed['temporal']['pca_min_distance']:.6f} | "
            f"{observed['temporal']['signature_count']} | `{str(row['match']['route_match']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`regime_robustness_stress_test`: `{report['decision']['regime_robustness_stress_test']}`",
            f"`route_match_rate`: `{report['decision']['route_match_rate']:.6f}`",
            "",
            "## Artifacts",
            "",
            "- `data/regime_robustness_stress_test.json`",
            "- `runners/run_regime_robustness_stress_test.py`",
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
