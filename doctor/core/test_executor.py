import pathlib
import os
import unittest

from doctor.core.test_executor import TestExecutor, _results_equal
from doctor.pipeline import run_pipeline


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOLUTION_FILE = ROOT / "solutions" / "cf2225g.py"


class DoctorPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_allow_exec = os.environ.get("DOCTOR_ALLOW_UNTRUSTED_EXECUTION")
        os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"

    def tearDown(self) -> None:
        if self._old_allow_exec is None:
            os.environ.pop("DOCTOR_ALLOW_UNTRUSTED_EXECUTION", None)
        else:
            os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = self._old_allow_exec

    @unittest.skip("legacy root doctor.py CLI was removed; canonical path is doctor.pipeline.run_pipeline")
    def test_gate3_reads_solution_file(self) -> None:
        pass

    def test_results_equal_requires_strict_minus_one(self) -> None:
        self.assertFalse(_results_equal(None, -1))
        self.assertTrue(_results_equal(-1, -1))

    def test_executor_reports_honest_arrangement_result(self) -> None:
        code = SOLUTION_FILE.read_text(encoding="utf-8")
        report = TestExecutor().verify("arrange_numbers_divisible", code)
        statuses = {result.label: result.passed for result in report.results}

        self.assertEqual(report.passed, 3)
        self.assertEqual(report.total, 4)
        self.assertTrue(statuses["sample"])
        self.assertTrue(statuses["impossible"])
        self.assertTrue(statuses["trivial_k1"])
        self.assertFalse(statuses["cross_boundary"])

    def test_syntax_error_returns_invalid_input_reason(self) -> None:
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken(:\n    pass\n",
        )

        self.assertEqual(report["verdict"], "InvalidInput")
        self.assertEqual(report["reason"], "syntax_error")

    def test_multiple_functions_without_context_returns_entrypoint_unresolvable(self) -> None:
        report = run_pipeline(
            "",
            """
def first(x):
    return x

def second(x):
    return x
""",
        )

        self.assertEqual(report["verdict"], "unrecognized_but_executable")
        self.assertIn(report["reason"], ["entrypoint_unresolvable", "insufficient structural signal"])

    def test_unverifiable_statement_returns_invalid_input_reason(self) -> None:
        report = run_pipeline("hello")

        self.assertEqual(report["verdict"], "InvalidInput")
        self.assertEqual(report["reason"], "unverifiable_statement")

    def test_code_only_single_executable_without_registry_match_is_formal_verdict(self) -> None:
        report = run_pipeline(
            "",
            """
def mystery(x):
    return x
""",
        )

        self.assertEqual(report["verdict"], "unrecognized_but_executable")
        self.assertEqual(report["risk"], "MEDIUM")

    def test_spec_hypothesis_appears_on_unrecognized_but_executable(self) -> None:
        report = run_pipeline(
            (
                "Given an integer array nums, return all valid elements where each element is valid "
                "if it is strictly greater than every element to its left, or strictly greater than "
                "every element to its right. The first and last elements are always valid."
            ),
            """
def solution(nums):
    if len(nums) == 1:
        return nums
    result = [nums[0]]
    for i in range(1, len(nums) - 1):
        if all(nums[i] > nums[j] for j in range(i)) or all(nums[i] > nums[j] for j in range(i+1, len(nums))):
            result.append(nums[i])
    result.append(nums[-1])
    return result
""",
        )

        self.assertEqual(report["verdict"], "unrecognized_but_executable")
        self.assertIn("spec_hypothesis", report)
        self.assertEqual(report["spec_hypothesis"]["inferred_input_schema"], {"nums": "list"})
        self.assertEqual(report["spec_hypothesis"]["inferred_output_shape"], "list")

    def test_spec_hypothesis_absent_on_correct(self) -> None:
        report = run_pipeline(
            "given an array of integers and a target, return indices of two numbers that add up to target",
            """
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""",
        )

        self.assertEqual(report["verdict"], "correct")
        self.assertNotIn("spec_hypothesis", report)

    def test_statement_only_recognition_does_not_leak_none_verdict(self) -> None:
        report = run_pipeline(
            "given an array of integers and a target, return indices of two numbers that add up to target"
        )

        self.assertEqual(report["verdict"], "InvalidInput")
        self.assertEqual(report["reason"], "pipeline_incomplete")
        self.assertEqual(report["pipeline_status"]["input_validity"], "valid")
        self.assertEqual(report["pipeline_status"]["pipeline_completeness"], "incomplete")

    def test_partial_executor_verdict_maps_to_incorrect(self) -> None:
        report = run_pipeline(
            "given an array of integers and a target, return indices of two numbers that add up to target",
            """
def twoSum(nums, target):
    return [0, 1]
""",
        )

        self.assertEqual(report["verdict"], "incorrect")
        self.assertEqual(report["doctor_verdict"]["truth"], "incorrect")
        self.assertEqual(report["pipeline_status"]["verification_state"], "unverified")

    def test_syntax_error_pipeline_status_marks_input_invalid(self) -> None:
        report = run_pipeline(
            "given an array and target, return the indices that add to the target",
            "def broken(:\n    pass\n",
        )

        self.assertEqual(report["verdict"], "InvalidInput")
        self.assertEqual(report["reason"], "syntax_error")
        self.assertEqual(report["pipeline_status"]["input_validity"], "invalid")
        self.assertEqual(report["pipeline_status"]["pipeline_completeness"], "complete")


if __name__ == "__main__":
    unittest.main()
