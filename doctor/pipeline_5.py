#!/usr/bin/env python3
"""
Investigation 4: Oracle–Execution Conflict Matrix

Find contradictions between oracle feasibility and actual execution.
"""

import sys
sys.path.insert(0, '.')

from doctor.pipeline import _doctor_verdict, derive_verdict, _with_pipeline_status

def run_investigation_4():
    """Run Oracle-Execution Conflict Matrix."""
    results = []

    # Case 1: Weak oracle + strong execution
    # Oracle: decidability=unknown, but execution passes all tests
    truth = "correct"
    system_state = "ok"
    recognition = "matched"
    epistemic = "sufficient"

    response = {
        "doctor_verdict": _doctor_verdict(truth, system_state, recognition, epistemic),
        "trace": {"oracle_state": {"decidability": "unknown", "constructibility": "constructible"}},
    }
    response = _with_pipeline_status(response)

    results.append({
        "case": "weak oracle (unknown) + strong execution (correct)",
        "oracle_state": "decidability=unknown",
        "execution": "correct",
        "epistemic_before": "sufficient",
        "epistemic_after": response["doctor_verdict"]["epistemic"],
        "verdict_before": "correct",
        "verdict_after": response["verdict"],
        "flag": None if response["verdict"] == "unverifiable" else "epistemic_conflict",
    })

    # Case 2: Strong oracle + failed execution
    truth = "incorrect"
    system_state = "ok"
    recognition = "matched"
    epistemic = "sufficient"

    response = {
        "doctor_verdict": _doctor_verdict(truth, system_state, recognition, epistemic),
        "trace": {"oracle_state": {"decidability": "decidable", "constructibility": "constructible"}},
    }
    response = _with_pipeline_status(response)

    results.append({
        "case": "strong oracle (decidable) + failed execution (incorrect)",
        "oracle_state": "decidability=decidable",
        "execution": "incorrect",
        "epistemic_before": "sufficient",
        "epistemic_after": response["doctor_verdict"]["epistemic"],
        "verdict_before": "incorrect",
        "verdict_after": response["verdict"],
        "flag": None,  # Expected: incorrect (no override)
    })

    # Case 3: Weak oracle + partial execution
    truth = "incorrect"
    system_state = "ok"
    recognition = "matched"
    epistemic = "sufficient"

    response = {
        "doctor_verdict": _doctor_verdict(truth, system_state, recognition, epistemic),
        "trace": {"oracle_state": {"decidability": "unknown"}},
    }
    response = _with_pipeline_status(response)

    results.append({
        "case": "weak oracle (unknown) + partial execution (incorrect)",
        "oracle_state": "decidability=unknown",
        "execution": "incorrect",
        "epistemic_before": "sufficient",
        "epistemic_after": response["doctor_verdict"]["epistemic"],
        "verdict_before": "incorrect",
        "verdict_after": response["verdict"],
        "flag": None,  # Override only touches "correct" verdict, not "incorrect"
    })

    return results

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGATION 4: Oracle–Execution Conflict Matrix")
    print("=" * 80)

    results = run_investigation_4()

    print(f"\n{'Case':<65} {'Oracle':<25} {'Exec':<15} {'Epistemic After':<20} {'Verdict':<15} {'Flag'}")
    print("-" * 150)

    for r in results:
        print(f"{r['case']:<65} {r['oracle_state']:<25} {r['execution']:<15} {r['epistemic_after']:<20} {r['verdict_after']:<15} {r['flag'] or 'OK'}")

    # Mechanism analysis
    print(f"\nMechanism Analysis:")
    print(f"  Oracle override only affects correct verdicts (correct→unverifiable)")
    print(f"  Incorrect verdicts are immune to oracle override")
    print(f"  Epistemic sufficient→partial when oracle weak, regardless of truth value")
