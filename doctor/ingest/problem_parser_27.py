import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from doctor.ingest.problem_parser import _check_structural_sufficiency

# Test PARTIAL_TERMINOLOGY cases
partial_cases = [
    "a list of numbers and a target, find two that add up",
    "check if brackets are matched and in order", 
    "find what multiple strings start with",
    "combine two sorted lists into one",
    "minimum coins needed for amount",
    "max sum of subarray contiguous",
    "longest unique char substring",
    "reverse a number and check overflow",
    "remove duplicate elements from array",
    "check if number reads same backwards",
]

print("Testing PARTIAL_TERMINOLOGY cases:")
for c in partial_cases:
    ok, reason = _check_structural_sufficiency(c)
    print(f"  {'PASS' if ok else 'FAIL'}: {c[:50]}")