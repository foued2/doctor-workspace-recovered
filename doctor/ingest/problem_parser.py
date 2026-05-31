#!/usr/bin/env python3
"""
Run ADV-03 and capture full pipeline trace.

ADV-03: Composite adversarial test stacking four weaknesses:
1. Weak schema - thin problem statement
2. Class ambiguity - signature matches multiple registry problems
3. Constant output solution - always returns 0
4. Partial agreement - some checkers pass, some fail

Expected: insufficient_evidence OR unverifiable
FAIL: Doctor returns correct or any confident positive verdict
"""

import sys
import json
sys.path.insert(0, '.')

from doctor.ingest.problem_parser import parse_problem_statement
from doctor.ingest.registry_matcher import match_to_registry
from doctor.pipeline import _doctor_verdict_from_execution, _with_pipeline_status
from doctor.analysis.spec_inferrer import infer_spec
from doctor.analysis.agreement import compute_agreement_multi, AgreementResult
from doctor.core.test_executor import TestExecutor

def run_adv03():
    """Run ADV-03 with full tracing."""

    print("=" * 80)
    print("ADV-03 COMPOSITE ADVERSARIAL TEST")
    print("=" * 80)

    # Test case definition
    statement = "Given a list of numbers, return the count."
    solution_code = "def solve(nums): return 0\n"

    trace = {
        'test_id': 'ADV-03',
        'statement': statement,
        'solution_code': solution_code,
        'expected_verdict': 'insufficient_evidence OR unverifiable',
        'fail_condition': 'correct or confident positive verdict',
    }

    print(f"\nStatement: {statement}")
    print(f"Solution: {solution_code.strip()}")

    # Stage 1: Parse problem statement
    print("\n" + "-" * 40)
    print("STAGE 1: PARSE PROBLEM STATEMENT")
    print("-" * 40)

    model = parse_problem_statement(statement)
    trace['parse_model'] = model

    print(f"Parsed model keys: {list(model.keys())}")
    print(f"Source statement: {model.get('source_statement', 'N/A')}")
    print(f"Input type: {model.get('input_type', 'N/A')}")
    print(f"Output type: {model.get('output_type', 'N/A')}")

    # Stage 2: Matcher decision
    print("\n" + "-" * 40)
    print("STAGE 2: MATCHER DECISION")
    print("-" * 40)

    match_id, reason, match_trace = match_to_registry(model)
    trace['matcher'] = {
        'match_id': match_id,
        'reason': reason,
        'trace': match_trace,
    }

    print(f"Match ID: {match_id}")
    print(f"Reason: {reason}")
    print(f"Alignment score: {match_trace.get('alignment_score', 'N/A')}")
    print(f"Second best: {match_trace.get('second_best_score', 'N/A')}")
    print(f"Decision: {match_trace.get('decision', 'N/A')}")

    # Stage 3: Truth assignment (execution)
    print("\n" + "-" * 40)
    print("STAGE 3: TRUTH ASSIGNMENT (EXECUTION)")
    print("-" * 40)

    if match_id:
        # Run against matched problem's test cases
        executor = TestExecutor()
        execution_report = executor.verify(match_id, solution_code)
        trace['execution'] = {
            'verdict': execution_report.verdict,
            'passed': execution_report.passed,
            'total': execution_report.total,
            'pass_rate': execution_report.pass_rate,
        }

        print(f"Matched problem: {match_id}")
        print(f"Execution verdict: {execution_report.verdict}")
        print(f"Pass rate: {execution_report.pass_rate:.2%} ({execution_report.passed}/{execution_report.total})")

        # Get truth from execution
        doctor_verdict = _doctor_verdict_from_execution(execution_report.verdict)
        trace['truth_assignment'] = {
            'truth': doctor_verdict.truth,
            'verdict': doctor_verdict.verdict,
            'epistemic': doctor_verdict.epistemic,
        }

        print(f"Truth: {doctor_verdict.truth}")
        print(f"Doctor verdict: {doctor_verdict.verdict}")
        print(f"Epistemic: {doctor_verdict.epistemic}")

    else:
        print("No match found - unrecognized path")
        trace['execution'] = {'verdict': 'no_match'}
        trace['truth_assignment'] = {'truth': None, 'verdict': 'unrecognized', 'epistemic': 'inconclusive'}

    # Stage 4: Agreement result
    print("\n" + "-" * 40)
    print("STAGE 4: AGREEMENT RESULT")
    print("-" * 40)

    # Build test results for agreement
    if match_id and execution_report:
        from doctor.registry.problem_registry import get_problems
        problems = get_problems()
        problem = problems.get(match_id)

        if problem:
            test_cases = problem.get('test_cases', [])
            test_results = []
            for tc in test_cases:
                input_args = tc.get('input')
                expected = tc.get('expected_output')
                # Run solution
                test_results.append((0, input_args))  # Constant output is 0

            # Get spec bundles
            from doctor.analysis.spec_inferrer import SpecBundle
            spec_bundles = [
                SpecBundle(problem_id=match_id, expected_output_type='integer',
                          expected_values=[], expected_exceptions=[''],
                          confidence=1.0, source='registry'),
            ]

            agreement = compute_agreement_multi(spec_bundles, test_results)
            trace['agreement'] = {
                'verdict': agreement.verdict,
                'agreeing_specs': agreement.agreeing_specs,
                'total_specs': agreement.total_specs,
                'dominant_source': agreement.dominant_source,
            }

            print(f"Agreement verdict: {agreement.verdict}")
            print(f"Agreeing specs: {agreement.agreeing_specs}/{agreement.total_specs}")
            print(f"Dominant source: {agreement.dominant_source}")

    # Stage 5: Final verdict with oracle override
    print("\n" + "-" * 40)
    print("STAGE 5: FINAL VERDICT (with oracle override)")
    print("-" * 40)

    # Build response for _with_pipeline_status
    response = {
        'doctor_verdict': doctor_verdict,
        'trace': {'oracle_state': {'decidability': 'unknown', 'constructibility': 'constructible'}},
        'reason': 'ADV-03 composite test',
    }

    final_response = _with_pipeline_status(response)
    final_dv = final_response.get('doctor_verdict')

    if isinstance(final_dv, dict):
        final_verdict = final_dv.get('verdict')
        final_truth = final_dv.get('truth')
        final_epistemic = final_dv.get('epistemic')
    else:
        final_verdict = final_dv.verdict
        final_truth = final_dv.truth
        final_epistemic = final_dv.epistemic

    trace['final'] = {
        'verdict': final_verdict,
        'truth': final_truth,
        'epistemic': final_epistemic,
    }

    print(f"Final verdict: {final_verdict}")
    print(f"Final truth: {final_truth}")
    print(f"Final epistemic: {final_epistemic}")

    # Evaluation
    print("\n" + "=" * 80)
    print("EVALUATION")
    print("=" * 80)

    confident_positives = ['correct', 'insufficient_evidence']  # sufficient evidence cases
    if final_verdict == 'correct':
        trace['result'] = 'FAIL'
        print(f"\n[FAIL] ADV-03 FAILED!")
        print(f"  Doctor returned '{final_verdict}' - a confident positive verdict")
        print(f"  This means the composite adversarial setup was NOT caught")
    else:
        trace['result'] = 'PASS'
        print(f"\n[PASS] ADV-03 passed")
        print(f"  Doctor returned '{final_verdict}' - not a confident positive verdict")
        print(f"  Composite adversarial setup was properly handled")

    # Analysis: which layer(s) failed?
    print("\n" + "-" * 40)
    print("LAYER ANALYSIS: What failed to catch constant output?")
    print("-" * 40)

    layers_failed = []

    if match_id:
        layers_failed.append(f"Matcher: matched to '{match_id}' (weak schema issue)")
    else:
        print("Matcher: correctly rejected (no match)")

    if execution_report and execution_report.pass_rate > 0:
        layers_failed.append(f"Execution: {execution_report.pass_rate:.0%} pass rate (constant output passed some tests)")
    else:
        print("Execution: constant output caught (0% pass rate)")

    if agreement and agreement.verdict != 'FAIL':
        layers_failed.append(f"Agreement: {agreement.verdict} (not FAIL)")

    if layers_failed:
        print("\nLayers that failed to catch constant output:")
        for layer in layers_failed:
            print(f"  - {layer}")
    else:
        print("\nAll layers properly caught the constant output")

    # Check if partial agreement was silenced
    print("\n" + "-" * 40)
    print("AGREEMENT SIGNAL ANALYSIS")
    print("-" * 40)

    if 'agreement' in trace:
        if trace['agreement']['verdict'] == 'INCONCLUSIVE':
            print("Partial agreement surfaced as INCONCLUSIVE")
        else:
            print(f"Agreement verdict: {trace['agreement']['verdict']}")
            print("Check if this was properly surfaced in final verdict")

    return trace

if __name__ == "__main__":
    trace = run_adv03()

    # Save trace to file
    trace_file = "F:/pythonProject1/scratch/adv03_trace.json"
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2, default=str)
    print(f"\nFull trace saved to: {trace_file}")
