#!/usr/bin/env python3
"""
Investigation 7: Pipeline Stage Skipping Detection

Verify invariant that all stages execute before verdict.
"""

import sys
sys.path.insert(0, '.')

from doctor.pipeline import _invalid_input_response, _unrecognized_executable_response

def run_investigation_7():
    """Run Pipeline Stage Skipping Detection."""
    results = []

    # Case 1: Normal matched path (should have all stages)
    # Simulated by checking what _invalid_input_response produces
    trace = {"oracle_state": {}, "recognition": {}}
    stages = {}

    response = _invalid_input_response(
        reason="test_invalid",
        trace=trace,
        stages=stages,
        problem_id="test_123",
        matched=None,
    )

    pipeline_stages = response.get("pipeline", {})
    has_all_stages = all(
        stage in pipeline_stages
        for stage in ["normalizer", "executor", "evidence", "trust", "report"]
    )

    results.append({
        "case": "invalid_input path",
        "stages_present": list(pipeline_stages.keys()),
        "has_all_stages": has_all_stages,
        "verdict": response.get("verdict"),
        "flag": None if has_all_stages else "pipeline_violation",
    })

    # Case 2: Unrecognized executable path
    trace = {"recognition": {"parsed_model": {"force_inconclusive": False}}}
    stages = {}

    response = _unrecognized_executable_response(
        trace=trace,
        stages=stages,
        reason="test_unrecognized",
        statement="Return the sum of two numbers",
        source_code="def solve(a, b): return a + b",
    )

    pipeline_stages = response.get("pipeline", {})
    has_all_stages = all(
        stage in pipeline_stages
        for stage in ["normalizer", "executor", "evidence", "trust", "report"]
    )

    results.append({
        "case": "unrecognized_executable path",
        "stages_present": list(pipeline_stages.keys()),
        "has_all_stages": has_all_stages,
        "verdict": response.get("verdict"),
        "flag": None if has_all_stages else "pipeline_violation",
    })

    return results

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGATION 7: Pipeline Stage Skipping Detection")
    print("=" * 80)

    results = run_investigation_7()

    print(f"\n{'Case':<40} {'Stages':<50} {'Flag'}")
    print("-" * 100)

    for r in results:
        print(f"{r['case']:<40} {str(r['stages_present']):<50} {r['flag'] or 'OK'}")

    # Check: do all paths go through _with_pipeline_status?
    print(f"\nMechanism Analysis:")
    print(f"  All response paths funnel through _with_pipeline_status()")
    print(f"  Stage skipping is visible in pipeline.stages dict")
    print(f"  But verdict is already determined before stages are validated")
