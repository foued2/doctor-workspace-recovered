from __future__ import annotations

import pytest

from doctor.adversarial.lc42_ground_truth import GroundTruthDomainError, lc42_brute_force
from doctor.adversarial.lc42_oracle import LC42OracleEvaluator, ValidationPredicate
from doctor.adversarial.comparators import ComparatorTypeMismatch, ExactIntComparator

_ORACLE = LC42OracleEvaluator()


def test_lc42_brute_force_basic_cases() -> None:
    assert lc42_brute_force(3, (0, 1, 0)) == 0
    assert lc42_brute_force(4, (1, 0, 0, 1)) == 2
    assert lc42_brute_force(6, (4, 2, 0, 3, 2, 5)) == 9
    assert lc42_brute_force(12, (0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1)) == 6


def test_lc42_brute_force_zero_and_edge() -> None:
    assert lc42_brute_force(3, (0, 0, 0)) == 0
    assert lc42_brute_force(2, (1, 2)) == 0
    assert lc42_brute_force(4, (5, 5, 5, 5)) == 0


def test_lc42_brute_force_rejects_large_input() -> None:
    with pytest.raises(GroundTruthDomainError, match="n <= 12"):
        lc42_brute_force(13, tuple(range(13)))


def test_lc42_oracle_agrees_with_brute_force_via_predicates() -> None:
    cases = [
        ((0, 1, 0), 0),
        ((1, 0, 0, 1), 2),
        ((4, 2, 0, 3, 2, 5), 9),
        ((0, 0, 0), 0),
        ((1, 2), 0),
        ((5, 5, 5, 5), 0),
    ]
    for arr, expected in cases:
        result = _ORACLE.evaluate(arr, (), solver_output=expected)
        assert result.brute_force_expected == expected
        assert result.brute_force_match is True


def test_lc42_oracle_detects_wrong_solver_output() -> None:
    arr = (4, 2, 0, 3, 2, 5)
    result = _ORACLE.evaluate(arr, (), solver_output=999)
    assert result.brute_force_expected == 9
    assert result.brute_force_match is False


def test_lc42_comparator_rejects_bool_int_confusion() -> None:
    with pytest.raises(ComparatorTypeMismatch):
        ExactIntComparator().compare(1, True)


def test_lc42_brute_force_via_total_trapped_water_symbol() -> None:
    from doctor.adversarial.lc42_symbol_registry import LC42_SYMBOL_REGISTRY

    for arr, expected in [
        ((4, 2, 0, 3, 2, 5), 9),
        ((1, 0, 0, 1), 2),
    ]:
        computed = LC42_SYMBOL_REGISTRY.get("total_trapped_water").compute({"arr": arr})
        assert computed == expected


def test_lc42_predicate_evaluation_happy_path() -> None:
    predicates = (
        ValidationPredicate("p1", "total_trapped_water", "==", "0"),
    )
    result = _ORACLE.evaluate((0, 1, 0), predicates)
    assert result.passed is True
    assert result.violated_predicate_ids == ()


def test_lc42_predicate_evaluation_violation() -> None:
    predicates = (
        ValidationPredicate("p1", "total_trapped_water", ">", "100"),
    )
    result = _ORACLE.evaluate((0, 1, 0), predicates)
    assert result.passed is False
    assert "p1" in result.violated_predicate_ids
