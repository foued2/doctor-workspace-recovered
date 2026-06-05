"""Tests for Week 6: C estimator wired into LC45.

Validates:
  - C_structured_fingerprint is in LC45_ESTIMATOR_NAMES
  - C_structured_fingerprint has a policy in LC45_ESTIMATOR_POLICIES
  - C row is present in the LC45 result JSON
  - C row has loss >= 0 and is not degenerate
  - The C guard status is "passed" (not "n/a")
  - LC322 behavior is unchanged (zero regression)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from doctor.adversarial.problem_class_config import (
    LC322_ESTIMATOR_NAMES,
    LC45_ESTIMATOR_NAMES,
    LC45_ESTIMATOR_POLICIES,
    get_problem_class_config,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LC45_RESULT = REPO_ROOT / "data" / "midweather_fingerprint_lc45.json"


def _load_result() -> dict:
    return json.loads(LC45_RESULT.read_text(encoding="utf-8"))


def test_lc45_estimator_names_includes_c():
    assert "C_structured_fingerprint" in LC45_ESTIMATOR_NAMES
    assert len(LC45_ESTIMATOR_NAMES) == 8


def test_lc45_estimator_names_match_lc322_count():
    assert len(LC45_ESTIMATOR_NAMES) == len(LC322_ESTIMATOR_NAMES) == 8


def test_lc45_estimator_policies_has_c():
    assert "C_structured_fingerprint" in LC45_ESTIMATOR_POLICIES
    policy = LC45_ESTIMATOR_POLICIES["C_structured_fingerprint"]
    assert callable(policy)


def test_lc45_c_policy_is_fail_count():
    policy = LC45_ESTIMATOR_POLICIES["C_structured_fingerprint"]
    assert policy(0, 15) == "ACCEPT"
    assert policy(1, 15) == "REJECT"
    assert policy(15, 15) == "REJECT"


def test_lc45_config_includes_c():
    cfg = get_problem_class_config("lc45")
    assert "C_structured_fingerprint" in cfg.estimator_names
    assert "C_structured_fingerprint" in cfg.estimator_policies


def test_lc45_result_has_c_row():
    result = _load_result()
    table = result["estimator_table"]
    c_rows = [r for r in table if r["estimator"] == "C_structured_fingerprint"]
    assert len(c_rows) == 1, f"Expected exactly 1 C row, got {len(c_rows)}"
    c_row = c_rows[0]
    assert c_row["decision_loss"] >= 0
    assert not c_row["degenerate_all_accept"]
    assert not c_row["degenerate_all_reject"]


def test_lc45_result_estimator_count_is_8():
    result = _load_result()
    assert len(result["estimator_table"]) == 8


def test_lc45_c_guard_status_passed():
    result = _load_result()
    c_guard = [g for g in result["guard_statuses"] if "C policy" in g["guard"]]
    assert len(c_guard) == 1
    assert c_guard[0]["status"] == "passed", (
        f"Expected C guard to be 'passed' (C is now active), "
        f"got {c_guard[0]['status']!r}: {c_guard[0]['evidence']}"
    )


def test_lc45_verdict_still_fail_via_b4():
    result = _load_result()
    assert result["decision"] == "FAIL"
    assert "B4_raw_full_tensor" in result["decision_reason"]


def test_lc45_c_does_not_beat_b1():
    result = _load_result()
    table = result["estimator_table"]
    b1_loss = next(r["decision_loss"] for r in table if r["estimator"] == "B1_count")
    c_loss = next(r["decision_loss"] for r in table if r["estimator"] == "C_structured_fingerprint")
    assert c_loss >= b1_loss, (
        f"C ({c_loss}) beat B1 ({b1_loss}) — this is a significant finding that "
        f"should be flagged in the handoff"
    )


def test_lc322_estimator_names_unchanged():
    assert LC322_ESTIMATOR_NAMES == [
        "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
        "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
        "B6_regularized_raw_tensor", "C_structured_fingerprint",
    ]


def test_lc322_config_unchanged():
    cfg = get_problem_class_config("lc322")
    assert len(cfg.estimator_names) == 8
    assert "C_structured_fingerprint" in cfg.estimator_names
