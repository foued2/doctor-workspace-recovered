"""LC128 negative-control calibration for Stage 2.1 discovery mode."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc128_ingestion_gate import lc128_nums_reordering_perturbations
from runners.run_lc128_gate import REFERENCE_TESTS, lc128_oracle

INSTANCES = 100
OUTPUT_PATH = PROJECT_ROOT / "data" / "lc128_negative_control.json"


def lc128_always_zero(nums: list[int]) -> int:
    """Genuine wrong control: only coincides with the empty-input oracle case."""
    del nums
    return 0


def _select_perturbation(original: dict[str, Any], instance_index: int) -> dict[str, Any]:
    candidates = lc128_nums_reordering_perturbations(copy.deepcopy(original), instance_index)
    if not candidates:
        raise ValueError("LC128 generator returned no perturbations")
    return copy.deepcopy(candidates[(instance_index - 1) % len(candidates)])


def _trace(instance_index: int) -> dict[str, Any]:
    original = copy.deepcopy(REFERENCE_TESTS[(instance_index - 1) % len(REFERENCE_TESTS)])
    perturbed = _select_perturbation(original, instance_index)
    perturbation_valid = sorted(original["nums"]) == sorted(perturbed["nums"])
    oracle_output = None
    solver_output = None
    if perturbation_valid:
        oracle_output = lc128_oracle(copy.deepcopy(perturbed["nums"]))
        solver_output = lc128_always_zero(copy.deepcopy(perturbed["nums"]))
    false_pass = perturbation_valid and type(solver_output) is type(oracle_output) and solver_output == oracle_output
    return {
        "problem_id": "LC128",
        "family": "ordering_invariant",
        "solver_id": "lc128_always_zero",
        "instance_index": instance_index,
        "perturbation_valid": perturbation_valid,
        "oracle_output": oracle_output,
        "solver_output": solver_output,
        "false_pass": false_pass,
        "rejection": perturbation_valid and not false_pass,
    }


def run() -> dict[str, Any]:
    records = [_trace(idx) for idx in range(1, INSTANCES + 1)]
    valid = [record for record in records if record["perturbation_valid"]]
    false_pass_count = sum(1 for record in valid if record["false_pass"])
    return {
        "problem_id": "LC128",
        "family": "ordering_invariant",
        "solver_id": "lc128_always_zero",
        "comparator": "exact_scalar",
        "comparator_validation": "post-audit exact_scalar type-exact equality",
        "total_generated": len(records),
        "invalid_count": len(records) - len(valid),
        "oracle_evaluated": len(valid),
        "false_pass_count": false_pass_count,
        "false_pass_rate": false_pass_count / len(valid) if valid else 0.0,
    }


def main() -> int:
    result = run()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(
        "LC128 negative control: "
        f"total_generated={result['total_generated']} "
        f"invalid_count={result['invalid_count']} "
        f"oracle_evaluated={result['oracle_evaluated']} "
        f"false_pass_rate={result['false_pass_rate']:.2f}"
    )
    print(f"Wrote: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
