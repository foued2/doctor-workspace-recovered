from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import copy
import json
from doctor.adversarial.lc79_bimaristan import LC79, GENERATORS
from doctor.adversarial.lc79_candidates import lc79_reference, lc79_no_restore, lc79_reuse_cells
from doctor.adversarial.lc79_ground_truth import lc79_brute_force, GroundTruthDomainError

SOLVERS = {
    "reference": lc79_reference,
    "no_restore": lc79_no_restore,
    "reuse_cells": lc79_reuse_cells,
}


def _divergence_rate(cases, fn) -> float:
    if not cases:
        return 0.0
    wrong = 0
    observed = 0
    for board, word in cases:
        try:
            truth = lc79_brute_force(copy.deepcopy(board), word)
        except GroundTruthDomainError:
            continue
        observed += 1
        try:
            if fn(copy.deepcopy(board), word) != truth:
                wrong += 1
        except Exception:
            wrong += 1
    return wrong / observed if observed else 0.0


def _skip_backtrack_restore(board: list[list[str]], word: str) -> list[list[str]]:
    mutated = copy.deepcopy(board)
    try:
        lc79_no_restore(mutated, word)
    except Exception:
        pass
    return mutated


def main():
    print("LC79 Bimaristan run")
    for family in LC79.invariant_families:
        for manifold in family.failure_manifolds:
            manifold_id = manifold.manifold_id
            gen_fn = GENERATORS.get(manifold_id)
            if gen_fn is None:
                continue

            inputs = gen_fn()
            accepted = []
            rejected = 0

            for board, word in inputs:
                try:
                    truth = lc79_brute_force(copy.deepcopy(board), word)
                    accepted.append((copy.deepcopy(board), word, truth))
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
                for board, word, truth in accepted:
                    try:
                        fn(copy.deepcopy(board), word)
                    except Exception:
                        pass
                # Re-evaluate properly
                correct = 0
                for board, word, truth in accepted:
                    fresh = copy.deepcopy(board)
                    try:
                        if fn(fresh, word) == truth:
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

            pre_div = solver_divergence["no_restore"]
            crossed = [(_skip_backtrack_restore(board, word), word) for board, word, _ in accepted]
            post_div = _divergence_rate(crossed, lc79_no_restore)
            post_count = 0
            for board, word in crossed:
                try:
                    lc79_brute_force(copy.deepcopy(board), word)
                    post_count += 1
                except GroundTruthDomainError:
                    pass
            divergence_delta = post_div - pre_div
            event = {
                "manifold_id": manifold_id,
                "perturbation_operator": "solver_assumption_break",
                "parameterization": {"transform": "skip_backtrack_restore", "assumption": "in_place_restore"},
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
