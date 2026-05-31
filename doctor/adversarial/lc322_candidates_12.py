from __future__ import annotations

import argparse
import itertools
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

from doctor.adversarial.lc322_candidates import (
    lc322_bfs_coin_count_cutoff,
    lc322_dp,
    lc322_greedy,
    lc322_modulo_memo_alias,
    lc322_ordering_commitment,
    lc322_reachability_lookahead,
    lc322_transition_asymmetric_forward_dp,
)
from doctor.adversarial.lc322_dimension_filters import EXPANDED_DIMENSIONS, dimension_filter
from doctor.adversarial.lc322_ground_truth import GroundTruthDomainError, lc322_brute_force


OUTPUT_JSON = PROJECT_ROOT / "data" / "lc322_density_blindspot_diagnostic.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_114.md"

TARGET_MUTANTS = ("mut_01", "mut_02", "mut_03", "mut_04", "mut_06")
DIMENSIONS = (
    *EXPANDED_DIMENSIONS,
)


def _split(nums: list[int]) -> tuple[list[int], int]:
    return [x for x in nums[:-1] if x > 0], int(nums[-1]) if nums else 0


def _greedy_in_order(nums: list[int]) -> int:
    return lc322_ordering_commitment(nums)


def _greedy_reverse_order(nums: list[int]) -> int:
    coins, amount = _split(nums)
    return _greedy_in_order([*reversed(coins), amount])


def _single_use_dp(nums: list[int]) -> int:
    coins, amount = _split(nums)
    if amount < 0:
        return -1
    dp = [math.inf] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        for value in range(amount, coin - 1, -1):
            dp[value] = min(dp[value], dp[value - coin] + 1)
    return -1 if dp[amount] == math.inf else int(dp[amount])


def _forward_dp(nums: list[int]) -> int:
    return lc322_transition_asymmetric_forward_dp(nums)


MUTANTS: dict[str, tuple[str, Callable[[list[int]], int]]] = {
    "mut_01": ("input_order_greedy", _greedy_in_order),
    "mut_02": ("reverse_input_order_greedy", _greedy_reverse_order),
    "mut_03": ("single_use_dp", _single_use_dp),
    "mut_04": ("forward_dp", _forward_dp),
    "mut_06": ("reachability_only_lookahead", lc322_reachability_lookahead),
}


def _iter_contexts(include_permutations: bool):
    for amount in range(1, 31):
        for size in range(1, 7):
            for coins in itertools.combinations(range(1, 16), size):
                try:
                    truth = lc322_brute_force(list(coins), amount)
                except GroundTruthDomainError:
                    continue
                orders = _representative_orders(list(coins)) if include_permutations else (tuple(coins),)
                for ordered in orders:
                    nums = [*ordered, amount]
                    yield {
                        "coins": list(ordered),
                        "amount": amount,
                        "nums": nums,
                        "truth": truth,
                        "dp": lc322_dp(nums),
                        "greedy": lc322_greedy(nums),
                        "bfs_cutoff": lc322_bfs_coin_count_cutoff(nums),
                        "modulo_alias": lc322_modulo_memo_alias(nums),
                        "reachability": lc322_reachability_lookahead(nums),
                    }


def _representative_orders(coins: list[int]) -> tuple[tuple[int, ...], ...]:
    orders = {
        tuple(coins),
        tuple(reversed(coins)),
        tuple(sorted(coins, reverse=True)),
    }
    if len(coins) > 2:
        orders.add(tuple(coins[1:] + coins[:1]))
        orders.add(tuple(coins[-1:] + coins[:-1]))
    return tuple(sorted(orders))


def _dimension_samples(cap: int) -> dict[str, list[dict[str, Any]]]:
    samples: dict[str, list[dict[str, Any]]] = {dim: [] for dim in DIMENSIONS}
    for dim in DIMENSIONS:
        if dim == "transition_asymmetry_sensitivity":
            samples[dim] = _transition_contexts(cap)
            continue
        include_permutations = dim in {
            "ordering_variation_sensitivity",
            "transition_asymmetry_sensitivity",
        }
        for context in _iter_contexts(include_permutations):
            if dimension_filter(dim, context):
                samples[dim].append(context)
                if len(samples[dim]) >= cap:
                    break
    return samples


