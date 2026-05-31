#!/usr/bin/env python3
"""Run Phase 3.6 Natural Phrasing Test."""

import json
import os
import sys

os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_PROVIDER"] = "openrouter"

sys.path.insert(0, os.path.dirname(__file__))

from doctor.ingest.problem_parser import parse_problem, _check_structural_sufficiency

# Parse file
cases = []
with open("phase3_6_natural.txt") as f:
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

print("=== PHASE 3.6: NATURAL PHRASING TEST ===\n")
print(f"Running {len(cases)} cases...\n")

# Track separately
match_cases = []
out_of_reg_cases = []
invalid_cases = []

for case in cases:
    case_id = case["id"]
    statement = case["statement"]
    expected = case["expected"]
    
    # Check gate
    is_suff, gate_reason = _check_structural_sufficiency(statement)
    
    # Get LLM result
    result = parse_problem(statement)
    analysis = result.get("_single_call_analysis", {})
    matched = analysis.get("match_candidate")
    decision = analysis.get("decision")
    
    # Categorize
    if expected.startswith("reject"):
        category = "invalid" if expected == "reject_invalid" else "out_of_registry"
        if category == "invalid":
            invalid_cases.append({**case, "matched": matched, "decision": decision, "gate": gate_reason})
        else:
            out_of_reg_cases.append({**case, "matched": matched, "decision": decision, "gate": gate_reason})
    else:
        match_cases.append({**case, "matched": matched, "decision": decision, "gate": gate_reason})

# Report by category
print("=== CATEGORY 1: MATCH ACCURACY (valid problems in registry) ===")
correct = 0
for c in match_cases:
    passed = (c["matched"] == c["expected"])
    if passed:
        correct += 1
    status = "PASS" if passed else "FAIL"
    print(f"{c['id']}: {status} | expected={c['expected']}, matched={c['matched']}")
print(f"\nMatch Accuracy: {correct}/{len(match_cases)} = {correct/len(match_cases)*100:.1f}%\n")

print("=== CATEGORY 2: OUT-OF-REGISTRY (well-formed, not in registry) ===")
rejected_cleanly = 0
for c in out_of_reg_cases:
    # Clean rejection = reject with no false match
    clean = (c["decision"] == "reject")
    if clean:
        rejected_cleanly += 1
    status = "CLEAN" if clean else "MATCHED"
    print(f"{c['id']}: {status} | expected=reject, matched={c['matched']}")
print(f"\nClean Rejection: {rejected_cleanly}/{len(out_of_reg_cases)} = {rejected_cleanly/len(out_of_reg_cases)*100:.1f}%\n")

print("=== CATEGORY 3: INVALID (underspecified) ===")
gate_caught = 0
llm_caught = 0
for c in invalid_cases:
    if not is_suff:
        gate_caught += 1
    elif c["decision"] == "reject":
        llm_caught += 1
    status = "GATE" if not is_suff else ("LLM" if c["decision"] == "reject" else "PASSED")
    print(f"{c['id']}: {status} | gate={'REJECT' if not is_suff else 'PASS'}, decision={c['decision']}")
print(f"\nGate caught: {gate_caught}/{len(invalid_cases)}")
print(f"LLM caught: {llm_caught}/{len(invalid_cases)}")