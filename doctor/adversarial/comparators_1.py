"""Visible-side greedy_trap family for v0.3 protocol plumbing.

This module is based on existing committed greedy-failure LC3928
adversarial_tradeoff assets. It generates no hidden set, performs no hidden validation,
makes no new benchmark claim, uses no external judge, and contains no LLM-generated problem statement.

Distinct focus: greedy/local heuristic failure under travel-plus-price
tradeoff cases, not broad graph shortest-path computation.
"""

from __future__ import annotations

import heapq
from dataclasses import asdict
from typing import Any, Callable

from doctor.adversarial.comparators import get_comparator
from doctor.adversarial.lc3928_candidates import (
    lc3928_exact_small_reference,
    lc3928_greedy_nearest_shop,
)
from doctor.adversarial.lc3928_oracle import INF, lc3928_exact_small
from doctor.v03.hash_utils import hash_json_object, hash_text
from doctor.v03.interfaces import (
    AbstractV03Generator,
    AbstractV03Oracle,
    GeneratedCase,
    GeneratorSpec,
    OracleResult,
    OracleSpec,
    ParameterEnvelope,
)


FAMILY_ID = "greedy_trap"
PROBLEM_ID = "LC3928"
COMPARATOR_ID = "ExactIntSequenceComparator"
SPLIT_ID = "visible"

SOURCE_BASIS = (
    "Existing committed LC3928 adversarial_tradeoff / local-vs-global "
    "tradeoff assets: LC3928_PROBLEM_MANIFEST.json, "
    "LC3928_SOLVER_MANIFEST.json, doctor/adversarial/lc3928_oracle.py, "
    "doctor/adversarial/lc3928_candidates.py, "
    "runners/run_doctor_probe_lc3928.py, data/lc3928_doctor_probe.json, "
    "findings/FINDINGS_154.md, and tests/test_lc3928_oracle_duel.py."
)
NO_EXTERNAL_DEPENDENCY_DECLARATION = True
NO_LLM_DEPENDENCY_DECLARATION = True
GREEDY_TRAP_FOCUS = (
    "greedy/local heuristic collapse under LC3928 adversarial_tradeoff cases"
)
WRONG_GREEDY_FAILURE_MODE = (
    "Greedy/local-price heuristics fail when local price or nearest-shop "
    "choice misses a lower total cost created by travel-plus-price tradeoffs."
)

GENERATOR_ID = "v03_greedy_trap_lc3928_visible_generator"
GENERATOR_VERSION = "1.0.0"
ORACLE_A_ID = "v03_greedy_trap_lc3928_existing_exact_oracle"
ORACLE_B_ID = "v03_greedy_trap_lc3928_independent_dijkstra_oracle"
ORACLE_VERSION = "1.0.0"
EXACT_SOLVER_ID = "v03_greedy_trap_exact_reference_solver"
GREEDY_SOLVER_ID = "v03_greedy_trap_known_wrong_nearest_shop_solver"

