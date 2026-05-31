#!/usr/bin/env python3
"""
Investigation D1/C1 -- Unrecognized Path Verdict Quality
"""

import sys
import json
sys.path.insert(0, '.')

from doctor.pipeline import run_pipeline

def run_case(case_id, statement, solution_code):
    print("\n" + "-"*80)
    print("CASE: " + case_id)
    print("-"*80)
    print("Statement: " + statement)
    print("Solution: " + solution_code.strip())

    result = run_pipeline(
        statement=statement,
        solution_code=solution_code,
        problem_id=None,
    )

    matched = result.get('matched')
    recognition = result.get('recognition_decision')
    doctor_verdict = result.get('doctor_verdict', {})
    final_verdict = result.get('verdict')
    pass_rate = result.get('pass_rate')

    if isinstance(doctor_verdict, dict):
        truth = doctor_verdict.get('truth')
        epistemic = doctor_verdict.get('epistemic')
    else:
        truth = getattr(doctor_verdict, 'truth', None)
        epistemic = getattr(doctor_verdict, 'epistemic', None)

    trace = result.get('trace', {})
    oracle_state = trace.get('oracle_state', {})

    # Check induction result for constant output flag
    induction = result.get('induction_result', {})
    constant_flagged = induction.get('rejection_reason') == 'constant_output'

    print("\nRESULTS:")
    print("  Matcher: " + str(matched) + " (" + str(recognition) + ")")
    print("  Oracle state: " + str(oracle_state))
    print("  Truth: " + str(truth))
    print("  Epistemic: " + str(epistemic))
    print("  Pass rate: " + str(pass_rate))
    print("  Final verdict: " + str(final_verdict))
    print("  Constant output flagged: " + str(constant_flagged))

    # Check actionable signal
    actionable = False
    if final_verdict in ('unrecognized_but_executable', 'insufficient_evidence'):
        if constant_flagged:
            actionable = True

    print("  Actionable signal: " + str(actionable))

    return {
        'case': case_id,
        'matcher': matched,
        'truth': truth,
        'epistemic': epistemic,
        'final_verdict': final_verdict,
        'constant_flagged': constant_flagged,
        'actionable': actionable,
    }

def main():
    print("-"*80)
    print("INVESTIGATION D1/C1 -- UNRECOGNIZED PATH VERDICT QUALITY")
    print("-"*80)

    # Case 1: Constant string output
    case1 = run_case(
        "Case 1: Constant string output",
        "Given a string, return the most frequent character.",
        'def solve(s): return "a"\n'
    )

    # Case 2: Constant integer output
    case2 = run_case(
        "Case 2: Constant integer output",
        "Given a grid, find the shortest path.",
        "def solve(grid): return 0\n"
    )

    # Summary
    print("\n" + "-"*80)
    print("SUMMARY")
    print("-"*80)

    for case in [case1, case2]:
        print("\n" + case['case'] + ":")
        print("  Verdict: " + str(case['final_verdict']))
        print("  Constant output flagged: " + str(case['constant_flagged']))
        print("  Actionable signal: " + str(case['actionable']))

    # Save results
    with open('F:/pythonProject1/scratch/d1_c1_results.json', 'w') as f:
        json.dump([case1, case2], f, indent=2, default=str)
    print("\nFull results saved to: F:/pythonProject1/scratch/d1_c1_results.json")

if __name__ == "__main__":
    main()
