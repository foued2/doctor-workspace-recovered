from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from doctor.adversarial.lc997_bimaristan import LC997, GENERATORS
from doctor.adversarial.lc997_candidates import lc997_reference, lc997_no_outdegree_check, lc997_wrong_threshold
from doctor.adversarial.lc997_ground_truth import lc997_brute_force, GroundTruthDomainError

SOLVERS = {
    "reference": lc997_reference,
    "no_outdegree": lc997_no_outdegree_check,
    "wrong_threshold": lc997_wrong_threshold,
}

DIVERGENCE_SOLVERS = ["no_outdegree", "wrong_threshold"]
CORRECT_SOLVERS = ["reference"]


def _add_self_trust_edge(n: int, trust: list[list[int]]) -> tuple[int, list[list[int]]]:
    crossed = [list(edge) for edge in trust]
    if n > 0:
        crossed.append([n, n])
    return n, crossed


def main():
    print("LC997 Bimaristan run")
    for family in LC997.invariant_families:
        for manifold in family.failure_manifolds:
            manifold_id = manifold.manifold_id
            gen_fn = GENERATORS.get(manifold_id)
            if gen_fn is None:
                continue

            inputs = gen_fn()
            accepted = []
            rejected = 0

            for n, trust in inputs:
                try:
                    truth = lc997_brute_force(n, trust)
                    if truth == -1 and manifold_id == "judge_exists_clear":
                        rejected += 1
                        continue
                    accepted.append((n, trust, truth))
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
                for n, trust, truth in accepted:
                    try:
                        if fn(n, trust) == truth:
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

            pre_divergence = solver_divergence["no_outdegree"]
            crossed = [
                _add_self_trust_edge(n, trust)
                for n, trust, _ in accepted[:max(1, len(accepted)//2)]
            ]
            post_wrong = 0
            post_observed = 0
            for n, trust in crossed:
                try:
                    t = lc997_brute_force(n, trust)
                    post_observed += 1
                    if lc997_no_outdegree_check(n, trust) == t:
                        post_wrong += 0
                    else:
                        post_wrong += 1
                except GroundTruthDomainError:
                    post_wrong += 1
            post_count = post_observed
            cross_solver_div = post_wrong / post_observed if post_observed else 0.0
            divergence_delta = cross_solver_div - pre_divergence
            satisfiability_delta = (post_count - len(crossed)) / max(1, len(crossed))

            event = {
                "manifold_id": manifold_id,
                "perturbation_operator": "solver_assumption_break",
                "parameterization": {
                    "transform": "add_self_trust_edge",
                    "assumption": "judge_trusts_nobody",
                },
                "pre_divergence_rate": round(pre_divergence, 4),
                "post_divergence_rate": round(cross_solver_div, 4),
                "pre_candidate_count": len(accepted),
                "post_candidate_count": post_count,
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
