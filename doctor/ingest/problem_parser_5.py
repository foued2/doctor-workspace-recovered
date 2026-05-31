#!/usr/bin/env python3
"""Test gate on IMPERATIVE_INCOMPLETE cases."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from doctor.ingest.problem_parser import analyze_problem

test_cases = [
    ("P3_01", "two sum nums target", "reject"),
    ("P3_02", "valid brackets string", "reject"),
    ("P3_03", "longest common prefix strings", "reject"),
    ("P3_04", "merge sorted lists", "reject"),
    ("P3_05", "coin change min", "reject"),
    ("P3_06", "max subarray", "reject"),
    ("P3_07", "longest unique string", "reject"),
    ("P3_08", "reverse integer", "reject"),
    ("P3_09", "remove dupes array", "reject"),
    ("P3_10", "palindrome check", "reject"),
]

print("Testing structural sufficiency gate...")
correct = 0

for case_id, statement, expected in test_cases:
    result = analyze_problem(statement)
    decision = result.get("decision")
    score = result.get("matcher_diagnostic_score")
    gate_rejection = result.get("structural_gate_rejection", False)
    justification = result.get("justification", "")
    
    passed = decision == expected
    if passed:
        correct += 1
    
    status = "PASS" if passed else "FAIL"
    print(f"{case_id}: {status} expected={expected} actual={decision} score={score} gate={gate_rejection}")
    if justification:
        print(f"  justification: {justification}")

print(f"\n=== Gate test: {correct}/10 correct ===")