def _transition_contexts(cap: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    amount = 2
    for size in range(2, 7):
        for tail in itertools.combinations(range(3, 16), size - 2):
            ordered = tuple(sorted((1, 2, *tail), reverse=True))
            nums = [*ordered, amount]
            truth = lc322_brute_force([1, 2, *tail], amount)
            context = {
                "coins": list(ordered),
                "amount": amount,
                "nums": nums,
                "truth": truth,
                "dp": lc322_dp(nums),
                "greedy": lc322_greedy(nums),
                "bfs_cutoff": lc322_bfs_coin_count_cutoff(nums),
                "modulo_alias": lc322_modulo_memo_alias(nums),
                "reachability": lc322_reachability_lookahead(nums),
            }
            if dimension_filter("transition_asymmetry_sensitivity", context):
                rows.append(context)
                if len(rows) >= cap:
                    return rows
    return rows


def _activation(samples: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    activation: dict[str, dict[str, Any]] = {}
    for mutant_id in TARGET_MUTANTS:
        label, solver = MUTANTS[mutant_id]
        dim_rates: dict[str, float] = {}
        dim_counts: dict[str, dict[str, int]] = {}
        for dim, rows in samples.items():
            divergent = 0
            observed = 0
            for row in rows:
                try:
                    observed += 1
                    if solver(row["nums"]) != row["truth"]:
                        divergent += 1
                except Exception:
                    divergent += 1
                    observed += 1
            rate = divergent / observed if observed else 0.0
            dim_rates[dim] = round(rate, 4)
            dim_counts[dim] = {"divergent": divergent, "observed": observed}
        activation[mutant_id] = {
            "label": label,
            "activation_by_dimension": dim_rates,
            "counts_by_dimension": dim_counts,
        }
    return activation


def _matrix(activation: dict[str, dict[str, Any]]) -> np.ndarray:
    return np.array(
        [[activation[mid]["activation_by_dimension"][dim] for dim in DIMENSIONS] for mid in TARGET_MUTANTS],
        dtype=float,
    )


def _pca2(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    if not np.any(centered):
        return np.zeros((matrix.shape[0], 2))
    u, s, _ = np.linalg.svd(centered, full_matrices=False)
    coords = u[:, :2] * s[:2]
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    return coords


def _separation(matrix: np.ndarray) -> dict[str, Any]:
    coords = _pca2(matrix)
    distances: dict[str, float] = {}
    for i, left in enumerate(TARGET_MUTANTS):
        for j, right in enumerate(TARGET_MUTANTS):
            if j <= i:
                continue
            distances[f"{left}:{right}"] = round(float(np.linalg.norm(coords[i] - coords[j])), 6)
    signature_count = len({tuple(row.round(4)) for row in matrix})
    min_pair = min(distances, key=distances.get) if distances else None
    min_distance = distances[min_pair] if min_pair else 0.0
    return {
        "pca_coordinates": {
            mutant_id: [round(float(value), 6) for value in coords[index]]
            for index, mutant_id in enumerate(TARGET_MUTANTS)
        },
        "pairwise_distances": distances,
        "min_pair": min_pair,
        "min_distance": min_distance,
        "signature_count": signature_count,
    }


def _assess(baseline: dict[str, Any], final: dict[str, Any]) -> dict[str, Any]:
    base_min = float(baseline["min_distance"])
    final_min = float(final["min_distance"])
    absolute_gain = final_min - base_min
    relative_gain = absolute_gain / max(base_min, 1e-9)
    passes = final_min >= 0.10 and absolute_gain >= 0.10 and relative_gain >= 0.25
    return {
        "criterion": (
            "density_scaling_success iff final_min_pca_distance >= 0.10, "
            "absolute_gain >= 0.10, and relative_gain >= 25%"
        ),
        "baseline_min_distance": round(base_min, 6),
        "final_min_distance": round(final_min, 6),
        "absolute_gain": round(absolute_gain, 6),
        "relative_gain": round(relative_gain, 6),
        "passes": passes,
        "verdict": "density_scaling_resolves" if passes else "density_scaling_fails",
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_114: LC322 Blind-Spot Density Diagnostic",
        "",
        "**Date:** 2026-05-15",
        "**Status:** CLOSED",
        "",
        "## Protocol Note",
        "",
        "The prior Config2 sensitivity artifact preserved the mutant labels but not executable mutant definitions. This runner therefore freezes explicit local definitions for `mut_01`, `mut_02`, `mut_03`, `mut_04`, and `mut_06` and reports those definitions in the JSON artifact. The conclusion is scoped to these frozen definitions and the existing LC322 five-family basis.",
        "",
        "## Failure Criterion",
        "",
        report["assessment"]["criterion"],
        "",
        "## Activation Matrix at Final Density",
        "",
        f"Final density cap per existing family: `{report['density_caps'][-1]}`.",
        "",
        "| Mutant | Label | " + " | ".join(DIMENSIONS) + " |",
        "|" + "---|" * (2 + len(DIMENSIONS)),
    ]
    final_activation = report["runs"][-1]["activation"]
    for mutant_id in TARGET_MUTANTS:
        row = final_activation[mutant_id]
        vals = [f"{row['activation_by_dimension'][dim]:.4f}" for dim in DIMENSIONS]
        lines.append(f"| `{mutant_id}` | `{row['label']}` | " + " | ".join(vals) + " |")

    lines.extend(["", "## Activation Summary", ""])
    for mutant_id in TARGET_MUTANTS:
        row = final_activation[mutant_id]
        active = [
            dim
            for dim in DIMENSIONS
            if row["activation_by_dimension"][dim] >= 0.05
        ]
        flat = [
            dim
            for dim in DIMENSIONS
            if row["activation_by_dimension"][dim] < 0.05
        ]
        lines.append(
            f"- `{mutant_id}` activates {', '.join(f'`{dim}`' for dim in active) or 'none'}; "
            f"flat on {', '.join(f'`{dim}`' for dim in flat) or 'none'}."
        )

    lines.extend(
        [
            "",
            "## Density Scaling",
            "",
            "| Cap | Signature count | Min PCA distance | Min pair |",
            "|---:|---:|---:|---|",
        ]
    )
    for run in report["runs"]:
        sep = run["separation"]
        lines.append(
            f"| {run['density_cap']} | {sep['signature_count']} | "
            f"{sep['min_distance']:.6f} | `{sep['min_pair']}` |"
        )

    assessment = report["assessment"]
    if assessment["passes"]:
        interpretation = (
            "Under the conservative criterion, the expanded LC322 basis resolves "
            "the tested blind spot region. The two added dimensions provide "
            "measurable separation for the ordering-variation and transition-"
            "asymmetry axes under density scaling."
        )
    else:
        interpretation = (
            "Under the conservative criterion, the expanded LC322 basis does not "
            "resolve the tested blind spot region. The probe design should not be "
            "promoted without another preregistered correction."
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"Density scaling verdict: **{assessment['verdict']}**.",
            "",
            f"Baseline min PCA distance: `{assessment['baseline_min_distance']:.6f}`.",
            f"Final min PCA distance: `{assessment['final_min_distance']:.6f}`.",
            f"Absolute gain: `{assessment['absolute_gain']:.6f}`.",
            f"Relative gain: `{assessment['relative_gain']:.6f}`.",
            "",
            interpretation,
            "",
            "## Artifacts",
            "",
            "- `data/lc322_density_blindspot_diagnostic.json`",
            "- `runners/run_lc322_density_blindspot_diagnostic.py`",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(density_caps: list[int]) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for cap in density_caps:
        samples = _dimension_samples(cap)
        activation = _activation(samples)
        matrix = _matrix(activation)
        runs.append(
            {
                "density_cap": cap,
                "dimension_counts": {dim: len(rows) for dim, rows in samples.items()},
                "activation": activation,
                "separation": _separation(matrix),
            }
        )
    report = {
        "problem_id": "lc322",
        "mutants": {mid: MUTANTS[mid][0] for mid in TARGET_MUTANTS},
        "dimensions": list(DIMENSIONS),
        "density_caps": density_caps,
        "runs": runs,
        "assessment": _assess(runs[0]["separation"], runs[-1]["separation"]),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--density-caps", nargs="+", type=int, default=[12, 24, 48, 96, 192])
    args = parser.parse_args()
    report = run(args.density_caps)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report)
    print(json.dumps(report["assessment"], indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
