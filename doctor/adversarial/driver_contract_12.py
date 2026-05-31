"""LC179 driver for the generalized ingestion gate (Largest Number).

``ordering_invariant`` family: input array order doesn't affect the output
— the largest number is determined solely by the multiset of numbers.
Shuffling input preserves the correct answer.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate


def lc179_nums_reordering_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Shuffle input ``nums`` order (ordering_invariant family)."""
    nums = test["nums"]
    original_multiset = sorted(nums)
    rng = random.Random(42)
    seen: set[tuple[int, ...]] = set()
    perturbations: list[dict[str, Any]] = []

    def add(n: list[int]) -> None:
        if sorted(n) != original_multiset:
            raise ValueError("LC179 ordering_invariant perturbation changed input multiset")
        key = tuple(n)
        if key not in seen:
            seen.add(key)
            perturbations.append({"nums": list(n)})

    add(sorted(nums))
    add(sorted(nums, reverse=True))

    for _ in range(n_samples):
        shuffled = list(nums)
        rng.shuffle(shuffled)
        add(shuffled)

    for _ in range(max(1, n_samples // 2)):
        perm = list(nums)
        rng.shuffle(perm)
        add(perm)

    return perturbations


def lc179_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[int]], str]],
    oracle: Callable[[list[int]], str],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem
    return ingestion_gate(
        problem_id="LC179",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["nums"]),
        apply_oracle=lambda o, t: o(t["nums"]),
        perturbation_strategy=lc179_nums_reordering_perturbations,
        comparator=get_driver_contract("LC179").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="ordering_invariant",
        thresholds=thresholds,
    )
