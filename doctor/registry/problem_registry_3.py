"""Run solution against test cases directly."""


import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.registry.problem_registry import get_problems
from cf2225g import solve_case

# Load test cases
problems = get_problems()
problem_id = "arrange_numbers_divisible"

if problem_id not in problems:
    print(f"Problem not found. Available: {list(problems.keys())}")
    sys.exit(1)

test_cases = problems[problem_id].get("execution", {}).get("test_cases", [])
print(f"Running {len(test_cases)} test cases for {problem_id}")
print()

# Run each test
passed = 0
failed = 0
results = []

for tc in test_cases:
    input_data = tc.get("input", [])
    expected = tc.get("expected")
    label = tc.get("label", "unnamed")
    
    # Extract args from input (handle different formats)
    if len(input_data) == 2 and isinstance(input_data[1], list):
        n = input_data[0]
        ks = input_data[1]
    else:
        n, ks = input_data[0], input_data[1] if len(input_data) > 1 else []
    
    # Run solution
    try:
        result = solve_case(n, ks)
    except Exception as e:
        result = f"ERROR: {e}"
    
    # Compare
    if expected == -1:
        # Expect failure
        ok = result is None
    else:
        ok = result == expected
    
    if ok:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    
    results.append((label, status, expected, result))
    print(f"{label}: {status}")
    print(f"  Expected: {expected}")
    print(f"  Got:      {result}")
    print()

print(f"Results: {passed}/{len(test_cases)} passed")
print(f"Pass rate: {100*passed/len(test_cases):.1f}%")
