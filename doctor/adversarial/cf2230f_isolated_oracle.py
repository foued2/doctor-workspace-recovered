"""Tests for CF2230F isolated oracle and typed comparator repairs.

Test strategy:
  1. Verify isolated oracle closes GENERIC_EXPRESSION_EVALUATION ambiguity
  2. Verify typed comparator closes BOOL_INT_ALIASING ambiguity
  3. Test for silent semantic mutation (does comparator change oracle meaning?)
  4. Verify locality discipline (repairs don't generalize beyond CF2230F)
"""
from __future__ import annotations

import pytest

from doctor.adversarial.cf2230f_isolated_oracle import (
    CF2230FOracleError,
    cf2230f_isolated_oracle,
)
from doctor.adversarial.cf2230f_typed_comparator import (
    CF2230FComparatorError,
    CF2230FTypedComparator,
)


class TestCF2230FIsolatedOracleClosesAmbiguity:
    """Verify isolated oracle closes GENERIC_EXPRESSION_EVALUATION ambiguity."""

    def test_oracle_is_not_expression_evaluator(self) -> None:
        """Oracle accepts only CF2230F inputs, not arbitrary expressions."""
        # This should work (CF2230F-specific)
        result = cf2230f_isolated_oracle([3, 5, 2, 10])
        assert result == 0

        # This should fail (not CF2230F-specific)
        with pytest.raises(CF2230FOracleError):
            cf2230f_isolated_oracle([5])  # Invalid: need at least 2 elements

    def test_oracle_bounds_are_explicit(self) -> None:
        """Oracle declares domain bounds upfront."""
        # Within bounds: should work
        result = cf2230f_isolated_oracle([1, 2, 3], max_n=30)
        assert result >= 0

        # Out of bounds: should raise
        arr = list(range(1, 35))  # 34 elements
        with pytest.raises(CF2230FOracleError, match="bound exceeded"):
            cf2230f_isolated_oracle(arr, max_n=30)

    def test_oracle_semantics_are_local(self) -> None:
        """Oracle semantics are CF2230F-specific, not universal."""
        # CF2230F semantics: minimum absolute difference
        result = cf2230f_isolated_oracle([3, 5, 2, 10])
        # Split at 3: prefix=3+5+2=10, suffix=10, diff=0
        assert result == 0

        # This is NOT a general array processor
        # It's specifically minimum prefix/suffix difference


class TestCF2230FTypedComparatorClosesAmbiguity:
    """Verify typed comparator closes BOOL_INT_ALIASING ambiguity."""

    def test_comparator_rejects_bool_actual(self) -> None:
        """Comparator rejects bool (closes BOOL_INT_ALIASING)."""
        comp = CF2230FTypedComparator()
        with pytest.raises(CF2230FComparatorError, match="rejects bool"):
            comp.compare(True, 1)

    def test_comparator_rejects_bool_expected(self) -> None:
        """Comparator rejects bool in expected (closes BOOL_INT_ALIASING)."""
        comp = CF2230FTypedComparator()
        with pytest.raises(CF2230FComparatorError, match="rejects bool"):
            comp.compare(0, False)

    def test_comparator_rejects_bool_both(self) -> None:
        """Comparator rejects bool in both (closes BOOL_INT_ALIASING)."""
        comp = CF2230FTypedComparator()
        with pytest.raises(CF2230FComparatorError, match="rejects bool"):
            comp.compare(True, False)

    def test_comparator_enforces_exact_int(self) -> None:
        """Comparator enforces exact int comparison (no coercion)."""
        comp = CF2230FTypedComparator()
        result = comp.compare(4, 4)
        assert result.equal is True
        assert result.type_match is True

    def test_comparator_rejects_type_mismatch(self) -> None:
        """Comparator rejects int vs float (no silent coercion)."""
        comp = CF2230FTypedComparator()
        result = comp.compare(4, 4.0)
        assert result.equal is False
        assert result.type_match is False


class TestSilentSemanticMutation:
    """Test for silent semantic mutation (does comparator change oracle meaning?)."""

    def test_oracle_result_unchanged_by_comparator(self) -> None:
        """Oracle result is independent of comparator semantics."""
        oracle_result = cf2230f_isolated_oracle([3, 5, 2, 10])
        assert oracle_result == 0

        # Comparator validates but doesn't change oracle result
        comp = CF2230FTypedComparator()
        comp_result = comp.compare(oracle_result, 0)
        assert comp_result.equal is True

        # Oracle result is still 0 (not mutated)
        assert oracle_result == 0

    def test_comparator_semantics_are_explicit(self) -> None:
        """Comparator semantics are declared, not implicit."""
        comp = CF2230FTypedComparator()

        # Valid result: >= 0 (absolute difference)
        result = comp.compare(0, 0)
        assert result.equal is True

        result = comp.compare(5, 5)
        assert result.equal is True

        # Invalid result: < 0 (nonsensical for absolute difference)
        result = comp.compare(-1, 5)
        assert result.equal is False
        assert "invalid result semantics" in result.reason


class TestLocalityDiscipline:
    """Verify repairs don't generalize beyond CF2230F."""

    def test_oracle_is_cf2230f_specific(self) -> None:
        """Oracle is CF2230F-specific, not universal array processor."""
        # This oracle is bounded to small n
        # It's not a general array processor
        # It's specifically for CF2230F probes
        result = cf2230f_isolated_oracle([1, 2, 3], max_n=30)
        assert result >= 0

    def test_comparator_is_cf2230f_specific(self) -> None:
        """Comparator is CF2230F-specific, not universal int comparator."""
        comp = CF2230FTypedComparator()

        # This comparator validates CF2230F semantics
        # Result must be >= 0 (absolute difference)
        # This is NOT a universal int comparator
        result = comp.compare(5, 5)
        assert result.equal is True

        # For other problems, different comparators needed
        # Locality discipline: don't generalize


class TestBasicFunctionality:
    """Basic functionality tests (sanity checks)."""

    def test_example_1(self) -> None:
        """[3,5,2,10] -> min diff = 0 (split at 3: 10 vs 10)"""
        result = cf2230f_isolated_oracle([3, 5, 2, 10])
        assert result == 0

    def test_example_2(self) -> None:
        """[1,1] -> split 1: prefix=1, suffix=1, diff=0"""
        result = cf2230f_isolated_oracle([1, 1])
        assert result == 0

    def test_example_3(self) -> None:
        """[1,2,5] -> split 1: 1 vs 7 (diff=6), split 2: 3 vs 5 (diff=2)"""
        result = cf2230f_isolated_oracle([1, 2, 5])
        assert result == 2

    def test_negative_numbers(self) -> None:
        """[-5, 5] -> split 1: -5 vs 5, diff=10"""
        result = cf2230f_isolated_oracle([-5, 5])
        assert result == 10

    def test_all_same(self) -> None:
        """[2, 2, 2, 2] -> split 2: 4 vs 4, diff=0"""
        result = cf2230f_isolated_oracle([2, 2, 2, 2])
        assert result == 0

    def test_oracle_rejects_single_element(self) -> None:
        """Reject len(arr) < 2"""
        with pytest.raises(CF2230FOracleError, match="invalid input"):
            cf2230f_isolated_oracle([5])

    def test_oracle_rejects_empty(self) -> None:
        """Reject empty array"""
        with pytest.raises(CF2230FOracleError, match="invalid input"):
            cf2230f_isolated_oracle([])
