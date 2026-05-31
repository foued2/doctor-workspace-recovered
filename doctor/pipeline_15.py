#!/usr/bin/env python3
"""
Run ADV-03: Composite Adversarial Test with full pipeline trace.

Stacking four weaknesses:
1. Weak schema - thin statement
2. Class ambiguity - signature matches multiple registry problems
3. Constant output - always returns 0
4. Partial agreement - some checkers pass, some fail
"""

import sys
import json
sys.path.insert(0, '.')

from doctor.pipeline import run_pipeline

def run_adv03():
    """Run ADV-03 through full pipeline and capture trace."""

    print("=" * 80)
    print("ADV-03 COMPOSITE ADVERSARIAL TEST")
    print("=" * 80)

    statement = "Given a list of integers and a target value, find two numbers that sum to the target and return their positions."
    solution_code = "def solve(nums, target): return [0, 1]\n"

    print(f"\nStatement: {statement}")
    print(f"Solution: {solution_code.strip()}")

    # Run through full pipeline
    print("\n" + "-" * 80)
    print("RUNNING FULL PIPELINE...")
    print("-" * 80 + "\n")

    result = run_pipeline(
        statement=statement,
        solution_code=solution_code,
        problem_id=None,  # Forces unrecognized path initially
    )

    # Extract trace information
    print("PIPELINE TRACE:")
    print("-" * 80)

    # 1. Matcher decision
    matched = result.get('matched')
    recognition = result.get('recognition_decision')
    print(f"\n1. MATCHER DECISION:")
    print(f"   Matched ID: {matched}")
    print(f"   Recognition: {recognition}")

    trace = result.get('trace', {})
    oracle_state = trace.get('oracle_state', {})
    print(f"   Oracle state: {oracle_state}")

    # 2. Execution/Truth assignment
    doctor_verdict = result.get('doctor_verdict', {})
    if isinstance(doctor_verdict, dict):
        truth = doctor_verdict.get('truth')
        verdict = doctor_verdict.get('verdict')
        epistemic = doctor_verdict.get('epistemic')
    else:
        truth = getattr(doctor_verdict, 'truth', None)
        verdict = getattr(doctor_verdict, 'verdict', None)
        epistemic = getattr(doctor_verdict, 'epistemic', None)

    print(f"\n2. TRUTH ASSIGNMENT:")
    print(f"   Truth: {truth}")
    print(f"   Epistemic: {epistemic}")

    # 3. Execution results
    pass_rate = result.get('pass_rate')
    print(f"\n3. EXECUTION:")
    print(f"   Pass rate: {pass_rate}")
    print(f"   Verdict: {verdict}")

    # 4. Agreement (if available)
    promotion_eligible = result.get('promotion_eligible')
    print(f"\n4. AGREEMENT:")
    print(f"   Promotion eligible: {promotion_eligible}")

    # 5. Final verdict
    final_verdict = result.get('verdict')
    print(f"\n5. FINAL VERDICT:")
    print(f"   {final_verdict}")

    # Evaluation
    print("\n" + "=" * 80)
    print("EVALUATION")
    print("=" * 80 + "\n")

    confident_positives = ['correct', 'insufficient_evidence']
    if final_verdict == 'correct':
        status = '[FAIL]'
        explanation = 'Doctor returned confident positive verdict - composite setup was NOT caught'
    elif final_verdict in ('insufficient_evidence', 'unverifiable', 'unrecognized_but_executable'):
        status = '[PASS]'
        explanation = 'Doctor properly handled composite adversarial setup'
    else:
        status = '[INFO]'
        explanation = f'Doctor returned: {final_verdict}'

    print(f"{status} ADV-03")
    print(f"  {explanation}")

    # Layer analysis
    print(f"\nLAYER ANALYSIS: Which layer(s) failed to catch constant output?")
    print("-" * 80)

    layers_failed = []

    if matched:
        layers_failed.append(f"Matcher: matched to '{matched}' (weak schema issue)")
    else:
        print("Matcher: correctly did not match (unrecognized)")

    if pass_rate and pass_rate > 0:
        layers_failed.append(f"Execution: {pass_rate:.0%} pass rate (constant output passed some tests)")
    else:
        print("Execution: constant output caught (0% pass rate)")

    if layers_failed:
        print("\nLayers that failed to catch constant output:")
        for layer in layers_failed:
            print(f"  - {layer}")
    else:
        print("\nAll layers properly caught the constant output")

    # Save full trace
    trace_file = "F:/pythonProject1/scratch/adv03_trace.json"
    with open(trace_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nFull trace saved to: {trace_file}")

    return result

if __name__ == "__main__":
    result = run_adv03()
