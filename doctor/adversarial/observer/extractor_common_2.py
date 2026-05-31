"""Partial-overlap structural relation detector for observer artifacts."""
from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doctor.adversarial.observer.extractor_common import ARTIFACT_ROOT
from doctor.adversarial.observer.trajectory import compare_trajectories, extract_trajectory


@dataclass(frozen=True)
class CandidateAnomaly:
    label: str
    manifold_a: str
    manifold_b: str
    score: float
    matching: list[str]
    joint_match_rarity: float


DIMENSIONS = (
    "locality_class",
    "dependency_depth",
    "rejection_concentration",
    "divergence_type_overlap",
    "relaxation_sensitivity",
    "scale_persistence",
    "semantic_perturbation_tolerance",
)


def load_artifacts(root: Path = ARTIFACT_ROOT) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*.json")):
        artifacts.append(json.loads(path.read_text(encoding="utf-8")))
    return artifacts


def dimension_match_probs(artifacts: list[dict[str, Any]]) -> dict[str, float]:
    counts = {dimension: 0 for dimension in DIMENSIONS}
    total = 0
    for left, right in itertools.combinations(artifacts, 2):
        if left["problem_id"] == right["problem_id"]:
            continue
        _, matching = score_pair(left, right)
        matching_set = set(matching)
        for dimension in DIMENSIONS:
            if dimension in matching_set:
                counts[dimension] += 1
        total += 1

    if total == 0:
        return {dimension: 0.0 for dimension in DIMENSIONS}
    return {dimension: counts[dimension] / total for dimension in DIMENSIONS}


def joint_match_rarity(match_vector: dict[str, bool] | list[str], match_probs: dict[str, float]) -> float:
    """
    Rarity product heuristic - not a formal likelihood ratio.
    Assumes dimension independence (known false; dimensions are correlated).
    Overstates rarity for correlated dimension clusters.
    Use for anomaly ranking only. Do not interpret magnitude probabilistically.
    """
    if isinstance(match_vector, dict):
        matched = [dimension for dimension, hit in match_vector.items() if hit]
    else:
        matched = list(match_vector)
    if not matched:
        return 1.0

    result = 1.0
    for dimension in matched:
        if match_probs[dimension] == 0.0:
            return math.inf
        result *= 1.0 / match_probs[dimension]
    return result


def detect_candidate_anomalies(artifacts: list[dict[str, Any]]) -> list[CandidateAnomaly]:
    candidates: list[CandidateAnomaly] = []
    match_probs = dimension_match_probs(artifacts)
    for left, right in itertools.combinations(artifacts, 2):
        if left["problem_id"] == right["problem_id"]:
            continue
        score, matching = score_pair(left, right)
        if score >= 4.0:
            candidates.append(
                CandidateAnomaly(
                    label="CANDIDATE_ANOMALY",
                    manifold_a=_artifact_name(left),
                    manifold_b=_artifact_name(right),
                    score=round(score, 2),
                    matching=matching,
                    joint_match_rarity=round(joint_match_rarity(matching, match_probs), 6),
                )
            )
    return sorted(candidates, key=lambda item: (-item.joint_match_rarity, -item.score, item.manifold_a, item.manifold_b))


def score_pair(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, list[str]]:
    # VALIDITY_BOUNDARY_GUARD: shared perturbation stability across a valid-region
    # control and a failure manifold is not shared failure geometry.
    if (_divergence_rate(left) == 0.0) != (_divergence_rate(right) == 0.0):
        return 0.0, []

    score = 0.0
    matching: list[str] = []
    if left["locality_class"]["value"] == right["locality_class"]["value"]:
        score += 1.0
        matching.append("locality_class")
    if left["dependency_depth"]["value"] == right["dependency_depth"]["value"]:
        score += 1.5
        matching.append("dependency_depth")
    if left["rejection_topology"]["concentration"] == right["rejection_topology"]["concentration"]:
        score += 0.5
        matching.append("rejection_concentration")
    if _divergence_types(left) & _divergence_types(right):
        score += 1.0
        matching.append("divergence_type_overlap")
    if abs(_relaxation(left) - _relaxation(right)) <= 0.15:
        score += 1.0
        matching.append("relaxation_sensitivity")
    if left["perturbation_stability"]["scale_persistence"] == right["perturbation_stability"]["scale_persistence"]:
        score += 1.0
        matching.append("scale_persistence")
    if abs(_semantic_tolerance(left) - _semantic_tolerance(right)) <= 0.15:
        score += 0.5
        matching.append("semantic_perturbation_tolerance")
    return score, matching


def score_pair_trajectory(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, list[str]]:
    left_trajectory = extract_trajectory(left)
    right_trajectory = extract_trajectory(right)
    return compare_trajectories(left_trajectory, right_trajectory)


def weakest_signal(artifacts: list[dict[str, Any]]) -> str:
    misses = {dimension: 0 for dimension in DIMENSIONS}
    for left, right in itertools.combinations(artifacts, 2):
        if left["problem_id"] == right["problem_id"]:
            continue
        _, matching = score_pair(left, right)
        for dimension in DIMENSIONS:
            if dimension not in matching:
                misses[dimension] += 1
    return max(misses, key=misses.get) if misses else "none"


def _artifact_name(artifact: dict[str, Any]) -> str:
    return f"{artifact['problem_id']}.{artifact['manifold_id']}"


def _divergence_types(artifact: dict[str, Any]) -> set[str]:
    return {
        divergence_type
        for divergence_type in artifact["divergence_profile"]["solver_divergence"].values()
        if divergence_type != "none"
    }


def _relaxation(artifact: dict[str, Any]) -> float:
    return float(artifact["perturbation_stability"]["relaxation_sensitivity"])


def _semantic_tolerance(artifact: dict[str, Any]) -> float:
    return float(artifact["perturbation_stability"]["semantic_perturbation_tolerance"])


def _divergence_rate(artifact: dict[str, Any]) -> float:
    return float(artifact["divergence_profile"]["divergence_rate"])
