"""Calibrated overlap anomaly detector for observer artifacts."""
from __future__ import annotations

import itertools
import json
import math
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "doctor" / "adversarial" / "observer" / "artifacts"


@dataclass(frozen=True)
class CandidateAnomaly:
    label: str
    manifold_a: str
    manifold_b: str
    score: float
    matching: list[str]
    null_percentile: float = 0.0
    joint_match_rarity: float = 0.0


@dataclass(frozen=True)
class NullLRGateFloor:
    value: float
    method: str
    null_pair_count: int
    null_lr_max: float


@dataclass(frozen=True)
class LODOLRDrift:
    lodo_lrs: dict[str, float]
    coefficient_of_variation: float
    instability_class: str


DIMENSIONS = (
    "locality_class",
    "dependency_depth",
    "rejection_concentration",
    "divergence_type_overlap",
    "relaxation_sensitivity",
    "scale_persistence",
    "semantic_perturbation_tolerance",
)


ATTENUATED_PROBLEM_WEIGHT_CAP = 0.25


LOCKED_PAIRS = frozenset(
    {
        frozenset(("lc322.greedy_trap_no_subdivision", "lc560.zero_sum_subarray_invisibility")),
        frozenset(("lc322.unreachable_greedy_confusion", "lc45.uniform_jump_array")),
        frozenset(("lc135.valley_forces_both_directions", "lc560.negative_breaks_sliding_window")),
    }
)


def load_artifacts(root: Path = ARTIFACT_ROOT) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*.json")):
        artifacts.append(json.loads(path.read_text(encoding="utf-8")))
    return artifacts


def build_null_model(artifacts: list[dict[str, Any]], attenuate_problem: str | None = None) -> list[float]:
    distribution: list[float] = []
    for left, right in _cross_domain_pairs(artifacts, include_locked=False):
        score, _ = score_pair(left, right)
        distribution.append(score)
    return sorted(distribution)


def percentile_rank(score: float, null_distribution: list[float]) -> float:
    if not null_distribution:
        return 0.0
    below_or_equal = bisect_right(null_distribution, score)
    return 100.0 * below_or_equal / len(null_distribution)


def dimension_match_probs(
    artifacts: list[dict[str, Any]], attenuate_problem: str | None = None
) -> dict[str, float]:
    counts = {dimension: 0.0 for dimension in DIMENSIONS}
    total = 0.0
    for left, right in _cross_domain_pairs(artifacts, include_locked=False):
        weight = _pair_weight(left, right, attenuate_problem)
        _, matching = score_pair(left, right)
        matching_set = set(matching)
        for dimension in DIMENSIONS:
            if dimension in matching_set:
                counts[dimension] += weight
        total += weight

    if total == 0.0:
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


