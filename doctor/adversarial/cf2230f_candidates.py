"""Visible-side state_space_search family for v0.3 protocol plumbing.

This module is based on existing committed CF2230F state-space minimax assets.
It uses q <= 6 only, generates no hidden set, performs no hidden validation,
makes no new benchmark claim, uses no external judge, and contains no
LLM-generated problem statement.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
import random
from typing import Any, Callable

from doctor.adversarial.cf2230f_candidates import (
    cf2230f_exact_bruteforce_small,
    cf2230f_greedy_deepest_start,
)
from doctor.adversarial.cf2230f_oracle import cf2230f_scores_small, validate_parent_sequence
from doctor.adversarial.comparators import get_comparator
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


FAMILY_ID = "state_space_search"
PROBLEM_ID = "CF2230F"
COMPARATOR_ID = "ExactIntSequenceComparator"
SPLIT_ID = "visible"
MAX_Q = 6

SOURCE_BASIS = (
    "Existing committed CF2230F / Game on Growing Tree assets: "
    "CF2230F_PROBLEM_MANIFEST.json, CF2230F_SOLVER_MANIFEST.json, "
    "doctor/adversarial/cf2230f_oracle.py, "
    "doctor/adversarial/cf2230f_candidates.py, "
    "runners/run_cf2230f_doctor_probe.py, "
    "tests/test_cf2230f_oracle_duel.py, data/cf2230f_doctor_probe.json, "
    "data/track_d_phase2_cf2230f_oracle_duel.json, findings/FINDINGS_152.md, "
    "and findings/FINDINGS_160.md."
)
NO_EXTERNAL_DEPENDENCY_DECLARATION = True
NO_LLM_DEPENDENCY_DECLARATION = True
VISIBLE_FAMILY_SCOPE = "visible-side family test only, not v0.3 validation"
WRONG_HEURISTIC_FAILURE_MODE = (
    "Local depth or greedy leaf heuristics fail because the minimax game state "
    "depends on future opponent choices, not only current tree depth."
)

GENERATOR_ID = "v03_state_space_search_cf2230f_visible_generator"
GENERATOR_VERSION = "1.0.0"
ORACLE_A_ID = "v03_state_space_search_cf2230f_existing_minimax_oracle"
ORACLE_B_ID = "v03_state_space_search_cf2230f_independent_minimax_oracle"
ORACLE_VERSION = "1.0.0"
EXACT_SOLVER_ID = "v03_state_space_search_exact_reference_solver"
WRONG_SOLVER_ID = "v03_state_space_search_known_wrong_depth_proxy_solver"

SAMPLE_PARENTS = [1, 1, 3, 3, 1, 2, 1, 2, 8]


def _build_visible_case_specs() -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for q in range(1, MAX_Q + 1):
        rows.append(
            {
                "case_id": f"v03_state_space_search_visible_sample_q{q}",
                "source_case_id": f"cf2230f_sample_prefix_q{q}",
                "suite": "sample_prefix",
                "parents": SAMPLE_PARENTS[:q],
            }
        )
    rows.extend(
        [
            {
                "case_id": "v03_state_space_search_visible_shape_path_q6",
                "source_case_id": "cf2230f_shape_path_q6",
                "suite": "deterministic_shape",
                "parents": [1, 2, 3, 4, 5, 6],
            },
            {
                "case_id": "v03_state_space_search_visible_shape_star_q6",
                "source_case_id": "cf2230f_shape_star_q6",
                "suite": "deterministic_shape",
                "parents": [1, 1, 1, 1, 1, 1],
            },
            {
                "case_id": "v03_state_space_search_visible_shape_balanced_q6",
                "source_case_id": "cf2230f_shape_balanced_q6",
                "suite": "deterministic_shape",
                "parents": [1, 1, 2, 2, 3, 3],
            },
            {
                "case_id": "v03_state_space_search_visible_shape_root_repeat_q5",
                "source_case_id": "cf2230f_shape_root_repeat_q5",
                "suite": "deterministic_shape",
                "parents": [1, 1, 1, 1, 1],
            },
            {
                "case_id": "v03_state_space_search_visible_shape_leaf_repeat_q5",
                "source_case_id": "cf2230f_shape_leaf_repeat_q5",
                "suite": "deterministic_shape",
                "parents": [1, 2, 3, 4, 5],
            },
        ]
    )
    rng = random.Random(2230_20260519)
    seen = {tuple(row["parents"]) for row in rows}
    random_index = 1
    while random_index <= 20:
        q = rng.randint(1, MAX_Q)
        parents = [rng.randint(1, i) for i in range(1, q + 1)]
        key = tuple(parents)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "case_id": f"v03_state_space_search_visible_random_{random_index:03d}",
                "source_case_id": f"cf2230f_random_q_le_6_{random_index:03d}",
                "suite": "deterministic_random",
                "parents": parents,
            }
        )
        random_index += 1
    return tuple(rows)


_VISIBLE_CASE_SPECS = _build_visible_case_specs()

_PARAMETER_ENVELOPE = ParameterEnvelope(
    family_id=FAMILY_ID,
    bounds={"q": (1, MAX_Q), "parent_value": (1, MAX_Q)},
    description="Visible CF2230F q <= 6 minimax state-space cases only.",
)

PARAMETER_ENVELOPE_HASH = hash_json_object(asdict(_PARAMETER_ENVELOPE))
VISIBLE_FAMILY_HASH = hash_json_object(
    {
        "family_id": FAMILY_ID,
        "problem_id": PROBLEM_ID,
        "split_id": SPLIT_ID,
        "max_q": MAX_Q,
        "scope": VISIBLE_FAMILY_SCOPE,
        "source_basis": SOURCE_BASIS,
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
ORACLE_A_HASH = hash_text(f"{ORACLE_A_ID}:{ORACLE_VERSION}:existing-cf2230f-minimax")
ORACLE_B_HASH = hash_text(f"{ORACLE_B_ID}:{ORACLE_VERSION}:independent-frozenset-minimax")
EXACT_SOLVER_HASH = hash_text(f"{EXACT_SOLVER_ID}:existing-cf2230f-exact-bruteforce-small:v1")
WRONG_SOLVER_HASH = hash_text(f"{WRONG_SOLVER_ID}:existing-cf2230f-greedy-deepest-start:v1")
VISIBLE_SEED_HASH = hash_text("deterministic-visible-cf2230f-q-le-6-cases")


class StateSpaceSearchVisibleGenerator(AbstractV03Generator):
    def spec(self) -> GeneratorSpec:
        return GeneratorSpec(
            family_id=FAMILY_ID,
            generator_id=GENERATOR_ID,
            generator_version=GENERATOR_VERSION,
            generator_hash=GENERATOR_HASH,
            deterministic_seed_policy="fixed committed CF2230F q <= 6 duel cases",
            parameter_envelope=self.parameter_envelope(),
            input_schema={
                "type": "object",
                "required": ["problem_id", "split_id", "parents", "q"],
                "properties": {
                    "problem_id": {"const": PROBLEM_ID},
                    "split_id": {"const": SPLIT_ID},
                    "parents": {"type": "array", "items": {"type": "integer"}},
                    "q": {"type": "integer", "minimum": 1, "maximum": MAX_Q},
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
        parents = list(spec["parents"])
        case = GeneratedCase(
            family_id=FAMILY_ID,
            case_id=case_id,
            input_payload={
                "problem_id": PROBLEM_ID,
                "split_id": SPLIT_ID,
                "source_case_id": spec["source_case_id"],
                "suite": spec["suite"],
                "q": len(parents),
                "parents": parents,
                "scope": VISIBLE_FAMILY_SCOPE,
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
        _coerce_input(case.input_payload)


class StateSpaceSearchExistingOracle(AbstractV03Oracle):
    def spec(self) -> OracleSpec:
        return _oracle_spec(
            ORACLE_A_ID,
            ORACLE_A_HASH,
            "Existing CF2230F exact small minimax oracle with q <= 6 gate.",
        )

    def solve(self, case: GeneratedCase) -> OracleResult:
        parents = _coerce_input(case.input_payload)
        expected = cf2230f_scores_small(parents, max_q=MAX_Q)
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
            raise ValueError("state_space_search uses exact ordered integer-list comparison only")

    def supports(self, case: GeneratedCase) -> bool:
        try:
            _coerce_input(case.input_payload)
        except ValueError:
            return False
        return case.family_id == FAMILY_ID and case.input_payload.get("split_id") == SPLIT_ID


class StateSpaceSearchIndependentOracle(AbstractV03Oracle):
    def spec(self) -> OracleSpec:
        return _oracle_spec(
            ORACLE_B_ID,
            ORACLE_B_HASH,
            "Independent minimax oracle adapted from committed CF2230F duel test.",
        )

    def solve(self, case: GeneratedCase) -> OracleResult:
        expected = independent_minimax_scores(case.input_payload)
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
            raise ValueError("state_space_search uses exact ordered integer-list comparison only")

    def supports(self, case: GeneratedCase) -> bool:
        try:
            _coerce_input(case.input_payload)
        except ValueError:
            return False
        return case.family_id == FAMILY_ID and case.input_payload.get("split_id") == SPLIT_ID


def visible_case_ids() -> list[str]:
    return [spec["case_id"] for spec in _VISIBLE_CASE_SPECS]


def max_visible_q() -> int:
    return max(len(spec["parents"]) for spec in _VISIBLE_CASE_SPECS)


def independent_minimax_scores(input_payload: dict[str, Any]) -> list[int]:
    parents = _coerce_input(input_payload)
    return [_score_prefix_independent(tuple(parents[:q])) for q in range(1, len(parents) + 1)]


def exact_reference_solver(input_payload: dict[str, Any]) -> list[int]:
    parents = _coerce_input(input_payload)
    return cf2230f_exact_bruteforce_small(parents)


def known_wrong_state_search_heuristic(input_payload: dict[str, Any]) -> list[int]:
    parents = _coerce_input(input_payload)
    return cf2230f_greedy_deepest_start(parents)


def duel_visible_oracles() -> list[dict[str, Any]]:
    generator = StateSpaceSearchVisibleGenerator()
    oracle_a = StateSpaceSearchExistingOracle()
    oracle_b = StateSpaceSearchIndependentOracle()
    rows = []
    for case in generator.generate_visible_cases():
        result_a = oracle_a.solve(case)
        result_b = oracle_b.solve(case)
        rows.append(
            {
                "family_id": FAMILY_ID,
                "split_id": SPLIT_ID,
                "case_id": case.case_id,
                "q": case.input_payload["q"],
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
    generator = StateSpaceSearchVisibleGenerator()
    oracle = StateSpaceSearchExistingOracle()
    solvers: tuple[tuple[str, str, Callable[[dict[str, Any]], list[int]]], ...] = (
        (EXACT_SOLVER_ID, EXACT_SOLVER_HASH, exact_reference_solver),
        (WRONG_SOLVER_ID, WRONG_SOLVER_HASH, known_wrong_state_search_heuristic),
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
                    "q": case.input_payload["q"],
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
            "required": ["problem_id", "split_id", "parents", "q"],
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
    raise ValueError(f"unknown visible state_space_search case_id: {case_id!r}")


def _coerce_input(input_payload: dict[str, Any]) -> list[int]:
    if input_payload.get("problem_id") != PROBLEM_ID:
        raise ValueError("state_space_search visible family uses existing CF2230F basis only")
    if input_payload.get("split_id") != SPLIT_ID:
        raise ValueError("state_space_search visible family rejects non-visible input")
    parents = input_payload.get("parents")
    q = input_payload.get("q")
    if type(parents) is not list:
        raise ValueError("parents must be a list")
    if type(q) is not int or type(q) is bool:
        raise ValueError("q must be an integer")
    if q != len(parents):
        raise ValueError("q must equal len(parents)")
    if q < 1 or q > MAX_Q:
        raise ValueError("CF2230F visible family q limit exceeded")
    if input_payload.get("scope") != VISIBLE_FAMILY_SCOPE:
        raise ValueError("state_space_search rows must be visible-side family test only")
    return list(validate_parent_sequence(parents))


def _score_prefix_independent(parents: tuple[int, ...]) -> int:
    n = len(parents) + 1
    neighbors = {node: set() for node in range(n)}
    for child, parent_one in enumerate(parents, start=1):
        parent = parent_one - 1
        neighbors[parent].add(child)
        neighbors[child].add(parent)

    @lru_cache(maxsize=None)
    def play(red: frozenset[int], blue: frozenset[int], chip: int | None, alice_turn: bool) -> int:
        occupied = red | blue
        white = frozenset(node for node in range(n) if node not in occupied)
        if alice_turn:
            if chip is None:
                moves = white
            else:
                moves = frozenset(node for node in neighbors[chip] if node in white)
            if not moves:
                return len(red)
            return max(play(red | frozenset([node]), blue, node, False) for node in moves)

        if not white:
            return len(red)
        return min(play(red, blue | frozenset([node]), chip, True) for node in white)

    return play(frozenset(), frozenset(), None, True)

