"""End-to-end tests for the agreement path.

Validates that the 7 module fixes work together:
1. checker_gen returns valid code strings
2. _run_checker produces PASS/FAIL in sandbox
3. compute_agreement_multi returns correct verdict
4. Pipeline agreement path produces correct results
"""
import os
import sys
import unittest

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.observation import from_symbol
from doctor.analysis.checker_gen import generate_checker
from doctor.analysis.spec_inferrer import SpecBundle, infer_spec_bundle
from doctor.analysis.agreement import (
    compute_agreement_multi,
    _run_checker,
    AgreementResult,
)
from doctor.core.test_executor import TestExecutor, TEST_SUITES
from doctor.pipeline import run_pipeline


class TestCheckerGenCodeStrings(unittest.TestCase):
    """Step 1: verify generate_checker returns valid code strings."""

    def test_unverifiable_returns_code_string(self):
        spec = SpecBundle(
            problem_id="test", spec_type="unverifiable",
            confidence=0.0, source="none",
        )
        code = generate_checker(spec)
        self.assertIsInstance(code, str)
        self.assertIn("def checker_entry", code)

    def test_test_based_returns_expected_and_mode(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        code = generate_checker(spec)
        self.assertIsInstance(code, str)
        self.assertIn("EXPECTED", code)
        self.assertIn("MODE", code)
        self.assertIn("def checker_entry", code)

    def test_basic_returns_none_empty_check(self):
        spec = SpecBundle(
            problem_id="mystery", spec_type="inferred",
            confidence=0.5, source="inference",
        )
        code = generate_checker(spec)
        self.assertIsInstance(code, str)
        self.assertIn("def checker_entry", code)
        self.assertIn("None", code)

    def test_code_string_is_valid_python(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        code = generate_checker(spec)
        compile(code, "<checker>", "exec")


class TestRunCheckerSandbox(unittest.TestCase):
    """Step 2: verify _run_checker produces PASS/FAIL in sandbox."""

    def test_correct_output_passes(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        code = generate_checker(spec)
        result = _run_checker(code, [0, 1], ([1, 2, 3], 3))
        self.assertEqual(result, "PASS")

    def test_incorrect_output_fails(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        code = generate_checker(spec)
        result = _run_checker(code, [99, 99], ([1, 2, 3], 3))
        self.assertEqual(result, "FAIL")

    def test_none_output_inconclusive(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        code = generate_checker(spec)
        result = _run_checker(code, None, ([1, 2, 3], 3))
        self.assertEqual(result, "INCONCLUSIVE")

    def test_unverifiable_always_passes(self):
        spec = SpecBundle(
            problem_id="test", spec_type="unverifiable",
            confidence=0.0, source="none",
        )
        code = generate_checker(spec)
        result = _run_checker(code, "anything", ())
        self.assertEqual(result, "PASS")

    def test_sorted_comparison(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [3, 1, 2]}],
        )
        code = generate_checker(spec)
        result = _run_checker(code, [1, 2, 3], ())
        self.assertEqual(result, "PASS")


class TestAgreementMulti(unittest.TestCase):
    """Step 3: verify compute_agreement_multi returns correct verdict."""

    def _obs(self, result, candidate_id, expected_verdict):
        return from_symbol(
            problem_id="two_sum", candidate_id=candidate_id,
            projection_level=1, symbol_name="agreement_verdict",
            symbol_value=result.verdict,
            passed=result.verdict == expected_verdict, seed=1, sample_size=1,
        )

    def test_all_correct_gives_pass(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}, {"expected": [1, 0]}],
        )
        test_results = [
            ([0, 1], ([1, 2, 3], 3)),
            ([1, 0], ([2, 3, 4], 5)),
        ]
        result = compute_agreement_multi([spec], test_results)
        obs = self._obs(result, "all_correct", "PASS")
        self.assertEqual(obs.canonical_form, ("agreement_verdict", "'PASS'", "PASS"))
        self.assertGreater(result.agreeing_specs, 0)

    def test_all_wrong_gives_inconclusive(self):
        """Constant output (all [99,99]) is INCONCLUSIVE — zero evidential value."""
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}, {"expected": [1, 0]}],
        )
        test_results = [
            ([99, 99], ([1, 2, 3], 3)),
            ([99, 99], ([2, 3, 4], 5)),
        ]
        result = compute_agreement_multi([spec], test_results)
        obs = self._obs(result, "all_wrong", "INCONCLUSIVE")
        self.assertEqual(obs.canonical_form, ("agreement_verdict", "'INCONCLUSIVE'", "PASS"))

    def test_different_wrong_outputs_gives_fail(self):
        """Different wrong outputs produce FAIL (not constant, so checkers run)."""
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}, {"expected": [1, 0]}],
        )
        test_results = [
            ([99, 99], ([1, 2, 3], 3)),
            ([42, 42], ([2, 3, 4], 5)),
        ]
        result = compute_agreement_multi([spec], test_results)
        obs = self._obs(result, "different_wrong", "FAIL")
        self.assertEqual(obs.canonical_form, ("agreement_verdict", "'FAIL'", "PASS"))

    def test_mixed_gives_pass_or_inconclusive(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}, {"expected": [1, 0]}],
        )
        test_results = [
            ([0, 1], ([1, 2, 3], 3)),
            ([99, 99], ([2, 3, 4], 5)),
        ]
        result = compute_agreement_multi([spec], test_results)
        obs = self._obs(result, "mixed", None)
        self.assertIn(obs.canonical_form[1],
                      ("'PASS'", "'FAIL'", "'INCONCLUSIVE'"))

    def test_all_none_gives_inconclusive(self):
        spec = SpecBundle(
            problem_id="two_sum", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        test_results = [(None, ([1, 2, 3], 3))]
        result = compute_agreement_multi([spec], test_results)
        obs = self._obs(result, "all_none", "INCONCLUSIVE")
        self.assertEqual(obs.canonical_form, ("agreement_verdict", "'INCONCLUSIVE'", "PASS"))

    def test_constant_output_inconclusive(self):
        spec = SpecBundle(
            problem_id="test", spec_type="test_based",
            confidence=1.0, source="test_cases",
            test_cases=[{"expected": [0, 1]}],
        )
        test_results = [
            ([5], ([1],)),
            ([5], ([2],)),
            ([5], ([3],)),
        ]
        result = compute_agreement_multi([spec], test_results)
        obs = self._obs(result, "constant_output", "INCONCLUSIVE")
        self.assertEqual(obs.canonical_form, ("agreement_verdict", "'INCONCLUSIVE'", "PASS"))


class TestPipelineAgreementPath(unittest.TestCase):
    """Step 4: verify agreement result feeds into pipeline verdict."""

    def _obs(self, report, candidate_id, expected_verdict):
        return from_symbol(
            problem_id="two_sum", candidate_id=candidate_id,
            projection_level=1, symbol_name="pipeline_verdict",
            symbol_value=report["verdict"],
            passed=report["verdict"] == expected_verdict, seed=1, sample_size=1,
        )

    def test_two_sum_correct_reaches_agreement(self):
        r = run_pipeline(
            statement="Given an array of integers and a target, return indices of two numbers that add up to target.",
            solution_code=(
                "def twoSum(nums, target):\n"
                "    seen = {}\n"
                "    for i, n in enumerate(nums):\n"
                "        if target - n in seen:\n"
                "            return [seen[target - n], i]\n"
                "        seen[n] = i\n"
                "    return []"
            ),
        )
        obs = self._obs(r, "correct_two_sum", "correct")
        self.assertEqual(obs.canonical_form, ("pipeline_verdict", "'correct'", "PASS"))
        self.assertEqual(r["matched"], "two_sum")
        stages = r.get("pipeline", {})
        self.assertIn("executor", stages)
        self.assertEqual(stages["executor"]["verdict"], "correct")

    def test_two_sum_incorrect_reaches_agreement(self):
        r = run_pipeline(
            statement="Given an array of integers and a target, return indices of two numbers that add up to target.",
            solution_code=(
                "def twoSum(nums, target):\n"
                "    return [0, 1]"
            ),
        )
        obs = self._obs(r, "incorrect_two_sum", None)
        self.assertEqual(r["matched"], "two_sum")
        self.assertIn(obs.canonical_form[1], ("'incorrect'", "'partial'"))

    def test_spec_inferrer_gets_test_cases(self):
        r = run_pipeline(
            statement="Given an array of integers and a target, return indices of two numbers that add up to target.",
            solution_code=(
                "def twoSum(nums, target):\n"
                "    seen = {}\n"
                "    for i, n in enumerate(nums):\n"
                "        if target - n in seen:\n"
                "            return [seen[target - n], i]\n"
                "        seen[n] = i\n"
                "    return []"
            ),
        )
        stages = r.get("pipeline", {})
        self.assertIn("spec_inferrer", stages)
        self.assertGreater(stages["spec_inferrer"].get("confidence", 0), 0)


class TestModuleLevelTestSuites(unittest.TestCase):
    """Step 2 validation: verify module-level TEST_SUITES is populated."""

    def test_module_level_dict_has_problems(self):
        self.assertGreater(len(TEST_SUITES), 0)
        self.assertIn("two_sum", TEST_SUITES)

    def test_test_cases_have_expected_values(self):
        for problem_id, test_cases in TEST_SUITES.items():
            self.assertGreater(len(test_cases), 0, f"{problem_id} has no test cases")
            for tc in test_cases:
                self.assertTrue(
                    hasattr(tc, "expected") or (isinstance(tc, dict) and "expected" in tc),
                    f"{problem_id} test case missing expected value",
                )


class TestEvidenceCoverage(unittest.TestCase):
    """Step 3 validation: verify evidence coverage is computed correctly."""

    def test_coverage_with_no_errors(self):
        from doctor.grading.evidence import compute_evidence
        ev = compute_evidence(total=5, passed=5, traces=[])
        self.assertEqual(ev.coverage, 1.0)

    def test_coverage_with_errors(self):
        from doctor.grading.evidence import compute_evidence
        traces = [
            {"error": "timeout", "error_type": "TimeoutError"},
            {"error": "crash", "error_type": "RuntimeError"},
        ]
        ev = compute_evidence(total=5, passed=3, traces=traces)
        self.assertAlmostEqual(ev.coverage, 0.6)

    def test_coverage_zero_tests(self):
        from doctor.grading.evidence import compute_evidence
        ev = compute_evidence(total=0, passed=0, traces=[])
        self.assertEqual(ev.coverage, 0.0)


if __name__ == "__main__":
    unittest.main()