def build_lodo_null_models(artifacts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    models: dict[str, dict[str, Any]] = {}
    for problem_id in sorted({artifact["problem_id"] for artifact in artifacts}):
        lodo_artifacts = [artifact for artifact in artifacts if artifact["problem_id"] != problem_id]
        match_probs = dimension_match_probs(lodo_artifacts)
        score_distribution: list[float] = []
        lr_distribution: list[float] = []
        for left, right in _cross_domain_pairs(lodo_artifacts, include_locked=False):
            score, matching = score_pair(left, right)
            score_distribution.append(score)
            lr_distribution.append(joint_match_rarity(matching, match_probs))
        models[problem_id] = {
            "score_distribution": sorted(score_distribution),
            "lr_distribution": sorted(lr_distribution),
            "match_probs": match_probs,
            "pair_count": len(score_distribution),
        }
    return models


def lodo_lr_variance(
    candidates: list[CandidateAnomaly],
    artifacts: list[dict[str, Any]],
    dimension_probs_fn: Any = dimension_match_probs,
) -> dict[str, LODOLRDrift]:
    lodo_keys = sorted(_candidate_problem_ids(candidates))
    results: dict[str, LODOLRDrift] = {}
    for candidate in candidates:
        lodo_lrs: dict[str, float] = {}
        for problem_id in lodo_keys:
            lodo_artifacts = [artifact for artifact in artifacts if artifact["problem_id"] != problem_id]
            match_probs = dimension_probs_fn(lodo_artifacts)
            lodo_lrs[problem_id] = round(joint_match_rarity(candidate.matching, match_probs), 6)
        cv = _coefficient_of_variation(list(lodo_lrs.values()))
        results[_candidate_key(candidate)] = LODOLRDrift(
            lodo_lrs=lodo_lrs,
            coefficient_of_variation=round(cv, 6),
            instability_class=_instability_class(cv),
        )
    return results


def null_lr_gate_floor(null_artifacts: list[dict[str, Any]]) -> NullLRGateFloor:
    match_probs = dimension_match_probs(null_artifacts)
    lr_distribution: list[float] = []
    for left, right in _cross_domain_pairs(null_artifacts, include_locked=False):
        _, matching = score_pair(left, right)
        lr_distribution.append(joint_match_rarity(matching, match_probs))

    if not lr_distribution:
        return NullLRGateFloor(value=0.0, method="empty_null", null_pair_count=0, null_lr_max=0.0)

    sorted_lrs = sorted(lr_distribution)
    null_lr_max = sorted_lrs[-1]
    if len(sorted_lrs) < 1000:
        return NullLRGateFloor(
            value=round(null_lr_max * 1.2, 6),
            method="margin_fallback",
            null_pair_count=len(sorted_lrs),
            null_lr_max=round(null_lr_max, 6),
        )

    index = max(0, math.ceil(len(sorted_lrs) * 0.999) - 1)
    return NullLRGateFloor(
        value=round(sorted_lrs[index], 6),
        method="top_0_1_percent",
        null_pair_count=len(sorted_lrs),
        null_lr_max=round(null_lr_max, 6),
    )


def run_observer_dual_mode(artifacts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "baseline": _observer_run(artifacts, attenuate_problem=None),
        "attenuated": _observer_run(artifacts, attenuate_problem="lc560"),
    }


def compare_runs(baseline: dict[str, Any], attenuated: dict[str, Any]) -> dict[str, Any]:
    baseline_candidates = baseline["audit_candidates"]
    attenuated_candidates = attenuated["audit_candidates"]
    baseline_by_key = {_candidate_key(candidate): candidate for candidate in baseline_candidates}
    attenuated_by_key = {_candidate_key(candidate): candidate for candidate in attenuated_candidates}
    keys = sorted(set(baseline_by_key) | set(attenuated_by_key))
    baseline_ranks = {_candidate_key(candidate): index for index, candidate in enumerate(baseline_candidates, start=1)}
    attenuated_ranks = {_candidate_key(candidate): index for index, candidate in enumerate(attenuated_candidates, start=1)}

    rank_shift_rows: list[dict[str, Any]] = []
    for key in keys:
        baseline_candidate = baseline_by_key.get(key)
        attenuated_candidate = attenuated_by_key.get(key)
        baseline_rank = baseline_ranks.get(key)
        attenuated_rank = attenuated_ranks.get(key)
        baseline_rarity = baseline_candidate.joint_match_rarity if baseline_candidate else 0.0
        attenuated_rarity = attenuated_candidate.joint_match_rarity if attenuated_candidate else 0.0
        rank_shift_rows.append(
            {
                "candidate": key,
                "baseline_rank": baseline_rank,
                "attenuated_rank": attenuated_rank,
                "rank_shift": None if baseline_rank is None or attenuated_rank is None else attenuated_rank - baseline_rank,
                "baseline_rarity": baseline_rarity,
                "attenuated_rarity": attenuated_rarity,
                "rarity_shift": attenuated_rarity - baseline_rarity,
                "baseline_survival": key in {_candidate_key(candidate) for candidate in baseline["gated_candidates"]},
                "attenuated_survival": key in {_candidate_key(candidate) for candidate in attenuated["gated_candidates"]},
            }
        )

    baseline_keys = set(baseline_by_key)
    attenuated_keys = set(attenuated_by_key)
    union_count = len(baseline_keys | attenuated_keys)
    overlap_percent = 100.0 * len(baseline_keys & attenuated_keys) / union_count if union_count else 100.0
    lc560_rows = [row for row in rank_shift_rows if "lc560." in row["candidate"]]
    lc560_sensitivity = _mean(
        [
            abs(row["rarity_shift"]) / row["baseline_rarity"]
            for row in lc560_rows
            if row["baseline_rarity"]
        ]
    )
    baseline_null_max = max(baseline["null_rarity_distribution"]) if baseline["null_rarity_distribution"] else 0.0
    attenuated_null_max = max(attenuated["null_rarity_distribution"]) if attenuated["null_rarity_distribution"] else 0.0
    compression_ratio = attenuated_null_max / baseline_null_max if baseline_null_max else 0.0
    return {
        "rank_shift_rows": rank_shift_rows,
        "candidate_set_overlap_percent": overlap_percent,
        "lc560_pair_sensitivity_index": lc560_sensitivity,
        "null_distribution_compression_ratio": compression_ratio,
        "classification": _classify_lc560_role(rank_shift_rows, lc560_sensitivity, compression_ratio),
    }


def candidate_centrality(candidates: list[CandidateAnomaly]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        for manifold in (candidate.manifold_a, candidate.manifold_b):
            problem_id = manifold.split(".", 1)[0]
            counts[problem_id] = counts.get(problem_id, 0) + 1

    total = len(candidates)
    table = [
        {
            "problem_id": problem_id,
            "appearances": appearances,
            "share": appearances / total if total else 0.0,
            "label": "hub_candidate" if total and appearances / total > 0.5 else "",
        }
        for problem_id, appearances in counts.items()
    ]
    return sorted(table, key=lambda row: (-row["appearances"], row["problem_id"]))


def detect_candidate_anomalies(
    artifacts: list[dict[str, Any]], *, apply_lr_gate: bool = True
) -> list[CandidateAnomaly]:
    return _detect_candidate_anomalies(artifacts, apply_lr_gate=apply_lr_gate, attenuate_problem=None)


def _detect_candidate_anomalies(
    artifacts: list[dict[str, Any]],
    *,
    apply_lr_gate: bool = True,
    attenuate_problem: str | None = None,
) -> list[CandidateAnomaly]:
    candidates: list[CandidateAnomaly] = []
    null_distribution = build_null_model(artifacts)
    match_probs = dimension_match_probs(artifacts, attenuate_problem=attenuate_problem)
    gate_floor = _null_lr_gate_floor_with_probs(artifacts, match_probs)
    for left, right in _cross_domain_pairs(artifacts):
        score, matching = score_pair(left, right)
        rarity = joint_match_rarity(matching, match_probs)
        if score >= 4.0 and (not apply_lr_gate or rarity >= gate_floor.value):
            candidates.append(
                CandidateAnomaly(
                    label="CANDIDATE_ANOMALY_ABOVE_LR_THRESHOLD",
                    manifold_a=_artifact_name(left),
                    manifold_b=_artifact_name(right),
                    score=round(score, 2),
                    matching=matching,
                    null_percentile=round(percentile_rank(score, null_distribution), 2),
                    joint_match_rarity=round(rarity, 6),
                )
            )
    return sorted(candidates, key=lambda item: (-item.joint_match_rarity, -item.score, item.manifold_a, item.manifold_b))


def _observer_run(artifacts: list[dict[str, Any]], attenuate_problem: str | None) -> dict[str, Any]:
    match_probs = dimension_match_probs(artifacts, attenuate_problem=attenuate_problem)
    null_rarity_distribution = _null_rarity_distribution(artifacts, match_probs)
    return {
        "attenuate_problem": attenuate_problem,
        "match_probs": match_probs,
        "null_rarity_distribution": null_rarity_distribution,
        "gate_floor": _gate_floor_from_distribution(null_rarity_distribution),
        "gated_candidates": _detect_candidate_anomalies(
            artifacts, apply_lr_gate=True, attenuate_problem=attenuate_problem
        ),
        "audit_candidates": _detect_candidate_anomalies(
            artifacts, apply_lr_gate=False, attenuate_problem=attenuate_problem
        ),
    }


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


def weakest_signal(artifacts: list[dict[str, Any]]) -> str:
    misses = {dimension: 0 for dimension in DIMENSIONS}
    for left, right in _cross_domain_pairs(artifacts):
        _, matching = score_pair(left, right)
        for dimension in DIMENSIONS:
            if dimension not in matching:
                misses[dimension] += 1
    return max(misses, key=misses.get) if misses else "none"


def _artifact_name(artifact: dict[str, Any]) -> str:
    return f"{artifact['problem_id']}.{artifact['manifold_id']}"


def _cross_domain_pairs(
    artifacts: list[dict[str, Any]], *, include_locked: bool = True
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    for left, right in itertools.combinations(artifacts, 2):
        if left["problem_id"] == right["problem_id"]:
            continue
        if not include_locked and _is_locked_pair(left, right):
            continue
        yield left, right


def _pair_weight(left: dict[str, Any], right: dict[str, Any], attenuate_problem: str | None) -> float:
    weight = 1.0
    if attenuate_problem in {left["problem_id"], right["problem_id"]}:
        return min(weight, ATTENUATED_PROBLEM_WEIGHT_CAP)
    return weight


def _null_rarity_distribution(artifacts: list[dict[str, Any]], match_probs: dict[str, float]) -> list[float]:
    distribution: list[float] = []
    for left, right in _cross_domain_pairs(artifacts, include_locked=False):
        _, matching = score_pair(left, right)
        distribution.append(joint_match_rarity(matching, match_probs))
    return sorted(distribution)


def _null_lr_gate_floor_with_probs(
    artifacts: list[dict[str, Any]], match_probs: dict[str, float]
) -> NullLRGateFloor:
    return _gate_floor_from_distribution(_null_rarity_distribution(artifacts, match_probs))


def _gate_floor_from_distribution(distribution: list[float]) -> NullLRGateFloor:
    if not distribution:
        return NullLRGateFloor(value=0.0, method="empty_null", null_pair_count=0, null_lr_max=0.0)

    sorted_values = sorted(distribution)
    null_lr_max = sorted_values[-1]
    if len(sorted_values) < 1000:
        return NullLRGateFloor(
            value=round(null_lr_max * 1.2, 6),
            method="margin_fallback",
            null_pair_count=len(sorted_values),
            null_lr_max=round(null_lr_max, 6),
        )

    index = max(0, math.ceil(len(sorted_values) * 0.999) - 1)
    return NullLRGateFloor(
        value=round(sorted_values[index], 6),
        method="top_0_1_percent",
        null_pair_count=len(sorted_values),
        null_lr_max=round(null_lr_max, 6),
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _classify_lc560_role(
    rank_shift_rows: list[dict[str, Any]], lc560_sensitivity: float, compression_ratio: float
) -> str:
    lc560_rows = [row for row in rank_shift_rows if "lc560." in row["candidate"]]
    lc560_survival_changed = any(row["baseline_survival"] != row["attenuated_survival"] for row in lc560_rows)
    lc560_reshuffled = any(row["rank_shift"] is not None and abs(row["rank_shift"]) >= 2 for row in lc560_rows)
    non_lc560_rows = [row for row in rank_shift_rows if "lc560." not in row["candidate"]]
    non_lc560_stable = all(
        row["rank_shift"] in {None, 0} or abs(row["rank_shift"]) <= 1 for row in non_lc560_rows
    )

    if lc560_sensitivity < 0.10 and compression_ratio > 0.90 and not lc560_survival_changed:
        return "true_structural_high_entropy_domain"
    if (lc560_sensitivity >= 0.40 or lc560_survival_changed or lc560_reshuffled) and non_lc560_stable:
        return "partial_axis_real_but_over_weighted"
    if lc560_sensitivity >= 0.40 or lc560_survival_changed or lc560_reshuffled:
        return "metric_amplifier_correlation_hub"
    return "mixed_stability_partial_axis"


def _is_locked_pair(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return frozenset((_artifact_name(left), _artifact_name(right))) in LOCKED_PAIRS


def _candidate_key(candidate: CandidateAnomaly) -> str:
    return f"{candidate.manifold_a} x {candidate.manifold_b}"


def _candidate_problem_ids(candidates: list[CandidateAnomaly]) -> set[str]:
    problem_ids: set[str] = set()
    for candidate in candidates:
        problem_ids.add(candidate.manifold_a.split(".", 1)[0])
        problem_ids.add(candidate.manifold_b.split(".", 1)[0])
    return problem_ids


def _coefficient_of_variation(values: list[float]) -> float:
    if any(not math.isfinite(value) for value in values):
        return math.inf
    mean = sum(values) / len(values)
    if mean == 0.0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance) / mean


def _instability_class(coefficient_of_variation: float) -> str:
    if coefficient_of_variation < 0.10:
        return "stable"
    if coefficient_of_variation <= 0.40:
        return "hub_sensitive"
    return "null_fragile"


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
