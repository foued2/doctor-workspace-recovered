#!/usr/bin/env python3
"""Track A: Run boundary cases through the system."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import os

os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_PROVIDER"] = "openrouter"


from doctor.ingest.problem_parser import parse_problem

# Parse boundary file
cases = []
with open("phase3_5_boundary.txt") as f:
    content = f.read()
    blocks = content.split("---")
    for block in blocks:
        if "id:" in block:
            lines = block.strip().split("\n")
            case = {}
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    case[key.strip()] = val.strip()
            if case.get("statement"):
                cases.append(case)

print("=== TRACK A: BOUNDARY CASES ===\n")
print(f"Running {len(cases)} cases...\n")

correct = 0
for case in cases:
    case_id = case["id"]
    statement = case["statement"]
    expected = case["expected"]
    
    result = parse_problem(statement)
    analysis = result.get("_single_call_analysis", {})
    actual = analysis.get("decision", "error")
    
    passed = (actual == expected)
    if passed:
        correct += 1
    
    status = "PASS" if passed else "FAIL"
    matched = analysis.get("match_candidate")
    print(f"{case_id}: {status}")
    print(f"  Expected: {expected}, Actual: {actual}")
    print(f"  Statement: {statement[:50]}...")
    print(f"  Matched: {matched}")
    print()

print(f"=== Track A Results: {correct}/{len(cases)} correct ===")
