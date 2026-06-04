"""Harden problem_parser — test keyword classification edge cases."""
import sys
sys.path.insert(0, ".")
from doctor.ingest.problem_parser import parse_problem


def test_case(label, statement, expected_objective):
    result = parse_problem(statement)
    obj = result.get("objective")
    status = "PASS" if obj == expected_objective else "FAIL"
    print(f"  {status} {label:40s} got={obj!r:30s} expected={expected_objective!r}")
    return obj == expected_objective


print("=" * 70)
print("  problem_parser hardening")
print("=" * 70)

passed = 0
total = 0

tests = [
    # Known problems
    ("LC322 coin change", "Return the fewest number of coins needed to make up the amount.", "lc322"),
    ("LC79 word search", "Given a grid of characters and a word, return true if the word exists.", "lc79"),
    ("Two Sum", "Find two numbers that add up to target.", "two_sum"),
    ("Max Subarray", "Find the contiguous subarray with the largest sum.", "max_subarray"),
    ("Climbing Stairs", "How many distinct ways can you climb to the top?", "climbing_stairs"),

    # Edge cases
    ("General find", "Find the minimum element in the array.", "general"),
    ("General return", "Return the sum of all elements.", "general"),
    ("No verb", "An array of integers.", None),
    ("Empty string", "", None),
    ("Whitespace only", "   ", None),
    ("Imperative incomplete", "Given an array, find the", "general"),

    # Input type detection
    ("Array type", "Given an array of integers, find the maximum.", "general"),
    ("String type", "Given a string, find the longest substring.", "general"),
    ("Tree type", "Given a binary tree, find the diameter.", "general"),
    ("Matrix type", "Given a matrix, find the path with minimum sum.", "general"),

    # Ambiguous
    ("Multiple matches", "Find two numbers that add up to target and return their indices.", "two_sum"),
    ("Long description", "You are given an integer array coins representing coins of different denominations and an integer amount representing a total amount of money. Return the fewest number of coins that you need to make up that amount.", "lc322"),
]

for label, statement, expected in tests:
    total += 1
    if test_case(label, statement, expected):
        passed += 1

print(f"\n  Results: {passed}/{total} passed")
