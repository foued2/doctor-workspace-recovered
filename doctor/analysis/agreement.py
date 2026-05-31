#!/usr/bin/env python3
"""
Investigation 1: Agreement–Truth Decoupling Sweep

Detects cases where agreement signal contradicts execution truth but has no effect.
"""

import sys
sys.path.insert(0, '.')

from doctor.analysis.agreement import compute_agreement_multi, AgreementResult
from doctor.analysis.spec_inferrer import SpecBundle
from doctor.pipeline import _doctor_verdict_from_execution

def build_spec_bundle(confidence: float = 1.0, source: str = "test") -> SpecBundle:
    """Build a minimal SpecBundle for testing."""
    return SpecBundle(
        problem_id="test",
        expected_output_type="integer",
        expected_values=[],
        expected_exceptions=[],
        confidence=confidence,
        source=source,
    )

def run_investigation_1():
    """Run Agreement-Truth Decoupling Sweep."""
    results = []

    spec_bundles = [build_spec_bundle(1.0, "registry"), build_spec_bundle(0.8, "inferred")]

    # Case 1: Partial execution (wrong outputs) - should be "incorrect" truth
    test_results_partial = [
        (42, {"input": 5}),   # correct
        (99, {"input": 3}),   # wrong
        (42, {"input": 7}),   # correct
        (99, {"input": 2}),   # wrong
    ]

    agreement = compute_agreement_multi(spec_bundles, test_results_partial)
    doctor_verdict = _doctor_verdict_from_execution("partial")

    flag = None
    if agreement.verdict != "PASS" and doctor_verdict.verdict == "incorrect":
        flag = "no_cross_layer_effect"  # Agreement doesn't affect verdict

    results.append({
        "case": "partial execution (50% pass)",
        "execution_verdict": "partial",
        "agreement_verdict": agreement.verdict,
        "truth": doctor_verdict.truth,
        "verdict": doctor_verdict.verdict,
        "flag": flag,
    })

    # Case 2: Incorrect but consistent outputs (all wrong same value)
    test_results_constant_wrong = [
        (99, {"input": 5}),
        (99, {"input": 3}),
        (99, {"input": 7}),
    ]

    agreement = compute_agreement_multi(spec_bundles, test_results_constant_wrong)
    doctor_verdict = _doctor_verdict_from_execution("incorrect")

    flag = None
    if agreement.verdict == "INCONCLUSIVE" and doctor_verdict.verdict == "incorrect":
        flag = "constant_output_INCONCLUSIVE_but_incorrect"

    results.append({
        "case": "incorrect + constant output",
        "execution_verdict": "incorrect",
        "agreement_verdict": agreement.verdict,
        "truth": doctor_verdict.truth,
        "verdict": doctor_verdict.verdict,
        "flag": flag,
    })

    # Case 3: Correct execution with None outputs (forces INCONCLUSIVE)
    test_results_with_none = [
        (None, {"input": 5}),
        (42, {"input": 3}),
    ]

    agreement = compute_agreement_multi(spec_bundles, test_results_with_none)
    doctor_verdict = _doctor_verdict_from_execution("correct")

    flag = None
    if agreement.verdict == "INCONCLUSIVE" and doctor_verdict.verdict == "correct":
        flag = "INCONCLUSIVE_agreement_but_correct_verdict"

    results.append({
        "case": "correct + None outputs (INCONCLUSIVE agreement)",
        "execution_verdict": "correct",
        "agreement_verdict": agreement.verdict,
        "truth": doctor_verdict.truth,
        "verdict": doctor_verdict.verdict,
        "flag": flag,
    })

    return results

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGATION 1: Agreement–Truth Decoupling Sweep")
    print("=" * 80)

    results = run_investigation_1()

    print(f"\n{'Case':<45} {'Exec':<12} {'Agreement':<15} {'Truth':<15} {'Verdict':<15} {'Flag'}")
    print("-" * 110)

    for r in results:
        print(f"{r['case']:<45} {r['execution_verdict']:<12} {r['agreement_verdict']:<15} {r['truth']:<15} {r['verdict']:<15} {r['flag'] or 'OK'}")

    # Mechanism analysis
    flags = [r['flag'] for r in results if r['flag']]
    print(f"\nMechanism Analysis:")
    if flags:
        print(f"  Cross-layer isolation confirmed: agreement verdict has NO pathway to truth/verdict")
        print(f"  Shared mechanism: agreement layer is advisory-only for matched problems")
    else:
        print(f"  No cross-layer inconsistencies found")
