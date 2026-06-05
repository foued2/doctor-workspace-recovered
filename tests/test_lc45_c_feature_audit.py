"""Tests for the LC45 C feature audit (Week 7 research artifact).

Validates:
  - Audit file exists and has the expected schema
  - 10 solver rows, each with 6 features
  - Survivor (solver_001) has pass_fail_rate = 1.0
  - Separation analysis covers all 6 features
  - clean_separation_count matches the actual number of features with clean separation
  - Conclusion string is present and non-empty

These tests guard the research artifact. They do NOT assert that C can or
cannot differentiate from B1 — that finding is in docs/LC45_C_POLICY_FINDING.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = REPO_ROOT / "data" / "lc45_c_feature_audit.json"
FINDING_PATH = REPO_ROOT / "docs" / "LC45_C_POLICY_FINDING.md"


def _load_audit() -> dict:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def test_audit_file_exists():
    assert AUDIT_PATH.exists(), f"Missing {AUDIT_PATH}"


def test_audit_schema():
    a = _load_audit()
    assert a["n_solvers"] == 10
    assert a["n_probes"] == 30
    assert a["survivor_id"] == "solver_001"
    assert len(a["feature_names"]) == 6
    assert len(a["feature_table"]) == 10
    assert len(a["separation_analysis"]) == 6
    assert "conclusion" in a
    assert isinstance(a["clean_separation_count"], int)


def test_audit_survivor_passes_all_probes():
    a = _load_audit()
    survivor = next(r for r in a["feature_table"] if r["solver_id"] == "solver_001")
    assert survivor["pass_count"] == 30
    assert survivor["features"]["pass_fail_rate"] == 1.0


def test_audit_all_solvers_have_6_features():
    a = _load_audit()
    expected_features = {
        "pass_fail_rate", "bfs_agrees_rate", "off_by_one_rate",
        "panics_on_dead_end_rate", "dead_end_present_rate", "is_uniform_array_rate",
    }
    for row in a["feature_table"]:
        assert set(row["features"].keys()) == expected_features
        for val in row["features"].values():
            assert 0.0 <= val <= 1.0


def test_audit_separation_covers_all_features():
    a = _load_audit()
    feature_names_in_analysis = {s["feature"] for s in a["separation_analysis"]}
    assert feature_names_in_analysis == set(a["feature_names"])


def test_audit_separation_fields():
    a = _load_audit()
    for s in a["separation_analysis"]:
        assert "survivor_value" in s
        assert "buggy_min" in s
        assert "buggy_max" in s
        assert "buggy_mean" in s
        assert "direction" in s
        assert "gap" in s
        assert "clean_separation" in s
        assert s["direction"] in ("survivor_above", "survivor_below", "overlap")


def test_audit_clean_separation_count_matches_analysis():
    a = _load_audit()
    actual_clean = sum(1 for s in a["separation_analysis"] if s["clean_separation"])
    assert a["clean_separation_count"] == actual_clean


def test_audit_bfs_agrees_is_zero_for_all_solvers():
    """After Week 8 encoder fix: bfs_agrees_rate compares against BFS reachable_count,
    which is a different quantity from min-jump count. No solver outputs the reachable
    count, so bfs_agrees_rate is 0.0 for all solvers. This is informationally distinct
    from pass_fail_rate (which varies across solvers)."""
    a = _load_audit()
    for row in a["feature_table"]:
        assert row["features"]["bfs_agrees_rate"] == 0.0, (
            f"bfs_agrees_rate should be 0.0 for all solvers after encoder fix, "
            f"got {row['features']['bfs_agrees_rate']} for {row['solver_id']}"
        )


def test_audit_bfs_agrees_distinct_from_pass_fail():
    """After Week 8 fix: bfs_agrees_rate is informationally distinct from pass_fail_rate.
    For the survivor, pass_fail_rate=1.0 but bfs_agrees_rate=0.0. For at least one
    solver, the two values must differ. Catches the encoder artifact regressing
    (bfs_agrees should NOT equal pass_fail for the survivor)."""
    a = _load_audit()
    survivor = next(r for r in a["feature_table"] if r["solver_id"] == "solver_001")
    assert survivor["features"]["bfs_agrees_rate"] != survivor["features"]["pass_fail_rate"], (
        f"bfs_agrees_rate regressed to pass_fail_rate for survivor: "
        f"both = {survivor['features']['pass_fail_rate']}"
    )


def test_audit_constant_probe_features():
    """dead_end_present_rate and is_uniform_array_rate are probe properties, constant across solvers."""
    a = _load_audit()
    dead_end_values = {row["features"]["dead_end_present_rate"] for row in a["feature_table"]}
    uniform_values = {row["features"]["is_uniform_array_rate"] for row in a["feature_table"]}
    assert len(dead_end_values) == 1, f"dead_end_present_rate varies: {dead_end_values}"
    assert len(uniform_values) == 1, f"is_uniform_array_rate varies: {uniform_values}"


def test_audit_conclusion_is_non_empty():
    a = _load_audit()
    assert a["conclusion"]
    assert "C" in a["conclusion"]


def test_finding_document_exists():
    assert FINDING_PATH.exists(), f"Missing {FINDING_PATH}"


def test_finding_document_contains_key_findings():
    text = FINDING_PATH.read_text(encoding="utf-8")
    assert "pass_fail_rate" in text
    assert "bfs_agrees_rate" in text
    assert "negative result" in text.lower() or "no separation" in text.lower()
    assert "B1" in text


def test_paper_has_reproducibility_gap_section():
    """Simple file-presence + string check on the paper's Reproducibility Gap section.
    Not content validation — guards against the section being accidentally deleted."""
    paper = REPO_ROOT / "doctor_bimaristan_scientific_paper.md"
    assert paper.exists(), f"Missing {paper}"
    text = paper.read_text(encoding="utf-8")
    assert "Reproducibility Gap" in text
    assert "27/3" in text
    assert "PhotoRec" in text
    assert "c3db242" in text