_VISIBLE_CASE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "case_id": "v03_greedy_trap_visible_001",
        "source_case_id": "lc3928_adv_tradeoff_001_cheap_distant_path",
        "suite": "adversarial_tradeoff",
        "trap_type": "cheap_distant_path",
        "n": 4,
        "prices": [100, 95, 90, 1],
        "roads": [[0, 1, 1, 1], [1, 2, 1, 1], [2, 3, 1, 1]],
    },
    {
        "case_id": "v03_greedy_trap_visible_002",
        "source_case_id": "lc3928_adv_tradeoff_011_cheap_near_high_tax",
        "suite": "adversarial_tradeoff",
        "trap_type": "cheap_near_high_tax",
        "n": 4,
        "prices": [30, 1, 25, 24],
        "roads": [[0, 1, 1, 2], [0, 2, 2, 1], [2, 3, 1, 1]],
    },
    {
        "case_id": "v03_greedy_trap_visible_003",
        "source_case_id": "lc3928_adv_tradeoff_021_different_return_path",
        "suite": "adversarial_tradeoff",
        "trap_type": "different_return_path",
        "n": 5,
        "prices": [70, 60, 4, 50, 45],
        "roads": [[0, 1, 1, 50], [1, 2, 1, 50], [0, 3, 1, 1], [3, 4, 1, 1], [4, 2, 1, 1]],
    },
    {
        "case_id": "v03_greedy_trap_visible_004",
        "source_case_id": "lc3928_adv_tradeoff_031_price_dominates_travel",
        "suite": "adversarial_tradeoff",
        "trap_type": "price_dominates_travel",
        "n": 3,
        "prices": [20, 1, 25],
        "roads": [[0, 1, 3, 1], [1, 2, 2, 1], [0, 2, 1, 100]],
    },
    {
        "case_id": "v03_greedy_trap_visible_005",
        "source_case_id": "lc3928_adv_tradeoff_041_near_equal_options",
        "suite": "adversarial_tradeoff",
        "trap_type": "near_equal_options",
        "n": 5,
        "prices": [100, 99, 100, 1, 100],
        "roads": [[0, 1, 1, 2], [1, 2, 1, 2], [2, 3, 10, 1], [0, 4, 2, 1], [4, 3, 2, 1]],
    },
    {
        "case_id": "v03_greedy_trap_visible_006",
        "source_case_id": "lc3928_adv_tradeoff_051_edge_weight_contrast",
        "suite": "adversarial_tradeoff",
        "trap_type": "edge_weight_contrast",
        "n": 6,
        "prices": [90, 80, 70, 60, 50, 1],
        "roads": [[0, 1, 1, 1], [1, 2, 5, 1], [2, 5, 1, 1], [0, 3, 2, 2], [3, 4, 2, 2], [4, 5, 2, 2]],
    },
    {
        "case_id": "v03_greedy_trap_visible_007",
        "source_case_id": "lc3928_adv_tradeoff_061_nearest_bad_tax",
        "suite": "adversarial_tradeoff",
        "trap_type": "nearest_bad_tax",
        "n": 6,
        "prices": [100, 2, 100, 100, 3, 100],
        "roads": [[0, 1, 1, 90], [0, 2, 2, 1], [2, 3, 2, 1], [3, 4, 2, 1], [4, 5, 1, 1]],
    },
    {
        "case_id": "v03_greedy_trap_visible_008",
        "source_case_id": "lc3928_adv_tradeoff_064_cheap_local_vs_better_route",
        "suite": "adversarial_tradeoff",
        "trap_type": "cheap_local_vs_better_route",
        "n": 7,
        "prices": [100, 1, 100, 100, 100, 2, 100],
        "roads": [[0, 1, 2, 60], [0, 2, 4, 1], [2, 3, 1, 1], [3, 4, 1, 1], [4, 5, 1, 1], [5, 6, 1, 1]],
    },
)

_PARAMETER_ENVELOPE = ParameterEnvelope(
    family_id=FAMILY_ID,
    bounds={
        "n": (3, 7),
        "roads_length": (3, 6),
        "price": (1, 100),
        "edge_cost": (1, 10),
        "edge_tax": (1, 90),
    },
    description="Visible LC3928 adversarial_tradeoff greedy-trap cases only.",
)

PARAMETER_ENVELOPE_HASH = hash_json_object(asdict(_PARAMETER_ENVELOPE))
VISIBLE_FAMILY_HASH = hash_json_object(
    {
        "family_id": FAMILY_ID,
        "problem_id": PROBLEM_ID,
        "split_id": SPLIT_ID,
        "source_basis": SOURCE_BASIS,
        "focus": GREEDY_TRAP_FOCUS,
        "cases": _VISIBLE_CASE_SPECS,
    }
)
GENERATOR_HASH = hash_json_object(
    {
        "generator_id": GENERATOR_ID,
        "version": GENERATOR_VERSION,
        "visible_family_hash": VISIBLE_FAMILY_HASH,
    }
)
ORACLE_A_HASH = hash_text(f"{ORACLE_A_ID}:{ORACLE_VERSION}:existing-lc3928-exact-small")
ORACLE_B_HASH = hash_text(f"{ORACLE_B_ID}:{ORACLE_VERSION}:independent-dijkstra")
EXACT_SOLVER_HASH = hash_text(f"{EXACT_SOLVER_ID}:existing-lc3928-exact-small-reference:v1")
GREEDY_SOLVER_HASH = hash_text(f"{GREEDY_SOLVER_ID}:existing-lc3928-greedy-nearest-shop:v1")
VISIBLE_SEED_HASH = hash_text("deterministic-visible-lc3928-adversarial-tradeoff-cases")


