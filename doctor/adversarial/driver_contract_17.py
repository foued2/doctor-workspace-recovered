"""LC47 driver for the generalized ingestion gate (Permutations II).

Duplicate-safe: input may contain duplicate elements. The perturbation
strategy uses ``sorted(nums)`` and shuffle, which preserve duplicate
structure — no ``set()`` collapsing anywhere.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate
from doctor.adversarial.structural_comparator import set_of_tuples


def lc47_nums_reordering_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Multiset-preserving shuffle of ``nums``.
    
    Duplicate-safe: ``sorted(nums)`` preserves duplicates (``[2,1,2]`` →
    ``[1,2,2]``).  No ``set()`` is applied to the element collection, only
    to the ``tuple`` dedup key for avoiding identical perturbations.
    """
    nums = test["nums"]
    rng = random.Random(42)
    seen: set[tuple[int, ...]] = set()
    perturbations: list[dict[str, Any]] = []

    def add(n: list[int]) -> None:
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


def lc47_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[int]], list[list[int]]]],
    oracle: Callable[[list[int]], list[list[int]]],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem
    return ingestion_gate(
        problem_id="LC47",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["nums"]),
        apply_oracle=lambda o, t: o(t["nums"]),
        perturbation_strategy=lc47_nums_reordering_perturbations,
        comparator=get_driver_contract("LC47").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="multiset_invariant",
        thresholds=thresholds,
    )
