"""LC134 driver for the generalized ingestion gate (Gas Station).

Perturbation family: ``paired_conservation`` — (gas, cost) are always perturbed
as a coupled pair.  Independent perturbation of either array is structurally
prevented: all operations rotate or shift both arrays together.

.. caution::

   ``paired_conservation`` on LC134 has a structural limitation with the gate's
   comparison model.  The gate compares ``solver(perturbed_input)`` against
   ``oracle(original_input)``.  Because LC134's output is a **positional index**
   (not an invariant scalar like jump count or candy total), perturbations that
   rotate the arrays change the correct answer's index even when the circuit
   semantics are preserved.  This produces ``memorization`` verdicts that are
   artifacts of the representation, not genuine solver failures.

   Uniform additive shift with identical shift on both arrays preserves the
   oracle answer exactly, but is too weak to distinguish correct from incorrect
   solvers (all current solvers share a ``_feasible()`` helper).  LC134 is a
   known boundary case for the current gate comparison model — see FINDINGS_087.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from doctor.adversarial.driver_contract import get_driver_contract
from doctor.adversarial.ingestion_gate import ingestion_gate
from doctor.adversarial.lc134_ground_truth import lc134_brute_force


def lc134_paired_perturbations(
    test: dict[str, Any], n_samples: int
) -> list[dict[str, Any]]:
    """Paired-conservation perturbations for Gas Station.

    Strategies (always coupled):
    1. **Uniform additive shift** — same constant added to every gas value
       and every cost value.  Preserves ``gas[i] - cost[i]`` per station.

    Cyclic rotation was removed — see module docstring (incompatible with the
    gate's comparison model for position-index outputs).
    """
    gas = test["gas"]
    cost = test["cost"]
    n = test["n"]
    rng = random.Random()
    rng.seed(hash((tuple(gas), tuple(cost))) & 0xFFFFFFFF)

    seen: set[tuple[tuple[int, ...], tuple[int, ...]]] = {(tuple(gas), tuple(cost))}
    perturbations: list[dict[str, Any]] = []

    for _ in range(n_samples * 5):
        shift = rng.randint(1, 10)
        p_gas = [g + shift for g in gas]
        p_cost = [c + shift for c in cost]

        key = (tuple(p_gas), tuple(p_cost))
        if key not in seen:
            seen.add(key)
            perturbations.append({"n": n, "gas": p_gas, "cost": p_cost})
            if len(perturbations) >= n_samples:
                break

    if not perturbations:
        return [{"n": n, "gas": list(gas), "cost": list(cost), "_note": "no_valid_perturbations"}]

    return perturbations


def _oracle_wrapper(gas: list[int], cost: list[int]) -> int:
    """Drop ``n`` from the oracle signature — derived from ``len(gas)``."""
    return lc134_brute_force(len(gas), gas, cost)


def lc134_ingestion_gate(
    problem: Mapping[str, Any],
    solvers: Sequence[Callable[[int, list[int], list[int]], int]],
    oracle: Callable[[list[int], list[int]], int],
    reference_tests: list[dict[str, Any]],
    perturbation_samples: int = 5,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    del problem

    return ingestion_gate(
        problem_id="LC134",
        reference_tests=reference_tests,
        solvers=solvers,
        oracle=_oracle_wrapper,
        apply_solver=lambda s, t: s(t["n"], t["gas"], t["cost"]),
        apply_oracle=lambda o, t: o(t["gas"], t["cost"]),
        perturbation_strategy=lc134_paired_perturbations,
        comparator=get_driver_contract("LC134").comparator,
        perturbation_samples=perturbation_samples,
        perturbation_family="paired_conservation",
        thresholds=thresholds,
    )
