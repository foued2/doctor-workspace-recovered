"""Run CF 607A solvers over random beacon configs and record results."""
from __future__ import annotations

import math
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from doctor.adversarial.cf607a_ground_truth import GroundTruthDomainError, cf607a_brute_force
from doctor.adversarial.cf607a_candidates import (
    cf607a_reference,
    cf607a_reverse_order,
    cf607a_no_add,
    cf607a_double_power,
    cf607a_center_add,
)


SOLVERS: dict[str, Callable[[int, Any], int]] = {
    "reference": cf607a_reference,
    "reverse_order": cf607a_reverse_order,
    "no_add": cf607a_no_add,
    "double_power": cf607a_double_power,
    "center_add": cf607a_center_add,
}
HEURISTIC_NAMES = tuple(k for k in SOLVERS if k != "reference")


def _safe_run(fn: Callable, n: int, data: Any) -> dict:
    started = perf_counter()
    try:
        output = fn(n, data)
        return {"status": "ok", "output": output, "runtime_ms": round((perf_counter() - started) * 1000, 3), "error": None}
    except Exception as exc:
        return {"status": "error", "output": None, "runtime_ms": round((perf_counter() - started) * 1000, 3), "error": f"{type(exc).__name__}: {exc}"}


def execute_record(record: dict) -> dict:
    n = int(record["n"])
    beacons = [(int(p), int(b)) for p, b in record["beacons"]]
    solver_results = {name: _safe_run(fn, n, beacons) for name, fn in SOLVERS.items()}

    oracle = {"available": False, "output": None, "error": None}
    if n <= 6:
        try:
            oracle["output"] = cf607a_brute_force(n, beacons)
            oracle["available"] = True
        except GroundTruthDomainError as exc:
            oracle["error"] = str(exc)

    correctness = None
    if oracle["available"]:
        correctness = {
            name: res["status"] == "ok" and res["output"] == oracle["output"]
            for name, res in solver_results.items()
        }

    return {
        "input_id": record["input_id"],
        "n": n,
        "beacons": beacons,
        "truth_model": "oracle" if oracle["available"] else "non_oracle_disagreement_only",
        "oracle": oracle,
        "solver_outputs": solver_results,
        "correctness_vs_oracle": correctness,
    }


def execute_matrix(records: list[dict]) -> list[dict]:
    return [execute_record(rec) for rec in records]


def main() -> None:
    import json
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("scratch/cf607a_phase_map/inputs.json"))
    parser.add_argument("--output", type=Path, default=Path("scratch/cf607a_phase_map/execution_matrix.json"))
    args = parser.parse_args()

    records = json.loads(args.input.read_text(encoding="utf-8"))
    matrix = execute_matrix(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    oracle_rows = sum(1 for row in matrix if row["truth_model"] == "oracle")
    print(f"Wrote {len(matrix)} executions to {args.output} ({oracle_rows} oracle rows)")


if __name__ == "__main__":
    main()