class GreedyTrapVisibleGenerator(AbstractV03Generator):
    def spec(self) -> GeneratorSpec:
        return GeneratorSpec(
            family_id=FAMILY_ID,
            generator_id=GENERATOR_ID,
            generator_version=GENERATOR_VERSION,
            generator_hash=GENERATOR_HASH,
            deterministic_seed_policy="fixed committed LC3928 adversarial_tradeoff cases",
            parameter_envelope=self.parameter_envelope(),
            input_schema={
                "type": "object",
                "required": ["problem_id", "split_id", "n", "prices", "roads", "trap_type"],
                "properties": {
                    "problem_id": {"const": PROBLEM_ID},
                    "split_id": {"const": SPLIT_ID},
                    "n": {"type": "integer", "minimum": 1},
                    "prices": {"type": "array", "items": {"type": "integer"}},
                    "roads": {"type": "array"},
                    "trap_type": {"type": "string"},
                },
            },
            output_case_schema={
                "type": "object",
                "required": ["family_id", "case_id", "input_payload"],
            },
        )

    def parameter_envelope(self) -> ParameterEnvelope:
        return _PARAMETER_ENVELOPE

    def generate_case(
        self, case_id: str, seed: str | int | None = None
    ) -> GeneratedCase:
        del seed
        spec = _case_spec_by_id(case_id)
        case = GeneratedCase(
            family_id=FAMILY_ID,
            case_id=case_id,
            input_payload={
                "problem_id": PROBLEM_ID,
                "split_id": SPLIT_ID,
                "source_case_id": spec["source_case_id"],
                "suite": spec["suite"],
                "trap_type": spec["trap_type"],
                "n": spec["n"],
                "prices": list(spec["prices"]),
                "roads": [list(road) for road in spec["roads"]],
            },
            parameter_envelope_hash=PARAMETER_ENVELOPE_HASH,
            generator_id=GENERATOR_ID,
            generator_hash=GENERATOR_HASH,
            seed_hash=VISIBLE_SEED_HASH,
        )
        self.validate_case(case)
        return case

    def generate_visible_cases(self) -> list[GeneratedCase]:
        return [self.generate_case(spec["case_id"]) for spec in _VISIBLE_CASE_SPECS]

    def validate_case(self, case: GeneratedCase) -> None:
        if case.family_id != FAMILY_ID:
            raise ValueError(f"unexpected family_id: {case.family_id!r}")
        if case.generator_id != GENERATOR_ID:
            raise ValueError(f"unexpected generator_id: {case.generator_id!r}")
        if case.input_payload.get("split_id") != SPLIT_ID:
            raise ValueError("greedy_trap generator emits visible cases only")
        if case.input_payload.get("suite") != "adversarial_tradeoff":
            raise ValueError("greedy_trap family admits adversarial_tradeoff cases only")
        _coerce_input(case.input_payload)


class GreedyTrapExistingOracle(AbstractV03Oracle):
    def spec(self) -> OracleSpec:
        return _oracle_spec(
            ORACLE_A_ID,
            ORACLE_A_HASH,
            "Existing LC3928 exact small oracle on adversarial_tradeoff cases.",
        )

    def solve(self, case: GeneratedCase) -> OracleResult:
        n, prices, roads = _coerce_input(case.input_payload)
        expected = lc3928_exact_small(n, prices, roads)
        result = OracleResult(
            family_id=FAMILY_ID,
            case_id=case.case_id,
            expected_output=expected,
            expected_output_hash=hash_json_object(expected),
            oracle_id=ORACLE_A_ID,
            oracle_hash=ORACLE_A_HASH,
            comparator_id=COMPARATOR_ID,
        )
        self.validate_result(case, result)
        return result

    def validate_result(self, case: GeneratedCase, result: OracleResult) -> None:
        if not self.supports(case):
            raise ValueError(f"unsupported case for {ORACLE_A_ID}: {case.case_id}")
        if result.comparator_id != COMPARATOR_ID:
            raise ValueError("greedy_trap uses exact ordered integer-list comparison only")

    def supports(self, case: GeneratedCase) -> bool:
        try:
            _coerce_input(case.input_payload)
        except ValueError:
            return False
        return case.family_id == FAMILY_ID and case.input_payload.get("split_id") == SPLIT_ID


