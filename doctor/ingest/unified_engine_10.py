"""Recall measurement: run all known accept cases through modified engine."""
import json
import os
import sys

sys.path.insert(0, "F:/pythonProject1")
os.environ.setdefault("LLM_PROVIDER", "openrouter")

from doctor.ingest.unified_engine import analyze_statement

# All known accept cases from Phase 3 and Phase 4 batches 1-2
# (these were recorded in the pushed test data)

known_accept_cases = [
    ("Validate if parentheses are balanced and properly nested.", "valid_parentheses"),
    ("Given an array of integers and a target sum, find two numbers that add up to the target.", "two_sum"),
    ("Find the maximum sum of any contiguous subarray.", "max_subarray"),
    ("Given two sorted arrays, merge them into one sorted array.", "merge_two_sorted_lists"),
    ("Find the longest increasing subsequence in an array.", "longest_increasing_subsequence"),
    ("Given coins and a target amount, find the minimum number of coins needed.", "coin_change"),
    ("Find the length of the longest substring without repeating characters.", "longest_substring_without_repeating_characters"),
    ("Count the minimum number of edits between two strings.", "edit_distance"),
    ("Find the minimum distance to insert/delete characters to transform one string to another.", "min_distance"),
    ("Given two sorted linked lists, merge them into one sorted linked list.", "merge_two_sorted_lists"),
    ("Find the maximum product of any subarray.", "max_subarray"),
    ("Find the contiguous subarray with the largest sum.", "max_subarray"),
    ("Determine if a string has all unique characters.", "is_unique"),
    ("Find the first missing positive integer in an array.", "first_missing_positive"),
    ("Given an array, find the subarray with the maximum product.", "max_subarray"),
    ("Find the longest increasing subsequence, but only consider even-indexed elements.", None),  # reject case
    ("Find two numbers that sum to target, but return indices not values.", None),  # slight variant
    ("Given a string, reverse words but keep punctuation.", None),  # different problem
]

print("Recall measurement: known accept cases with new modifier check")
print("=" * 60)

flipped = []
passed = 0

for statement, expected in known_accept_cases:
    try:
        result = analyze_statement(statement)
        status = result.get("status", "unknown")

        is_accept = "success" in str(status).lower() or "accept" in str(status).lower()

        if is_accept:
            passed += 1
            print("ACCEPT: {0} -> {1}".format(expected or "unknown", status))
        else:
            print("REJECT: {0} -> {1} ({2})".format(
                expected or "unknown", status, result.get("error", "none")[:50] if result.get("error") else "no error"
            ))
            if expected:
                flipped.append((statement, expected, status))
    except Exception as e:
        print("ERROR: {0} -> {1}".format(expected or "unknown", str(e)[:30]))

print("=" * 60)
print("Passed: {0}/{1}".format(passed, len(known_accept_cases)))
print("Flipped from accept: {0}".format(len(flipped)))

if flipped:
    print("\nFlipped cases:")
    for st, exp, status in flipped:
        print("  - {0} (expected {1})".format(st[:50], exp))
