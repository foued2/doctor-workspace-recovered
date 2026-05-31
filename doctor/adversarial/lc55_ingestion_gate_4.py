from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc55_ingestion_gate import generate_minimum_margin_instance, lc55_ingestion_gate
from runners.run_lc55_gate import (
    REFERENCE_TESTS,
    lc55_oracle,
    solver_always_false,
    solver_always_true,
    solver_dp_forward,
    solver_greedy_ltr,
    solver_greedy_rtl,
)
from solvers.negative_controls import lc55_reachability_optimism, lc55_slack_dependent


OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_130.md"


def _round(value: float) -> float:
    return round(float(value), 6)


def _filtered_rows() -> list[dict[str, Any]]:
    rows = []
    for test in REFERENCE_TESTS:
        nums = list(test["nums"])
        compressed = generate_minimum_margin_instance(nums)
        rows.append(
            {
                "nums": nums,
                "truth": lc55_oracle(nums),
                "compressed": compressed,
                "compressed_truth": lc55_oracle(compressed),
                "accepted_by_gate": lc55_oracle(compressed),
            }
        )
    return rows


def _gate(name: str, solvers: list[Callable[[list[int]], bool]]) -> dict[str, Any]:
    result = lc55_ingestion_gate({}, solvers, lc55_oracle, REFERENCE_TESTS)
    metrics = result.get("metrics", {})
    return {
        "name": name,
        "ingest": result["ingest"],
        "reason": result["reason"],
        "oracle_alignment": _round(float(metrics.get("oracle_alignment", 0.0))) if metrics else 0.0,
        "avg_perturbation_stability": _round(float(metrics.get("avg_perturbation_stability", 0.0))) if metrics else 0.0,
        "per_solver": metrics.get("perturbation_stability", {}).get("per_solver", {}) if metrics else {},
    }


def _solver_alignment(name: str, solver: Callable[[list[int]], bool], rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["accepted_by_gate"]]
    baseline_correct = 0
    compressed_correct = 0
    for row in accepted:
        baseline_correct += int(solver(list(row["nums"])) == row["truth"])
        compressed_correct += int(solver(list(row["compressed"])) == row["truth"])
    total = len(accepted)
    return {
        "solver": name,
        "accepted_rows": total,
        "baseline_alignment": _round(baseline_correct / total if total else 0.0),
        "compressed_alignment": _round(compressed_correct / total if total else 0.0),
    }


def run() -> dict[str, Any]:
    rows = _filtered_rows()
    solver_checks = [
        _solver_alignment("always_true", solver_always_true, rows),
        _solver_alignment("always_false", solver_always_false, rows),
        _solver_alignment("lc55_slack_dependent", lc55_slack_dependent, rows),
        _solver_alignment("lc55_reachability_optimism", lc55_reachability_optimism, rows),
    ]
    return {
        "accepted_reference_rows": sum(1 for row in rows if row["accepted_by_gate"]),
        "rejected_reference_rows": sum(1 for row in rows if not row["accepted_by_gate"]),
        "diagnostic_gate_results": [
            _gate("original_constant_pair", [solver_always_true, solver_always_false]),
            _gate("semantic_negative_controls", [lc55_slack_dependent, lc55_reachability_optimism]),
            _gate("falsifiable_negative_pair", [solver_always_false, lc55_slack_dependent]),
            _gate("good_solvers", [solver_greedy_rtl, solver_greedy_ltr, solver_dp_forward]),
        ],
        "solver_alignment_on_accepted_rows": solver_checks,
        "root_cause": (
            "minimum_margin_feasibility keeps only feasible compressed rows; "
            "always_true and lc55_reachability_optimism are therefore accidentally competent on the accepted surface. "
            "The gate threshold is not the root cause."
        ),
        "fix": "run_lc55_gate.py now uses solver_always_false and lc55_slack_dependent as the must-fail negative-control lane.",
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_130: LC55 Gate Repair",
        "",
        "## Reference Surface",
        "",
        f"- Accepted rows: `{report['accepted_reference_rows']}`",
        f"- Rejected rows: `{report['rejected_reference_rows']}`",
        "",
        "## Solver Alignment On Accepted Rows",
        "",
        "| Solver | Rows | Baseline alignment | Compressed alignment |",
        "|---|---:|---:|---:|",
    ]
    for row in report["solver_alignment_on_accepted_rows"]:
        lines.append(
            f"| `{row['solver']}` | {row['accepted_rows']} | {row['baseline_alignment']:.6f} | {row['compressed_alignment']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Gate Diagnostics",
            "",
            "| Suite | Ingest | Reason | Oracle alignment | Avg stability | Per solver |",
            "|---|---|---|---:|---:|---|",
        ]
    )
    for row in report["diagnostic_gate_results"]:
        lines.append(
            f"| `{row['name']}` | `{row['ingest']}` | `{row['reason']}` | "
            f"{row['oracle_alignment']:.6f} | {row['avg_perturbation_stability']:.6f} | `{row['per_solver']}` |"
        )
    lines.extend(
        [
            "",
            "## Root Cause",
            "",
            report["root_cause"],
            "",
            "## Fix",
            "",
            report["fix"],
            "",
            "## Artifacts",
            "",
            "- `runners/run_lc55_gate_repair.py`",
            "- `findings/FINDINGS_130.md`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run()
    _write_markdown(report)
    for row in report["diagnostic_gate_results"]:
        print(
            f"{row['name']}: ingest={row['ingest']} reason={row['reason']} "
            f"oracle_alignment={row['oracle_alignment']} avg_stability={row['avg_perturbation_stability']}"
        )
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
