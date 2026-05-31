"""Phase 5 / FINDINGS 058: controlled heuristic synthesis for CF2227H.

Generate degraded solvers from the exact CF2227H reference along three axes:

- memory bound: cap stored subtree leaf counts before parity aggregation
- locality truncation: ignore leaf evidence farther than a bounded radius
- approximation depth: limit odd-leaf adjustment search over unpaired leaves
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.cf2227h_candidates import cf2227h_reference
from generators.cf2227h_universal_generator import generate_inputs


DEFAULT_OUTPUT_DIR = Path("scratch/phase5_cf2227h_synthesis")


@dataclass(frozen=True)
class DegradationSpec:
    name: str
    axis: str
    level: str
    memory_cap: int | None = None
    locality_radius: int | None = None
    candidate_limit: int | None = None
    ancestor_depth_limit: int | None = None


def _build_adj(n: int, edges: Sequence[tuple[int, int]]) -> list[list[int]]:
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u - 1].append(v - 1)
        adj[v - 1].append(u - 1)
    return adj


def _root_tree(adj: list[list[int]]) -> tuple[int, list[int], list[int], list[int]]:
    root = 0
    for i, row in enumerate(adj):
        if len(row) > 1:
            root = i
            break
    parent = [-1] * len(adj)
    depth = [0] * len(adj)
    order: list[int] = []
    stack = [root]
    parent[root] = root
    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if parent[v] == -1:
                parent[v] = u
                depth[v] = depth[u] + 1
                stack.append(v)
    return root, parent, depth, order


def _leaf_subtree_counts(
    adj: list[list[int]],
    root: int,
    parent: list[int],
    order: list[int],
    spec: DegradationSpec,
) -> list[int]:
    counts = [0] * len(adj)
    for u in reversed(order):
        if len(adj[u]) == 1 and u != root:
            raw = 1
        else:
            raw = sum(counts[v] for v in adj[u] if v != parent[u])
        if spec.memory_cap is not None:
            raw = min(raw, spec.memory_cap)
        counts[u] = raw
    return counts


def _local_leaf_counts(
    adj: list[list[int]],
    root: int,
    parent: list[int],
    order: list[int],
    depth: list[int],
    radius: int,
) -> list[int]:
    """Count descendant leaves only if they are within radius edges of node."""
    leaves_under: list[list[int]] = [[] for _ in adj]
    for u in reversed(order):
        if len(adj[u]) == 1 and u != root:
            leaves_under[u] = [u]
        else:
            merged: list[int] = []
            for v in adj[u]:
                if v != parent[u]:
                    merged.extend(leaves_under[v])
            leaves_under[u] = merged
    return [
        sum(1 for leaf in leaves_under[u] if depth[leaf] - depth[u] <= radius)
        for u in range(len(adj))
    ]


def _ancestor_within(
    anc: int,
    node: int,
    parent: list[int],
    root: int,
    depth_limit: int | None,
) -> bool:
    u = node
    walked = 0
    while u != root:
        if u == anc:
            return True
        if depth_limit is not None and walked >= depth_limit:
            return False
        u = parent[u]
        walked += 1
    return anc == root


def synthesize_solver(spec: DegradationSpec) -> Callable[[int, Sequence[tuple[int, int]]], int]:
    """Return a deterministic solver degraded from the reference computation."""

    def solver(n: int, edges: Sequence[tuple[int, int]]) -> int:
        adj = _build_adj(n, edges)
        root, parent, depth, order = _root_tree(adj)
        if spec.locality_radius is None:
            leaf_cnt = _leaf_subtree_counts(adj, root, parent, order, spec)
        else:
            leaf_cnt = _local_leaf_counts(adj, root, parent, order, depth, spec.locality_radius)
            if spec.memory_cap is not None:
                leaf_cnt = [min(value, spec.memory_cap) for value in leaf_cnt]

        leaves = [i for i, row in enumerate(adj) if len(row) == 1]
        total_leaves_observed = leaf_cnt[root]
        base = sum(leaf_cnt[u] % 2 for u in range(n) if u != root)
        if total_leaves_observed % 2 == 0:
            return base

        candidates = leaves
        if spec.candidate_limit is not None:
            candidates = sorted(leaves, key=lambda u: (depth[u], u), reverse=True)[: spec.candidate_limit]
        best = 10**9
        for unpaired in candidates:
            total = 0
            for u in range(n):
                if u == root:
                    continue
                if _ancestor_within(u, unpaired, parent, root, spec.ancestor_depth_limit):
                    cnt = max(0, leaf_cnt[u] - 1)
                else:
                    cnt = leaf_cnt[u]
                total += cnt % 2
            best = min(best, total)
        return best if best != 10**9 else base

    return solver


def specs() -> list[DegradationSpec]:
    return [
        DegradationSpec("memory_cap_1", "memory_bound", "severe", memory_cap=1),
        DegradationSpec("memory_cap_2", "memory_bound", "moderate", memory_cap=2),
        DegradationSpec("memory_cap_4", "memory_bound", "light", memory_cap=4),
        DegradationSpec("local_radius_1", "locality_truncation", "severe", locality_radius=1),
        DegradationSpec("local_radius_2", "locality_truncation", "moderate", locality_radius=2),
        DegradationSpec("local_radius_4", "locality_truncation", "light", locality_radius=4),
        DegradationSpec("candidate_limit_1", "approximation_depth", "severe", candidate_limit=1),
        DegradationSpec("candidate_limit_3", "approximation_depth", "moderate", candidate_limit=3),
        DegradationSpec("ancestor_depth_2", "approximation_depth", "local_adjustment", ancestor_depth_limit=2),
    ]


def _run_one(fn: Callable[[int, Sequence[tuple[int, int]]], int], n: int, edges: list[tuple[int, int]]) -> dict[str, Any]:
    try:
        return {"ok": True, "output": fn(n, edges), "error": None}
    except Exception as exc:  # pragma: no cover - experiment diagnostic
        return {"ok": False, "output": None, "error": f"{type(exc).__name__}: {exc}"}


def execute(records: list[dict[str, Any]], degradation_specs: list[DegradationSpec]) -> list[dict[str, Any]]:
    solvers = {spec.name: synthesize_solver(spec) for spec in degradation_specs}
    rows = []
    for rec in records:
        n = int(rec["n"])
        edges = [(int(u), int(v)) for u, v in rec["edges"]]
        ref = _run_one(cf2227h_reference, n, edges)
        outputs = {"reference": ref}
        for name, fn in solvers.items():
            outputs[name] = _run_one(fn, n, edges)
        rows.append(
            {
                "input_id": rec["input_id"],
                "n": n,
                "edges": edges,
                "reference": ref["output"],
                "outputs": outputs,
                "correctness": {
                    name: result["ok"] and ref["ok"] and result["output"] == ref["output"]
                    for name, result in outputs.items()
                    if name != "reference"
                },
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]], degradation_specs: list[DegradationSpec]) -> dict[str, Any]:
    spec_by_name = {spec.name: spec for spec in degradation_specs}
    by_solver: dict[str, dict[str, Any]] = {}
    for spec in degradation_specs:
        values = [row["correctness"][spec.name] for row in rows]
        by_n: dict[int, list[bool]] = defaultdict(list)
        for row in rows:
            by_n[int(row["n"])].append(row["correctness"][spec.name])
        by_solver[spec.name] = {
            **asdict(spec),
            "accuracy": round(sum(values) / len(values), 6),
            "wrong": sum(1 for v in values if not v),
            "by_n_accuracy": {
                str(n): round(sum(vals) / len(vals), 6)
                for n, vals in sorted(by_n.items())
            },
        }

    collapse_by_axis: dict[str, dict[str, Any]] = {}
    for axis in sorted({spec.axis for spec in degradation_specs}):
        names = [spec.name for spec in degradation_specs if spec.axis == axis]
        collapsed = 0
        total = 0
        by_n_counts: dict[int, Counter] = defaultdict(Counter)
        for row in rows:
            correctness = [row["correctness"][name] for name in names]
            if not correctness:
                continue
            total += 1
            is_collapsed = all(not value for value in correctness)
            collapsed += int(is_collapsed)
            by_n_counts[int(row["n"])]["collapsed" if is_collapsed else "noncollapsed"] += 1
        collapse_by_axis[axis] = {
            "solver_names": names,
            "collapse_rate": round(collapsed / total, 6) if total else 0.0,
            "collapsed": collapsed,
            "total": total,
            "by_n": {
                str(n): {
                    "collapsed": counts["collapsed"],
                    "total": counts["collapsed"] + counts["noncollapsed"],
                    "rate": round(counts["collapsed"] / (counts["collapsed"] + counts["noncollapsed"]), 6),
                }
                for n, counts in sorted(by_n_counts.items())
            },
        }

    all_names = [spec.name for spec in degradation_specs]
    all_collapsed = sum(1 for row in rows if all(not row["correctness"][name] for name in all_names))
    return {
        "records": len(rows),
        "solver_count": len(degradation_specs),
        "overall_controlled_collapse": round(all_collapsed / len(rows), 6) if rows else 0.0,
        "all_collapsed": all_collapsed,
        "by_solver": by_solver,
        "collapse_by_axis": collapse_by_axis,
        "axis_mean_accuracy": {
            axis: round(statistics.fmean(by_solver[name]["accuracy"] for name in payload["solver_names"]), 6)
            for axis, payload in collapse_by_axis.items()
        },
    }


def write_findings(summary: dict[str, Any], out_dir: Path) -> None:
    lines = [
        "# FINDINGS 058 — Controlled Heuristic Synthesis Framework",
        "",
        "## Claim",
        "",
        "Phase 5 starts by replacing hand-authored broken solvers with systematic degradations of a correct solver. "
        "For CF2227H, the reference computation is degraded along explicit observability channels: stored subtree-count memory, local evidence radius, and depth of the odd-leaf adjustment search.",
        "",
        "This shifts the experiment from 'which heuristic did a human write?' to 'which observability channel was removed, and how much?'",
        "",
        "## Framework",
        "",
        "| Axis | Degradation | CF2227H channel attacked |",
        "|---|---|---|",
        "| Memory bound | Cap subtree leaf counts before parity aggregation | Global multiplicity of leaves under each edge |",
        "| Locality truncation | Count only descendant leaves within radius r | Long-range leaf evidence needed for subtree parity |",
        "| Approximation depth | Limit candidate unpaired leaves or ancestor-walk depth | Odd-leaf correction search over global root-to-leaf paths |",
        "",
        "## CF2227H Pilot",
        "",
        f"Records: {summary['records']}. Synthetic solvers: {summary['solver_count']}. "
        f"Overall controlled collapse: {summary['overall_controlled_collapse']:.3f}.",
        "",
        "| Axis | Mean accuracy | Collapse rate within axis |",
        "|---|---:|---:|",
    ]
    for axis, mean_acc in sorted(summary["axis_mean_accuracy"].items()):
        payload = summary["collapse_by_axis"][axis]
        lines.append(f"| {axis} | {mean_acc:.3f} | {payload['collapse_rate']:.3f} |")

    lines.extend([
        "",
        "## Solver Accuracy",
        "",
        "| Solver | Axis | Level | Accuracy | Wrong |",
        "|---|---|---|---:|---:|",
    ])
    for name, payload in sorted(summary["by_solver"].items()):
        lines.append(
            f"| {name} | {payload['axis']} | {payload['level']} | "
            f"{payload['accuracy']:.3f} | {payload['wrong']} |"
        )

    lines.extend([
        "",
        "## Initial Interpretation",
        "",
        "The framework is intentionally not a final taxonomy result. It is a measurement scaffold for testing whether collapse regimes remain stable when the broken-solver ensemble is generated from controlled information loss rather than handcrafted intuitions.",
        "",
        "For CF2227H, memory and locality degradations attack the same mathematical bottleneck: subtree leaf-count parity. Approximation-depth degradations isolate the odd-leaf correction term. If future families show the same axis-specific collapse profile under synthesized degradations, the class is more likely problem-intrinsic; if profiles move with the axis mix, the class is observability-channel-intrinsic.",
        "",
        "## Artifacts",
        "",
        f"- `{out_dir / 'controlled_matrix.json'}`",
        f"- `{out_dir / 'summary.json'}`",
        "- `phase5/cf2227h_controlled_synthesis.py`",
    ])
    Path("FINDINGS_058.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2227)
    parser.add_argument("--small-per-n", type=int, default=12)
    parser.add_argument("--large-count", type=int, default=36)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    records = generate_inputs(args.seed, args.small_per_n, args.large_count)
    degradation_specs = specs()
    rows = execute(records, degradation_specs)
    summary = summarize(rows, degradation_specs)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "controlled_matrix.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_findings(summary, args.output_dir)
    print(f"Wrote {len(rows)} rows to {args.output_dir / 'controlled_matrix.json'}")
    print("Wrote FINDINGS_058.md")


if __name__ == "__main__":
    main()
