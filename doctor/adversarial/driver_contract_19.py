"""LC56 driver for the generalized ingestion gate (Merge Intervals).

Output is order-insensitive on outer list; ``set_of_tuples`` comparator
preserves inner ``[start, end]`` order while ignoring outer order.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate
from doctor.adversarial.structural_comparator import set_of_tuples


def lc56_intervals_reordering_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Shuffle input ``intervals`` order (ordering_invariant family)."""
    intervals = test["intervals"]
    rng = random.Random(42)
    seen: set[tuple[tuple[int, int], ...]] = set()
    perturbations: list[dict[str, Any]] = []

    def add(iv: list[list[int]]) -> None:
        key = tuple(tuple(i) for i in iv)
        if key not in seen:
            seen.add(key)
            perturbations.append({"intervals": [list(i) for i in iv]})

    add(sorted(intervals))
    add(sorted(intervals, reverse=True))

    for _ in range(n_samples):
        shuffled = list(intervals)
        rng.shuffle(shuffled)
        add(shuffled)

    for _ in range(max(1, n_samples // 2)):
        perm = list(intervals)
        rng.shuffle(perm)
        add(perm)

    return perturbations


def lc56_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[list[int]]], list[list[int]]]],
    oracle: Callable[[list[list[int]]], list[list[int]]],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem
    return ingestion_gate(
        problem_id="LC56",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["intervals"]),
        apply_oracle=lambda o, t: o(t["intervals"]),
        perturbation_strategy=lc56_intervals_reordering_perturbations,
        comparator=get_driver_contract("LC56").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="ordering_invariant",
        thresholds=thresholds,
    )
