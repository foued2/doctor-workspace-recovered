from __future__ import annotations

import heapq
import json
from pathlib import Path
from typing import Any

import pytest

from doctor.adversarial.comparators import ExactIntSequenceComparator
from doctor.adversarial.lc3928_oracle import lc3928_exact_small


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTIFACT = ROOT / "data" / "lc3928_doctor_probe.json"
DUEL_ARTIFACT = ROOT / "data" / "track_d_phase2_lc3928_oracle_duel.json"


def test_lc3928_oracle_duel_artifact_records_100_agreements() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    assert artifact["target"] == "LC3928"
    assert artifact["cases_checked"] == 100
    assert artifact["agreements"] == 100
    assert artifact["disagreements"] == 0
    assert len(artifact["per_case"]) == 100
    assert artifact["forbidden_experiments_run"] is False


def test_lc3928_independent_dijkstra_oracle_agrees_on_selected_cases() -> None:
    source = _load_json(SOURCE_ARTIFACT)
    by_case_id = {case["case_id"]: case for case in source["case_records"]}
    artifact = _load_json(DUEL_ARTIFACT)

    for row in artifact["per_case"]:
        source_case = by_case_id[row["case_id"]]
        payload = source_case["input"]
        existing = lc3928_exact_small(payload["n"], payload["prices"], payload["roads"])
        independent = lc3928_dijkstra_oracle_small(payload["n"], payload["prices"], payload["roads"])
        assert row["existing_oracle_output"] == existing
        assert row["independent_oracle_output"] == independent
        assert independent == existing == source_case["oracle_output"]
        assert row["agreement"] is True


def test_lc3928_duel_case_mix_is_deterministic() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    assert artifact["case_mix"] == {
        "sample": 3,
        "shape_focused": 10,
        "adversarial_tradeoff": 25,
        "random_small": 50,
        "exhaustive_tiny": 12,
    }
    assert [row["case_id"] for row in artifact["per_case"]] == [
        case["case_id"] for case in _selected_source_cases(_load_json(SOURCE_ARTIFACT))
    ]


def test_lc3928_independent_oracle_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="n must be positive"):
        lc3928_dijkstra_oracle_small(0, [], [])
    with pytest.raises(ValueError, match="prices.length"):
        lc3928_dijkstra_oracle_small(2, [1], [])
    with pytest.raises(ValueError, match="repeated edge"):
        lc3928_dijkstra_oracle_small(2, [1, 2], [[0, 1, 1, 1], [1, 0, 2, 2]])


def test_lc3928_duel_comparator_rejects_bool_int_confusion() -> None:
    result = ExactIntSequenceComparator().compare([1], [True])
    assert result.equal is False
    assert result.type_match is False


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _selected_source_cases(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = source["case_records"]
    selected: list[dict[str, Any]] = []
    selected.extend(_first_by_suite(rows, "sample", 3))
    selected.extend(_first_by_suite(rows, "shape_focused", 10))
    selected.extend(_first_by_suite(rows, "adversarial_tradeoff", 23))
    selected.extend(_by_id(rows, ["lc3928_adv_tradeoff_065_max_small_path", "lc3928_adv_tradeoff_066_max_small_tax"]))
    selected.extend(_by_id(rows, ["lc3928_random_028"]))
    selected.extend(_first_by_suite_excluding(rows, "random_small", 49, {"lc3928_random_028"}))
    selected.extend(_first_by_suite(rows, "exhaustive_tiny", 12))
    assert len(selected) == 100
    return selected


def _first_by_suite(rows: list[dict[str, Any]], suite: str, count: int) -> list[dict[str, Any]]:
    return [row for row in rows if row["suite"] == suite][:count]


def _first_by_suite_excluding(
    rows: list[dict[str, Any]],
    suite: str,
    count: int,
    excluded_ids: set[str],
) -> list[dict[str, Any]]:
    return [row for row in rows if row["suite"] == suite and row["case_id"] not in excluded_ids][:count]


def _by_id(rows: list[dict[str, Any]], case_ids: list[str]) -> list[dict[str, Any]]:
    by_id = {row["case_id"]: row for row in rows}
    return [by_id[case_id] for case_id in case_ids]


def lc3928_dijkstra_oracle_small(n: int, prices: list[int], roads: list[list[int]]) -> list[int]:
    _validate_lc3928_small_input(n, prices, roads)
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


def _validate_lc3928_small_input(n: int, prices: list[int], roads: list[list[int]]) -> None:
    if n < 1:
        raise ValueError("n must be positive")
    if len(prices) != n:
        raise ValueError("prices.length must equal n")
    if any(type(price) is not int or type(price) is bool or price < 1 for price in prices):
        raise ValueError("prices must be positive integers")
    seen: set[tuple[int, int]] = set()
    for road in roads:
        if len(road) != 4:
            raise ValueError("road must have four integers")
        u, v, cost, tax = road
        if not (0 <= u < n and 0 <= v < n) or u == v:
            raise ValueError("invalid edge endpoints")
        if cost < 1 or tax < 1:
            raise ValueError("cost and tax must be positive")
        key = (min(u, v), max(u, v))
        if key in seen:
            raise ValueError("repeated edge")
        seen.add(key)


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
