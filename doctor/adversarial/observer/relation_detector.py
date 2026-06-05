from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import copy
import itertools
import random
from collections.abc import Callable
from typing import Any


THRESHOLD = 3.5
SEED = 20260508


def main() -> None:
    artifacts = load_artifacts()
    baseline = trajectory_candidates(artifacts)
    print("Trajectory Falsification Harness")
    print(f"Artifacts: {len(artifacts)}")
    print(f"Threshold: {THRESHOLD:.1f}")
    print(f"Seed: {SEED}")
    print()
    print_candidate_block("Baseline", baseline)

    attacks: list[tuple[str, Callable[[list[dict[str, Any]]], list[dict[str, Any]]]]] = [
        ("sequence_preserving_semantic_destruction", sequence_preserving_semantic_destruction),
        ("causal_order_inversion", causal_order_inversion),
        ("equivalent_terminal_different_paths", equivalent_terminal_different_paths),
        ("identical_paths_swapped_semantic_operators", identical_paths_swapped_semantic_operators),
        ("synthetic_trajectory_injection", synthetic_trajectory_injection),
    ]
    for name, attack in attacks:
        attacked = attack(artifacts)
        attacked_candidates = trajectory_candidates(attacked)
        print()
        print(f"Attack: {name}")
        print_candidate_block("After attack", attacked_candidates)
        print_comparison(baseline, attacked_candidates)


def trajectory_candidates(artifacts: list[dict[str, Any]]) -> list[tuple[str, float, tuple[str, ...]]]:
    candidates: list[tuple[str, float, tuple[str, ...]]] = []
    for left, right in itertools.combinations(artifacts, 2):
        if left["problem_id"] == right["problem_id"]:
            continue
        score, matching = score_pair_trajectory(left, right)
        if score >= THRESHOLD:
            candidates.append((_pair_key(left, right), score, tuple(matching)))
    return sorted(candidates, key=lambda item: (-item[1], item[0], item[2]))


def print_candidate_block(label: str, candidates: list[tuple[str, float, tuple[str, ...]]]) -> None:
    print(f"{label} candidate count: {len(candidates)}")
    print(f"{label} top 5:")
    for key, score, matching in candidates[:5]:
        print(f"  score={score:.2f}, pair={key}, matching={list(matching)}")
    if not candidates:
        print("  none")


def print_comparison(
    baseline: list[tuple[str, float, tuple[str, ...]]],
    attacked: list[tuple[str, float, tuple[str, ...]]],
) -> None:
    baseline_keys = [key for key, _, _ in baseline]
    attacked_keys = [key for key, _, _ in attacked]
    baseline_set = set(baseline_keys)
    attacked_set = set(attacked_keys)
    surviving = sorted(baseline_set & attacked_set)
    top5_overlap = _overlap_percent(baseline_keys[:5], attacked_keys[:5], denominator=5)
    candidate_overlap = _overlap_percent(baseline_keys, attacked_keys, denominator=len(baseline_keys))
    print(f"Candidate overlap with baseline: {candidate_overlap:.2f}%")
    print(f"Top-5 overlap with baseline: {top5_overlap:.2f}%")
    print(f"Surviving baseline candidates ({len(surviving)}):")
    for key in surviving:
        print(f"  {key}")
    if not surviving:
        print("  none")


def sequence_preserving_semantic_destruction(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attacked = copy.deepcopy(artifacts)
    replacements = {
        "predicate_removal": "semantic_perturbation",
        "scale_increase": "predicate_removal",
        "semantic_perturbation": "scale_increase",
    }
    for artifact in attacked:
        for event in artifact["perturbation_stability"]["lineage"]:
            event["perturbation_operator"] = replacements[event["perturbation_operator"]]
    return attacked


def causal_order_inversion(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attacked = copy.deepcopy(artifacts)
    for artifact in attacked:
        artifact["perturbation_stability"]["lineage"] = list(
            reversed(artifact["perturbation_stability"]["lineage"])
        )
    return attacked


def equivalent_terminal_different_paths(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attacked = copy.deepcopy(artifacts)
    for index, artifact in enumerate(attacked):
        lineage = artifact["perturbation_stability"]["lineage"]
        if len(lineage) < 3:
            continue
        divergence_total = sum(float(event["divergence_delta"]) for event in lineage)
        satisfiability_total = sum(float(event["satisfiability_delta"]) for event in lineage)
        if index % 2 == 0:
            divergence_path = [divergence_total, 0.0, 0.0]
            satisfiability_path = [satisfiability_total, 0.0, 0.0]
        else:
            divergence_path = [0.0, 0.0, divergence_total]
            satisfiability_path = [0.0, 0.0, satisfiability_total]
        for event, divergence_delta, satisfiability_delta in zip(
            lineage, divergence_path, satisfiability_path
        ):
            event["divergence_delta"] = divergence_delta
            event["satisfiability_delta"] = satisfiability_delta
    return attacked


def identical_paths_swapped_semantic_operators(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attacked = copy.deepcopy(artifacts)
    for index, artifact in enumerate(attacked):
        lineage = artifact["perturbation_stability"]["lineage"]
        if len(lineage) < 3:
            continue
        if index % 2 == 0:
            operator_sequence = ["predicate_removal", "scale_increase", "semantic_perturbation"]
        else:
            operator_sequence = ["semantic_perturbation", "scale_increase", "predicate_removal"]
        for event, operator in zip(lineage, operator_sequence):
            event["perturbation_operator"] = operator
    return attacked


def synthetic_trajectory_injection(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attacked = copy.deepcopy(artifacts)
    synthetic = copy.deepcopy(attacked[0])
    synthetic["problem_id"] = "synthetic"
    synthetic["manifold_id"] = "implausible_zigzag_trajectory"
    synthetic["perturbation_stability"]["lineage"] = [
        {
            "source_manifold_id": "implausible_zigzag_trajectory",
            "perturbation_operator": "semantic_perturbation",
            "parameterization": {"operator": "synthetic_jump"},
            "satisfiability_delta": 0.8,
            "divergence_delta": 0.9,
            "resulting_behavior": "manifold_collapsed",
        },
        {
            "source_manifold_id": "implausible_zigzag_trajectory",
            "perturbation_operator": "predicate_removal",
            "parameterization": {"removed_predicate": "synthetic_restore"},
            "satisfiability_delta": -0.8,
            "divergence_delta": -0.9,
            "resulting_behavior": "manifold_preserved",
        },
        {
            "source_manifold_id": "implausible_zigzag_trajectory",
            "perturbation_operator": "scale_increase",
            "parameterization": {"scale_factor": 99, "domain_limit": 1},
            "satisfiability_delta": 0.7,
            "divergence_delta": 0.9,
            "resulting_behavior": "domain_limited",
        },
    ]
    attacked.append(synthetic)
    return attacked


def _pair_key(left: dict[str, Any], right: dict[str, Any]) -> str:
    return f"{left['problem_id']}.{left['manifold_id']} x {right['problem_id']}.{right['manifold_id']}"


def _overlap_percent(left: list[str], right: list[str], *, denominator: int) -> float:
    if denominator == 0:
        return 100.0
    return 100.0 * len(set(left) & set(right)) / denominator


if __name__ == "__main__":
    main()
