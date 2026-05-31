from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc42_synthesizer import evaluate_lc42_candidates, synthesize_lc42_inputs


def main() -> None:
    batch = synthesize_lc42_inputs()
    evaluations = evaluate_lc42_candidates(batch)

    total = len(batch.accepted) + len(batch.rejected)
    rejection_rate = len(batch.rejected) / total * 100 if total else 0.0

    print("LC42 Bimaristan native run")
    print("Generated candidates per GeometryGenerator:")
    print(f"  {batch.generator_id}: {len(batch.accepted)}")
    print("Rejection rate per GeometryGenerator:")
    print(f"  {batch.generator_id}: {rejection_rate:.2f}%")
    print("SynthesisYieldWarnings:")
    print(f"  {batch.warning if batch.warning else 'none'}")
    print("Per-candidate results:")
    for result in evaluations:
        candidate_total = result.accepted_count + result.rejected_count
        acceptance_rate = result.accepted_count / candidate_total * 100 if candidate_total else 0.0
        candidate_rejection_rate = result.rejected_count / candidate_total * 100 if candidate_total else 0.0
        print(f"  {result.candidate_name}:")
        print(f"    Acceptance rate: {acceptance_rate:.2f}% ({result.accepted_count}/{candidate_total})")
        print(f"    Rejection rate: {candidate_rejection_rate:.2f}% ({result.rejected_count}/{candidate_total})")
        print(f"    Violated predicates: {list(result.violated_predicate_ids) if result.violated_predicate_ids else 'none'}")
        print(f"    Synthesis warnings: {list(result.warnings) if result.warnings else 'none'}")
        if result.false_pass_inputs:
            print("    FALSE PASS:")
            for arr in result.false_pass_inputs:
                print(f"      {list(arr)}")
        else:
            print("    FALSE PASS: none")


if __name__ == "__main__":
    main()
