"""Quick test of doctor.py components."""
import sys
sys.path.insert(0, "F:/pythonProject1")

# Test classification
print("Testing Step 1: Classification...")
from doctor.ingest.unified_engine import analyze_statement
r = analyze_statement("The numbers 0,1,...,n-1 are given. Arrange so adjacent differences are divisible by k1,k2,...,km")
print(f"  Status: {r.get('status')}")
print(f"  Match: {r.get('match')}")
trace = r.get('decision_trace', {})
print(f"  Matcher Diagnostic: {trace.get('matcher_diagnostic_score')}")
print()

# Test test loading
print("Testing Step 3: Test loading...")
from doctor.registry.problem_registry import get_problems
problems = get_problems()
print(f"  arrange_numbers_divisible in registry: {'arrange_numbers_divisible' in problems}")
if 'arrange_numbers_divisible' in problems:
    tests = problems['arrange_numbers_divisible'].get('execution', {}).get('test_cases', [])
    print(f"  Test cases: {len(tests)}")
print()

# Test execution
print("Testing Step 4: Execution...")
from solutions.cf2225g import solve_case
from doctor.core.test_executor import _results_equal

test_cases = [
    ((10, [2, 3]), [1, 3, 5, 7, 9, 0, 2, 4, 6, 8]),
    ((6, [2]), None),
]

passed = 0
for input_args, expected in test_cases:
    got = solve_case(*input_args)
    equal = _results_equal(got, expected)
    passed += 1 if equal else 0
    print(f"  {input_args}: {'PASS' if equal else 'FAIL'}")

print(f"  Passed: {passed}/{len(test_cases)}")
print()

# Report generation
print("Testing Step 5: Report...")
if passed == len(test_cases):
    print("  Verdict: CORRECT")
    print("  Trust: aligned_confident_correct")
    print("  Risk: LOW")
else:
    print("  Verdict: INCORRECT")
    print("  Trust: false_justified_confidence")
    print("  Risk: HIGH")