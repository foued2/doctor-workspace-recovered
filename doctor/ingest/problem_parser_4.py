#!/usr/bin/env python3
"""Phase 3 runner - real entropy test."""

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

with open("phase3_pack.json") as f:
    cases = json.load(f)

results = []
correct = 0

print(f"Running {len(cases)} Phase 3 cases...")

for case in cases:
    case_id = case["id"]
    statement = case["statement"]
    expected = case["expected"]
    
    print(f"Processing {case_id}...", flush=True)
    
    try:
        result = parse_problem(statement)
        analysis = result.get("_single_call_analysis", {})
        matched = analysis.get("match_candidate")
        score = analysis.get("matcher_diagnostic_score")
        decision = analysis.get("decision")
        
        actual = decision
        passed = actual == expected
        
        if passed:
            correct += 1
        
        results.append({
            "id": case_id,
            "base_problem_id": case["base_problem_id"],
            "variant_type": case["variant_type"],
            "statement": statement,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "matched": matched,
            "score": score,
        })
        
        status = "PASS" if passed else "FAIL"
        print(f"  {case_id}: {status} (expected={expected}, actual={actual}, matched={matched}, score={score})")
        
    except Exception as e:
        results.append({
            "id": case_id,
            "statement": statement,
            "expected": expected,
            "actual": "error",
            "passed": False,
            "error": str(e),
        })
        print(f"  {case_id}: ERROR - {e}")

# Stats by variant type
variant_stats = {}
for r in results:
    vt = r.get("variant_type", "unknown")
    if vt not in variant_stats:
        variant_stats[vt] = {"correct": 0, "total": 0}
    variant_stats[vt]["total"] += 1
    if r.get("passed"):
        variant_stats[vt]["correct"] += 1

print(f"\n=== Results: {correct}/{len(results)} correct ===")
print("\nBy variant type:")
for vt, stats in variant_stats.items():
    print(f"  {vt}: {stats['correct']}/{stats['total']}")

output_file = "phase3_results.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nOutput: {output_file}")
