#!/usr/bin/env python3
"""Cold run: LeetCode 3915 through Doctor's dynamic pipeline."""
import os
import sys

# Set env vars BEFORE any Doctor imports
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["OPENROUTER_MODEL"] = "deepseek/deepseek-chat-v3-0324"

# Verify the key works at the llm_client level first
import importlib
import doctor.llm_client as llm_client
importlib.reload(llm_client)

STATEMENT = """3915. Maximum Sum of Alternating Subsequence With Distance at Least K
Hard
You are given an integer array nums of length n and an integer k.
Pick a subsequence with indices 0 <= i1 < i2 < ... < im < n such that:
For every 1 <= t < m, it+1 - it >= k.
The selected values form a strictly alternating sequence. In other words, either:
nums[i1] < nums[i2] > nums[i3] < ..., or
nums[i1] > nums[i2] < nums[i3] > ...
A subsequence of length 1 is also considered strictly alternating. The score of a valid subsequence is the sum of its selected values.
Return an integer denoting the maximum possible score of a valid subsequence.
 
Example 1:
Input: nums = [5,4,2], k = 2
Output: 7
Explanation:
An optimal choice is indices [0, 2], which gives values [5, 2].
The distance condition holds because 2 - 0 = 2 >= k.
The values are strictly alternating because 5 > 2.
The score is 5 + 2 = 7.
Example 2:
Input: nums = [3,5,4,2,4], k = 1
Output: 14
Explanation:
An optimal choice is indices [0, 1, 3, 4], which gives values [3, 5, 2, 4].
The distance condition holds because each pair of consecutive chosen indices differs by at least k = 1.
The values are strictly alternating since 3 < 5 > 2 < 4.
The score is 3 + 5 + 2 + 4 = 14.
Example 3:
Input: nums = [5], k = 1
Output: 5
Explanation:
The only valid subsequence is [5]. A subsequence with 1 element is always strictly alternating, so the score is 5.
 
Constraints:
1 <= n == nums.length <= 105
1 <= nums[i] <= 105
1 <= k <= n
"""

from experimental.dynamic.pipeline import run_pipeline

result = run_pipeline(STATEMENT)

print("=" * 70)
print("FULL PIPELINE TRACE")
print("=" * 70)

print(f"\nLayer 0: Classification")
c = result.get("classification", {})
print(f"  domain: {c.get('domain', 'N/A')}")
print(f"  paradigm: {c.get('paradigm', 'N/A')}")
print(f"  confidence: {c.get('confidence', 'N/A')}")
print(f"  error: {c.get('error', 'N/A')}")

print(f"\nLayer 1: Schema Extraction")
print(f"  schema: {'OK' if result.get('schema') else 'FAILED'}")
if result.get("schema"):
    s = result["schema"]
    print(f"  problem_id: {s.get('problem_id')}")
    print(f"  problem_class: {s.get('problem_class')}")
    print(f"  has_multiple_valid_outputs: {s.get('has_multiple_valid_outputs')}")
    inp = s.get("input_structure", {})
    print(f"  input_structure.type: {inp.get('type')}")
    print(f"  per_case_format:")
    for f in inp.get("per_case_format", []):
        print(f"    {f['name']}: {f['type']}")
    print(f"  output_format: {s.get('output_format')}")
    print(f"  constraints: {list(s.get('constraints', {}).keys())}")
    print(f"  invariants: {s.get('invariants', [])}")
    print(f"  validation_type: {s.get('validation_type')}")
    print(f"  sample_cases: {len(s.get('sample_cases', []))} extracted")
    for sc in s.get("sample_cases", []):
        print(f"    input={sc.get('input','')[:50]} output={sc.get('output','')}")

print(f"\nLayer 2: Checker Generation")
print(f"  checker: {'OK' if result.get('checker_source') else 'FAILED'}")
print(f"  checker_confidence: {result.get('checker_confidence')}")
if result.get("checker_source"):
    print(f"  checker source length: {len(result['checker_source'])}")
    print(f"  checker preview: {result['checker_source'][:200]}...")

print(f"\nLayer 3: Agreement Gate")
sa = result.get("solver_agreement")
if sa:
    print(f"  agreed: {sa.get('agreed')}/{sa.get('total_attempts')}")
    print(f"  disagreed: {sa.get('disagreed')}")
    for i, trace in enumerate(sa.get("traces", [])):
        print(f"    Case {i}: agreed={trace['agreed']}, attempts={trace['attempts']}")
else:
    print(f"  solver_agreement: None (generation failed or no solvers)")

print(f"\nLayer 4: Execution Gate")
eg = result.get("execution_gate")
if eg:
    print(f"  passed: {eg.get('passed')}")
    print(f"  reason: {eg.get('reason')}")
else:
    print(f"  execution_gate: None (pre-gate failure)")

print(f"\nLayer 5: Ingestion")
print(f"  ingested: {result.get('ingested')}")
print(f"  registry_key: {result.get('registry_key')}")

print(f"\nLayer 6: Trust Verdict")
print(f"  verdict: {result.get('verdict')}")
print(f"  trust: {result.get('trust')}")
print(f"  risk: {result.get('risk')}")
print(f"  provenance: {result.get('provenance')}")
print(f"  E: {result.get('E')}")
print(f"  e: {result.get('e')}")
print(f"  failure_mode: {result.get('failure_mode')}")

print(f"\nTest Results:")
sr = result.get("sample_results")
if sr:
    print(f"  Sample: {sr['passed']}/{sr['total']}")
    for d in sr.get("details", []):
        status = "PASS" if d.get("passed") else "FAIL"
        print(f"    [{status}] input={d['input'][:50]}, expected={d['expected']}, actual={d.get('actual')}, error={d.get('error')}")
gr = result.get("generated_results")
if gr:
    print(f"  Generated: {gr['passed']}/{gr['total']}")
    for d in gr.get("details", []):
        status = "PASS" if d.get("passed") else "FAIL"
        print(f"    [{status}] input={d['input'][:50]}, expected={d['expected']}, actual={d.get('actual')}, error={d.get('error')}")
print(f"  Total: {result.get('tests_passed')}/{result.get('tests_total')}")
