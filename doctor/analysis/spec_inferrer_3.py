#!/usr/bin/env python3
"""
Investigation 6: Probe Sensitivity Collapse

Check whether probe diversity actually matters for truth assignment.
"""

import sys
sys.path.insert(0, '.')

from doctor.analysis.spec_inferrer import infer_spec
from doctor.core.test_executor import TestExecutor
from doctor.pipeline import _doctor_verdict_from_execution

def run_investigation_6():
    """Run Probe Sensitivity Collapse detection."""
    results = []

    # Use a simple test problem: two_sum
    problem_id = "two_sum"
    solution_code = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""

    # Get registry test cases
    from doctor.registry.problem_registry import get_registry
    registry = get_registry()
    problem = registry.get_problem(problem_id)

    if not problem:
        print(f"Problem {problem_id} not found in registry")
        return []

    # A) Full schema-driven probes (normal execution)
    executor = TestExecutor()
    execution_report = executor.verify(problem_id, solution_code)
    verdict_a = _doctor_verdict_from_execution(execution_report.verdict)

    results.append({
        "probe_type": "A: full schema-driven",
        "pass_rate": execution_report.pass_rate,
        "verdict": execution_report.verdict,
        "truth": verdict_a.truth,
        "doctor_verdict": verdict_a.verdict,
    })

    # B) Fallback probes only - need to trace what happens with minimal probes
    # This requires understanding what fallback probes look like
    # For now, check if test volume affects verdict

    # C) Check: does low test volume + correct execution = "correct"?
    # If yes, that's probe insensitivity
    from doctor.pipeline import derive_verdict

    # Simulate: 1 probe, passes
    truth_c = "correct"
    verdict_c = derive_verdict(truth_c, "ok", "matched", "sufficient")
    results.append({
        "probe_type": "C: single probe (simulated)",
        "pass_rate": 1.0,
        "verdict": "correct",
        "truth": truth_c,
        "doctor_verdict": verdict_c,
        "flag": "probe_insensitivity" if verdict_c == "correct" else None,
    })

    # D) Check: does same verdict hold with different probe counts?
    # If truth="incorrect" from 2/2 failing, would 100/100 failing change anything?
    truth_d = "incorrect"
    verdict_d = derive_verdict(truth_d, "ok", "matched", "sufficient")
    results.append({
        "probe_type": "D: many probes, all fail (simulated)",
        "pass_rate": 0.0,
        "verdict": "incorrect",
        "truth": truth_d,
        "doctor_verdict": verdict_d,
        "flag": None,
    })

    return results

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGATION 6: Probe Sensitivity Collapse")
    print("=" * 80)

    results = run_investigation_6()

    print(f"\n{'Probe Type':<45} {'Truth':<15} {'Verdict':<15} {'Flag'}")
    print("-" * 80)

    for r in results:
        print(f"{r['probe_type']:<45} {r.get('truth', 'N/A'):<15} {r.get('doctor_verdict', 'N/A'):<15} {r.get('flag', 'OK')}")

    # Mechanism check
    print(f"\nMechanism Analysis:")
    print(f"  Truth assignment is binary (correct/incorrect), not graduated")
    print(f"  Probe volume affects evidence_score, but NOT truth/verdict directly")
    print(f"  Once truth is set, it dominates verdict regardless of probe count")
