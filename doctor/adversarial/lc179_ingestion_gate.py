"""LC179 comparator perturbation calibration.

Single-purpose Stage 2.1 opening gate: hold the LC179 perturbation family fixed
and relax the comparator locally to test whether the 0.16 false-pass rate moves.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc179_ingestion_gate import lc179_nums_reordering_perturbations
from runners.run_lc179_gate import REFERENCE_TESTS, lc179_oracle
from solvers.negative_controls import lc179_numeric_descending

INSTANCES = 100
EPSILON_SWEEP = (0, 1, 2)
OUTPUT_PATH = PROJECT_ROOT / "data" / "comparator_perturbation_lc179.json"


def _numeric_string(value: Any) -> int | None:
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _epsilon_equal(left: Any, right: Any, epsilon: int) -> bool:
    left_num = _numeric_string(left)
    right_num = _numeric_string(right)
    if left_num is None or right_num is None:
        return type(left) is type(right) and left == right
    return abs(left_num - right_num) <= epsilon


def _select_perturbation(original: dict[str, Any], instance_index: int) -> dict[str, Any]:
    candidates = lc179_nums_reordering_perturbations(copy.deepcopy(original), instance_index)
    if not candidates:
        raise ValueError("LC179 generator returned no perturbations")
    return copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])


def _trace(epsilon: int, instance_index: int) -> dict[str, Any]:
    original = copy.deepcopy(REFERENCE_TESTS[(instance_index - 1) % len(REFERENCE_TESTS)])
    perturbed = _select_perturbation(original, instance_index)
    perturbation_valid = sorted(original["nums"]) == sorted(perturbed["nums"])
    if not perturbation_valid:
        raise AssertionError("LC179 perturbation changed input multiset")

    oracle_output = lc179_oracle(copy.deepcopy(perturbed["nums"]))
    solver_output = lc179_numeric_descending(copy.deepcopy(perturbed["nums"]))
    false_pass = _epsilon_equal(solver_output, oracle_output, epsilon)
    return {
        "epsilon": epsilon,
        "instance_index": instance_index,
        "oracle_output": oracle_output,
        "solver_output": solver_output,
        "false_pass": false_pass,
        "rejection": not false_pass,
    }


def run_sweep() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for epsilon in EPSILON_SWEEP:
        records = [_trace(epsilon, idx) for idx in range(1, INSTANCES + 1)]
        false_pass_count = sum(1 for record in records if record["false_pass"])
        results.append(
            {
                "problem_id": "LC179",
                "solver_id": "lc179_numeric_descending",
                "comparator": "epsilon_numeric_string",
                "epsilon": epsilon,
                "total_valid_instances": len(records),
                "false_pass_count": false_pass_count,
                "false_pass_rate": false_pass_count / len(records),
            }
        )
    return results


def main() -> int:
    results = run_sweep()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    for row in results:
        print(
            f"epsilon={row['epsilon']} "
            f"false_pass_rate={row['false_pass_rate']:.2f} "
            f"false_pass_count={row['false_pass_count']}/{row['total_valid_instances']}"
        )
    print(f"Wrote: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
