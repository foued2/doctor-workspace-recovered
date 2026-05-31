#!/usr/bin/env python3
"""Test 7-class schema gate on Phase 3.6 valid cases."""

import os
import sys

os.environ["OPENROUTER_API_KEY"] = "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"

sys.path.insert(0, os.path.dirname(__file__))

from doctor.ingest.problem_parser import _check_structural_sufficiency, classify_objective

# 13 valid Phase 3.6 cases
cases = [
    ('N01', "hey, i need to find two numbers in my list that add up to some target", 'two_sum'),
    ('N02', "can you check if a word reads the same forwards and backwards", 'palindrome_number'),
    ('N03', "basically i have a bunch of strings and i want to find what they all start with", 'longest_common_prefix'),
    ('N04', "got two sorted lists, how do i combine them into one sorted list", 'merge_two_sorted_lists'),
    ('N05', "what's the smallest number of coins i need to make this amount", 'coin_change'),
    ('N06', "i need to find the biggest sum i can get from a subarray", 'max_subarray'),
    ('N07', "how long can a string get if i don't repeat any characters", 'longest_substring_without_repeating_characters'),
    ('N08', "reverse all the digits in this number but watch out for overflow", 'reverse_integer'),
    ('N09', "my array has duplicates, remove them and tell me how many are left", 'remove_duplicates'),
    ('N10', "are my brackets properly matched and in the right order", 'valid_parentheses'),
    ('N14', "how many ways can i climb to the top of the stairs", 'climbing_stairs'),
    ('N15', "calculate the area of the largest rectangle possible", 'largest_rectangle_area'),
    ('N16', "given an array find the median", 'find_median_sorted_arrays'),
]

print("=== 7-CLASS SCHEMA GATE TEST ===\n")
print(f"{'ID':<5} {'Problem':<25} {'Class':<15} {'Conf':<6} {'Gate':<6} {'Match'}")
print("-" * 80)

passed = 0
for id, statement, expected in cases:
    # Get classification
    obj_class, conf, err = classify_objective(statement)
    
    # Get gate decision
    is_suff, gate_reason = _check_structural_sufficiency(statement)
    
    gate = 'PASS' if is_suff else 'REJECT'
    if is_suff:
        passed += 1
    
    print(f"{id:<5} {expected:<25} {obj_class:<15} {conf:<6} {gate:<6} {expected}")

print(f"\n=== Results: {passed}/13 passed ===")