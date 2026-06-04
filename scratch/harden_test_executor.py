"""Harden test_executor and evidence — verify execution and serialization."""
import sys
sys.path.insert(0, ".")
from doctor.core.test_executor import TestExecutor, _results_equal, ExecutionReport
from doctor.grading.evidence import compute_evidence
from dataclasses import asdict

print("=" * 70)
print("  test_executor hardening")
print("=" * 70)

executor = TestExecutor()

# Test 1: Two Sum correct solution
print("\n--- Two Sum correct ---")
code = """
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""
report = executor.verify("two_sum", code)
print(f"  verdict: {report.verdict}, passed: {report.passed}/{report.total}")
assert report.verdict == "correct", f"Expected correct, got {report.verdict}"
assert report.passed == report.total

# Test 2: Two Sum incorrect solution (some pass due to coincidental matches)
print("\n--- Two Sum incorrect ---")
code_bad = """
def twoSum(nums, target):
    return [0, 1]
"""
report2 = executor.verify("two_sum", code_bad)
print(f"  verdict: {report2.verdict}, passed: {report2.passed}/{report2.total}")
assert report2.verdict in ("incorrect", "partial"), f"Expected incorrect/partial, got {report2.verdict}"
assert report2.passed < report2.total

# Test 3: Partial result
print("\n--- Two Sum partial (off-by-one) ---")
code_partial = """
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
report3 = executor.verify("two_sum", code_partial)
print(f"  verdict: {report3.verdict}, passed: {report3.passed}/{report3.total}")
assert report3.verdict == "correct", f"Expected correct, got {report3.verdict}"

# Test 4: _results_equal edge cases
print("\n--- _results_equal edge cases ---")
assert _results_equal(None, None) == True
assert _results_equal(None, -1) == False
assert _results_equal(-1, -1) == True
assert _results_equal([1, 2], [1, 2]) == True
assert _results_equal([1, 2], [2, 1]) == False
assert _results_equal({1, 2}, {2, 1}) == True
print("  All edge cases passed")

# Test 5: ExecutionReport serialization
print("\n--- ExecutionReport serialization ---")
report_dict = asdict(report)
assert "verdict" in report_dict
assert "results" in report_dict
assert isinstance(report_dict["results"], list)
print(f"  Serialized: {list(report_dict.keys())}")

print("\n" + "=" * 70)
print("  evidence hardening")
print("=" * 70)

# Test 1: compute_evidence with correct results
print("\n--- Evidence from correct results ---")
ev = compute_evidence(total=5, passed=5)
print(f"  pass_rate={ev.pass_rate}, volume={ev.test_volume}, coverage={ev.coverage}")
assert ev.pass_rate == 1.0
assert ev.test_volume == 5

# Test 2: compute_evidence with mixed results
print("\n--- Evidence from mixed results ---")
ev2 = compute_evidence(total=5, passed=2, traces=[{"error": "timeout", "error_type": "TimeoutError"}])
print(f"  pass_rate={ev2.pass_rate}, volume={ev2.test_volume}, error_flags={ev2.error_flags}")
assert ev2.pass_rate == 0.4
assert "TimeoutError" in ev2.error_flags

# Test 3: compute_evidence with zero tests
print("\n--- Evidence from zero tests ---")
ev3 = compute_evidence(total=0, passed=0)
print(f"  pass_rate={ev3.pass_rate}, volume={ev3.test_volume}")
assert ev3.pass_rate == 0.0

print("\n" + "=" * 70)
print("  ALL TESTS PASSED")
print("=" * 70)
