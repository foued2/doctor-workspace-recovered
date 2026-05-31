from __future__ import annotations

import pytest

from doctor.adversarial.comparators import (
    ComparatorTypeMismatch,
    ExactBoolComparator,
    ExactIntComparator,
    ExactIntSequenceComparator,
    ExactListComparator,
    MultisetComparator,
    StrictTypeComparator,
    StructuredComparator,
)
from doctor.adversarial.oracle_comparison import compare_values


def test_exact_int_rejects_bool() -> None:
    with pytest.raises(ComparatorTypeMismatch, match="rejects bool"):
        ExactIntComparator().compare(1, True)
    with pytest.raises(ComparatorTypeMismatch, match="rejects bool"):
        ExactIntComparator().compare(False, 0)
    with pytest.raises(ComparatorTypeMismatch, match="rejects bool"):
        ExactIntComparator().compare(True, 1)


def test_exact_int_accepts_valid_ints() -> None:
    r = ExactIntComparator().compare(42, 42)
    assert r.equal is True
    r = ExactIntComparator().compare(42, 43)
    assert r.equal is False


def test_exact_bool_rejects_non_bool() -> None:
    r = ExactBoolComparator().compare(1, True)
    assert r.equal is False
    assert r.type_match is False
    r = ExactBoolComparator().compare(False, 0)
    assert r.equal is False
    assert r.type_match is False


def test_exact_bool_accepts_valid_bools() -> None:
    r = ExactBoolComparator().compare(True, True)
    assert r.equal is True
    r = ExactBoolComparator().compare(False, False)
    assert r.equal is True
    r = ExactBoolComparator().compare(True, False)
    assert r.equal is False


def test_structured_comparator_rejects_bool_int() -> None:
    r = StructuredComparator().compare(1, True)
    assert r.equal is False
    assert r.type_match is False


def test_structured_comparator_rejects_float_int() -> None:
    r = StructuredComparator().compare(1, 1.0)
    assert r.equal is False
    assert r.type_match is False


def test_compare_values_rejects_bool_int_ordering() -> None:
    with pytest.raises(ComparatorTypeMismatch, match="rejects bool"):
        compare_values(1, "<", True)
    with pytest.raises(ComparatorTypeMismatch, match="rejects bool"):
        compare_values(False, ">=", 0)


def test_compare_values_typed_equality_rejects_bool_int() -> None:
    r = compare_values(1, "==", True)
    assert r is False
    r = compare_values(0, "==", False)
    assert r is False


def test_exact_int_sequence_rejects_bool_element() -> None:
    r = ExactIntSequenceComparator().compare([1, True], [1, 1])
    assert r.equal is False
    assert r.type_match is False
    r = ExactIntSequenceComparator().compare([1, 0], [1, False])
    assert r.equal is False
    assert r.type_match is False


def test_exact_int_sequence_accepts_valid_ints() -> None:
    r = ExactIntSequenceComparator().compare([1, 2, 3], [1, 2, 3])
    assert r.equal is True
    r = ExactIntSequenceComparator().compare([1, 2], [1, 3])
    assert r.equal is False


def test_exact_list_rejects_type_mismatch_elements() -> None:
    r = ExactListComparator().compare([1, True], [1, 1])
    assert r.equal is False
    assert r.type_match is False


def test_multiset_comparator_order_independence() -> None:
    r = MultisetComparator().compare([1, 2, 3], [3, 1, 2])
    assert r.equal is True
    r = MultisetComparator().compare([1, 2], [1, 3])
    assert r.equal is False


def test_strict_type_rejects_bool_int() -> None:
    r = StrictTypeComparator().compare(1, True)
    assert r.equal is False
    assert r.type_match is False
    r = StrictTypeComparator().compare(True, True)
    assert r.equal is True
    assert r.type_match is True


def test_structured_rejects_list_order_mismatch() -> None:
    r = StructuredComparator().compare([1, 2, 3], [3, 2, 1])
    assert r.equal is False


def test_structured_accepts_identical_lists() -> None:
    r = StructuredComparator().compare([1, 2, 3], [1, 2, 3])
    assert r.equal is True


def test_structured_accepts_nested_structures() -> None:
    r = StructuredComparator().compare({"a": [1, 2]}, {"a": [1, 2]})
    assert r.equal is True
    r = StructuredComparator().compare({"a": [1, 2]}, {"a": [1, 3]})
    assert r.equal is False


def test_compare_values_typed_ordering_same_type() -> None:
    assert compare_values(1, "<", 2) is True
    assert compare_values(3, ">", 1) is True
    assert compare_values(2, "<=", 2) is True
    assert compare_values(3, ">=", 3) is True
