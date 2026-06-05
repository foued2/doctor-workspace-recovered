"""Tests for the doctor-certify CLI surface.

Each test invokes the CLI's main() with a controlled argv and asserts the
declared exit code (0=PASS, 1=FAIL, 2=REFUSED, 3=ERROR). Fixtures use the
real LC322 + LC45 freezes/manifests for positive cases and tmp_path-based
minimal artifacts for the negative cases.

The test suite runs the protocol against the real solvers and freeze; the
``run`` tests use ``--output`` to write the result JSON into tmp_path so the
canonical ``data/midweather_fingerprint_*.json`` files are not modified.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from doctor.adversarial.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent
LC322_FREEZE = REPO_ROOT / "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"
LC45_FREEZE = REPO_ROOT / "MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json"
LC322_MANIFEST = REPO_ROOT / "data" / "midweather_fingerprint_lc322_seval_manifest.json"


def test_cli_list_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["list"]) == 0
    captured = capsys.readouterr()
    assert "lc322" in captured.out
    assert "lc45" in captured.out


def test_cli_validate_freeze_lc322_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["validate-freeze", "--freeze", str(LC322_FREEZE)]) == 0
    captured = capsys.readouterr()
    assert "PASS: all 7 freeze validators passed" in captured.out


def test_cli_validate_freeze_lc45_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["validate-freeze", "--freeze", str(LC45_FREEZE)]) == 0
    captured = capsys.readouterr()
    assert "PASS: all 7 freeze validators passed" in captured.out


def test_cli_validate_freeze_invalid_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    invalid = tmp_path / "invalid_freeze.json"
    invalid.write_text(json.dumps({
        "freeze_id": "midweather_fingerprint_lc322_clean_001",
        "protocol_commit": "abc",
        "frozen_files": [],
    }))
    assert main(["validate-freeze", "--freeze", str(invalid)]) == 2
    captured = capsys.readouterr()
    assert "REFUSED: freeze_validation:" in captured.err
    assert "OBSERVATION_BUDGET_MISSING" in captured.err


def test_cli_validate_manifest_lc322_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([
        "validate-manifest",
        "--seval-manifest", str(LC322_MANIFEST),
        "--freeze", str(LC322_FREEZE),
    ]) == 0
    captured = capsys.readouterr()
    assert "PASS: manifest is valid" in captured.out


def test_cli_validate_manifest_freeze_mismatch_exits_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([
        "validate-manifest",
        "--seval-manifest", str(LC322_MANIFEST),
        "--freeze", str(LC45_FREEZE),
    ]) == 2
    captured = capsys.readouterr()
    assert "REFUSED: manifest_certification:" in captured.err
    assert "SEVAL_FREEZE_ID_MISMATCH" in captured.err


def test_cli_run_lc322_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "lc322_result.json"
    assert main(["run", "--problem-class=lc322", "--output", str(output)]) == 1
    captured = capsys.readouterr()
    assert "Decision: FAIL" in captured.out
    assert "degenerate: all-reject in B4_raw_full_tensor" in captured.out
    assert output.exists()
    result = json.loads(output.read_text())
    assert result["decision"] == "FAIL"
    assert result["problem_class"] == "lc322"


def test_cli_run_lc45_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "lc45_result.json"
    assert main(["run", "--problem-class=lc45", "--output", str(output)]) == 1
    captured = capsys.readouterr()
    assert "Decision: FAIL" in captured.out
    assert "degenerate: all-reject in B4_raw_full_tensor" in captured.out
    assert output.exists()
    result = json.loads(output.read_text())
    assert result["decision"] == "FAIL"
    assert result["problem_class"] == "lc45"
    estimator_names = [row["estimator"] for row in result["estimator_table"]]
    assert "C_structured_fingerprint" in estimator_names
    assert len(estimator_names) == 8


def test_cli_freeze_id_mismatch_exits_three(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([
        "run", "--problem-class=lc322", "--freeze", str(LC45_FREEZE),
    ]) == 3
    captured = capsys.readouterr()
    assert "ERROR: freeze_id_mismatch" in captured.err
    assert "lc45" in captured.err
    assert "lc322" in captured.err


def test_cli_run_nonexistent_freeze_exits_three(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([
        "run", "--problem-class=lc322",
        "--freeze", str(tmp_path / "no_such_freeze.json"),
    ]) == 3
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err
    assert "no_such_freeze.json" in captured.err


def test_cli_validate_freeze_nonexistent_exits_three(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([
        "validate-freeze", "--freeze", str(tmp_path / "no_such_freeze.json"),
    ]) == 3
    captured = capsys.readouterr()
    assert "ERROR: freeze_not_found" in captured.err
