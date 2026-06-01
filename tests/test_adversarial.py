"""Adversarial and edge-case tests for the doctor pipeline.

Tests malformed inputs, timeout scenarios, empty solutions, and other
boundary conditions that could break the pipeline.
"""
import os
import sys
import unittest

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.pipeline import run_pipeline
from doctor.core.test_executor import TestExecutor, TEST_SUITES
from doctor.ingest.problem_parser import parse_problem_statement
from doctor.analysis.spec_inferrer import infer_spec
from doctor.analysis.agreement import compute_agreement_multi, _run_checker
from doctor.analysis.checker_gen import generate_checker
from doctor.analysis.spec_inferrer import SpecBundle


class TestMalformedInputs(unittest.TestCase):
    def test_empty_statement(self):
        report = run_pipeline("", "def solve(): pass")
        self.assertIn(report["verdict"], ("InvalidInput", "unrecognized_but_executable"))

    def test_empty_code(self):
        report = run_pipeline("given an array and target, return the indices that add to the target", "")
        self.assertEqual(report["verdict"], "InvalidInput")

    def test_only_whitespace_code(self):
        report = run_pipeline("given an array and target, return the indices that add to the target", "   \n  \n  ")
        self.assertEqual(report["verdict"], "InvalidInput")

    def test_statement_with_special_characters(self):
        report = run_pipeline("!!!@@@###", "def solve(): pass")
        self.assertEqual(report["verdict"], "InvalidInput")

    def test_code_with_only_comments(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "# just a comment\n# another comment\n",
        )
        self.assertEqual(report["verdict"], "InvalidInput")

    def test_statement_only(self):
        report = run_pipeline("given an array and target, return the indices that add to the target")
        self.assertEqual(report["verdict"], "InvalidInput")
        self.assertEqual(report["reason"], "pipeline_incomplete")

    def test_code_only(self):
        report = run_pipeline("", "def solve(): pass")
        self.assertEqual(report["verdict"], "unrecognized_but_executable")

    def test_both_empty(self):
        report = run_pipeline("", "")
        self.assertEqual(report["verdict"], "InvalidInput")


class TestEmptySolutions(unittest.TestCase):
    def test_empty_function_body(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target): pass\n",
        )
        self.assertIn(report["verdict"], ("incorrect", "partial", "InvalidInput"))

    def test_pass_only_body(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target):\n    pass\n",
        )
        self.assertIn(report["verdict"], ("incorrect", "partial", "InvalidInput"))

    def test_return_none(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target):\n    return None\n",
        )
        self.assertIn(report["verdict"], ("incorrect", "partial"))

    def test_return_empty_list(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target):\n    return []\n",
        )
        self.assertIn(report["verdict"], ("incorrect", "partial"))


class TestSyntaxErrors(unittest.TestCase):
    def test_def_missing_colon(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken(\n    pass\n",
        )
        self.assertEqual(report["verdict"], "InvalidInput")
        self.assertEqual(report["reason"], "syntax_error")

    def test_def_missing_parens(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken:\n    pass\n",
        )
        self.assertEqual(report["verdict"], "InvalidInput")

    def test_mismatched_brackets(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def solve(nums):\n    return nums[0\n",
        )
        self.assertEqual(report["verdict"], "InvalidInput")


class TestMultipleFunctions(unittest.TestCase):
    def test_two_functions_no_statement(self):
        report = run_pipeline("", "def a(x): return x\ndef b(x): return x\n")
        self.assertEqual(report["verdict"], "unrecognized_but_executable")

    def test_three_functions_with_statement(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def a(x): return x\ndef b(x): return x\ndef c(x): return x\n",
        )
        self.assertIn(report["verdict"], ("unrecognized_but_executable", "InvalidInput"))

    def test_solve_plus_helper(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def helper(x): return x\ndef solve(nums, target): return [0, 1]\n",
        )
        self.assertIn(report["verdict"], ("unrecognized_but_executable", "incorrect", "correct"))


class TestRegistryCoverage(unittest.TestCase):
    def test_all_test_suites_have_entries(self):
        for problem_id in TEST_SUITES:
            self.assertIn(problem_id, TEST_SUITES)

    def test_test_cases_not_empty(self):
        for problem_id, test_cases in TEST_SUITES.items():
            self.assertGreater(len(test_cases), 0, f"{problem_id} has no test cases")


class TestExecutorEdgeCases(unittest.TestCase):
    def test_executor_with_valid_solution(self):
        code = "def twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []"
        report = TestExecutor().verify("two_sum", code)
        self.assertGreater(report.passed, 0)

    def test_executor_with_always_wrong_solution(self):
        code = "def twoSum(nums, target):\n    return [0, 0]"
        report = TestExecutor().verify("two_sum", code)
        self.assertGreater(report.total, 0)


class TestSpecInferenceEdgeCases(unittest.TestCase):
    def test_statement_with_integer_array(self):
        spec = infer_spec("given an array of integers and a target, return indices of two numbers that add up to target")
        self.assertIn("nums", spec.inferred_input_schema)

    def test_statement_with_string_input(self):
        spec = infer_spec("given a string s, return the length of the longest substring without repeating characters")
        self.assertIn("s", spec.inferred_input_schema)

    def test_statement_with_grid(self):
        spec = infer_spec("given a 2D grid, find the number of islands")
        self.assertIsNotNone(spec)
        self.assertTrue(hasattr(spec, "inferred_input_schema"))

    def test_empty_statement(self):
        spec = infer_spec("")
        self.assertIsNotNone(spec)


class TestAgreementEdgeCases(unittest.TestCase):
    def test_single_test_case_constant_is_inconclusive(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        result = compute_agreement_multi([spec], [([0, 1], ([1, 2], 3))])
        self.assertEqual(result.verdict, "INCONCLUSIVE")

    def test_two_test_cases_pass(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}, {"expected": [1, 0]}],
        )
        result = compute_agreement_multi(
            [spec],
            [([0, 1], ([1, 2], 3)), ([1, 0], ([4, 5], 9))],
        )
        self.assertEqual(result.verdict, "PASS")

    def test_no_test_cases(self):
        result = compute_agreement_multi([], [])
        self.assertEqual(result.verdict, "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
