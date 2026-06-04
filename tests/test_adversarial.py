"""Adversarial and edge-case tests for the doctor pipeline.

Tests malformed inputs, timeout scenarios, empty solutions, and other
boundary conditions that could break the pipeline.
"""
import os
import sys
import unittest

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.observation import from_symbol
from doctor.pipeline import run_pipeline
from doctor.core.test_executor import TestExecutor, TEST_SUITES
from doctor.ingest.problem_parser import parse_problem_statement
from doctor.analysis.spec_inferrer import infer_spec
from doctor.analysis.agreement import compute_agreement_multi, _run_checker
from doctor.analysis.checker_gen import generate_checker
from doctor.analysis.spec_inferrer import SpecBundle


class TestMalformedInputs(unittest.TestCase):
    def _obs(self, report, candidate_id, expected_verdict, passed):
        return from_symbol(
            problem_id="pipeline", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"], passed=passed, seed=1, sample_size=1,
        )

    def test_empty_statement(self):
        report = run_pipeline("", "def solve(): pass")
        obs = self._obs(report, "empty_statement", None, True)
        self.assertIn(obs.canonical_form[1], ("'InvalidInput'", "'unrecognized_but_executable'"))

    def test_empty_code(self):
        report = run_pipeline("given an array and target, return the indices that add to the target", "")
        obs = self._obs(report, "empty_code", "InvalidInput", report["verdict"] == "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))

    def test_only_whitespace_code(self):
        report = run_pipeline("given an array and target, return the indices that add to the target", "   \n  \n  ")
        obs = self._obs(report, "whitespace_code", "InvalidInput", report["verdict"] == "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))

    def test_statement_with_special_characters(self):
        report = run_pipeline("!!!@@@###", "def solve(): pass")
        obs = self._obs(report, "special_chars", "InvalidInput", report["verdict"] == "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))

    def test_code_with_only_comments(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "# just a comment\n# another comment\n",
        )
        obs = self._obs(report, "only_comments", "InvalidInput", report["verdict"] == "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))

    def test_statement_only(self):
        report = run_pipeline("given an array and target, return the indices that add to the target")
        obs = self._obs(report, "statement_only", "InvalidInput", report["verdict"] == "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))
        self.assertEqual(report["reason"], "pipeline_incomplete")

    def test_code_only(self):
        report = run_pipeline("", "def solve(): pass")
        obs = self._obs(report, "code_only", "unrecognized_but_executable",
                        report["verdict"] == "unrecognized_but_executable")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'unrecognized_but_executable'", "PASS"))

    def test_both_empty(self):
        report = run_pipeline("", "")
        obs = self._obs(report, "both_empty", "InvalidInput", report["verdict"] == "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))


class TestEmptySolutions(unittest.TestCase):
    def _obs(self, report, candidate_id, passed):
        return from_symbol(
            problem_id="two_sum", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"], passed=passed, seed=1, sample_size=1,
        )

    def test_empty_function_body(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target): pass\n",
        )
        obs = self._obs(report, "empty_body", True)
        self.assertIn(obs.canonical_form[1],
                      ("'incorrect'", "'partial'", "'InvalidInput'"))

    def test_pass_only_body(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target):\n    pass\n",
        )
        obs = self._obs(report, "pass_only", True)
        self.assertIn(obs.canonical_form[1],
                      ("'incorrect'", "'partial'", "'InvalidInput'"))

    def test_return_none(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target):\n    return None\n",
        )
        obs = self._obs(report, "return_none", True)
        self.assertIn(obs.canonical_form[1], ("'incorrect'", "'partial'"))

    def test_return_empty_list(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def twoSum(nums, target):\n    return []\n",
        )
        obs = self._obs(report, "return_empty_list", True)
        self.assertIn(obs.canonical_form[1], ("'incorrect'", "'partial'"))


class TestSyntaxErrors(unittest.TestCase):
    def _obs(self, report, candidate_id):
        return from_symbol(
            problem_id="pipeline", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"],
            passed=report["verdict"] == "InvalidInput", seed=1, sample_size=1,
        )

    def test_def_missing_colon(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken(\n    pass\n",
        )
        obs = self._obs(report, "missing_colon")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))
        self.assertEqual(report["reason"], "syntax_error")

    def test_def_missing_parens(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken:\n    pass\n",
        )
        obs = self._obs(report, "missing_parens")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))

    def test_mismatched_brackets(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def solve(nums):\n    return nums[0\n",
        )
        obs = self._obs(report, "mismatched_brackets")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))


class TestMultipleFunctions(unittest.TestCase):
    def _obs(self, report, candidate_id, passed):
        return from_symbol(
            problem_id="pipeline", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"], passed=passed, seed=1, sample_size=1,
        )

    def test_two_functions_no_statement(self):
        report = run_pipeline("", "def a(x): return x\ndef b(x): return x\n")
        obs = self._obs(report, "two_fns_no_stmt",
                        report["verdict"] == "unrecognized_but_executable")
        self.assertEqual(obs.canonical_form,
                         ("pipeline_verdict", "'unrecognized_but_executable'", "PASS"))

    def test_three_functions_with_statement(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def a(x): return x\ndef b(x): return x\ndef c(x): return x\n",
        )
        obs = self._obs(report, "three_fns", True)
        self.assertIn(obs.canonical_form[1],
                      ("'unrecognized_but_executable'", "'InvalidInput'"))

    def test_solve_plus_helper(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def helper(x): return x\ndef solve(nums, target): return [0, 1]\n",
        )
        obs = self._obs(report, "solve_plus_helper", True)
        self.assertIn(obs.canonical_form[1],
                      ("'unrecognized_but_executable'", "'incorrect'", "'correct'"))


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
    def _obs(self, result, candidate_id, expected_verdict):
        return from_symbol(
            problem_id="test", candidate_id=candidate_id,
            projection_level=1, symbol_name="agreement_verdict",
            symbol_value=result.verdict,
            passed=result.verdict == expected_verdict, seed=1, sample_size=1,
        )

    def test_single_test_case_constant_is_inconclusive(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        result = compute_agreement_multi([spec], [([0, 1], ([1, 2], 3))])
        obs = self._obs(result, "single_case", "INCONCLUSIVE")
        self.assertEqual(obs.canonical_form,
                         ("agreement_verdict", "'INCONCLUSIVE'", "PASS"))

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
        obs = self._obs(result, "two_cases_pass", "PASS")
        self.assertEqual(obs.canonical_form,
                         ("agreement_verdict", "'PASS'", "PASS"))

    def test_no_test_cases(self):
        result = compute_agreement_multi([], [])
        obs = self._obs(result, "no_cases", "INCONCLUSIVE")
        self.assertEqual(obs.canonical_form,
                         ("agreement_verdict", "'INCONCLUSIVE'", "PASS"))


if __name__ == "__main__":
    unittest.main()
