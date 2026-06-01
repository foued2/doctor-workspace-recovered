"""Tests for checker_gen — expanded coverage for string, list, and object outputs."""
import os
import sys
import unittest

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.analysis.checker_gen import generate_checker, _infer_mode
from doctor.analysis.spec_inferrer import SpecBundle
from doctor.analysis.agreement import _run_checker


class TestInferMode(unittest.TestCase):
    def test_list_returns_sorted(self):
        self.assertEqual(_infer_mode([1, 2, 3]), "sorted")

    def test_tuple_returns_sorted(self):
        self.assertEqual(_infer_mode((1, 2)), "sorted")

    def test_set_returns_sorted(self):
        self.assertEqual(_infer_mode({1, 2, 3}), "sorted")

    def test_frozenset_returns_sorted(self):
        self.assertEqual(_infer_mode(frozenset({1})), "sorted")

    def test_string_returns_scalar(self):
        self.assertEqual(_infer_mode("hello"), "scalar")

    def test_int_returns_scalar(self):
        self.assertEqual(_infer_mode(42), "scalar")

    def test_float_returns_scalar(self):
        self.assertEqual(_infer_mode(3.14), "scalar")

    def test_none_returns_scalar(self):
        self.assertEqual(_infer_mode(None), "scalar")

    def test_dict_returns_scalar(self):
        self.assertEqual(_infer_mode({"a": 1}), "scalar")


class TestCheckerGenScalarExpected(unittest.TestCase):
    def test_int_expected(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": 42}],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = 42", code)
        self.assertIn("MODE = 'scalar'", code)

    def test_string_expected(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": "hello"}],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = 'hello'", code)
        self.assertIn("MODE = 'scalar'", code)

    def test_none_expected_falls_to_basic(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": None}],
        )
        code = generate_checker(spec)
        self.assertIn("def checker_entry", code)
        self.assertNotIn("EXPECTED", code)

    def test_bool_expected(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": True}],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = True", code)

    def test_float_expected(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": 3.14}],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = 3.14", code)


class TestCheckerGenCollectionExpected(unittest.TestCase):
    def test_list_expected_sorted_mode(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [3, 1, 2]}],
        )
        code = generate_checker(spec)
        self.assertIn("MODE = 'sorted'", code)
        self.assertIn("sorted(actual) == sorted(expected)", code)

    def test_tuple_expected_sorted_mode(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": (1, 2, 3)}],
        )
        code = generate_checker(spec)
        self.assertIn("MODE = 'sorted'", code)

    def test_set_expected_sorted_mode(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": {3, 1, 2}}],
        )
        code = generate_checker(spec)
        self.assertIn("MODE = 'sorted'", code)


class TestCheckerGenEdgeCases(unittest.TestCase):
    def test_empty_list_expected(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": []}],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = []", code)
        self.assertIn("MODE = 'sorted'", code)

    def test_nested_list_expected(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [[1, 2], [3, 4]]}],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = [[1, 2], [3, 4]]", code)

    def test_dict_expected_scalar_mode(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": {"key": "value"}}],
        )
        code = generate_checker(spec)
        self.assertIn("MODE = 'scalar'", code)

    def test_first_test_case_used(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[
                {"expected": [0, 1]},
                {"expected": [1, 0]},
            ],
        )
        code = generate_checker(spec)
        self.assertIn("EXPECTED = [0, 1]", code)


class TestCheckerGenSandboxRoundtrip(unittest.TestCase):
    """Verify generated checkers actually run in _run_checker sandbox."""

    def test_scalar_pass(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": 42}],
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, 42, ()), "PASS")

    def test_scalar_fail(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": 42}],
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, 99, ()), "FAIL")

    def test_string_pass(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": "hello"}],
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, "hello", ()), "PASS")

    def test_string_fail(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": "hello"}],
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, "world", ()), "FAIL")

    def test_list_sorted_pass(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [3, 1, 2]}],
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, [1, 2, 3], ()), "PASS")

    def test_list_sorted_fail(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [3, 1, 2]}],
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, [1, 2, 4], ()), "FAIL")

    def test_none_in_basic_checker(self):
        spec = SpecBundle(
            problem_id="test", spec_type="inferred",
            confidence=0.5, source="inference",
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, None, ()), "FAIL")

    def test_empty_string_in_basic_checker(self):
        spec = SpecBundle(
            problem_id="test", spec_type="inferred",
            confidence=0.5, source="inference",
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, "", ()), "FAIL")

    def test_none_in_basic_checker(self):
        spec = SpecBundle(
            problem_id="test", spec_type="inferred",
            confidence=0.5, source="inference",
        )
        code = generate_checker(spec)
        self.assertEqual(_run_checker(code, None, ()), "FAIL")


class TestCheckerGenValidity(unittest.TestCase):
    def test_all_variants_produce_valid_python(self):
        specs = [
            SpecBundle(problem_id="a", spec_type="unverifiable", confidence=0, source="none"),
            SpecBundle(problem_id="b", spec_type="test_based", confidence=1, source="t", test_cases=[{"expected": 42}]),
            SpecBundle(problem_id="c", spec_type="test_based", confidence=1, source="t", test_cases=[{"expected": "hello"}]),
            SpecBundle(problem_id="d", spec_type="test_based", confidence=1, source="t", test_cases=[{"expected": [3, 1, 2]}]),
            SpecBundle(problem_id="e", spec_type="test_based", confidence=1, source="t", test_cases=[{"expected": {"a": 1}}]),
            SpecBundle(problem_id="f", spec_type="inferred", confidence=0.5, source="inference"),
        ]
        for spec in specs:
            code = generate_checker(spec)
            compile(code, f"<checker_{spec.problem_id}>", "exec")


if __name__ == "__main__":
    unittest.main()
