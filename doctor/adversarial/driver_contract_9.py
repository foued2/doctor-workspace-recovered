"""LC135 driver for the generalized ingestion gate (Candy).

Perturbation family: ``plateaumorphic_invariant`` — order-isomorphic +
plateau-isomorphic relabeling of rating values.  Preserves equality groups,
strict ordering between distinct values, and adjacency structure of plateau
blocks.  The brute-force oracle (domain cap n <= 8) enumerates all valid
candy distributions to find the minimum total.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate


def lc135_plateaumorphic_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Order-isomorphic + plateau-isomorphic relabeling of rating values.

    The transformation is a strictly increasing function applied to the set of
    unique rating values, then applied elementwise.  This preserves:

    *   **Equality groups** — equal ratings map to equal values.
    *   **Strict ordering** — if ``a < b`` then ``f(a) < f(b)``.
    *   **Adjacency structure** — the equality/inequality relationship between
        every adjacent pair is unchanged.

    The constraint propagation in LC135 depends only on these three properties,
    not on the absolute magnitude of rating values.  Solvers that depend on
    magnitude ratios or absolute thresholds will diverge under this perturbation.
    """
    ratings = test["ratings"]
    rng = random.Random()
    rng.seed(hash(tuple(ratings)) & 0xFFFFFFFF)
    unique = sorted(set(ratings))

    seen: set[tuple[int, ...]] = {tuple(ratings)}
    perturbations: list[dict[str, Any]] = []

    for _ in range(n_samples * 5):
        mapping: dict[int, int] = {}
        current = rng.randint(1, 10)
        for v in unique:
            mapping[v] = current
            step = rng.randint(1, 5)
            current += step
        perturbed = [mapping[v] for v in ratings]
        key = tuple(perturbed)
        if key not in seen:
            seen.add(key)
            perturbations.append({"ratings": perturbed})
            if len(perturbations) >= n_samples:
                break

    if not perturbations:
        return [{"ratings": list(ratings), "_note": "no_valid_perturbations"}]

    return perturbations


def lc135_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[int]], int]],
    oracle: Callable[[list[int]], int | bool],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem

    return ingestion_gate(
        problem_id="LC135",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["ratings"]),
        apply_oracle=lambda o, t: o(t["ratings"]),
        perturbation_strategy=lc135_plateaumorphic_perturbations,
        comparator=get_driver_contract("LC135").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="plateaumorphic_invariant",
        thresholds=thresholds,
    )
