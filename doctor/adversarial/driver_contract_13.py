"""LC322 driver for the generalized ingestion gate (coin-change II)."""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate


def lc322_coin_reordering_perturbations(test: dict[str, Any], n_samples: int) -> list[dict[str, Any]]:
    """Multiset-preserving coin order perturbations (one concrete perturbation strategy)."""
    coins = test["coins"]
    amount = test["amount"]
    rng = random.Random(42)
    seen: set[tuple[tuple[int, ...], int]] = set()
    perturbations: list[dict[str, Any]] = []

    def add(c: list[int], a: int) -> None:
        key = (tuple(c), a)
        if key not in seen:
            seen.add(key)
            perturbations.append({"coins": list(c), "amount": a})

    add(sorted(coins), amount)
    add(sorted(coins, reverse=True), amount)

    for _ in range(n_samples):
        shuffled = list(coins)
        rng.shuffle(shuffled)
        add(shuffled, amount)

    for _ in range(max(1, n_samples // 2)):
        perm = list(coins)
        rng.shuffle(perm)
        add(perm, amount)

    return perturbations


def lc322_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[int], int], int]],
    oracle: Callable[[list[int], int], int | bool],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem  # reserved for caller/schema parity with other problem drivers
    return ingestion_gate(
        problem_id="LC322",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["coins"], t["amount"]),
        apply_oracle=lambda o, t: o(t["coins"], t["amount"]),
        perturbation_strategy=lc322_coin_reordering_perturbations,
        comparator=get_driver_contract("LC322").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="multiset_invariant",
        thresholds=thresholds,
    )
