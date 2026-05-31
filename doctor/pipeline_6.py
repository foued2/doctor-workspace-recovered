#!/usr/bin/env python3
"""
Investigation 5: Unrecognized Path Leakage (D1/C1 expansion)

Detects leakage from unrecognized → incorrect/correct boundary.
"""

import sys
sys.path.insert(0, '.')

from doctor.pipeline import _doctor_verdict, derive_verdict, _with_pipeline_status
from doctor.analysis.spec_inferrer import infer_spec

def run_investigation_5():
    """Run Unrecognized Path Leakage detection."""

    results = []

    # Case 1: Unrecognized with constant output, no checker
    # Simulates: executable code, constant outputs, checker=None
    truth = None  # No execution for unrecognized
    system_state = "ok"
    recognition = "unrecognized"
    epistemic = "inconclusive"  # No grounding

    verdict = derive_verdict(truth, system_state, recognition, epistemic)
    dv = _doctor_verdict(truth, system_state, recognition, epistemic)

    results.append({
        "case": "unrecognized + constant output + no checker",
        "truth": truth,
        "system_state": system_state,
        "recognition": recognition,
        "epistemic": epistemic,
        "verdict": verdict,
        "expected": "unrecognized_but_executable or insufficient_evidence",
        "flag": None if verdict in ("unrecognized_but_executable", "insufficient_evidence") else "verdict_boundary_leak",
    })

    # Case 2: Unrecognized with executable code, weak checker, partial pass
    truth = None
    system_state = "ok"
    recognition = "unrecognized"
    epistemic = "insufficient"

    verdict = derive_verdict(truth, system_state, recognition, epistemic)
    dv = _doctor_verdict(truth, system_state, recognition, epistemic)

    results.append({
        "case": "unrecognized + weak checker + partial pass",
        "truth": truth,
        "system_state": system_state,
        "recognition": recognition,
        "epistemic": epistemic,
        "verdict": verdict,
        "expected": "insufficient_evidence",
        "flag": None if verdict == "insufficient_evidence" else "verdict_boundary_leak",
    })

    # Case 3: Unrecognized but code executes correctly against something
    # This shouldn't produce "correct" without oracle grounding
    truth = "correct"  # Hypothetical
    system_state = "ok"
    recognition = "unrecognized"
    epistemic = "not_evaluated"

    verdict = derive_verdict(truth, system_state, recognition, epistemic)
    # But oracle override should catch this
    response = {
        "doctor_verdict": _doctor_verdict(truth, system_state, recognition, epistemic),
        "trace": {"oracle_state": {"decidability": "unknown"}},
    }
    response = _with_pipeline_status(response)

    results.append({
        "case": "unrecognized + correct execution + weak oracle",
        "truth": truth,
        "system_state": system_state,
        "recognition": recognition,
        "epistemic": epistemic,
        "verdict": response.get("verdict"),
        "expected": "unverifiable",
        "flag": None if response.get("verdict") == "unverifiable" else "verdict_boundary_leak",
    })

    return results

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGATION 5: Unrecognized Path Leakage")
    print("=" * 80)

    results = run_investigation_5()

    print(f"\n{'Case':<50} {'Verdict':<25} {'Expected':<30} {'Flag'}")
    print("-" * 110)

    for r in results:
        print(f"{r['case']:<50} {r['verdict']:<25} {r['expected']:<30} {r['flag'] or 'OK'}")

    # Summary
    flags = [r['flag'] for r in results if r['flag']]
    print(f"\nSummary: {len(flags)} verdict boundary leaks found")
    for f in set(flags):
        print(f"  - {f}")
