from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import pytest

from doctor.adversarial.comparators import ExactIntComparator, ComparatorTypeMismatch
from doctor.adversarial.lc322_ground_truth import GroundTruthDomainError, lc322_brute_force
from doctor.adversarial.provenance import input_hash


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_MANIFEST = ROOT / "EXTERNAL_VALIDATION_MANIFEST.json"
DUEL_ARTIFACT = ROOT / "data" / "track_d_phase2_lc322_oracle_duel.json"


HELD_OUT_INTERNAL_CASES: tuple[dict[str, Any], ...] = (
    {"case_id": "lc322_holdout_internal_001", "source": "held_out", "coins": [1, 3, 4], "amount": 6},
    {"case_id": "lc322_holdout_internal_002", "source": "held_out", "coins": [2, 5, 10], "amount": 27},
    {"case_id": "lc322_holdout_internal_003", "source": "held_out", "coins": [3, 7, 12], "amount": 24},
    {"case_id": "lc322_holdout_internal_004", "source": "held_out", "coins": [6, 10, 14], "amount": 25},
)


EDGE_SHAPE_CASES: tuple[dict[str, Any], ...] = (
    {"case_id": "lc322_edge_amount_zero", "source": "edge_shape", "coins": [1, 2, 5], "amount": 0},
    {"case_id": "lc322_edge_single_coin_exact", "source": "edge_shape", "coins": [7], "amount": 21},
    {"case_id": "lc322_edge_single_coin_unreachable", "source": "edge_shape", "coins": [7], "amount": 20},
    {"case_id": "lc322_edge_unreachable_amount", "source": "edge_shape", "coins": [2], "amount": 3},
    {"case_id": "lc322_edge_duplicate_coin_values", "source": "edge_shape", "coins": [1, 1, 2, 5], "amount": 11},
    {"case_id": "lc322_edge_large_coin_greater_than_amount", "source": "edge_shape", "coins": [9, 10], "amount": 8},
    {"case_id": "lc322_edge_gcd_unreachable", "source": "edge_shape", "coins": [6, 10, 14], "amount": 25},
    {"case_id": "lc322_edge_canonical_example", "source": "edge_shape", "coins": [1, 2, 5], "amount": 11},
    {"case_id": "lc322_edge_no_solution_example", "source": "edge_shape", "coins": [2], "amount": 3},
    {"case_id": "lc322_edge_greedy_trap", "source": "edge_shape", "coins": [1, 3, 4], "amount": 6},
)


def test_lc322_oracle_duel_artifact_records_required_coverage() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    assert artifact["target"] == "LC322"
    assert artifact["cases_checked"] == 119
    assert artifact["agreements"] == 119
    assert artifact["disagreements"] == 0
    assert artifact["held_out_cases_checked"] == 4
    assert artifact["held_out_disagreements"] == 0
    assert artifact["case_mix"] == {
        "held_out": 4,
        "external_validation": 5,
        "random_small": 100,
        "edge_shape": 10,
        "other": 0,
    }
    assert len(artifact["per_case"]) == 119
    assert artifact["forbidden_experiments_run"] is False


def test_lc322_independent_dp_oracle_agrees_on_all_duel_cases() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    for row in artifact["per_case"]:
        independent = lc322_dp_oracle_independent(row["coins"], row["amount"])
        existing = lc322_brute_force(row["coins"], row["amount"])
        assert row["existing_expected"] == existing
        assert row["independent_oracle_output"] == independent
        assert row["agreement"] is True
        assert independent == existing
        assert row["input_hash"] == input_hash({"coins": row["coins"], "amount": row["amount"]})


def test_lc322_external_validation_cases_are_included() -> None:
    artifact_ids = {row["case_id"] for row in _load_json(DUEL_ARTIFACT)["per_case"]}
    external = _external_validation_cases()
    assert len(external) == 5
    assert {row["case_id"] for row in external}.issubset(artifact_ids)


def test_lc322_independent_oracle_handles_amount_zero_and_unreachable() -> None:
    assert lc322_dp_oracle_independent([1, 2, 5], 0) == 0
    assert lc322_dp_oracle_independent([2], 3) == -1
    assert lc322_dp_oracle_independent([6, 10, 14], 25) == -1


def test_lc322_independent_oracle_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="amount must be non-negative"):
        lc322_dp_oracle_independent([1], -1)
    with pytest.raises(ValueError, match="coins must be positive integers"):
        lc322_dp_oracle_independent([1, 0], 3)
    with pytest.raises(ValueError, match="coins must be positive integers"):
        lc322_dp_oracle_independent([True, 2], 3)
    with pytest.raises(ValueError, match="coins must be a non-empty list"):
        lc322_dp_oracle_independent([], 3)


def test_lc322_comparator_rejects_bool_int_confusion() -> None:
    with pytest.raises(ComparatorTypeMismatch):
        ExactIntComparator().compare(1, True)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_lc322_duel_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    cases.extend(dict(row) for row in HELD_OUT_INTERNAL_CASES)
    cases.extend(_external_validation_cases())
    cases.extend(_random_small_cases())
    cases.extend(dict(row) for row in EDGE_SHAPE_CASES)
    assert len(cases) == 119
    return cases


def _external_validation_cases() -> list[dict[str, Any]]:
    payload = _load_json(EXTERNAL_MANIFEST)
    cases = []
    for case in payload["cases"]:
        input_payload = case["input"]
        cases.append(
            {
                "case_id": case["case_id"],
                "source": "external_validation",
                "coins": list(input_payload["coins"]),
                "amount": int(input_payload["amount"]),
                "manifest_expected_output": case["expected_output"],
            }
        )
    return cases


def _random_small_cases() -> list[dict[str, Any]]:
    rng = random.Random(32220260519)
    cases = []
    for index in range(100):
        coin_count = rng.randint(1, 5)
        coins = sorted({rng.randint(1, 15) for _ in range(coin_count)})
        amount = rng.randint(0, 30)
        cases.append(
            {
                "case_id": f"lc322_random_small_{index + 1:03d}",
                "source": "random_small",
                "coins": coins,
                "amount": amount,
            }
        )
    return cases


def lc322_dp_oracle_independent(coins: list[int], amount: int) -> int:
    if type(amount) is not int or type(amount) is bool or amount < 0:
        raise ValueError("amount must be non-negative integer")
    if type(coins) is not list or not coins:
        raise ValueError("coins must be a non-empty list")
    if any(type(coin) is not int or type(coin) is bool or coin <= 0 for coin in coins):
        raise ValueError("coins must be positive integers")
    inf = amount + 1
    dp = [0] + [inf] * amount
    for value in range(1, amount + 1):
        best = inf
        for coin in coins:
            if coin <= value:
                candidate = dp[value - coin] + 1
                if candidate < best:
                    best = candidate
        dp[value] = best
    return -1 if dp[amount] == inf else dp[amount]
