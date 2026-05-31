"""
Test: Partial artifact pre-verdict protection.

Verifies that artifacts are NOT written when the final verdict 
will be something other than a valid induction candidate.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'F:/pythonProject1')

from doctor.pipeline import run_pipeline
from doctor.candidates.artifact_writer import PENDING_DIR

def test_artifact_not_written_for_incorrect_verdict():
    """Artifact should NOT be written for incorrect solutions on unrecognized problems."""
    print("=== Test: Partial Artifact Pre-Verdict Protection ===")
    
    # Unrecognized problem with wrong solution
    # Should get UBE verdict, but induction might be eligible
    # Artifact should NOT be written because the solution is wrong
    code = "def solution(nums, target):\n    return [99, 99]"  # Always wrong
    
    # Count artifacts before
    pending_before = list(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
    
    result = run_pipeline(
        statement="Given a list of numbers and a target, find two numbers that sum to target.",
        solution_code=code,
    )
    
    # Count artifacts after
    pending_after = list(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
    
    verdict = result.get("verdict")
    induction_eligible = result.get("induction_result", {}).get("eligible")
    
    print(f"  verdict={verdict}")
    print(f"  induction_eligible={induction_eligible}")
    print(f"  artifacts before={len(pending_before)}, after={len(pending_after)}")
    
    # Artifacts should NOT increase for wrong solutions
    if len(pending_after) > len(pending_before):
        print("  VIOLATION: Artifact written for wrong solution!")
        return True  # violation
    
    print("  No artifacts written for wrong solution. PASS.")
    return False  # no violation


def test_artifact_written_only_for_eligible():
    """Artifact should only be written when induction is eligible."""
    print("\n=== Test: Artifact Only For Eligible Induction ===")
    
    # Use a code that will be executable but unrecognized
    code = "def solution(x):\n    return x"  # Simple identity
    
    pending_before = list(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
    
    result = run_pipeline(
        statement="Given an integer n, return the nth value in the fibonacci sequence.",
        solution_code=code,
    )
    
    pending_after = list(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
    
    verdict = result.get("verdict")
    induction_eligible = result.get("induction_result", {}).get("eligible")
    
    print(f"  verdict={verdict}")
    print(f"  induction_eligible={induction_eligible}")
    print(f"  artifacts before={len(pending_before)}, after={len(pending_after)}")
    
    if induction_eligible:
        if len(pending_after) <= len(pending_before):
            print("  VIOLATION: Eligible induction but no artifact written!")
            return True
        print("  Artifact written for eligible induction. PASS.")
    else:
        if len(pending_after) > len(pending_before):
            print("  VIOLATION: Artifact written for ineligible induction!")
            return True
        print("  No artifact for ineligible induction. PASS.")
    
    return False


if __name__ == "__main__":
    violations = []
    
    if test_artifact_not_written_for_incorrect_verdict():
        violations.append("Artifact written for wrong solution")
    
    if test_artifact_written_only_for_eligible():
        violations.append("Artifact eligibility mismatch")
    
    print("\n" + "=" * 50)
    if violations:
        print(f"FAILURES: {len(violations)}")
        for v in violations:
            print(f"  - {v}")
    else:
        print("All tests passed.")
    print("=" * 50)
