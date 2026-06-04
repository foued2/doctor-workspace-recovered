"""Pipeline integration tests — moved from numbered investigation scripts."""
import os
import pathlib
import sys
import unittest

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.observation import from_symbol
from doctor.core.test_executor import TestExecutor, _results_equal
from doctor.pipeline import run_pipeline


ROOT = pathlib.Path(__file__).resolve().parents[1] / "doctor"
SOLUTION_FILE = ROOT / "cf2225g.py"


class TestResultsEqual(unittest.TestCase):
    def test_none_vs_minus_one(self):
        self.assertFalse(_results_equal(None, -1))

    def test_minus_one_vs_minus_one(self):
        self.assertTrue(_results_equal(-1, -1))

    def test_none_vs_none(self):
        self.assertTrue(_results_equal(None, None))

    def test_lists_equal(self):
        self.assertTrue(_results_equal([1, 2], [1, 2]))

    def test_lists_order_matters(self):
        self.assertFalse(_results_equal([1, 2], [2, 1]))

    def test_sets_equal(self):
        self.assertTrue(_results_equal({1, 2}, {2, 1}))


class TestExecutorHonestResult(unittest.TestCase):
    def test_executor_reports_honest_arrangement_result(self):
        code = SOLUTION_FILE.read_text(encoding="utf-8")
        report = TestExecutor().verify("arrange_numbers_divisible", code)
        statuses = {result.label: result.passed for result in report.results}

        self.assertEqual(report.passed, 3)
        self.assertEqual(report.total, 4)
        self.assertTrue(statuses["sample"])
        self.assertTrue(statuses["impossible"])
        self.assertTrue(statuses["trivial_k1"])
        self.assertFalse(statuses["cross_boundary"])


class TestPipelineVerdicts(unittest.TestCase):
    def _obs(self, report, candidate_id, expected_verdict):
        return from_symbol(
            problem_id="pipeline", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"],
            passed=report["verdict"] == expected_verdict, seed=1, sample_size=1,
        )

    def test_syntax_error_returns_invalid_input(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken(:\n    pass\n",
        )
        obs = self._obs(report, "syntax_error", "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))
        self.assertEqual(report["reason"], "syntax_error")

    def test_syntax_error_pipeline_status(self):
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken(:\n    pass\n",
        )
        self.assertEqual(report["pipeline_status"]["input_validity"], "invalid")
        self.assertEqual(report["pipeline_status"]["pipeline_completeness"], "complete")

    def test_multiple_functions_unresolvable(self):
        report = run_pipeline(
            "",
            "def first(x):\n    return x\n\ndef second(x):\n    return x\n",
        )
        obs = self._obs(report, "multiple_unresolvable", "unrecognized_but_executable")
        self.assertEqual(obs.canonical_form,
                         ("pipeline_verdict", "'unrecognized_but_executable'", "PASS"))
        self.assertIn(report["reason"], ["entrypoint_unresolvable", "insufficient structural signal"])

    def test_unverifiable_statement(self):
        report = run_pipeline("hello")
        obs = self._obs(report, "unverifiable", "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))
        self.assertEqual(report["reason"], "unverifiable_statement")

    def test_code_only_single_executable(self):
        report = run_pipeline("", "def mystery(x):\n    return x\n")
        obs = self._obs(report, "code_only_exec", "unrecognized_but_executable")
        self.assertEqual(obs.canonical_form,
                         ("pipeline_verdict", "'unrecognized_but_executable'", "PASS"))
        self.assertEqual(report["risk"], "MEDIUM")

    def test_statement_only_no_code(self):
        report = run_pipeline(
            "given an array of integers and a target, return indices of two numbers that add up to target"
        )
        obs = self._obs(report, "statement_no_code", "InvalidInput")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'InvalidInput'", "PASS"))
        self.assertEqual(report["reason"], "pipeline_incomplete")
        self.assertEqual(report["pipeline_status"]["input_validity"], "valid")
        self.assertEqual(report["pipeline_status"]["pipeline_completeness"], "incomplete")

    def test_partial_verdict_maps_to_incorrect(self):
        report = run_pipeline(
            "given an array of integers and a target, return indices of two numbers that add up to target",
            "def twoSum(nums, target):\n    return [0, 1]\n",
        )
        obs = self._obs(report, "partial_incorrect", "incorrect")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'incorrect'", "PASS"))
        self.assertEqual(report["doctor_verdict"]["truth"], "incorrect")
        self.assertEqual(report["pipeline_status"]["verification_state"], "unverified")


class TestSpecHypothesis(unittest.TestCase):
    def _obs(self, report, candidate_id, expected_verdict):
        return from_symbol(
            problem_id="pipeline", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"],
            passed=report["verdict"] == expected_verdict, seed=1, sample_size=1,
        )

    def test_spec_hypothesis_appears_on_unrecognized(self):
        report = run_pipeline(
            (
                "Given an integer array nums, return all valid elements where each element is valid "
                "if it is strictly greater than every element to its left, or strictly greater than "
                "every element to its right. The first and last elements are always valid."
            ),
            (
                "def solution(nums):\n"
                "    if len(nums) == 1:\n"
                "        return nums\n"
                "    result = [nums[0]]\n"
                "    for i in range(1, len(nums) - 1):\n"
                "        if all(nums[i] > nums[j] for j in range(i)) or all(nums[i] > nums[j] for j in range(i+1, len(nums))):\n"
                "            result.append(nums[i])\n"
                "    result.append(nums[-1])\n"
                "    return result\n"
            ),
        )
        obs = self._obs(report, "spec_hypothesis_present", "unrecognized_but_executable")
        self.assertEqual(obs.canonical_form,
                         ("pipeline_verdict", "'unrecognized_but_executable'", "PASS"))
        self.assertIn("spec_hypothesis", report)
        self.assertEqual(report["spec_hypothesis"]["inferred_input_schema"], {"nums": "list"})
        self.assertEqual(report["spec_hypothesis"]["inferred_output_shape"], "list")

    def test_spec_hypothesis_absent_on_correct(self):
        report = run_pipeline(
            "given an array of integers and a target, return indices of two numbers that add up to target",
            (
                "def twoSum(nums, target):\n"
                "    seen = {}\n"
                "    for i, n in enumerate(nums):\n"
                "        if target - n in seen:\n"
                "            return [seen[target - n], i]\n"
                "        seen[n] = i\n"
                "    return []\n"
            ),
        )
        obs = self._obs(report, "correct_two_sum", "correct")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'correct'", "PASS"))
        self.assertNotIn("spec_hypothesis", report)


if __name__ == "__main__":
    unittest.main()
