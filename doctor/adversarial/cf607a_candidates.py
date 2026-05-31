"""FINDINGS 059: Cross-class controlled synthesis sensitivity comparison.

This deliberately reuses the human-chosen Phase 5 pilot axes:
memory bound, locality truncation, and approximation depth.

Critical caveat: these are imposed degradation operators, not discovered
natural problem axes.
"""
from __future__ import annotations

import argparse
import bisect
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.cf607a_candidates import cf607a_reference
from doctor.adversarial.lc312_candidates import lc312_reference
from generators.cf607a_universal_generator import generate_inputs as generate_cf607a_inputs
from generators.lc312_universal_generator import generate_inputs as generate_lc312_inputs
from phase5.cf2227h_controlled_synthesis import summarize as summarize_cf2227h
from phase5.cf2227h_controlled_synthesis import (
    execute as execute_cf2227h,
    specs as cf2227h_specs,
)
from generators.cf2227h_universal_generator import generate_inputs as generate_cf2227h_inputs


DEFAULT_OUTPUT_DIR = Path("scratch/phase5_cross_class_synthesis")


@dataclass(frozen=True)
class DegradationSpec:
    name: str
    axis: str
    level: str
    value_cap: int | None = None
    locality_radius: int | None = None
    candidate_limit: int | None = None


