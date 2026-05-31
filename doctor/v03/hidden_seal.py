from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from doctor.v03.hidden_seal import recompute_manifest_hash, recompute_seal_hash


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "manifests" / "v03"
BENCHMARK_POOL = MANIFEST_DIR / "V03_BENCHMARK_POOL_MANIFEST.json"
SPLIT_MANIFEST = MANIFEST_DIR / "V03_SPLIT_MANIFEST.json"
HIDDEN_SEAL = MANIFEST_DIR / "V03_HIDDEN_SEAL_MANIFEST.json"
VALIDATION_RESULTS = MANIFEST_DIR / "V03_VALIDATION_RESULTS.json"
COMPARATOR_MANIFEST = MANIFEST_DIR / "V03_COMPARATOR_KSTACK_MANIFEST.json"

EXPECTED_COUNTS = {
    "dp_recurrence": 8,
    "graph_shortest_path": 8,
    "greedy_trap": 8,
    "state_space_search": 31,
    "combinatorics_counting": 8,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def test_hidden_seal_manifests_exist() -> None:
    assert BENCHMARK_POOL.is_file()
    assert SPLIT_MANIFEST.is_file()
    assert HIDDEN_SEAL.is_file()


def test_hidden_counts_are_exact() -> None:
    pool = _read_json(BENCHMARK_POOL)
    split = _read_json(SPLIT_MANIFEST)
    seal = _read_json(HIDDEN_SEAL)

    assert pool["total_hidden_cases"] == 63
    assert seal["total_hidden_cases"] == 63
    assert pool["hidden_family_counts"] == EXPECTED_COUNTS
    assert split["hidden_case_count"] == EXPECTED_COUNTS
    assert seal["per_family_counts"] == EXPECTED_COUNTS
    assert len(pool["entries"]) == 63
    assert len(split["entries"]) == 63


def test_hidden_entries_are_sealed_and_unopened() -> None:
    pool = _read_json(BENCHMARK_POOL)
    split = _read_json(SPLIT_MANIFEST)
    seal = _read_json(HIDDEN_SEAL)

    assert pool["hidden_opened"] is False
    assert split["hidden_opened"] is False
    assert seal["hidden_opened"] is False
    assert pool["hidden_validation_run"] is False
    assert split["hidden_validation_run"] is False
    assert seal["hidden_validation_run"] is False
    assert all(entry["split_id"] == "hidden" for entry in pool["entries"])
    assert all(entry["split_id"] == "hidden" for entry in split["entries"])


def test_no_validation_results_or_hidden_solver_result_fields_exist() -> None:
    assert not VALIDATION_RESULTS.exists()
    for manifest in (_read_json(BENCHMARK_POOL), _read_json(SPLIT_MANIFEST), _read_json(HIDDEN_SEAL)):
        for node in _walk_dicts(manifest):
            assert "solver_result" not in node
            assert "solver_results" not in node
            assert "observed_output" not in node
            assert "expected_output" not in node


def test_hidden_entries_have_hashes_without_readable_outputs() -> None:
    pool = _read_json(BENCHMARK_POOL)
    split = _read_json(SPLIT_MANIFEST)

    for entry in pool["entries"]:
        assert entry["input_hash"]
        assert entry["expected_output_hash"]
        assert "expected_output" not in entry
        assert "observed_output" not in entry
        assert entry["hidden_validation_run"] is False

    for entry in split["entries"]:
        assert entry["input_hash"]
        assert entry["expected_output_hash"]
        assert "expected_output" not in entry
        assert "observed_output" not in entry


def test_no_visible_hidden_input_hash_overlap() -> None:
    split = _read_json(SPLIT_MANIFEST)
    visible = {
        value
        for family_values in split["visible_input_hashes_by_family"].values()
        for value in family_values
    }
    hidden = set(split["input_hashes"])

    assert split["no_visible_hidden_input_hash_overlap"] is True
    assert visible.isdisjoint(hidden)
    assert len(hidden) == 63


def test_family_parameter_gates_are_preserved() -> None:
    pool = _read_json(BENCHMARK_POOL)
    state_q = [
        entry["parameter_metadata"]["q"]
        for entry in pool["entries"]
        if entry["family_id"] == "state_space_search"
    ]
    combo_entries = [
        entry
        for entry in pool["entries"]
        if entry["family_id"] == "combinatorics_counting"
    ]

    assert max(state_q) <= 6
    assert len(state_q) == 31
    assert all(entry["parameter_metadata"]["candidate_count"] <= 6 for entry in combo_entries)
    assert all(0 <= entry["parameter_metadata"]["target"] <= 50 for entry in combo_entries)


def test_comparator_ids_match_locked_kstack_manifest() -> None:
    pool = _read_json(BENCHMARK_POOL)
    comparator_manifest = _read_json(COMPARATOR_MANIFEST)
    locked = {
        entry["family_id"]: entry["comparator_id"]
        for entry in comparator_manifest["comparators"]
    }

    for entry in pool["entries"]:
        assert entry["comparator_id"] == locked[entry["family_id"]]


def test_manifest_hashes_are_stable_under_reload() -> None:
    pool = _read_json(BENCHMARK_POOL)
    split = _read_json(SPLIT_MANIFEST)
    seal = _read_json(HIDDEN_SEAL)

    assert recompute_manifest_hash(pool) == pool["manifest_hash"]
    assert recompute_manifest_hash(split) == split["manifest_hash"]
    assert recompute_seal_hash(seal) == seal["seal_hash"]

