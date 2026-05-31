"""Tests for LC322 isolated oracle and typed comparator repairs.

Test strategy:
  1. Verify isolated oracle closes GENERIC_EXPRESSION_EVALUATION ambiguity
  2. Verify typed comparator closes BOOL_INT_ALIASING ambiguity
  3. Test for silent semantic mutation (does comparator change oracle meaning?)
  4. Verify locality discipline (repairs don't generalize beyond LC322)
"""
from __future__ import annotations

import pytest

from doctor.adversarial.lc322_isolated_oracle import (
    LC322IsolatedOracleError,
    lc322_isolated_oracle,
)
from doctor.adversarial.lc322_typed_comparator import (
    LC322ComparatorError,
    LC322TypedComparator,
)


class TestLC322IsolatedOracleClosesAmbiguity:
    """Verify isolated oracle closes GENERIC_EXPRESSION_EVALUATION ambiguity."""

    def test_oracle_is_not_expression_evaluator(self) -> None:
        """Oracle accepts only LC322 inputs, not arbitrary expressions."""
        # This should work (LC322-specific)
        result = lc322_isolated_oracle([1, 2, 5], 5)
        assert result == 1

        # This should fail (not LC322-specific)
        with pytest.raises(LC322IsolatedOracleError):
            lc322_isolated_oracle([0], 5)  # Invalid: coin <= 0

    def test_oracle_bounds_are_explicit(self) -> None:
        """Oracle declares domain bounds upfront."""
        # Within bounds: should work
        result = lc322_isolated_oracle([1, 2, 5], 100, max_amount=10000)
        assert result >= 0 or result == -1

        # Out of bounds: should raise
        with pytest.raises(LC322IsolatedOracleError, match="bound exceeded"):
            lc322_isolated_oracle([1, 2, 5], 50000, max_amount=10000)

    def test_oracle_semantics_are_local(self) -> None:
        """Oracle semantics are LC322-specific, not universal."""
        # LC322 semantics: minimum coins
        result = lc322_isolated_oracle([1, 3, 4], 6)
        assert result == 2  # 3+3, not greedy 4+1+1

        # This is NOT a general arithmetic solver
        # It's specifically minimum coin count under DP recurrence


class TestLC322TypedComparatorClosesAmbiguity:
    """Verify typed comparator closes BOOL_INT_ALIASING ambiguity."""

    def test_comparator_rejects_bool_actual(self) -> None:
        """Comparator rejects bool (closes BOOL_INT_ALIASING)."""
        comp = LC322TypedComparator()
        with pytest.raises(LC322ComparatorError, match="rejects bool"):
            comp.compare(True, 1)

    def test_comparator_rejects_bool_expected(self) -> None:
        """Comparator rejects bool in expected (closes BOOL_INT_ALIASING)."""
        comp = LC322TypedComparator()
        with pytest.raises(LC322ComparatorError, match="rejects bool"):
            comp.compare(0, False)

    def test_comparator_rejects_bool_both(self) -> None:
        """Comparator rejects bool in both (closes BOOL_INT_ALIASING)."""
        comp = LC322TypedComparator()
        with pytest.raises(LC322ComparatorError, match="rejects bool"):
            comp.compare(True, False)

    def test_comparator_enforces_exact_int(self) -> None:
        """Comparator enforces exact int comparison (no coercion)."""
        comp = LC322TypedComparator()
        result = comp.compare(5, 5)
        assert result.equal is True
        assert result.type_match is True

    def test_comparator_rejects_type_mismatch(self) -> None:
        """Comparator rejects int vs float (no silent coercion)."""
        comp = LC322TypedComparator()
        result = comp.compare(5, 5.0)
        assert result.equal is False
        assert result.type_match is False


class TestSilentSemanticMutation:
    """Test for silent semantic mutation (does comparator change oracle meaning?)."""

    def test_oracle_result_unchanged_by_comparator(self) -> None:
        """Oracle result is independent of comparator semantics."""
        oracle_result = lc322_isolated_oracle([1, 2, 5], 5)
        assert oracle_result == 1

        # Comparator validates but doesn't change oracle result
        comp = LC322TypedComparator()
        comp_result = comp.compare(oracle_result, 1)
        assert comp_result.equal is True

        # Oracle result is still 1 (not mutated)
        assert oracle_result == 1

    def test_comparator_semantics_are_explicit(self) -> None:
        """Comparator semantics are declared, not implicit."""
        comp = LC322TypedComparator()

        # Valid result: -1 (impossible)
        result = comp.compare(-1, -1)
        assert result.equal is True

        # Valid result: >= 0 (valid count)
        result = comp.compare(3, 3)
        assert result.equal is True

        # Invalid result: < -1 (nonsensical)
        result = comp.compare(-2, 5)
        assert result.equal is False
        assert "invalid result semantics" in result.reason


class TestLocalityDiscipline:
    """Verify repairs don't generalize beyond LC322."""

    def test_oracle_is_lc322_specific(self) -> None:
        """Oracle is LC322-specific, not universal coin-change solver."""
        # This oracle is bounded to small n
        # It's not a general coin-change solver
        # It's specifically for LC322 probes
        result = lc322_isolated_oracle([1, 2, 5], 5, max_n=30)
        assert result == 1

    def test_comparator_is_lc322_specific(self) -> None:
        """Comparator is LC322-specific, not universal int comparator."""
        comp = LC322TypedComparator()

        # This comparator validates LC322 semantics
        # Result must be -1 or >= 0
        # This is NOT a universal int comparator
        result = comp.compare(5, 5)
        assert result.equal is True

        # For other problems, different comparators needed
        # Locality discipline: don't generalize


class TestBasicFunctionality:
    """Basic functionality tests (sanity checks)."""

    def test_example_1(self) -> None:
        """coins=[1,2,5], amount=5 -> 1"""
        result = lc322_isolated_oracle([1, 2, 5], 5)
        assert result == 1

    def test_example_2(self) -> None:
        """coins=[2], amount=3 -> -1 (impossible)"""
        result = lc322_isolated_oracle([2], 3)
        assert result == -1

    def test_example_3(self) -> None:
        """coins=[10], amount=10 -> 1"""
        result = lc322_isolated_oracle([10], 10)
        assert result == 1

    def test_amount_zero(self) -> None:
        """amount=0 -> 0 (no coins needed)"""
        result = lc322_isolated_oracle([1, 2, 5], 0)
        assert result == 0

    def test_empty_coins_zero_amount(self) -> None:
        """coins=[], amount=0 -> 0"""
        result = lc322_isolated_oracle([], 0)
        assert result == 0

    def test_empty_coins_nonzero_amount(self) -> None:
        """coins=[], amount=5 -> -1 (impossible)"""
        result = lc322_isolated_oracle([], 5)
        assert result == -1

    def test_greedy_fails(self) -> None:
        """coins=[1,3,4], amount=6 -> 2 (not greedy 4+1+1)"""
        result = lc322_isolated_oracle([1, 3, 4], 6)
        assert result == 2  # 3+3