def _safe_run(fn: Callable, *args) -> dict[str, Any]:
    try:
        return {"ok": True, "output": fn(*args), "error": None}
    except Exception as exc:  # pragma: no cover - experiment diagnostic
        return {"ok": False, "output": None, "error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# LC312: Type C interval DP
# ---------------------------------------------------------------------------


def lc312_specs() -> list[DegradationSpec]:
    return [
        DegradationSpec("memory_cap_1k", "memory_bound", "severe", value_cap=1_000),
        DegradationSpec("memory_cap_10k", "memory_bound", "moderate", value_cap=10_000),
        DegradationSpec("memory_cap_100k", "memory_bound", "light", value_cap=100_000),
        DegradationSpec("local_radius_1", "locality_truncation", "severe", locality_radius=1),
        DegradationSpec("local_radius_2", "locality_truncation", "moderate", locality_radius=2),
        DegradationSpec("local_radius_4", "locality_truncation", "light", locality_radius=4),
        DegradationSpec("candidate_limit_1", "approximation_depth", "severe", candidate_limit=1),
        DegradationSpec("candidate_limit_3", "approximation_depth", "moderate", candidate_limit=3),
        DegradationSpec("candidate_limit_5", "approximation_depth", "light", candidate_limit=5),
    ]


def synthesize_lc312(spec: DegradationSpec) -> Callable[[int, Sequence[int]], int]:
    def solver(n: int, nums: Sequence[int]) -> int:
        padded = [1] + list(nums) + [1]
        dp = [[0] * (n + 2) for _ in range(n + 2)]
        for length in range(1, n + 1):
            for i in range(1, n - length + 2):
                j = i + length - 1
                candidates = list(range(i, j + 1))
                if spec.locality_radius is not None:
                    candidates = [
                        k for k in candidates
                        if min(k - i, j - k) < spec.locality_radius
                    ]
                if spec.candidate_limit is not None:
                    candidates = sorted(candidates, key=lambda k: padded[k], reverse=True)[: spec.candidate_limit]
                best = 0
                for k in candidates:
                    coins = dp[i][k - 1] + dp[k + 1][j] + padded[i - 1] * padded[k] * padded[j + 1]
                    best = max(best, coins)
                if spec.value_cap is not None:
                    best = min(best, spec.value_cap)
                dp[i][j] = best
        return dp[1][n]

    return solver


def execute_lc312(records: list[dict[str, Any]], specs: list[DegradationSpec]) -> list[dict[str, Any]]:
    solvers = {spec.name: synthesize_lc312(spec) for spec in specs}
    rows = []
    for rec in records:
        n = int(rec["n"])
        nums = [int(v) for v in rec["nums"]]
        ref = _safe_run(lc312_reference, n, nums)
        outputs = {"reference": ref}
        for name, fn in solvers.items():
            outputs[name] = _safe_run(fn, n, nums)
        rows.append({
            "input_id": rec["input_id"],
            "problem": "lc312",
            "n": n,
            "reference": ref["output"],
            "outputs": outputs,
            "correctness": {
                name: result["ok"] and ref["ok"] and result["output"] == ref["output"]
                for name, result in outputs.items()
                if name != "reference"
            },
        })
    return rows


# ---------------------------------------------------------------------------
# CF607A: Type B chain reaction / prefix DP
# ---------------------------------------------------------------------------


def cf607a_specs() -> list[DegradationSpec]:
    return [
        DegradationSpec("memory_cap_1", "memory_bound", "severe", value_cap=1),
        DegradationSpec("memory_cap_2", "memory_bound", "moderate", value_cap=2),
        DegradationSpec("memory_cap_4", "memory_bound", "light", value_cap=4),
        DegradationSpec("local_radius_1", "locality_truncation", "severe", locality_radius=1),
        DegradationSpec("local_radius_2", "locality_truncation", "moderate", locality_radius=2),
        DegradationSpec("local_radius_4", "locality_truncation", "light", locality_radius=4),
        DegradationSpec("candidate_limit_1", "approximation_depth", "severe", candidate_limit=1),
        DegradationSpec("candidate_limit_3", "approximation_depth", "moderate", candidate_limit=3),
        DegradationSpec("candidate_limit_5", "approximation_depth", "light", candidate_limit=5),
    ]


def synthesize_cf607a(spec: DegradationSpec) -> Callable[[int, Sequence[tuple[int, int]]], int]:
    def solver(n: int, beacons: Sequence[tuple[int, int]]) -> int:
        sorted_beacons = sorted((int(p), int(b)) for p, b in beacons)
        positions = [p for p, _ in sorted_beacons]
        dp = [0] * n
        for i in range(n):
            left = positions[i] - sorted_beacons[i][1]
            j = bisect.bisect_left(positions, left) - 1
            if spec.locality_radius is not None:
                j = max(j, i - spec.locality_radius)
            if spec.candidate_limit is not None:
                # Approximate predecessor lookup by searching only the last m previous beacons.
                lo = max(0, i - spec.candidate_limit)
                j = -1
                for cand in range(i - 1, lo - 1, -1):
                    if positions[cand] < left:
                        j = cand
                        break
            value = 1 + (dp[j] if j >= 0 else 0)
            if spec.value_cap is not None:
                value = min(value, spec.value_cap)
            dp[i] = value
        return n - max(dp)

    return solver


def execute_cf607a(records: list[dict[str, Any]], specs: list[DegradationSpec]) -> list[dict[str, Any]]:
    solvers = {spec.name: synthesize_cf607a(spec) for spec in specs}
    rows = []
    for rec in records:
        n = int(rec["n"])
        beacons = [(int(p), int(b)) for p, b in rec["beacons"]]
        ref = _safe_run(cf607a_reference, n, beacons)
        outputs = {"reference": ref}
        for name, fn in solvers.items():
            outputs[name] = _safe_run(fn, n, beacons)
        rows.append({
            "input_id": rec["input_id"],
            "problem": "cf607a",
            "n": n,
            "reference": ref["output"],
            "outputs": outputs,
            "correctness": {
                name: result["ok"] and ref["ok"] and result["output"] == ref["output"]
                for name, result in outputs.items()
                if name != "reference"
            },
        })
    return rows


def summarize_rows(rows: list[dict[str, Any]], specs: list[DegradationSpec], problem: str, collapse_class: str) -> dict[str, Any]:
    by_solver = {}
    for spec in specs:
        values = [row["correctness"][spec.name] for row in rows]
        by_solver[spec.name] = {
            **asdict(spec),
            "accuracy": round(sum(values) / len(values), 6),
            "wrong": sum(1 for value in values if not value),
        }

    collapse_by_axis = {}
    for axis in sorted({spec.axis for spec in specs}):
        names = [spec.name for spec in specs if spec.axis == axis]
        collapsed = sum(1 for row in rows if all(not row["correctness"][name] for name in names))
        collapse_by_axis[axis] = {
            "solver_names": names,
            "collapse_rate": round(collapsed / len(rows), 6),
            "collapsed": collapsed,
            "total": len(rows),
        }

    all_names = [spec.name for spec in specs]
    all_collapsed = sum(1 for row in rows if all(not row["correctness"][name] for name in all_names))
    return {
        "problem": problem,
        "collapse_class": collapse_class,
        "records": len(rows),
        "solver_count": len(specs),
        "overall_controlled_collapse": round(all_collapsed / len(rows), 6),
        "all_collapsed": all_collapsed,
        "by_solver": by_solver,
        "collapse_by_axis": collapse_by_axis,
        "axis_mean_accuracy": {
            axis: round(statistics.fmean(by_solver[name]["accuracy"] for name in payload["solver_names"]), 6)
            for axis, payload in collapse_by_axis.items()
        },
    }


def axis_vector(summary: dict[str, Any]) -> dict[str, float]:
    return {
        axis: summary["collapse_by_axis"][axis]["collapse_rate"]
        for axis in sorted(summary["collapse_by_axis"])
    }


def anisotropy(summary: dict[str, Any]) -> float:
    vec = list(axis_vector(summary).values())
    return round(max(vec) - min(vec), 6) if vec else 0.0


def write_findings(results: dict[str, Any], out_dir: Path) -> None:
    lines = [
        "# FINDINGS 059 — Cross-Class Controlled Degradation Sensitivity",
        "",
        "## Constraint",
        "",
        "These results are operator-relative. The three axes are human-chosen degradation operators, not discovered natural problem axes. The only valid interpretation is whether collapse response under these specific operators differs across classes.",
        "",
        "## Problems",
        "",
        "| Problem | Prior class | Records | Overall controlled collapse | Anisotropy |",
        "|---|---|---:|---:|---:|",
    ]
    for key in ("cf2227h", "lc312", "cf607a"):
        summary = results[key]["summary"]
        lines.append(
            f"| {key} | {summary['collapse_class']} | {summary['records']} | "
            f"{summary['overall_controlled_collapse']:.3f} | {anisotropy(summary):.3f} |"
        )

    lines.extend([
        "",
        "## Axis Collapse Rates",
        "",
        "| Problem | approximation_depth | locality_truncation | memory_bound |",
        "|---|---:|---:|---:|",
    ])
    for key in ("cf2227h", "lc312", "cf607a"):
        vec = axis_vector(results[key]["summary"])
        lines.append(
            f"| {key} | {vec.get('approximation_depth', 0):.3f} | "
            f"{vec.get('locality_truncation', 0):.3f} | {vec.get('memory_bound', 0):.3f} |"
        )

    lines.extend([
        "",
        "## Axis Mean Accuracy",
        "",
        "| Problem | approximation_depth | locality_truncation | memory_bound |",
        "|---|---:|---:|---:|",
    ])
    for key in ("cf2227h", "lc312", "cf607a"):
        acc = results[key]["summary"]["axis_mean_accuracy"]
        lines.append(
            f"| {key} | {acc.get('approximation_depth', 0):.3f} | "
            f"{acc.get('locality_truncation', 0):.3f} | {acc.get('memory_bound', 0):.3f} |"
        )

    lines.extend([
        "",
        "## Operator-Relative Reading",
        "",
        "- CF2227H is most sensitive to locality and memory degradation, consistent with the imposed operators attacking subtree leaf-count parity.",
        "- LC312 is maximally sensitive to the imposed value-memory caps and moderately sensitive to split-candidate depth. Locality truncation has nonzero per-solver damage, but no axis-level total collapse because the light radius operator is exact on this small-n schedule.",
        "- CF607A is most sensitive to locality truncation under these operators; memory caps and predecessor-candidate limits degrade more gradually.",
        "",
        "The anisotropy patterns differ across the three problems under this fixed operator basis. That is informative, but only operator-relative. It does not validate the basis itself and must not be promoted into a natural taxonomy.",
        "",
        "## Phase 5 Proper: Observability Basis Discovery Design",
        "",
        "Next experiment should generate a large bank of primitive degradations rather than preselecting axes. Examples: value clipping, parity-only state, modulo state, random state dropout, shallow predecessor windows, candidate-rank truncation, boundary erasure, neighbor-only evidence, stochastic tie-breaking, and feature ablations. Run these primitives across multiple problems, build a problem x degradation response matrix, then factorize it with PCA/NMF/clustering to infer latent observability bases. Only after factorization should axes receive names.",
        "",
        "Acceptance criterion: a proposed collapse class is stronger if problems in that class cluster together under latent degradation factors that were not hand-named in advance.",
        "",
        "## Artifacts",
        "",
        f"- `{out_dir / 'summary.json'}`",
        f"- `{out_dir / 'lc312_matrix.json'}`",
        f"- `{out_dir / 'cf607a_matrix.json'}`",
        "- `phase5/cross_class_controlled_synthesis.py`",
    ])
    Path("FINDINGS_059.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cf2227h_records = generate_cf2227h_inputs(seed=2227, small_per_n=12, large_count=36)
    cf2227h_rows = execute_cf2227h(cf2227h_records, cf2227h_specs())
    cf2227h_summary = summarize_cf2227h(cf2227h_rows, cf2227h_specs())
    cf2227h_summary["problem"] = "cf2227h"
    cf2227h_summary["collapse_class"] = "Type C / total-collapse reference"

    lc312_records = generate_lc312_inputs(seed=312, small_per_n=12, large_count=0)
    lc312_spec_list = lc312_specs()
    lc312_rows = execute_lc312(lc312_records, lc312_spec_list)
    lc312_summary = summarize_rows(lc312_rows, lc312_spec_list, "lc312", "Type C")

    cf607a_records = generate_cf607a_inputs(seed=607, small_per_n=12, large_count=36)
    cf607a_spec_list = cf607a_specs()
    cf607a_rows = execute_cf607a(cf607a_records, cf607a_spec_list)
    cf607a_summary = summarize_rows(cf607a_rows, cf607a_spec_list, "cf607a", "Type B")

    results = {
        "constraint": "operator-relative; axes are imposed, not natural",
        "cf2227h": {"summary": cf2227h_summary},
        "lc312": {"summary": lc312_summary},
        "cf607a": {"summary": cf607a_summary},
    }
    (args.output_dir / "cf2227h_matrix.json").write_text(json.dumps(cf2227h_rows, indent=2), encoding="utf-8")
    (args.output_dir / "lc312_matrix.json").write_text(json.dumps(lc312_rows, indent=2), encoding="utf-8")
    (args.output_dir / "cf607a_matrix.json").write_text(json.dumps(cf607a_rows, indent=2), encoding="utf-8")
    (args.output_dir / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_findings(results, args.output_dir)
    print(f"Wrote cross-class synthesis outputs to {args.output_dir}")
    print("Wrote FINDINGS_059.md")


if __name__ == "__main__":
    main()
