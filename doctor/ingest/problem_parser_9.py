#!/usr/bin/env python3
"""Run Phase 3.7 stress test - intra-class collision detection."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os

os.environ["OPENROUTER_API_KEY"] = "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"


from doctor.ingest.problem_parser import parse_problem, _check_structural_sufficiency, classify_objective

# Parse test file
cases = []
with open("phase3_7_stress.txt") as f:
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

print("=== PHASE 3.7 STRESS TEST ===\n")
print(f"{'ID':<4} {'Type':<4} {'Gate':<6} {'Class':<15} {'Matched':<30} {'Expected':<30} {'Result'}")
print("-" * 120)

for case in cases:
    id = case["id"]
    stmt = case["statement"]
    expected = case["expected_match"]
    
    # Gate
    is_suff, gate_reason = _check_structural_sufficiency(stmt)
    obj_class, conf, _ = classify_objective(stmt)
    gate = "PASS" if is_suff else "REJECT"
    
    # Matcher (only if gate passed)
    if is_suff:
        result = parse_problem(stmt)
        analysis = result.get("_single_call_analysis", {})
        matched = analysis.get("match_candidate", "none")
    else:
        matched = "GATE_REJECT"
    
    # Result
    if expected == "reject":
        # Expect rejection - either gate reject or "no match" from matcher
        passed = (matched in ["GATE_REJECT", "no match", "None", None])
    else:
        # Expect specific match
        passed = (matched == expected)
    
    result_str = "OK" if passed else "FAIL"
    
    # Truncate for display
    matched_disp = str(matched)[:28] if matched else "none"
    expected_disp = expected[:28]
    
    print(f"{id:<4} {case['type']:<4} {gate:<6} {obj_class:<15} {matched_disp:<30} {expected_disp:<30} {result_str}")

print("\n=== ANALYSIS ===")
# Count by outcome
gate_rejects = sum(1 for c in cases if _check_structural_sufficiency(c["statement"])[0] == False)
matcher_results = []
for case in cases:
    is_suff, _ = _check_structural_sufficiency(case["statement"])
    if is_suff:
        result = parse_problem(case["statement"])
        matched = result.get("_single_call_analysis", {}).get("match_candidate", "none")
        expected = case["expected_match"]
        
        if expected == "reject":
            clean = (matched in ["no match", "None", None])
            matcher_results.append(("clean_reject" if clean else "wrong_match", case["id"], matched))
        else:
            correct = (matched == expected)
            matcher_results.append(("correct_match" if correct else "wrong_match", case["id"], matched))

print(f"Gate rejected: {gate_rejects}/{len(cases)}")
for outcome, id, matched in matcher_results:
    if outcome == "wrong_match":
        print(f"  WRONG: {id} matched={matched}")
