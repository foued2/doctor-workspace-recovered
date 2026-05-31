"""LC45 driver for the generalized ingestion gate (Jump Game II).

Perturbation family: ``suffix_reach_invariant`` — increments jump values at
positions that already reach the end directly.  See FINDINGS_084 for the
structural argument and validity scope.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate


def lc45_suffix_reach_perturbations(
    test: dict[str, Any], n_samples: int, oracle: Callable[..., int]
) -> list[dict[str, Any]]:
    """Perturb qualifying positions by incrementing their jump values.

    Narrow falsification target — solvers using ``==`` instead of ``>=`` for
    threshold comparison, or solvers with magnitude-dependent internal state.

    A position i is qualifying iff ``nums[i] >= len(nums) - 1 - i`` (it can
    reach the end in one jump).  Incrementing the value at such positions
    preserves the minimum jump count because the contribution is binary —
    the threshold is already cleared.  See FINDINGS_084 for the full argument.
    """
    nums = test["nums"]
    n = len(nums)

    qualifying = [i for i in range(n) if nums[i] >= n - 1 - i]

    if not qualifying:
        return [{"nums": list(nums), "_note": "no_qualifying_positions"}]

    rng = random.Random(42)
    seen: set[tuple[int, ...]] = set()
    perturbations: list[dict[str, Any]] = []

    # Generate candidate perturbations and verify oracle equivalence.
    for _ in range(n_samples * 3):
        subset = rng.sample(qualifying, max(1, rng.randint(1, min(3, len(qualifying)))))
        perturbed = list(nums)
        for i in subset:
            perturbed[i] += rng.randint(1, 3)
        key = tuple(perturbed)
        if key not in seen:
            seen.add(key)
            try:
                if oracle(perturbed) == oracle(nums):
                    perturbations.append({"nums": perturbed})
            except Exception:
                continue
            if len(perturbations) >= n_samples:
                break

    if not perturbations:
        return [{"nums": list(nums), "_note": "no_valid_perturbations"}]

    return perturbations


def lc45_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[list[int]], int]],
    oracle: Callable[[list[int]], int | bool],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem

    def _perturbations(test: dict[str, Any], n_samples: int) -> list[dict[str, Any]]:
        return lc45_suffix_reach_perturbations(test, n_samples, oracle)

    return ingestion_gate(
        problem_id="LC45",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=oracle,
        apply_solver=lambda s, t: s(t["nums"]),
        apply_oracle=lambda o, t: o(t["nums"]),
        perturbation_strategy=_perturbations,
        comparator=get_driver_contract("LC45").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="suffix_reach_invariant",
        thresholds=thresholds,
    )
