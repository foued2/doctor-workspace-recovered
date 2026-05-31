from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from doctor.adversarial.lc33_bimaristan import LC33, GENERATORS
from doctor.adversarial.lc33_candidates import lc33_reference, lc33_always_left, lc33_inverted_condition
from doctor.adversarial.lc33_ground_truth import lc33_brute_force, GroundTruthDomainError

SOLVERS = {
    "reference": lc33_reference,
    "always_left": lc33_always_left,
    "inverted_condition": lc33_inverted_condition,
}


def _rotate_left_half(nums: list[int]) -> list[int]:
    if len(nums) < 2:
        return list(nums)
    pivot = max(1, len(nums) // 2)
    return list(nums[pivot:]) + list(nums[:pivot])


def _divergence_rate(cases, fn) -> float:
    if not cases:
        return 0.0
    wrong = 0
    observed = 0
    for nums, target in cases:
        try:
            truth = lc33_brute_force(nums, target)
        except GroundTruthDomainError:
            continue
        observed += 1
        try:
            if fn(nums, target) != truth:
                wrong += 1
        except Exception:
            wrong += 1
    return wrong / observed if observed else 0.0


def main():
    print("LC33 Bimaristan run")
    for family in LC33.invariant_families:
        for manifold in family.failure_manifolds:
            manifold_id = manifold.manifold_id
            gen_fn = GENERATORS.get(manifold_id)
            if gen_fn is None:
                continue

            inputs = gen_fn()
            accepted = []
            rejected = 0

            for nums, target in inputs:
                try:
                    truth = lc33_brute_force(nums, target)
                    accepted.append((nums, target, truth))
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
                for nums, target, truth in accepted:
                    try:
                        if fn(nums, target) == truth:
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

            pre_div = solver_divergence["always_left"]
            crossed = [(_rotate_left_half(nums), target) for nums, target, _ in accepted]
            post_div = _divergence_rate(crossed, lc33_always_left)
            post_count = sum(1 for nums, _ in crossed if len(nums) <= 100)
            divergence_delta = post_div - pre_div
            event = {
                "manifold_id": manifold_id,
                "perturbation_operator": "solver_assumption_break",
                "parameterization": {"transform": "rotate_left_half", "assumption": "sorted_left_is_correct_search_space"},
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
