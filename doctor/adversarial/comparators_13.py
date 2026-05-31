from __future__ import annotations

import heapq
import json
from pathlib import Path
from typing import Any

import pytest

from doctor.adversarial.comparators import (
    ComparatorTypeMismatch,
    ExactIntComparator,
    ExactIntSequenceComparator,
    StructuredComparator,
)
from doctor.adversarial.experiment_contract import ExperimentContractError, validate_provenance
from doctor.adversarial.experiment_runner import (
    PerturbationScoringBlocked,
    recompute_oracles,
    validate_scoring_gate,
)
from doctor.adversarial.lc3928_oracle import lc3928_exact_small
from doctor.adversarial.perturbation_validity import PerturbationClass, PerturbationDeclaration


ROOT = Path(__file__).resolve().parents[1]


def _raw_equal(actual: Any, expected: Any) -> bool:
    return actual == expected


def test_d1_stale_oracle_mutant_is_detectable() -> None:
    base_input = {"value": 2}
    perturbed_input = {"value": 5}

    def oracle(case: dict[str, int]) -> int:
        return case["value"] * 10

    def solver(case: dict[str, int]) -> int:
        return case["value"] * 10

    expected_base, expected_perturbed = recompute_oracles(
        oracle,
        base_input,
        perturbed_input,
        lambda fn, case: fn(case),
    )

    correct_verdict = solver(perturbed_input) == expected_perturbed
    stale_mutant_verdict = solver(perturbed_input) == expected_base

    assert expected_base != expected_perturbed
    assert correct_verdict is True
    assert stale_mutant_verdict is False


def test_d2_typed_comparators_kill_raw_equality_mutant() -> None:
    assert _raw_equal(1, True) is True
    assert _raw_equal([1], [True]) is True
    assert _raw_equal([[1]], [[True]]) is True

    with pytest.raises(ComparatorTypeMismatch):
        ExactIntComparator().compare(1, True)

    flat = ExactIntSequenceComparator().compare([1], [True])
    assert flat.equal is False
    assert flat.type_match is False

    nested = StructuredComparator().compare([[1]], [[True]])
    assert nested.equal is False
    assert nested.type_match is False


def test_d3_output_preserving_without_proof_card_is_blocked() -> None:
    import doctor.adversarial.perturbation_validity as pv

    key = ("TRACK_D", "proofless_output_preserving")
    original = pv.PERTURBATION_VALIDITY_REGISTRY.get(key)
    pv.PERTURBATION_VALIDITY_REGISTRY[key] = PerturbationDeclaration(
        perturbation_class=PerturbationClass.OUTPUT_PRESERVING,
        justification="Track D mutant: proof-card bypass",
        proof_card_id=None,
    )
    try:
        with pytest.raises(PerturbationScoringBlocked, match="proof_card_id"):
            validate_scoring_gate(*key)
    finally:
        if original is None:
            del pv.PERTURBATION_VALIDITY_REGISTRY[key]
        else:
            pv.PERTURBATION_VALIDITY_REGISTRY[key] = original


@pytest.mark.parametrize(
    "klass,family",
    [
        (PerturbationClass.UNKNOWN_UNTIL_ORACLE_RECOMPUTE, "unknown_until_recompute"),
        (PerturbationClass.INVALID, "invalid_family"),
    ],
)
def test_d4_unknown_and_invalid_perturbations_are_blocked(
    klass: PerturbationClass,
    family: str,
) -> None:
    import doctor.adversarial.perturbation_validity as pv

    key = ("TRACK_D", family)
    original = pv.PERTURBATION_VALIDITY_REGISTRY.get(key)
    pv.PERTURBATION_VALIDITY_REGISTRY[key] = PerturbationDeclaration(
        perturbation_class=klass,
        justification="Track D mutant: unsafe scoring class",
        proof_card_id=None,
    )
    try:
        with pytest.raises(PerturbationScoringBlocked, match="scoring blocked"):
            validate_scoring_gate(*key)
    finally:
        if original is None:
            del pv.PERTURBATION_VALIDITY_REGISTRY[key]
        else:
            pv.PERTURBATION_VALIDITY_REGISTRY[key] = original


def test_d5_missing_provenance_metric_result_is_rejected() -> None:
    with pytest.raises(ExperimentContractError, match="missing k_provenance"):
        validate_provenance({"metric": "pass_rate", "value": 1.0})


def test_d6_lc3928_generator_contrast_exposes_random_only_weakness() -> None:
    data = json.loads((ROOT / "data" / "lc3928_doctor_probe.json").read_text())
    rows = {
        (row["solver_name"], row["suite"]): row
        for row in data["result_rows"]
    }

    for solver in ("lc3928_naive_local_price", "lc3928_greedy_nearest_shop"):
        exhaustive = rows[(solver, "exhaustive_tiny")]
        adversarial = rows[(solver, "adversarial_tradeoff")]
        assert exhaustive["case_count"] == 3423
        assert exhaustive["pass_count"] == 3423
        assert exhaustive["fail_count"] == 0
        assert adversarial["case_count"] == 66
        assert adversarial["pass_count"] == 0
        assert adversarial["fail_count"] == 66


def test_d7_lc3928_independent_dijkstra_oracle_duel_agrees_on_selected_cases() -> None:
    data = json.loads((ROOT / "data" / "lc3928_doctor_probe.json").read_text())
    selected = []
    per_suite = {"sample": 3, "shape_focused": 5, "adversarial_tradeoff": 6, "random_small": 6}
    counts = {suite: 0 for suite in per_suite}
    for case in data["case_records"]:
        suite = case["suite"]
        if suite in per_suite and counts[suite] < per_suite[suite]:
            selected.append(case)
            counts[suite] += 1
        if len(selected) == sum(per_suite.values()):
            break

    assert len(selected) == 20
    for case in selected:
        payload = case["input"]
        expected = lc3928_exact_small(payload["n"], payload["prices"], payload["roads"])
        duel = _lc3928_dijkstra_oracle_small(payload["n"], payload["prices"], payload["roads"])
        assert duel == expected == case["oracle_output"]


def _lc3928_dijkstra_oracle_small(n: int, prices: list[int], roads: list[list[int]]) -> list[int]:
    empty_graph = [[] for _ in range(n)]
    loaded_graph = [[] for _ in range(n)]
    for u, v, cost, tax in roads:
        empty_graph[u].append((v, cost))
        empty_graph[v].append((u, cost))
        loaded_cost = cost * tax
        loaded_graph[u].append((v, loaded_cost))
        loaded_graph[v].append((u, loaded_cost))

    empty_dist = [_dijkstra(empty_graph, start) for start in range(n)]
    loaded_dist = [_dijkstra(loaded_graph, start) for start in range(n)]
    answer = []
    for start in range(n):
        best = prices[start]
        for shop in range(n):
            best = min(best, empty_dist[start][shop] + prices[shop] + loaded_dist[shop][start])
        answer.append(best)
    return answer


def _dijkstra(graph: list[list[tuple[int, int]]], start: int) -> list[int]:
    inf = 10**30
    dist = [inf] * len(graph)
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost != dist[node]:
            continue
        for nxt, weight in graph[node]:
            candidate = cost + weight
            if candidate < dist[nxt]:
                dist[nxt] = candidate
                heapq.heappush(heap, (candidate, nxt))
    return dist
