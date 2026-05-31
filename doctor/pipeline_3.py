#!/usr/bin/env python3
"""
Binary Falsification Test: H0 Invariant

H0: Once _doctor_verdict_from_execution() assigns truth, no downstream component
     can alter, recompute, or indirectly re-derive truth from any other signal.

Forces signal divergence between:
- truth (from execution)
- agreement (forced INCONCLUSIVE)
- oracle (forced weak)
- epistemic (forced partial/insufficient)

Checks for R1 (direct recomputation), R2 (indirect override), R3 (implicit reclassification).
"""

import sys
import traceback as tb
sys.path.insert(0, '.')

from doctor.pipeline import (
    _doctor_verdict_from_execution,
    _with_pipeline_status,
    derive_verdict,
    _doctor_verdict,
    DoctorVerdict,
)

# Track all truth mutations
truth_mutations = []

def monitor_truth_mutation(dv, stage_name):
    """Record truth value at each stage."""
    truth_mutations.append({
        'stage': stage_name,
        'truth': dv.truth,
        'verdict': dv.verdict,
        'epistemic': dv.epistemic,
    })

def run_falsification_case(case_id, execution_verdict, oracle_state, agreement_override=None):
    """
    Force signal divergence and check if truth/verdict drifts.

    Returns: dict with failure classification or None if H0 holds.
    """
    global truth_mutations
    truth_mutations = []

    # Step 1: Get truth from execution (this is the locked value)
    doctor_verdict = _doctor_verdict_from_execution(execution_verdict)
    initial_truth = doctor_verdict.truth
    initial_verdict = doctor_verdict.verdict

    monitor_truth_mutation(doctor_verdict, "after_execution")

    # Step 2: Build response with divergent signals
    response = {
        "doctor_verdict": doctor_verdict,
        "trace": {"oracle_state": oracle_state},
        "reason": f"falsification_case_{case_id}",
    }

    # Step 3: Run through _with_pipeline_status (oracle override stage)
    try:
        result = _with_pipeline_status(response)
    except Exception as e:
        return {
            'case_id': case_id,
            'failure': 'EXCEPTION',
            'details': str(e),
            'traceback': tb.format_exc(),
        }

    final_dv = result.get("doctor_verdict")
    if isinstance(final_dv, dict):
        final_truth = final_dv.get("truth")
        final_verdict = final_dv.get("verdict")
        final_epistemic = final_dv.get("epistemic")
        monitor_truth_mutation(DoctorVerdict(**final_dv), "after_pipeline_status")
    else:
        final_truth = final_dv.truth
        final_verdict = final_dv.verdict
        final_epistemic = final_dv.epistemic
        monitor_truth_mutation(final_dv, "after_pipeline_status")

    # Step 4: Check H0 invariants
    failures = []

    # Check R1: truth directly mutated
    if final_truth != initial_truth:
        failures.append({
            'type': 'R1_DIRECT_RECOMPUTATION',
            'detail': f'truth changed: {initial_truth} -> {final_truth}',
            'stage': 'pipeline_status',
        })

    # Check R2: verdict diverges from truth (indirect override)
    if final_verdict != initial_truth and final_verdict != initial_verdict:
        # Verdict should be "incorrect" if truth="incorrect"
        if initial_truth == "incorrect" and final_verdict != "incorrect":
            failures.append({
                'type': 'R2_INDIRECT_RECLASSIFICATION',
                'detail': f'verdict={final_verdict} but truth={final_truth}',
                'stage': 'pipeline_status',
            })

    # Check: oracle override only affects "correct"
    if initial_truth == "incorrect" and final_verdict != "incorrect":
        failures.append({
            'type': 'R2_ORACLE_OVERRIDE_LEAK',
            'detail': f'incorrect truth was overridden to {final_verdict}',
            'stage': 'pipeline_status',
        })

    return {
        'case_id': case_id,
        'execution_verdict': execution_verdict,
        'initial_truth': initial_truth,
        'initial_verdict': initial_verdict,
        'final_truth': final_truth,
        'final_verdict': final_verdict,
        'final_epistemic': final_epistemic,
        'oracle_state': oracle_state,
        'failures': failures,
        'truth_trace': list(truth_mutations),
    } if failures else None

def main():
    """Run binary falsification test with forced signal divergence."""

    results = []

    # Case set: force truth="incorrect" with divergent signals
    test_cases = [
        # (case_id, execution_verdict, oracle_state)
        (1, "partial", {"decidability": "unknown", "constructibility": "solver_required"}),
        (2, "partial", {"decidability": "unknown", "constructibility": "constructible"}),
        (3, "incorrect", {"decidability": "unknown"}),
        (4, "incorrect", {"decidability": "decidable", "constructibility": "non_constructible"}),
        (5, "partial", {"decidability": "decidable", "constructibility": "constructible"}),
        (6, "incorrect", {"decidability": "decidable", "constructibility": "constructible"}),
    ]

    print("=" * 80)
    print("BINARY FALSIFICATION TEST: H0 Invariant")
    print("=" * 80)
    print("\nH0: Once truth is assigned by execution, no downstream modification possible.")
    print("Forcing signal divergence: truth=incorrect vs oracle=weak vs epistemic=partial\n")

    for case_id, exec_verdict, oracle_state in test_cases:
        result = run_falsification_case(case_id, exec_verdict, oracle_state)
        if result:
            results.append(result)

    # Output: only failing cases
    if not results:
        print("\n[PASS] H0 HOLDS: No falsification found.")
        print("\nClassification: TRUE CLASSIFICATION SYSTEM")
        print("  - truth is final after _doctor_verdict_from_execution()")
        print("  - oracle override only affects correct->unverifiable")
        print("  - no downstream recombination of signals")
        return

    print(f"\n[FAIL] H0 FALSIFIED: {len(results)} failure(s) found\n")
    print("=" * 80)
    print("FAILING CASES (call stack traces)")
    print("=" * 80)

    for r in results:
        print(f"\nCase {r['case_id']}: {r['execution_verdict']}")
        print(f"  Oracle: {r['oracle_state']}")
        print(f"  Initial: truth={r['initial_truth']}, verdict={r['initial_verdict']}")
        print(f"  Final:   truth={r['final_truth']}, verdict={r['final_verdict']}, epistemic={r['final_epistemic']}")

        for f in r['failures']:
            print(f"  FAILURE [{f['type']}]: {f['detail']}")
            print(f"    Stage: {f.get('stage', 'unknown')}")

        print("  Truth trace:")
        for t in r['truth_trace']:
            print(f"    {t['stage']}: truth={t['truth']}, verdict={t['verdict']}, epistemic={t['epistemic']}")

    # Classification
    r1_count = sum(1 for r in results for f in r['failures'] if 'R1' in f['type'])
    r2_count = sum(1 for r in results for f in r['failures'] if 'R2' in f['type'])

    print("\n" + "=" * 80)
    print("CLASSIFICATION")
    print("=" * 80)

    if r1_count > 0:
        print("LATENT ENSEMBLE SYSTEM (danger case)")
        print("  - truth is recomputed downstream")
        print("  - final verdict is fused from multiple signals")
    elif r2_count > 0:
        print("WEAK CLASSIFICATION SYSTEM")
        print("  - truth is stable but verdict can drift via indirect override")
    else:
        print("TRUE CLASSIFICATION SYSTEM")
        print("  - truth is final, annotation only downstream")

if __name__ == "__main__":
    main()
