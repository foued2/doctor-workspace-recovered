"""LC49 driver for the generalized ingestion gate (Group Anagrams).

Perturbation family ``ordering_invariant``: shuffles the ORDER of words in
the input list.  Individual word strings are NOT modified (that would change
which anagram group they belong to).

Comparator ``multiset_of_multisets``: groups are order-independent (outer
multiset) and words within each group are order-independent (inner multiset).
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate
from doctor.adversarial.structural_comparator import multiset_of_multisets


def lc49_strs_ordering_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Shuffle the ORDER of words in ``strs``.
    
    Individual strings are never modified — only their position in the
    input list changes.  This is ``ordering_invariant``, not
    ``multiset_invariant`` (which would shuffle characters within each word).
    """
    strs_list = test["strs"]
    rng = random.Random(42)
    seen: set[tuple[str, ...]] = set()
    perturbations: list[dict[str, Any]] = []

    def add(s: list[str]) -> None:
        key = tuple(s)
        if key not in seen:
            seen.add(key)
            perturbations.append({"strs": list(s)})

    add(sorted(strs_list))
    add(sorted(strs_list, reverse=True))

    for _ in range(n_samples):
        shuffled = list(strs_list)
        rng.shuffle(shuffled)
        add(shuffled)

    for _ in range(max(1, n_samples // 2)):
        perm = list(strs_list)
        rng.shuffle(perm)
        add(perm)

    return perturbations


def lc49_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[str]], list[list[str]]]],
    oracle: Callable[[list[str]], list[list[str]]],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem
    return ingestion_gate(
        problem_id="LC49",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["strs"]),
        apply_oracle=lambda o, t: o(t["strs"]),
        perturbation_strategy=lc49_strs_ordering_perturbations,
        comparator=get_driver_contract("LC49").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="ordering_invariant",
        thresholds=thresholds,
    )
