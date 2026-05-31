#!/usr/bin/env python3
"""
Investigation 3: Matcher Dominance Stress (ADV-class expansion)

Expose structural fragility in matching heuristic.
"""

import sys
sys.path.insert(0, '.')

from doctor.ingest.registry_matcher import (
    match_to_registry, _rule_score, _keyword_score, _fallback_score, _tokens
)
from doctor.ingest.problem_parser import FORCE_INCONCLUSIVE_TOKEN

def build_model(statement, input_type="", output_type="", objective=""):
    return {
        "source_statement": statement,
        "input_type": input_type,
        "output_type": output_type,
        "objective": objective,
        "constraints": [],
        "edge_conditions": [],
    }

def run_investigation_3():
    """Run Matcher Dominance Stress."""
    results = []

    # Get a registry problem to test against
    from doctor.registry.problem_registry import get_problems
    problems = get_problems()

    if not problems:
        print("No registry problems found")
        return results

    # Pick a well-known problem
    target_id = "two_sum" if "two_sum" in problems else list(problems.keys())[0]
    target_entry = problems[target_id]

    # Case 1: Correct statement — should match
    correct_statement = "Given an array of integers, return the indices of the two numbers that add up to a specific target."
    model = build_model(correct_statement, "array of integers, integer", "list of integers", "find indices of two numbers that sum to target")
    match_id, reason, trace = match_to_registry(model)

    results.append({
        "case": "correct statement",
        "statement": correct_statement[:50],
        "match": match_id,
        "score": trace.get("alignment_score", 0),
        "second_score": trace.get("second_best_score", 0),
        "ratio": trace.get("alignment_score", 0) / max(trace.get("second_best_score", 1), 0.01),
        "flag": None if match_id == target_id else "wrong_match",
    })

    # Case 2: Remove keywords
    stripped_statement = "Find positions where values equal goal."
    model = build_model(stripped_statement)
    match_id, reason, trace = match_to_registry(model)

    results.append({
        "case": "stripped keywords",
        "statement": stripped_statement,
        "match": match_id,
        "score": trace.get("alignment_score", 0),
        "second_score": trace.get("second_best_score", 0),
        "ratio": trace.get("alignment_score", 0) / max(trace.get("second_best_score", 1), 0.01),
        "flag": "matcher_instability" if (trace.get("alignment_score", 0) - trace.get("second_best_score", 0)) < 0.1 else None,
    })

    # Case 3: Inject irrelevant dominant tokens
    # "palindrome" is a strong rule token for longest_palindrome problem
    injection_statement = "Given an array, return the indices for target. This is a palindrome check."
    model = build_model(injection_statement)
    match_id, reason, trace = match_to_registry(model)

    results.append({
        "case": "injected dominant token (palindrome)",
        "statement": injection_statement,
        "match": match_id,
        "score": trace.get("alignment_score", 0),
        "second_score": trace.get("second_best_score", 0),
        "ratio": trace.get("alignment_score", 0) / max(trace.get("second_best_score", 1), 0.01),
        "flag": "wrong_match_by_token_injection" if match_id and match_id != target_id else None,
    })

    # Case 4: Hybrid prompt (mix two problems)
    hybrid_statement = "Given array and target, find two sum. Also check if it's a valid palindrome."
    model = build_model(hybrid_statement)
    match_id, reason, trace = match_to_registry(model)

    results.append({
        "case": "hybrid prompt (two_sum + palindrome)",
        "statement": hybrid_statement,
        "match": match_id,
        "score": trace.get("alignment_score", 0),
        "second_score": trace.get("second_best_score", 0),
        "ratio": trace.get("alignment_score", 0) / max(trace.get("second_best_score", 1), 0.01),
        "flag": "unstable_dominance" if (trace.get("alignment_score", 0) - trace.get("second_best_score", 0)) < 0.1 else None,
    })

    return results

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGATION 3: Matcher Dominance Stress")
    print("=" * 80)

    results = run_investigation_3()

    print(f"\n{'Case':<45} {'Match':<20} {'Score':<8} {'2nd':<8} {'Ratio':<8} {'Flag'}")
    print("-" * 110)

    for r in results:
        print(f"{r['case']:<45} {str(r['match']):<20} {r['score']:<8.3f} {r['second_score']:<8.3f} {r['ratio']:<8.2f} {r['flag'] or 'OK'}")

    # Mechanism analysis
    print(f"\nMechanism Analysis:")
    print(f"  Matcher uses max(rule, keyword, lexical*0.7) — single component dominance")
    print(f"  No component fusion — winner-takes-all scoring")
    print(f"  This is the ENTRY POINT for error lock-in:")
    print(f"  Wrong match → wrong problem_id → wrong test cases → wrong truth assignment")
