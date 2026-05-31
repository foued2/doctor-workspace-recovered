"""LC135 survival matrix for 2.1 topology-divergence scoring.

Perturbation family: plateaumorphic_invariant — order-isomorphic relabeling
preserves equality groups and strict ordering but changes absolute magnitudes.

This is the first test of a non-reordering perturbation family under the new
second-order metrics.  If any problem can produce topology divergence, this
should be it — left_pass_only and right_pass_only heuristics may show different
sensitivity to threshold/magnitude changes vs reference-only evaluation.
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

from doctor.adversarial.lc135_candidates import (
    lc135_left_pass_only,
    lc135_right_pass_only,
    lc135_two_pass,
)
from doctor.adversarial.lc135_ground_truth import lc135_brute_force, GroundTruthDomainError
from doctor.adversarial.lc135_ingestion_gate import lc135_plateaumorphic_perturbations
from doctor.grading.survival_scoring import compute_survival_topology_metrics

INSTANCES = 100
NEGATIVE_CONTROL_THRESHOLD = 0.20
ADVERSARIAL_SURVIVAL_THRESHOLD = 0.20
OUTPUT_PATH = PROJECT_ROOT / "data" / "lc135_survival_matrix.json"

REFERENCE_TESTS: list[dict[str, list[int]]] = [
    {"ratings": [1, 0, 2]},
    {"ratings": [1, 2, 2]},
    {"ratings": [1, 3, 2, 2, 1]},
    {"ratings": [1, 2, 3, 4, 5]},
    {"ratings": [5, 4, 3, 2, 1]},
    {"ratings": [1, 1, 1, 1]},
    {"ratings": [3, 2, 1, 0, 1, 2, 3]},
    {"ratings": [1, 2, 3, 3, 2, 1]},
    {"ratings": [2, 2, 2, 1, 1, 1]},
    {"ratings": [1, 3, 5, 3, 1, 2, 4]},
    {"ratings": [4, 3, 3, 2, 2, 1, 1]},
    {"ratings": [1, 5, 2, 4, 3, 6, 0, 2]},
]

SOLVERS: tuple[tuple[str, Callable[[list[int]], int]], ...] = (
    ("lc135_two_pass", lc135_two_pass),
    ("lc135_left_pass_only", lc135_left_pass_only),
    ("lc135_right_pass_only", lc135_right_pass_only),
)


def _filter_in_domain(tests: list[dict[str, list[int]]]) -> list[dict[str, list[int]]]:
    valid: list[dict[str, list[int]]] = []
    for t in tests:
        try:
            lc135_brute_force(t["ratings"])
            valid.append(t)
        except GroundTruthDomainError:
            pass
    return valid


def _rate_on_reference(solver: Callable[[list[int]], int]) -> float:
    false_pass = 0
    for test in REFERENCE_TESTS:
        oracle_output = lc135_brute_force(copy.deepcopy(test["ratings"]))
        solver_output = solver(copy.deepcopy(test["ratings"]))
        if type(solver_output) is type(oracle_output) and solver_output == oracle_output:
            false_pass += 1
    return false_pass / len(REFERENCE_TESTS)


def _select_perturbation(original: dict[str, Any], instance_index: int) -> dict[str, Any]:
    candidates = lc135_plateaumorphic_perturbations(copy.deepcopy(original), 10)
    if not candidates:
        raise ValueError("LC135 generator returned no perturbations")
    return copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])


def _rate_on_perturbations(solver: Callable[[list[int]], int]) -> float:
    false_pass = 0
    valid = 0
    for instance_index in range(1, INSTANCES + 1):
        original = copy.deepcopy(REFERENCE_TESTS[(instance_index - 1) % len(REFERENCE_TESTS)])
        perturbed = _select_perturbation(original, instance_index)
        try:
            oracle_output = lc135_brute_force(copy.deepcopy(perturbed["ratings"]))
        except GroundTruthDomainError:
            continue
        valid += 1
        solver_output = solver(copy.deepcopy(perturbed["ratings"]))
        if type(solver_output) is type(oracle_output) and solver_output == oracle_output:
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
        "problem_id": "LC135",
        "perturbation_family": "plateaumorphic_invariant",
        "negative_control_threshold": NEGATIVE_CONTROL_THRESHOLD,
        "adversarial_survival_threshold": ADVERSARIAL_SURVIVAL_THRESHOLD,
        "rows": rows,
        "overlap_count": len(negative_survivors & adversarial_survivors),
        "adversarial_only_survivors": sorted(adversarial_survivors - negative_survivors),
        "negative_control_only_survivors": sorted(negative_survivors - adversarial_survivors),
        **topology,
    }


def main() -> int:
    filtered = _filter_in_domain(REFERENCE_TESTS)
    if len(filtered) < len(REFERENCE_TESTS):
        print(f"WARNING: {len(REFERENCE_TESTS) - len(filtered)} tests exceeded oracle domain")
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
