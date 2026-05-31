from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from doctor.adversarial.cf2227h_bimaristan import CF2227H, GENERATORS
from doctor.adversarial.cf2227h_candidates import (
    cf2227h_reference,
    cf2227h_greedy_nearest,
    cf2227h_greedy_farthest,
    cf2227h_dfs_order,
)
from doctor.adversarial.cf2227h_ground_truth import cf2227h_brute_force, GroundTruthDomainError

SOLVERS = {
    "reference": cf2227h_reference,
    "greedy_nearest": cf2227h_greedy_nearest,
    "greedy_farthest": cf2227h_greedy_farthest,
    "dfs_order": cf2227h_dfs_order,
}


def _solver_safe_output(fn, n, edges):
    try:
        return fn(n, edges)
    except Exception:
        return None


def main():
    print("CF 2227H Bimaristan run")
    for family in CF2227H.invariant_families:
        for manifold in family.failure_manifolds:
            manifold_id = manifold.manifold_id
            gen_fn = GENERATORS.get(manifold_id)
            if gen_fn is None:
                continue

            inputs = gen_fn()
            accepted = []
            rejected = 0

            for n, edges in inputs:
                try:
                    truth = cf2227h_brute_force(n, edges)
                    accepted.append((n, edges, truth))
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
                for n, edges, truth in accepted:
                    out = _solver_safe_output(fn, n, edges)
                    if out is not None and out == truth:
                        correct += 1
                solver_correct[name] = correct
                solver_divergence[name] = (len(accepted) - correct) / len(accepted) if accepted else 0.0

            print(f"Manifold: {manifold_id}")
            print(f"  Candidates generated: {len(accepted)}")
            print(f"  Rejection rate: {rejection_rate:.2f}%")

            for name in SOLVERS:
                div_rate = solver_divergence[name] * 100
                corr = solver_correct[name]
                print(f"  {name} divergence rate: {div_rate:.2f}%")
                print(f"  {name} agrees with truth: {corr}/{len(accepted)}")

            divergence_delta = (
                solver_divergence.get("greedy_farthest", 0.0)
                - solver_divergence.get("greedy_nearest", 0.0)
            )
            event = {
                "manifold_id": manifold_id,
                "perturbation_operator": "solver_assumption_break",
                "parameterization": {"manifold": manifold_id},
                "pre_divergence_rate": round(solver_divergence.get("greedy_nearest", 0.0), 4),
                "post_divergence_rate": round(solver_divergence.get("greedy_farthest", 0.0), 4),
                "pre_candidate_count": len(accepted),
                "post_candidate_count": len(accepted),
                "satisfiability_delta": 0.0,
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