class GreedyTrapDijkstraOracle(AbstractV03Oracle):
    def spec(self) -> OracleSpec:
        return _oracle_spec(
            ORACLE_B_ID,
            ORACLE_B_HASH,
            "Independent Dijkstra oracle for adversarial_tradeoff cases.",
        )

    def solve(self, case: GeneratedCase) -> OracleResult:
        expected = dijkstra_independent_oracle(case.input_payload)
        result = OracleResult(
            family_id=FAMILY_ID,
            case_id=case.case_id,
            expected_output=expected,
            expected_output_hash=hash_json_object(expected),
            oracle_id=ORACLE_B_ID,
            oracle_hash=ORACLE_B_HASH,
            comparator_id=COMPARATOR_ID,
        )
        self.validate_result(case, result)
        return result

    def validate_result(self, case: GeneratedCase, result: OracleResult) -> None:
        if not self.supports(case):
            raise ValueError(f"unsupported case for {ORACLE_B_ID}: {case.case_id}")
        if result.comparator_id != COMPARATOR_ID:
            raise ValueError("greedy_trap uses exact ordered integer-list comparison only")

    def supports(self, case: GeneratedCase) -> bool:
        try:
            _coerce_input(case.input_payload)
        except ValueError:
            return False
        return case.family_id == FAMILY_ID and case.input_payload.get("split_id") == SPLIT_ID


def visible_case_ids() -> list[str]:
    return [spec["case_id"] for spec in _VISIBLE_CASE_SPECS]


def visible_trap_types() -> list[str]:
    return [spec["trap_type"] for spec in _VISIBLE_CASE_SPECS]


def dijkstra_independent_oracle(input_payload: dict[str, Any]) -> list[int]:
    n, prices, roads = _coerce_input(input_payload)
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
    answer: list[int] = []
    for start in range(n):
        best = prices[start]
        for shop in range(n):
            if empty_dist[start][shop] >= INF or loaded_dist[shop][start] >= INF:
                continue
            best = min(best, empty_dist[start][shop] + prices[shop] + loaded_dist[shop][start])
        answer.append(int(best))
    return answer


def exact_reference_solver(input_payload: dict[str, Any]) -> list[int]:
    n, prices, roads = _coerce_input(input_payload)
    return lc3928_exact_small_reference(n, prices, roads)


def known_wrong_greedy_solver(input_payload: dict[str, Any]) -> list[int]:
    n, prices, roads = _coerce_input(input_payload)
    return lc3928_greedy_nearest_shop(n, prices, roads)


def duel_visible_oracles() -> list[dict[str, Any]]:
    generator = GreedyTrapVisibleGenerator()
    oracle_a = GreedyTrapExistingOracle()
    oracle_b = GreedyTrapDijkstraOracle()
    rows = []
    for case in generator.generate_visible_cases():
        result_a = oracle_a.solve(case)
        result_b = oracle_b.solve(case)
        rows.append(
            {
                "family_id": FAMILY_ID,
                "split_id": SPLIT_ID,
                "case_id": case.case_id,
                "trap_type": case.input_payload["trap_type"],
                "oracle_a_id": result_a.oracle_id,
                "oracle_b_id": result_b.oracle_id,
                "oracle_a_output": result_a.expected_output,
                "oracle_b_output": result_b.expected_output,
                "agreement": result_a.expected_output == result_b.expected_output,
            }
        )
    return rows


