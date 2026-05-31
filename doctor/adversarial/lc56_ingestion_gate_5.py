"""LC56 survival matrix for 2.1 topology-divergence scoring.

Evaluates every solver (good + negative control) on both the reference test
suite and the ordering_invariant perturbation family, then computes
second-order survival topology metrics via ``survival_scoring``.
"""
from __future__ import annotations

import copy
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc56_ingestion_gate import lc56_intervals_reordering_perturbations
from doctor.adversarial.structural_comparator import set_of_tuples
from doctor.grading.survival_scoring import compute_survival_topology_metrics
from runners.run_lc56_gate import (
    REFERENCE_TESTS,
    lc56_oracle,
    solver_sort_merge,
    solver_sort_merge_lambda,
    solver_in_place,
    solver_no_merge,
    solver_bogus,
)

INSTANCES = 100
NEGATIVE_CONTROL_THRESHOLD = 0.20
ADVERSARIAL_SURVIVAL_THRESHOLD = 0.20
OUTPUT_PATH = PROJECT_ROOT / "data" / "lc56_survival_matrix.json"

SOLVERS: tuple[tuple[str, Callable[[list[list[int]]], list[list[int]]]], ...] = (
    ("solver_sort_merge", solver_sort_merge),
    ("solver_sort_merge_lambda", solver_sort_merge_lambda),
    ("solver_in_place", solver_in_place),
    ("solver_no_merge", solver_no_merge),
    ("solver_bogus", solver_bogus),
)


def _rate_on_reference(solver: Callable[[list[list[int]]], list[list[int]]]) -> float:
    """Fraction of reference tests where solver output matches oracle."""
    false_pass = 0
    for test in REFERENCE_TESTS:
        oracle_output = lc56_oracle(copy.deepcopy(test["intervals"]))
        solver_output = solver(copy.deepcopy(test["intervals"]))
        if set_of_tuples(solver_output, oracle_output):
            false_pass += 1
    return false_pass / len(REFERENCE_TESTS)


def _select_perturbation(original: dict[str, Any], instance_index: int) -> dict[str, Any]:
    """Deterministic perturbation selection cycling through candidates."""
    candidates = lc56_intervals_reordering_perturbations(copy.deepcopy(original), 10)
    if not candidates:
        raise ValueError("LC56 generator returned no perturbations")
    return copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])


def _rate_on_perturbations(solver: Callable[[list[list[int]]], list[list[int]]]) -> float:
    """Fraction of valid perturbations where solver output matches oracle."""
    false_pass = 0
    valid = 0
    for instance_index in range(1, INSTANCES + 1):
        original = copy.deepcopy(REFERENCE_TESTS[(instance_index - 1) % len(REFERENCE_TESTS)])
        perturbed = _select_perturbation(original, instance_index)
        if sorted(original["intervals"]) != sorted(perturbed["intervals"]):
            continue
        valid += 1
        oracle_output = lc56_oracle(copy.deepcopy(perturbed["intervals"]))
        solver_output = solver(copy.deepcopy(perturbed["intervals"]))
        if set_of_tuples(solver_output, oracle_output):
            false_pass += 1
    return false_pass / valid if valid else 0.0


def run() -> dict[str, Any]:
    rows = []
    for solver_id, solver in SOLVERS:
        negative_rate = _rate_on_reference(solver)
        adversarial_rate = _rate_on_perturbations(solver)
        rows.append(
            {
                "solver_id": solver_id,
                "negative_control_false_pass_rate": negative_rate,
                "adversarial_false_pass_rate": adversarial_rate,
                "survives_negative_control": negative_rate > NEGATIVE_CONTROL_THRESHOLD,
                "survives_adversarial": adversarial_rate > ADVERSARIAL_SURVIVAL_THRESHOLD,
            }
        )

    negative_survivors = {row["solver_id"] for row in rows if row["survives_negative_control"]}
    adversarial_survivors = {row["solver_id"] for row in rows if row["survives_adversarial"]}
    topology = compute_survival_topology_metrics(adversarial_survivors, negative_survivors)
    return {
        "problem_id": "LC56",
        "comparator": "set_of_tuples",
        "negative_control_threshold": NEGATIVE_CONTROL_THRESHOLD,
        "adversarial_survival_threshold": ADVERSARIAL_SURVIVAL_THRESHOLD,
        "rows": rows,
        "overlap_count": len(negative_survivors & adversarial_survivors),
        "adversarial_only_survivors": sorted(adversarial_survivors - negative_survivors),
        "negative_control_only_survivors": sorted(negative_survivors - adversarial_survivors),
        **topology,
    }


def main() -> int:
    result = run()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    print(f"Wrote: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
