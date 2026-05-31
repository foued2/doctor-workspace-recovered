"""LC39 driver for the generalized ingestion gate (Combination Sum)."""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate
from doctor.adversarial.structural_comparator import multiset_of_multisets


def lc39_candidate_reordering_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Multiset-preserving ``candidates`` order perturbations."""
    candidates = test["candidates"]
    target = test["target"]
    rng = random.Random(42)
    seen: set[tuple[int, ...]] = set()
    perturbations: list[dict[str, Any]] = []

    def add(c: list[int]) -> None:
        key = tuple(c)
        if key not in seen:
            seen.add(key)
            perturbations.append({"candidates": list(c), "target": target})

    add(sorted(candidates))
    add(sorted(candidates, reverse=True))

    for _ in range(n_samples):
        shuffled = list(candidates)
        rng.shuffle(shuffled)
        add(shuffled)

    for _ in range(max(1, n_samples // 2)):
        perm = list(candidates)
        rng.shuffle(perm)
        add(perm)

    return perturbations


def lc39_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[int], int], list[list[int]]]],
    oracle: Callable[[list[int], int], list[list[int]]],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem
    return ingestion_gate(
        problem_id="LC39",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["candidates"], t["target"]),
        apply_oracle=lambda o, t: o(t["candidates"], t["target"]),
        perturbation_strategy=lc39_candidate_reordering_perturbations,
        comparator=get_driver_contract("LC39").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="multiset_invariant",
        thresholds=thresholds,
    )
