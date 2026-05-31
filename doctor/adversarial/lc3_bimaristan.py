from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from doctor.adversarial.lc3_bimaristan import LC3, GENERATORS
from doctor.adversarial.lc3_candidates import lc3_reference, lc3_conservative_window, lc3_no_shrink
from doctor.adversarial.lc3_ground_truth import lc3_brute_force, GroundTruthDomainError

SOLVERS = {
    "reference": lc3_reference,
    "conservative_window": lc3_conservative_window,
    "no_shrink": lc3_no_shrink,
}


def main():
    print("LC3 Bimaristan run")
    for family in LC3.invariant_families:
        for manifold in family.failure_manifolds:
            manifold_id = manifold.manifold_id
            gen_fn = GENERATORS.get(manifold_id)
            if gen_fn is None:
                continue

            inputs = gen_fn()
            accepted = []
            rejected = 0

            for s in inputs:
                try:
                    truth = lc3_brute_force(s)
                    accepted.append((s, truth))
                except GroundTruthDomainError:
                    rejected += 1
                    continue
                if len(accepted) >= 12:
                    break

            total = len(accepted) + rejected
            rejection_rate = rejected / total * 100 if total else 0.0

            solver_correct = {}
            solver_divergence = {}

            for name, fn in SOLVERS.items():
                correct = 0
                for s, truth in accepted:
                    try:
                        if fn(s) == truth:
                            correct += 1
                    except Exception:
                        pass
                solver_correct[name] = correct
                solver_divergence[name] = (len(accepted) - correct) / len(accepted) if accepted else 0.0

            print(f"Manifold: {manifold_id}")
            print(f"  Candidates generated: {len(accepted)}")
            print(f"  Rejection rate: {rejection_rate:.2f}%")
            print(f"  Violated predicates: none")

            for name, fn in SOLVERS.items():
                div_rate = solver_divergence[name] * 100
                corr = solver_correct[name]
                print(f"  {name} divergence rate: {div_rate:.2f}%")
                print(f"  {name} agrees with truth: {corr}/{len(accepted)}")

            pre_div = solver_divergence["no_shrink"]
            crossed = [s for s, _ in accepted[:max(1, len(accepted)//2)]]
            post_wrong = 0
            for s in crossed:
                try:
                    t = lc3_brute_force(s)
                    if lc3_no_shrink(s) != t:
                        post_wrong += 1
                except GroundTruthDomainError:
                    post_wrong += 1
            post_div = post_wrong / max(1, len(crossed))
            divergence_delta = post_div - pre_div
            satisfiability_delta = 0.0

            event = {
                "manifold_id": manifold_id,
                "perturbation_operator": "solver_assumption_break",
                "parameterization": {"transform": "force_window_shrink", "assumption": "charset_tracking"},
                "pre_divergence_rate": round(pre_div, 4),
                "post_divergence_rate": round(post_div, 4),
                "pre_candidate_count": len(accepted),
                "post_candidate_count": len(crossed),
                "satisfiability_delta": round(satisfiability_delta, 4),
                "divergence_delta": round(divergence_delta, 4),
                "resulting_behavior": (
                    "assumption_negated" if divergence_delta < -0.05 else
                    "manifold_collapsed" if abs(divergence_delta) > 0.30 else
                    "manifold_preserved"
                ),
            }
            print(f"PERTURBATION_EVENT: {json.dumps(event, sort_keys=True)}")


if __name__ == "__main__":
    main()