def evaluate_visible_cases(
    repo_commit: str = "visible-family-test-context",
) -> list[dict[str, Any]]:
    generator = GreedyTrapVisibleGenerator()
    oracle = GreedyTrapExistingOracle()
    solvers: tuple[tuple[str, str, Callable[[dict[str, Any]], list[int]]], ...] = (
        (EXACT_SOLVER_ID, EXACT_SOLVER_HASH, exact_reference_solver),
        (GREEDY_SOLVER_ID, GREEDY_SOLVER_HASH, known_wrong_greedy_solver),
    )
    comparator = get_comparator(COMPARATOR_ID)
    rows: list[dict[str, Any]] = []
    for case in generator.generate_visible_cases():
        expected = oracle.solve(case)
        for solver_id, solver_hash, solver in solvers:
            observed = solver(case.input_payload)
            comparison = comparator.compare(observed, expected.expected_output)
            rows.append(
                {
                    "family_id": FAMILY_ID,
                    "split_id": SPLIT_ID,
                    "case_id": case.case_id,
                    "trap_type": case.input_payload["trap_type"],
                    "generator_id": case.generator_id,
                    "generator_hash": case.generator_hash,
                    "oracle_id": expected.oracle_id,
                    "oracle_hash": expected.oracle_hash,
                    "comparator_id": expected.comparator_id,
                    "solver_id": solver_id,
                    "solver_hash": solver_hash,
                    "input_hash": hash_json_object(case.input_payload),
                    "expected_output_hash": expected.expected_output_hash,
                    "observed_output_hash": hash_json_object(observed),
                    "scoring_decision": "pass" if comparison.equal else "fail",
                    "repo_commit": repo_commit,
                    "manifest_hash": VISIBLE_FAMILY_HASH,
                    "expected_output": expected.expected_output,
                    "observed_output": observed,
                }
            )
    return rows


def _oracle_spec(oracle_id: str, oracle_hash: str, exactness_claim: str) -> OracleSpec:
    return OracleSpec(
        family_id=FAMILY_ID,
        oracle_id=oracle_id,
        oracle_version=ORACLE_VERSION,
        oracle_hash=oracle_hash,
        supported_input_schema={
            "type": "object",
            "required": ["problem_id", "split_id", "n", "prices", "roads", "trap_type"],
        },
        supported_parameter_envelope=_PARAMETER_ENVELOPE,
        exactness_claim=exactness_claim,
        expected_output_schema={"type": "array", "items": {"type": "integer"}},
        comparator_id=COMPARATOR_ID,
    )


def _case_spec_by_id(case_id: str) -> dict[str, Any]:
    for spec in _VISIBLE_CASE_SPECS:
        if spec["case_id"] == case_id:
            return spec
    raise ValueError(f"unknown visible greedy_trap case_id: {case_id!r}")


def _coerce_input(input_payload: dict[str, Any]) -> tuple[int, list[int], list[list[int]]]:
    if input_payload.get("problem_id") != PROBLEM_ID:
        raise ValueError("greedy_trap visible family uses existing LC3928 basis only")
    if input_payload.get("split_id") != SPLIT_ID:
        raise ValueError("greedy_trap visible family rejects non-visible input")
    if input_payload.get("suite") != "adversarial_tradeoff":
        raise ValueError("greedy_trap visible family requires adversarial_tradeoff suite")
    if not input_payload.get("trap_type"):
        raise ValueError("greedy_trap visible family requires trap_type")
    n = input_payload.get("n")
    prices = input_payload.get("prices")
    roads = input_payload.get("roads")
    if type(n) is not int or type(n) is bool or n < 1:
        raise ValueError("n must be a positive integer")
    if type(prices) is not list or len(prices) != n:
        raise ValueError("prices must be a list of length n")
    if any(type(price) is not int or type(price) is bool or price < 1 for price in prices):
        raise ValueError("prices must be positive integers")
    if type(roads) is not list:
        raise ValueError("roads must be a list")
    seen: set[tuple[int, int]] = set()
    normalized_roads: list[list[int]] = []
    for road in roads:
        if type(road) is not list or len(road) != 4:
            raise ValueError("road must have four integers")
        u, v, cost, tax = road
        if any(type(value) is not int or type(value) is bool for value in road):
            raise ValueError("road values must be integers")
        if not (0 <= u < n and 0 <= v < n) or u == v:
            raise ValueError("invalid edge endpoints")
        if cost < 1 or tax < 1:
            raise ValueError("cost and tax must be positive")
        key = (min(u, v), max(u, v))
        if key in seen:
            raise ValueError("repeated edge")
        seen.add(key)
        normalized_roads.append([u, v, cost, tax])
    return n, list(prices), normalized_roads


def _dijkstra(graph: list[list[tuple[int, int]]], start: int) -> list[int]:
    dist = [INF] * len(graph)
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
