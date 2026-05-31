#!/usr/bin/env python3
"""Phase 2 perturbation pack runner."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import os

# Set credentials BEFORE importing the parser (module reads at import time)
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_PROVIDER"] = "openrouter"


from doctor.ingest.problem_parser import parse_problem

PHASE2_PACK = [
    {
        "id": "P2_01",
        "base_problem_id": "two_sum",
        "perturbation_type": "DOMAIN_DISGUISE",
        "statement": "Within a list of product prices and a budget ceiling, determine which two items bring the total to exactly the budget, returning their positions.",
        "expected": "accept",
    },
    {
        "id": "P2_02",
        "base_problem_id": "two_sum",
        "perturbation_type": "OPERATION_ALIAS",
        "statement": "Given an array of integers and a target sum, locate a pair of elements that together equal the target, outputting their positions.",
        "expected": "accept",
    },
    {
        "id": "P2_03",
        "base_problem_id": "two_sum",
        "perturbation_type": "OBJECTIVE_SHIFT",
        "statement": "Given an array of integers and a target value, list all unique pairs of elements whose sum matches the target.",
        "expected": "reject",
    },
    {
        "id": "P2_04",
        "base_problem_id": "two_sum",
        "perturbation_type": "CONSTRAINT_INJECTION",
        "statement": "Find two numbers in an array that add up to a target, but the indices must not be consecutive.",
        "expected": "reject",
    },
    {
        "id": "P2_05",
        "base_problem_id": "two_sum",
        "perturbation_type": "STRUCTURE_SUPPRESSION",
        "statement": "Identify which single number can be added to itself to reach a target value.",
        "expected": "reject",
    },
    {
        "id": "P2_06",
        "base_problem_id": "valid_parentheses",
        "perturbation_type": "DOMAIN_DISGUISE",
        "statement": "In a nested folder system where each opening folder must have a matching closing folder, determine whether the structure is properly organized.",
        "expected": "accept",
    },
    {
        "id": "P2_07",
        "base_problem_id": "valid_parentheses",
        "perturbation_type": "STRUCTURE_SUPPRESSION",
        "statement": "Given a string of grouping symbols, check if every opening symbol has any closing symbol anywhere in the string, ignoring order.",
        "expected": "reject",
    },
    {
        "id": "P2_08",
        "base_problem_id": "longest_common_prefix",
        "perturbation_type": "OPERATION_ALIAS",
        "statement": "Given a collection of text strings, identify the longest shared beginning segment across all of them.",
        "expected": "accept",
    },
    {
        "id": "P2_09",
        "base_problem_id": "longest_common_prefix",
        "perturbation_type": "CONSTRAINT_INJECTION",
        "statement": "Find the common prefix of a list of strings, but the prefix must be at least 3 characters long.",
        "expected": "reject",
    },
    {
        "id": "P2_10",
        "base_problem_id": "coin_change",
        "perturbation_type": "OBJECTIVE_SHIFT",
        "statement": "Given coin denominations and a target amount, determine whether ANY combination exists that sums to the target, not the minimum count.",
        "expected": "reject",
    },
    {
        "id": "P2_11",
        "base_problem_id": "coin_change",
        "perturbation_type": "CONSTRAINT_INJECTION",
        "statement": "Find the minimum number of coins to reach a target, but you may use each coin denomination at most once.",
        "expected": "reject",
    },
    {
        "id": "P2_12",
        "base_problem_id": "course_schedule",
        "perturbation_type": "DOMAIN_DISGUISE",
        "statement": "In a university curriculum where some courses have prerequisites for others, determine if it is possible to complete all courses without conflicts.",
        "expected": "accept",
    },
    {
        "id": "P2_13",
        "base_problem_id": "course_schedule",
        "perturbation_type": "OBJECTIVE_SHIFT",
        "statement": "Given course prerequisites, determine the minimum number of semesters needed to complete all courses.",
        "expected": "reject",
    },
    {
        "id": "P2_14",
        "base_problem_id": "merge_two_sorted_lists",
        "perturbation_type": "OPERATION_ALIAS",
        "statement": "Combine two sorted collections into one unified collection that remains in order.",
        "expected": "accept",
    },
    {
        "id": "P2_15",
        "base_problem_id": "valid_parentheses",
        "perturbation_type": "CONSTRAINT_INJECTION",
        "statement": "Given a string of brackets, determine if every opening bracket is matched by exactly one closing bracket in the same position when counting forward only.",
        "expected": "reject",
    },
]


def run_phase2():
    results = []
    correct = 0

    for case in PHASE2_PACK:
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
            justification = analysis.get("justification", "")

            actual = decision
            passed = actual == expected

            if passed:
                correct += 1

            results.append({
                "id": case_id,
                "base_problem_id": case["base_problem_id"],
                "perturbation_type": case["perturbation_type"],
                "statement": statement,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "matched": matched,
                "score": score,
                "justification": justification,
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

    output_file = "phase2_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults: {correct}/{len(results)} correct")
    print(f"Output: {output_file}")

    return results


if __name__ == "__main__":
    run_phase2()
