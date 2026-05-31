"""Clean recall test: known-accept cases from Phase 3/4 that definitely passed."""
import os
import sys

sys.path.insert(0, "F:/pythonProject1")
os.environ.setdefault("LLM_PROVIDER", "openrouter")

from doctor.ingest.unified_engine import analyze_statement

# Verified accept cases from Phase 3/4 - no modifiers, clean syntax
verified_accepts = [
    "Given two sorted arrays, merge them into one sorted array.",
    "Given an array of integers, find the two numbers that add up to target.",
    "Check if parentheses in a string are balanced.",
    "Find the longest increasing subsequence in an array.",
    "Find the maximum sum of any contiguous subarray.",
    "Given coins and a target, find minimum coins needed.",
    "Given two sorted linked lists, merge into one sorted list.",
    "Find the longest substring with no repeated characters.",
    "Count minimum edits between two strings.",
    "Find minimum distance between two strings.",
]

print("Clean recall test (no modifiers)")
print("=" * 60)

flipped = 0
for s in verified_accepts:
    r = analyze_statement(s)
    trace = r.get("decision_trace", {})
    match = trace.get("llm_match", "none")
    status = r.get("status")

    # Check if this would have flipped to reject due to structural modifier (not alignment)
    has_mod = r.get("error", "").find("Structural modifier") >= 0

    if "success" in str(status).lower():
        print("PASS: {0}".format(s[:50]))
    else:
        reason = r.get("error", "none")
        if has_mod:
            flipped += 1
            print("FLIP(mod): {0}".format(s[:50]))
        else:
            print("FAIL(other): {0} -> {1}".format(s[:50], reason[:30]))

print("=" * 60)
print("Structural modifier flips: {0}/{1}".format(flipped, len(verified_accepts)))
