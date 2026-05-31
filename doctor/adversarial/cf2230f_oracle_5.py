"""Hash-only v0.3 hidden-set sealing helper.

This module generates the approved v0.3 hidden set and writes sealed manifests.
It computes hidden expected-output hashes through committed source oracles only.
It does not run hidden validation, does not run candidate solvers, and does not
write readable expected outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import subprocess
from typing import Any, Callable

from doctor.adversarial.cf2230f_oracle import cf2230f_scores_small
from doctor.adversarial.lc322_ground_truth import lc322_brute_force
from doctor.adversarial.lc3928_oracle import lc3928_exact_small
from doctor.adversarial.lc39_ground_truth import lc39_brute_force
from doctor.v03.families import (
    combinatorics_counting,
    dp_recurrence,
    graph_shortest_path,
    greedy_trap,
    state_space_search,
)
from doctor.v03.hash_utils import hash_file, hash_json_object, hash_text


PROTOCOL_VERSION = "v0.3-hidden-seal-1"
SCHEMA_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "manifests" / "v03"
VISIBLE_FAMILY_MANIFEST_PATH = MANIFEST_DIR / "V03_VISIBLE_FAMILY_MANIFEST.json"
COMPARATOR_KSTACK_MANIFEST_PATH = MANIFEST_DIR / "V03_COMPARATOR_KSTACK_MANIFEST.json"
BENCHMARK_POOL_MANIFEST_PATH = MANIFEST_DIR / "V03_BENCHMARK_POOL_MANIFEST.json"
SPLIT_MANIFEST_PATH = MANIFEST_DIR / "V03_SPLIT_MANIFEST.json"
HIDDEN_SEAL_MANIFEST_PATH = MANIFEST_DIR / "V03_HIDDEN_SEAL_MANIFEST.json"


@dataclass(frozen=True)
class HiddenFamilyConfig:
    family_id: str
    problem_id: str
    expected_count: int
    source_basis: str
    generator_id: str
    generator_hash: str
    oracle_id: str
    oracle_hash: str
    comparator_id: str
    parameter_envelope_hash: str


@dataclass(frozen=True)
class HiddenCase:
    family_id: str
    problem_id: str
    case_id: str
    input_payload: dict[str, Any]
    parameter_metadata: dict[str, Any]
    config: HiddenFamilyConfig


def write_hidden_seal_manifests(output_dir: Path = MANIFEST_DIR) -> dict[str, str]:
    repo_commit = _repo_commit()
    hidden_cases = generate_hidden_cases()
    visible_input_hashes = _visible_input_hashes_by_family()
    hidden_input_hashes = {hash_json_object(case.input_payload) for case in hidden_cases}
    visible_flat = {value for values in visible_input_hashes.values() for value in values}
    overlap = sorted(visible_flat.intersection(hidden_input_hashes))
    if overlap:
        raise RuntimeError("visible/hidden input_hash overlap detected")

    benchmark_pool = _build_benchmark_pool_manifest(repo_commit, hidden_cases)
    benchmark_pool_hash = _manifest_hash(benchmark_pool)
    benchmark_pool["manifest_hash"] = benchmark_pool_hash

    split_manifest = _build_split_manifest(
        repo_commit=repo_commit,
        hidden_cases=hidden_cases,
        visible_input_hashes=visible_input_hashes,
        benchmark_pool_manifest_hash=benchmark_pool_hash,
    )
    split_manifest_hash = _manifest_hash(split_manifest)
    split_manifest["manifest_hash"] = split_manifest_hash

    visible_family_manifest_hash = hash_file(VISIBLE_FAMILY_MANIFEST_PATH)
    comparator_kstack_manifest_hash = hash_file(COMPARATOR_KSTACK_MANIFEST_PATH)
    hidden_seal = _build_hidden_seal_manifest(
        repo_commit=repo_commit,
        hidden_cases=hidden_cases,
        benchmark_pool_manifest_hash=benchmark_pool_hash,
        split_manifest_hash=split_manifest_hash,
        visible_family_manifest_hash=visible_family_manifest_hash,
        comparator_kstack_manifest_hash=comparator_kstack_manifest_hash,
    )
    hidden_seal_hash = _manifest_hash(hidden_seal)
    hidden_seal["seal_hash"] = hidden_seal_hash

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / BENCHMARK_POOL_MANIFEST_PATH.name, benchmark_pool)
    _write_json(output_dir / SPLIT_MANIFEST_PATH.name, split_manifest)
    _write_json(output_dir / HIDDEN_SEAL_MANIFEST_PATH.name, hidden_seal)
    return {
        "benchmark_pool_manifest_hash": benchmark_pool_hash,
        "split_manifest_hash": split_manifest_hash,
        "visible_family_manifest_hash": visible_family_manifest_hash,
        "comparator_kstack_manifest_hash": comparator_kstack_manifest_hash,
        "seal_hash": hidden_seal_hash,
    }


def generate_hidden_cases() -> list[HiddenCase]:
    cases: list[HiddenCase] = []
    cases.extend(_dp_hidden_cases())
    cases.extend(_graph_hidden_cases())
    cases.extend(_greedy_hidden_cases())
    cases.extend(_state_hidden_cases())
    cases.extend(_combo_hidden_cases())
    _assert_expected_counts(cases)
    return cases


def recompute_seal_hash(seal_manifest: dict[str, Any]) -> str:
    return _manifest_hash(seal_manifest)


def recompute_manifest_hash(manifest: dict[str, Any]) -> str:
    return _manifest_hash(manifest)


def _build_benchmark_pool_manifest(
    repo_commit: str,
    hidden_cases: list[HiddenCase],
) -> dict[str, Any]:
    entries = [_benchmark_entry(case) for case in hidden_cases]
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "repo_commit": repo_commit,
        "manifest_kind": "benchmark_pool",
        "sealed": True,
        "hidden_opened": False,
        "visible_family_source": _visible_family_source_summary(),
        "hidden_family_counts": _counts_by_family(hidden_cases),
        "total_hidden_cases": len(hidden_cases),
        "hidden_set_generated": True,
        "hidden_validation_run": False,
        "contains_hidden_content": True,
        "contains_expected_output_hashes": True,
        "contains_readable_expected_outputs": False,
        "no_solver_results_on_hidden": True,
        "entries": entries,
    }


def _build_split_manifest(
    *,
    repo_commit: str,
    hidden_cases: list[HiddenCase],
    visible_input_hashes: dict[str, list[str]],
    benchmark_pool_manifest_hash: str,
) -> dict[str, Any]:
    hidden_entries = [_split_entry(case) for case in hidden_cases]
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "repo_commit": repo_commit,
        "manifest_kind": "split",
        "sealed": True,
        "split_locked": True,
        "hidden_opened": False,
        "hidden_validation_run": False,
        "visible_case_count": {family: len(values) for family, values in visible_input_hashes.items()},
        "hidden_case_count": _counts_by_family(hidden_cases),
        "hidden_entries_by_family": _entries_by_family(hidden_entries),
        "visible_input_hashes_by_family": visible_input_hashes,
        "input_hashes": [entry["input_hash"] for entry in hidden_entries],
        "expected_output_hashes": [entry["expected_output_hash"] for entry in hidden_entries],
        "no_visible_hidden_input_hash_overlap": True,
        "benchmark_pool_manifest_hash": benchmark_pool_manifest_hash,
        "seal_manifest_hash": None,
        "entries": hidden_entries,
    }


def _build_hidden_seal_manifest(
    *,
    repo_commit: str,
    hidden_cases: list[HiddenCase],
    benchmark_pool_manifest_hash: str,
    split_manifest_hash: str,
    visible_family_manifest_hash: str,
    comparator_kstack_manifest_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "repo_commit": repo_commit,
        "manifest_kind": "hidden_seal",
        "hidden_set_generated": True,
        "hidden_opened": False,
        "hidden_validation_run": False,
        "total_hidden_cases": len(hidden_cases),
        "per_family_counts": _counts_by_family(hidden_cases),
        "benchmark_pool_manifest_hash": benchmark_pool_manifest_hash,
        "split_manifest_hash": split_manifest_hash,
        "visible_family_manifest_hash": visible_family_manifest_hash,
        "comparator_kstack_manifest_hash": comparator_kstack_manifest_hash,
        "forbidden_actions_confirmed": {
            "no_hidden_validation_run": True,
            "no_solver_results_on_hidden": True,
            "no_readable_expected_outputs": True,
            "no_claim_upgrade": True,
            "no_paper_update": True,
            "no_gap_map_update": True,
            "no_findings_update": True,
        },
    }


def _benchmark_entry(case: HiddenCase) -> dict[str, Any]:
    expected_hash = _expected_output_hash(case)
    input_hash = hash_json_object(case.input_payload)
    entry = {
        "problem_id": case.problem_id,
        "problem_definition_hash": hash_text(case.config.source_basis),
        "family_id": case.family_id,
        "case_id": case.case_id,
        "split_id": "hidden",
        "input_hash": input_hash,
        "expected_output_hash": expected_hash,
        "generator_id": case.config.generator_id,
        "generator_hash": case.config.generator_hash,
        "oracle_id": case.config.oracle_id,
        "oracle_hash": case.config.oracle_hash,
        "comparator_id": case.config.comparator_id,
        "comparator_hash": hash_text(case.config.comparator_id),
        "parameter_envelope_hash": case.config.parameter_envelope_hash,
        "deterministic_case_hash": hash_json_object(
            {
                "case_id": case.case_id,
                "input_hash": input_hash,
                "parameter_metadata": case.parameter_metadata,
            }
        ),
        "source_basis": case.config.source_basis,
        "hidden_validation_run": False,
        "perturbation_id": "identity_no_perturbation",
        "perturbation_class": "identity_baseline",
        "parameter_metadata": case.parameter_metadata,
    }
    return entry


def _split_entry(case: HiddenCase) -> dict[str, Any]:
    input_hash = hash_json_object(case.input_payload)
    expected_hash = _expected_output_hash(case)
    material = {
        "problem_id": f"{case.problem_id}:{case.case_id}",
        "family_id": case.family_id,
        "case_id": case.case_id,
        "split_id": "hidden",
        "input_hash": input_hash,
        "expected_output_hash": expected_hash,
    }
    return {
        **material,
        "entry_hash": hash_json_object(material),
        "parameter_metadata": case.parameter_metadata,
    }


def _expected_output_hash(case: HiddenCase) -> str:
    expected_by_family: dict[str, Callable[[dict[str, Any]], Any]] = {
        "dp_recurrence": lambda payload: lc322_brute_force(payload["coins"], payload["amount"]),
        "graph_shortest_path": lambda payload: lc3928_exact_small(
            payload["n"], payload["prices"], payload["roads"]
        ),
        "greedy_trap": lambda payload: lc3928_exact_small(
            payload["n"], payload["prices"], payload["roads"]
        ),
        "state_space_search": lambda payload: cf2230f_scores_small(
            payload["parents"], max_q=state_space_search.MAX_Q
        ),
        "combinatorics_counting": lambda payload: lc39_brute_force(
            payload["candidates"], payload["target"]
        ),
    }
    return hash_json_object(expected_by_family[case.family_id](case.input_payload))


def _dp_hidden_cases() -> list[HiddenCase]:
    config = HiddenFamilyConfig(
        family_id=dp_recurrence.FAMILY_ID,
        problem_id=dp_recurrence.PROBLEM_ID,
        expected_count=8,
        source_basis=dp_recurrence.SOURCE_BASIS,
        generator_id=dp_recurrence.GENERATOR_ID,
        generator_hash=dp_recurrence.GENERATOR_HASH,
        oracle_id=dp_recurrence.ORACLE_A_ID,
        oracle_hash=dp_recurrence.ORACLE_A_HASH,
        comparator_id=dp_recurrence.COMPARATOR_ID,
        parameter_envelope_hash=dp_recurrence.PARAMETER_ENVELOPE_HASH,
    )
    specs = (
        ([1, 4, 7], 18),
        ([2, 5, 9], 23),
        ([3, 6, 10], 29),
        ([4, 6], 14),
        ([5, 11, 13], 27),
        ([7, 10], 1),
        ([1, 8, 12, 15], 30),
        ([2, 3, 11], 17),
    )
    return [
        _make_hidden_case(
            config,
            index,
            {"coins": list(coins), "amount": amount},
            {"coin_count": len(coins), "amount": amount},
        )
        for index, (coins, amount) in enumerate(specs, start=1)
    ]


def _graph_hidden_cases() -> list[HiddenCase]:
    config = HiddenFamilyConfig(
        family_id=graph_shortest_path.FAMILY_ID,
        problem_id=graph_shortest_path.PROBLEM_ID,
        expected_count=8,
        source_basis=graph_shortest_path.SOURCE_BASIS,
        generator_id=graph_shortest_path.GENERATOR_ID,
        generator_hash=graph_shortest_path.GENERATOR_HASH,
        oracle_id=graph_shortest_path.ORACLE_A_ID,
        oracle_hash=graph_shortest_path.ORACLE_A_HASH,
        comparator_id=graph_shortest_path.COMPARATOR_ID,
        parameter_envelope_hash=graph_shortest_path.PARAMETER_ENVELOPE_HASH,
    )
    specs = (
        (4, [12, 6, 18, 3], [[0, 1, 2, 2], [1, 2, 1, 4], [2, 3, 3, 1], [0, 3, 8, 1]]),
        (5, [9, 13, 4, 17, 5], [[0, 1, 1, 3], [1, 2, 2, 2], [2, 3, 2, 5], [3, 4, 1, 1], [0, 4, 7, 2]]),
        (6, [15, 8, 22, 7, 30, 2], [[0, 1, 3, 1], [1, 2, 1, 6], [2, 3, 2, 2], [3, 4, 2, 2], [4, 5, 1, 3], [0, 5, 10, 1]]),
        (3, [20, 1, 15], [[0, 1, 4, 1], [1, 2, 2, 3], [0, 2, 3, 2]]),
        (7, [40, 35, 28, 3, 25, 18, 6], [[0, 1, 1, 4], [1, 2, 1, 4], [2, 3, 1, 4], [3, 4, 2, 1], [4, 5, 2, 1], [5, 6, 1, 2], [0, 6, 9, 1]]),
        (5, [11, 12, 13, 2, 14], [[0, 1, 2, 5], [1, 2, 2, 5], [2, 3, 2, 1], [3, 4, 1, 1], [0, 4, 6, 2]]),
        (8, [8, 21, 5, 34, 3, 13, 2, 55], [[0, 1, 1, 7], [1, 2, 2, 2], [2, 3, 1, 5], [3, 4, 3, 1], [4, 5, 1, 3], [5, 6, 2, 1], [6, 7, 1, 2], [0, 7, 11, 1]]),
        (4, [6, 50, 7, 1], [[0, 1, 1, 10], [1, 2, 1, 10], [2, 3, 1, 1], [0, 3, 5, 1]]),
    )
    return [
        _make_hidden_case(
            config,
            index,
            {"n": n, "prices": list(prices), "roads": [list(road) for road in roads]},
            {"n": n, "edge_count": len(roads)},
        )
        for index, (n, prices, roads) in enumerate(specs, start=1)
    ]


def _greedy_hidden_cases() -> list[HiddenCase]:
    config = HiddenFamilyConfig(
        family_id=greedy_trap.FAMILY_ID,
        problem_id=greedy_trap.PROBLEM_ID,
        expected_count=8,
        source_basis=greedy_trap.SOURCE_BASIS,
        generator_id=greedy_trap.GENERATOR_ID,
        generator_hash=greedy_trap.GENERATOR_HASH,
        oracle_id=greedy_trap.ORACLE_A_ID,
        oracle_hash=greedy_trap.ORACLE_A_HASH,
        comparator_id=greedy_trap.COMPARATOR_ID,
        parameter_envelope_hash=greedy_trap.PARAMETER_ENVELOPE_HASH,
    )
    specs = (
        ("hidden_tradeoff_tax_wall", 4, [90, 2, 80, 3], [[0, 1, 1, 80], [0, 2, 3, 1], [2, 3, 1, 1], [1, 3, 8, 1]]),
        ("hidden_tradeoff_price_vs_return", 5, [70, 60, 1, 65, 4], [[0, 1, 1, 3], [1, 2, 5, 1], [0, 3, 2, 1], [3, 4, 1, 1], [4, 2, 1, 1]]),
        ("hidden_tradeoff_nearest_bad", 6, [55, 1, 50, 45, 4, 40], [[0, 1, 1, 90], [0, 2, 2, 1], [2, 3, 1, 1], [3, 4, 1, 1], [4, 5, 1, 1]]),
        ("hidden_tradeoff_local_decoy", 4, [18, 1, 17, 2], [[0, 1, 1, 40], [0, 2, 3, 1], [2, 3, 1, 1], [1, 3, 4, 1]]),
        ("hidden_tradeoff_chain_decoy", 7, [100, 95, 90, 85, 1, 80, 4], [[0, 1, 1, 2], [1, 2, 1, 2], [2, 3, 1, 2], [3, 4, 1, 2], [0, 5, 3, 1], [5, 6, 1, 1], [6, 4, 1, 1]]),
        ("hidden_tradeoff_return_penalty", 5, [30, 2, 29, 28, 3], [[0, 1, 1, 70], [0, 2, 2, 1], [2, 3, 1, 1], [3, 4, 1, 1], [1, 4, 5, 1]]),
        ("hidden_tradeoff_low_price_far", 6, [44, 40, 36, 32, 28, 1], [[0, 1, 1, 1], [1, 2, 1, 1], [2, 3, 1, 1], [3, 4, 1, 1], [4, 5, 1, 1]]),
        ("hidden_tradeoff_cross_route", 5, [25, 24, 2, 23, 3], [[0, 1, 1, 20], [1, 2, 1, 20], [0, 3, 2, 1], [3, 4, 1, 1], [4, 2, 1, 1]]),
    )
    return [
        _make_hidden_case(
            config,
            index,
            {
                "source_case_id": label,
                "suite": "adversarial_tradeoff",
                "trap_type": label,
                "n": n,
                "prices": list(prices),
                "roads": [list(road) for road in roads],
            },
            {"n": n, "edge_count": len(roads), "trap_type_hash": hash_text(label)},
        )
        for index, (label, n, prices, roads) in enumerate(specs, start=1)
    ]


def _state_hidden_cases() -> list[HiddenCase]:
    config = HiddenFamilyConfig(
        family_id=state_space_search.FAMILY_ID,
        problem_id=state_space_search.PROBLEM_ID,
        expected_count=31,
        source_basis=state_space_search.SOURCE_BASIS,
        generator_id=state_space_search.GENERATOR_ID,
        generator_hash=state_space_search.GENERATOR_HASH,
        oracle_id=state_space_search.ORACLE_A_ID,
        oracle_hash=state_space_search.ORACLE_A_HASH,
        comparator_id=state_space_search.COMPARATOR_ID,
        parameter_envelope_hash=state_space_search.PARAMETER_ENVELOPE_HASH,
    )
    parent_specs: list[list[int]] = [
        [1],
        [1, 2],
        [1, 1],
        [1, 2, 3],
        [1, 1, 2],
        [1, 2, 2],
        [1, 1, 1],
        [1, 2, 3, 4],
        [1, 1, 2, 2],
        [1, 2, 1, 4],
        [1, 1, 1, 1],
    ]
    rng = random.Random(2230_300_19)
    seen = {tuple(parents) for parents in parent_specs}
    while len(parent_specs) < config.expected_count:
        q = rng.randint(1, state_space_search.MAX_Q)
        parents = [rng.randint(1, i) for i in range(1, q + 1)]
        key = tuple(parents)
        if key in seen:
            continue
        seen.add(key)
        parent_specs.append(parents)
    return [
        _make_hidden_case(
            config,
            index,
            {"parents": list(parents), "q": len(parents)},
            {"q": len(parents)},
        )
        for index, parents in enumerate(parent_specs, start=1)
    ]


def _combo_hidden_cases() -> list[HiddenCase]:
    config = HiddenFamilyConfig(
        family_id=combinatorics_counting.FAMILY_ID,
        problem_id=combinatorics_counting.PROBLEM_ID,
        expected_count=8,
        source_basis=combinatorics_counting.SOURCE_BASIS,
        generator_id=combinatorics_counting.GENERATOR_ID,
        generator_hash=combinatorics_counting.GENERATOR_HASH,
        oracle_id=combinatorics_counting.ORACLE_A_ID,
        oracle_hash=combinatorics_counting.ORACLE_A_HASH,
        comparator_id=combinatorics_counting.COMPARATOR_ID,
        parameter_envelope_hash=combinatorics_counting.PARAMETER_ENVELOPE_HASH,
    )
    specs = (
        ([2, 4, 7], 14),
        ([3, 4, 6, 8], 12),
        ([5, 9, 10], 20),
        ([1, 5, 6], 7),
        ([4, 6, 9], 5),
        ([2, 5, 10, 13], 15),
        ([3, 7, 11, 14], 21),
        ([6], 0),
    )
    return [
        _make_hidden_case(
            config,
            index,
            {"candidates": list(candidates), "target": target},
            {"candidate_count": len(candidates), "target": target},
        )
        for index, (candidates, target) in enumerate(specs, start=1)
    ]


def _make_hidden_case(
    config: HiddenFamilyConfig,
    index: int,
    payload_fields: dict[str, Any],
    parameter_metadata: dict[str, Any],
) -> HiddenCase:
    case_id = f"v03_{config.family_id}_hidden_{index:03d}"
    payload = {
        "problem_id": config.problem_id,
        "split_id": "hidden",
        "case_id": case_id,
        "seed_id": f"sealed-hidden-{config.family_id}-{index:03d}",
        **payload_fields,
    }
    return HiddenCase(
        family_id=config.family_id,
        problem_id=config.problem_id,
        case_id=case_id,
        input_payload=payload,
        parameter_metadata=parameter_metadata,
        config=config,
    )


def _visible_input_hashes_by_family() -> dict[str, list[str]]:
    visible_modules = (
        dp_recurrence,
        graph_shortest_path,
        greedy_trap,
        state_space_search,
        combinatorics_counting,
    )
    result: dict[str, list[str]] = {}
    for module in visible_modules:
        generator_class = _visible_generator_class(module)
        generator = generator_class()
        result[module.FAMILY_ID] = [
            hash_json_object(case.input_payload)
            for case in generator.generate_visible_cases()
        ]
    return result


def _visible_generator_class(module):
    for value in vars(module).values():
        if isinstance(value, type) and value.__name__.endswith("VisibleGenerator"):
            return value
    raise RuntimeError(f"visible generator class not found for {module.__name__}")


def _visible_family_source_summary() -> list[dict[str, Any]]:
    manifest = json.loads(VISIBLE_FAMILY_MANIFEST_PATH.read_text(encoding="utf-8"))
    return [
        {
            "family_id": family["family_id"],
            "visible_module": family["visible_module"],
            "visible_test_file": family["visible_test_file"],
            "comparator_id": family["comparator_id"],
            "case_count": family["case_count"],
        }
        for family in manifest["families"]
    ]


def _entries_by_family(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        grouped.setdefault(entry["family_id"], []).append(
            {
                "case_id": entry["case_id"],
                "input_hash": entry["input_hash"],
                "expected_output_hash": entry["expected_output_hash"],
                "parameter_metadata": entry["parameter_metadata"],
            }
        )
    return grouped


def _counts_by_family(hidden_cases: list[HiddenCase]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in hidden_cases:
        counts[case.family_id] = counts.get(case.family_id, 0) + 1
    return counts


def _assert_expected_counts(hidden_cases: list[HiddenCase]) -> None:
    counts = _counts_by_family(hidden_cases)
    expected = {
        dp_recurrence.FAMILY_ID: 8,
        graph_shortest_path.FAMILY_ID: 8,
        greedy_trap.FAMILY_ID: 8,
        state_space_search.FAMILY_ID: 31,
        combinatorics_counting.FAMILY_ID: 8,
    }
    if counts != expected:
        raise RuntimeError(f"hidden family counts mismatch: {counts!r}")
    if len(hidden_cases) != 63:
        raise RuntimeError(f"hidden case count mismatch: {len(hidden_cases)}")
    if max(case.parameter_metadata.get("q", 0) for case in hidden_cases) > state_space_search.MAX_Q:
        raise RuntimeError("state_space_search q limit exceeded")
    for case in hidden_cases:
        if case.family_id == combinatorics_counting.FAMILY_ID:
            if case.parameter_metadata["candidate_count"] > combinatorics_counting.MAX_CANDIDATES:
                raise RuntimeError("combinatorics_counting candidate cap exceeded")
            target = case.parameter_metadata["target"]
            if target < combinatorics_counting.TARGET_MIN or target > combinatorics_counting.TARGET_MAX:
                raise RuntimeError("combinatorics_counting target cap exceeded")


def _manifest_hash(manifest: dict[str, Any]) -> str:
    material = dict(manifest)
    material.pop("manifest_hash", None)
    material.pop("seal_hash", None)
    return hash_json_object(material)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _repo_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    write_hidden_seal_manifests()
