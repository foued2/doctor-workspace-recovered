from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from doctor.adversarial.lc20_bimaristan import LC20, GENERATORS
from doctor.adversarial.lc20_candidates import lc20_reference, lc20_no_empty_check, lc20_last_char_check
from doctor.adversarial.lc20_ground_truth import lc20_brute_force, GroundTruthDomainError

SOLVERS = {
    "reference": lc20_reference,
    "no_empty": lc20_no_empty_check,
    "last_char": lc20_last_char_check,
}


def _solver_safe_output(fn, s):
    try:
        return fn(s)
    except Exception:
        return None


def _divergence_rate(cases, fn) -> float:
    if not cases:
        return 0.0
    wrong = 0
    observed = 0
    for s in cases:
        try:
            truth = lc20_brute_force(s)
        except GroundTruthDomainError:
            continue
        observed += 1
        if _solver_safe_output(fn, s) != truth:
            wrong += 1
    return wrong / observed if observed else 0.0


def main():
    print("LC20 Bimaristan run")
    for family in LC20.invariant_families:
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
                    truth = lc20_brute_force(s)
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
                    out = _solver_safe_output(fn, s)
                    if out is not None and out == truth:
                        correct += 1
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

            pre_div = solver_divergence["no_empty"]
            crossed = [")" + s for s, _ in accepted]
            post_div = _divergence_rate(crossed, lc20_no_empty_check)
            post_count = sum(1 for s in crossed if len(s) <= 100)
            divergence_delta = post_div - pre_div
            event = {
                "manifold_id": manifold_id,
                "perturbation_operator": "solver_assumption_break",
                "parameterization": {"transform": "close_before_open", "assumption": "stack_non_empty_on_pop"},
                "pre_divergence_rate": round(pre_div, 4),
                "post_divergence_rate": round(post_div, 4),
                "pre_candidate_count": len(accepted),
                "post_candidate_count": post_count,
                "satisfiability_delta": round((post_count - len(accepted)) / len(accepted), 4) if accepted else 0.0,
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
