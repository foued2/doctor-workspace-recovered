"""Tests for the Week 5 real LC322 benchmark.

Validates:
- Manifest schema compliance
- 30 solver files present and SHA-matching
- Pre-run check log present and all-pass
- Freeze file correct
- Result JSON has verdict, 7 estimator rows, 30 solver files
- No `partial: true` flag (full 30/30 catalog)
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(r"C:\Users\pakla\PycharmProjects\doctor-workspace-recovered")

REAL_FREEZE = ROOT / "MIDWEATHER_FINGERPRINT_GATE_LC322_REAL_FREEZE.json"
REAL_MANIFEST = ROOT / "data" / "midweather_fingerprint_lc322_real_claude_sonnet_4_seval_manifest.json"
REAL_RESULT = ROOT / "data" / "midweather_fingerprint_lc322_real_claude_sonnet_4.json"
PRE_RUN_LOG = ROOT / "data" / "lc322_real_pre_run_check.json"
SCHEMA = ROOT / "MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json"
SOLVERS_DIR = ROOT / "experiments" / "frozen_taxonomy_lc322_real_claude_sonnet_4" / "solvers"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_manifest_exists():
    assert REAL_MANIFEST.exists(), f"Missing: {REAL_MANIFEST}"


def test_real_manifest_schema_valid():
    manifest = _load(REAL_MANIFEST)
    schema = _load(SCHEMA)
    jsonschema.validate(manifest, schema)


def test_real_manifest_has_30_solvers():
    manifest = _load(REAL_MANIFEST)
    assert len(manifest["solver_files"]) == 30, \
        f"Expected 30 solver files, got {len(manifest['solver_files'])}"


def test_real_manifest_pack_source():
    manifest = _load(REAL_MANIFEST)
    assert manifest["pack_source"] == "hand_curated_real", \
        f"pack_source should be hand_curated_real, got {manifest['pack_source']}"


def test_real_manifest_no_model_id():
    manifest = _load(REAL_MANIFEST)
    assert "model_id" not in manifest, "Real hand-curated manifest should not have model_id"
    assert "prompt_versions" not in manifest, "Real hand-curated manifest should not have prompt_versions"


def test_real_manifest_freeze_linkage():
    manifest = _load(REAL_MANIFEST)
    assert manifest["protocol_freeze_id"] == "midweather_fingerprint_lc322_real_clean_001", \
        f"protocol_freeze_id mismatch: {manifest['protocol_freeze_id']}"


def test_all_30_solver_files_present():
    for i in range(1, 31):
        sf = SOLVERS_DIR / f"solver_{i:03d}.py"
        assert sf.exists(), f"Missing solver file: {sf}"


def test_manifest_sha_matches_files():
    manifest = _load(REAL_MANIFEST)
    for entry in manifest["solver_files"]:
        path = ROOT / entry["path"]
        assert path.exists(), f"Solver file missing: {path}"
        actual = path.read_bytes()
        import hashlib
        actual_sha = hashlib.sha256(actual).hexdigest()
        assert actual_sha == entry["sha256"], \
            f"SHA mismatch for {entry['path']}: manifest={entry['sha256']}, actual={actual_sha}"


def test_pre_run_check_log_exists():
    assert PRE_RUN_LOG.exists(), f"Missing pre-run check log: {PRE_RUN_LOG}"


def test_pre_run_check_all_pass():
    log = _load(PRE_RUN_LOG)
    assert log["n_solvers"] == 30, f"Expected 30 solvers checked, got {log['n_solvers']}"
    assert log["n_pass"] == 30, f"Expected 30 passes, got {log['n_pass']}"
    assert log["n_fail"] == 0, f"Expected 0 failures, got {log['n_fail']}"


def test_real_freeze_exists():
    assert REAL_FREEZE.exists(), f"Missing: {REAL_FREEZE}"


def test_real_freeze_id():
    freeze = _load(REAL_FREEZE)
    assert freeze["freeze_id"] == "midweather_fingerprint_lc322_real_clean_001", \
        f"freeze_id mismatch: {freeze['freeze_id']}"


def test_real_freeze_cites_stub_freeze():
    freeze = _load(REAL_FREEZE)
    sources = freeze.get("_provenance", {}).get("sources", {})
    stub_cited = any("MIDWEATHER_FINGERPRINT_GATE_FREEZE.json" in k for k in sources.keys())
    assert stub_cited, "Real freeze should cite stub freeze in _provenance.sources"


def test_real_freeze_no_stub_freeze_in_frozen_files():
    """The stub freeze path must NOT be in frozen_files (validator looks for that path)."""
    freeze = _load(REAL_FREEZE)
    for ff in freeze["frozen_files"]:
        assert ff["path"] != "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json", \
            "Stub freeze path should not be in real freeze frozen_files (causes SHA mismatch)"


def test_real_freeze_has_30_solver_entries():
    freeze = _load(REAL_FREEZE)
    solver_paths = [ff for ff in freeze["frozen_files"] if "solver_" in ff["path"] and ".py" in ff["path"]]
    assert len(solver_paths) == 30, f"Expected 30 solver entries in freeze, got {len(solver_paths)}"


def test_real_result_exists():
    assert REAL_RESULT.exists(), f"Missing: {REAL_RESULT}"


def test_real_result_has_verdict():
    result = _load(REAL_RESULT)
    assert "decision" in result, "Result must have decision"
    assert result["decision"] in ("PASS", "FAIL"), f"Invalid decision: {result['decision']}"


def test_real_result_no_partial():
    result = _load(REAL_RESULT)
    assert "partial" not in result or result.get("partial") is not True, \
        "Real benchmark should not be partial (all 30 solvers passed pre-run)"


def test_real_result_split_reasonable():
    result = _load(REAL_RESULT)
    summary = result["ground_truth_summary"]
    n_good = summary["n_good_solvers"]
    n_bad = summary["n_bad_solvers"]
    assert n_good + n_bad == 30, f"Expected 30 total, got {n_good + n_bad}"
    assert n_good >= 8, f"Expected >= 8 good solvers (10 explicit correct), got {n_good}"
    assert n_bad >= 10, f"Expected >= 10 bad solvers, got {n_bad}"


def test_real_result_estimator_table_has_8_rows():
    result = _load(REAL_RESULT)
    table = result["estimator_table"]
    assert len(table) == 8, f"Expected 8 estimator rows (B0-B6 + C_structured_fingerprint), got {len(table)}"


def test_real_result_summarizes_30_solvers():
    result = _load(REAL_RESULT)
    assert result["n_solvers"] == 30, f"Expected n_solvers=30, got {result['n_solvers']}"
