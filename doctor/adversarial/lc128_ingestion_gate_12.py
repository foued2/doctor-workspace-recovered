"""LC128 survival matrix for Stage 2.1 interpretation."""
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

from doctor.adversarial.lc128_ingestion_gate import lc128_nums_reordering_perturbations
from doctor.grading.survival_scoring import compute_survival_topology_metrics
from runners.run_lc128_adversarial import lc128_input_order_consecutive_scan
from runners.run_lc128_gate import (
    REFERENCE_TESTS,
    lc128_oracle,
    solver_return_len,
    solver_set_based,
    solver_sorted_scan,
    solver_union_find,
)
from runners.run_lc128_negative_control import lc128_always_zero

INSTANCES = 100
NEGATIVE_CONTROL_THRESHOLD = 0.20
ADVERSARIAL_SURVIVAL_THRESHOLD = 0.20
OUTPUT_PATH = PROJECT_ROOT / "data" / "lc128_survival_matrix.json"


def lc128_distinct_count(nums: list[int]) -> int:
    """Miscalibrated control retained for survival analysis provenance."""
    return len(set(nums))


SOLVERS: tuple[tuple[str, Callable[[list[int]], int]], ...] = (
    ("solver_set_based", solver_set_based),
    ("solver_sorted_scan", solver_sorted_scan),
    ("solver_union_find", solver_union_find),
    ("lc128_always_zero", lc128_always_zero),
    ("solver_return_len", solver_return_len),
    ("lc128_distinct_count", lc128_distinct_count),
    ("lc128_input_order_consecutive_scan", lc128_input_order_consecutive_scan),
)


def _select_perturbation(original: dict[str, Any], instance_index: int) -> dict[str, Any]:
    candidates = lc128_nums_reordering_perturbations(copy.deepcopy(original), instance_index)
    if not candidates:
        raise ValueError("LC128 generator returned no perturbations")
    return copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])


def _rate_on_reference(solver: Callable[[list[int]], int]) -> float:
    false_pass = 0
    for test in REFERENCE_TESTS:
        oracle_output = lc128_oracle(copy.deepcopy(test["nums"]))
        solver_output = solver(copy.deepcopy(test["nums"]))
        if type(solver_output) is type(oracle_output) and solver_output == oracle_output:
            false_pass += 1
    return false_pass / len(REFERENCE_TESTS)


def _rate_on_perturbations(solver: Callable[[list[int]], int]) -> float:
    false_pass = 0
    valid = 0
    for instance_index in range(1, INSTANCES + 1):
        original = copy.deepcopy(REFERENCE_TESTS[(instance_index - 1) % len(REFERENCE_TESTS)])
        perturbed = _select_perturbation(original, instance_index)
        if sorted(original["nums"]) != sorted(perturbed["nums"]):
            continue
        valid += 1
        oracle_output = lc128_oracle(copy.deepcopy(perturbed["nums"]))
        solver_output = solver(copy.deepcopy(perturbed["nums"]))
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
        "problem_id": "LC128",
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
