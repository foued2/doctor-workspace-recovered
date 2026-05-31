from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc997_synthesizer import (
    evaluate_lc997_candidates,
    generator_counts,
    synthesize_lc997_inputs,
)


def main() -> None:
    batch = synthesize_lc997_inputs()
    evaluations = evaluate_lc997_candidates(batch)

    print("LC997 Bimaristan native run")
    print("Generated candidates per GeometryGenerator:")
    for generator_id, accepted, _rejected in generator_counts(batch):
        print(f"  {generator_id}: {accepted}")
    print("Rejection rate per GeometryGenerator:")
    for generator_id, accepted, rejected in generator_counts(batch):
        total = accepted + rejected
        rejection_rate = rejected / total * 100 if total else 0.0
        print(f"  {generator_id}: {rejection_rate:.2f}%")
    print("SynthesisYieldWarnings:")
    if batch.warnings:
        for warning in batch.warnings:
            print(f"  {warning}")
    else:
        print("  none")
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
            for n, trust in result.false_pass_inputs:
                print(f"      n={n}, trust={[list(pair) for pair in trust]}")
        else:
            print("    FALSE PASS: none")


if __name__ == "__main__":
    main()
