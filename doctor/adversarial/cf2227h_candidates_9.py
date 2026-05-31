"""FINDINGS 068 raw CF2227H perturbation and structural matrices.

This script keeps the two preregistered corpora separate:

- structural corpus: recurrence metrics only
- evaluation corpus: primitive collapse behavior only

It computes no correlation.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.cf2227h_candidates import cf2227h_reference
from generators.cf2227h_universal_generator import generate_inputs, random_tree
from identity_check_cf2227h import aggregation_depths, canonical_graph, run_identity_check
from phase5.observability_basis_discovery import cf2227h_degraded, primitive_names

DEFAULT_OUTPUT_DIR = Path("scratch/phase5_cf2227h_raw_perturbation_068")
ROOT_RAW_MATRIX_ARTIFACT = Path("FINDINGS_068_CF2227H_RAW_MATRICES.json")
FINDINGS_PATH = Path("FINDINGS_068.md")
FROZEN_SEED = 42
STRUCTURAL_PER_CLASS = 20
EVALUATION_RECORDS = 160


def safe_call(fn, *args: Any) -> dict[str, Any]:
    try:
        return {"ok": True, "output": fn(*args)}
    except Exception as exc:
        return {"ok": False, "output": None, "error": f"{type(exc).__name__}: {exc}"}


def star(n: int) -> list[tuple[int, int]]:
    return [(1, i) for i in range(2, n + 1)]


def path(n: int) -> list[tuple[int, int]]:
    return [(i, i + 1) for i in range(1, n)]


def complete_binary(levels: int) -> tuple[int, list[tuple[int, int]]]:
    n = 2**levels - 1
    edges = []
    for i in range(1, 2 ** (levels - 1)):
        edges.append((i, 2 * i))
        edges.append((i, 2 * i + 1))
    return n, edges


def caterpillar(spine: int, side_pattern: list[int]) -> tuple[int, list[tuple[int, int]]]:
    edges = [(i, i + 1) for i in range(1, spine)]
    nxt = spine + 1
    for i, leaves in enumerate(side_pattern, 1):
        for _ in range(leaves):
            edges.append((i, nxt))
            nxt += 1
    return nxt - 1, edges


def degrees(n: int, edges: Sequence[tuple[int, int]]) -> list[int]:
    deg = [0] * (n + 1)
    for u, v in edges:
        deg[u] += 1
        deg[v] += 1
    return deg[1:]


def is_path_shape(n: int, edges: Sequence[tuple[int, int]]) -> bool:
    ds = degrees(n, edges)
    return ds.count(1) == 2 and all(d <= 2 for d in ds)


def is_star_shape(n: int, edges: Sequence[tuple[int, int]]) -> bool:
    ds = degrees(n, edges)
    return max(ds) == n - 1 and ds.count(1) == n - 1


def is_complete_binary_shape(n: int, edges: Sequence[tuple[int, int]]) -> bool:
    ds = sorted(degrees(n, edges))
    return n in {7, 15, 31} and ds.count(1) == (n + 1) // 2 and ds.count(2) == 1 and ds.count(3) == (n - 3) // 2


def is_caterpillar_shape(n: int, edges: Sequence[tuple[int, int]]) -> bool:
    adj = [set() for _ in range(n + 1)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    non_leaves = [u for u in range(1, n + 1) if len(adj[u]) > 1]
    if not non_leaves:
        return False
    sub_edges = 0
    for u in non_leaves:
        for v in adj[u]:
            if v in non_leaves and u < v:
                sub_edges += 1
    ds = [sum(1 for v in adj[u] if v in non_leaves) for u in non_leaves]
    return sub_edges == len(non_leaves) - 1 and ds.count(1) <= 2 and all(d <= 2 for d in ds)


def classify_topology(n: int, edges: Sequence[tuple[int, int]]) -> str:
    if is_star_shape(n, edges):
        return "star"
    if is_path_shape(n, edges):
        return "path"
    if is_complete_binary_shape(n, edges):
        return "complete_binary_tree"
    if is_caterpillar_shape(n, edges):
        return "caterpillar"
    return "irregular"


def structural_corpus(seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    corpus: list[dict[str, Any]] = []
    for i in range(STRUCTURAL_PER_CLASS):
        n = 5 + i % 20
        corpus.append({"input_id": f"struct_star_{i:02d}", "topology_class": "star", "n": n, "edges": star(n)})
    for i in range(STRUCTURAL_PER_CLASS):
        n = 5 + i % 20
        corpus.append({"input_id": f"struct_path_{i:02d}", "topology_class": "path", "n": n, "edges": path(n)})
    for i in range(STRUCTURAL_PER_CLASS):
        n, edges = complete_binary([3, 4, 5][i % 3])
        corpus.append({"input_id": f"struct_complete_binary_tree_{i:02d}", "topology_class": "complete_binary_tree", "n": n, "edges": edges})
    for i in range(STRUCTURAL_PER_CLASS):
        spine = 5 + (i % 8)
        pattern = [0 if j in (0, spine - 1) else (i + j) % 4 for j in range(spine)]
        n, edges = caterpillar(spine, pattern)
        corpus.append({"input_id": f"struct_caterpillar_{i:02d}", "topology_class": "caterpillar", "n": n, "edges": edges})
    i = 0
    while i < STRUCTURAL_PER_CLASS:
        n = rng.randint(12, 40)
        edges = random_tree(n, rng)
        if classify_topology(n, edges) == "irregular":
            corpus.append({"input_id": f"struct_irregular_{i:02d}", "topology_class": "irregular", "n": n, "edges": edges})
            i += 1

    for record in corpus:
        observed = classify_topology(record["n"], record["edges"])
        if observed != record["topology_class"]:
            raise RuntimeError(f"topology label mismatch for {record['input_id']}: declared={record['topology_class']} observed={observed}")
    return corpus


def entropy(counts: Sequence[int]) -> float:
    total = sum(counts)
    if total <= 0 or len(counts) <= 1:
        return 0.0
    raw = -sum((count / total) * math.log2(count / total) for count in counts if count)
    return raw / math.log2(len(counts))


def recurrence_metrics(n: int, edges: Sequence[tuple[int, int]]) -> dict[str, Any]:
    states, transitions, _ = canonical_graph(n, tuple(tuple(edge) for edge in edges))
    depths = aggregation_depths(states, transitions)
    child_outgoing = Counter(src for src, label, _ in transitions if label == "child")
    collisions = [child_outgoing[state] for state in states if child_outgoing[state] > 1]
    by_depth: dict[int, list[int]] = defaultdict(list)
    for state in states:
        count = child_outgoing[state]
        if count > 1 and state in depths:
            by_depth[depths[state]].append(count)
    return {
        "max_collision_multiplicity": max((child_outgoing[state] for state in states), default=0),
        "mean_collision_multiplicity": round(statistics.fmean(collisions), 6) if collisions else 0.0,
        "collision_depth_profile": {
            str(depth): {
                "max": max(values),
                "mean": round(statistics.fmean(values), 6),
                "states": len(values),
            }
            for depth, values in sorted(by_depth.items())
        },
        "convergence_entropy": round(entropy(collisions), 6),
    }


def summarize_structural(rows: list[dict[str, Any]]) -> dict[str, Any]:
    maxes = [row["metrics"]["max_collision_multiplicity"] for row in rows]
    means = [row["metrics"]["mean_collision_multiplicity"] for row in rows]
    entropies = [row["metrics"]["convergence_entropy"] for row in rows]
    depth_values: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        for depth, profile in row["metrics"]["collision_depth_profile"].items():
            depth_values[depth].append(int(profile["max"]))
    return {
        "graphs": len(rows),
        "max_collision_multiplicity_distribution": {str(k): v for k, v in sorted(Counter(maxes).items())},
        "mean_collision_multiplicity": round(statistics.fmean(means), 6) if means else 0.0,
        "collision_depth_profile": {
            depth: {
                "max": max(values),
                "mean_max": round(statistics.fmean(values), 6),
                "graphs": len(values),
            }
            for depth, values in sorted(depth_values.items(), key=lambda item: int(item[0]))
        },
        "convergence_entropy": round(statistics.fmean(entropies), 6) if entropies else 0.0,
        "shallow_fraction_max_le_2": round(sum(1 for value in maxes if value <= 2) / max(len(maxes), 1), 6),
    }


def compute_structural_payload(seed: int) -> dict[str, Any]:
    records = structural_corpus(seed)
    rows = []
    for record in records:
        rows.append({
            "input_id": record["input_id"],
            "topology_class": record["topology_class"],
            "n": record["n"],
            "metrics": recurrence_metrics(record["n"], record["edges"]),
        })
    by_class = {
        cls: summarize_structural([row for row in rows if row["topology_class"] == cls])
        for cls in ["star", "path", "caterpillar", "complete_binary_tree", "irregular"]
    }
    aggregated = summarize_structural(rows)
    abort = aggregated["shallow_fraction_max_le_2"] >= 0.60
    if abort:
        raise RuntimeError("structural corpus abort: >=60% graphs have max_collision_multiplicity <= 2")
    return {
        "protocol": {
            "seed": seed,
            "topology_classification_precedes_metrics": True,
            "topology_classification_basis": "degree sequence, caterpillar spine structure, leaf count; no collision metrics",
            "structural_corpus_only": True,
            "evaluation_corpus_used": False,
            "hard_abort_rule": "abort if >=60% graphs have max_collision_multiplicity <= 2",
            "star_known_confound": "high multiplicity with zero entropy and depth 1",
        },
        "aggregated": aggregated,
        "by_class": by_class,
        "rows": rows,
    }


def evaluation_corpus(seed: int) -> list[dict[str, Any]]:
    records = generate_inputs(seed=seed, small_per_n=10, large_count=70)
    if len(records) != EVALUATION_RECORDS:
        raise RuntimeError(f"expected {EVALUATION_RECORDS} evaluation records, got {len(records)}")
    return records


def compute_evaluation_payload(seed: int) -> dict[str, Any]:
    records = evaluation_corpus(seed)
    names = primitive_names()
    correct = {name: 0 for name in names}
    totals = {name: 0 for name in names}
    raw_rows = []
    ref_ok = 0

    for record in records:
        n = int(record["n"])
        edges = [(int(u), int(v)) for u, v in record["edges"]]
        ref = safe_call(cf2227h_reference, n, edges)
        if not ref["ok"]:
            continue
        ref_ok += 1
        primitive_outputs = {}
        for name in names:
            got = safe_call(cf2227h_degraded, n, edges, name)
            totals[name] += 1
            primitive_outputs[name] = got["output"] if got["ok"] else got
            if got["ok"] and got["output"] == ref["output"]:
                correct[name] += 1
        raw_rows.append({
            "input_id": record["input_id"],
            "n": n,
            "reference": ref["output"],
            "primitive_outputs": primitive_outputs,
        })

    return {
        "protocol": {
            "seed": seed,
            "records": len(records),
            "reference_ok": ref_ok,
            "primitive_names": names,
            "evaluation_corpus_only": True,
            "structural_metrics_used": False,
            "collapse_score": "1 - cf2227h_degraded_accuracy_against_cf2227h_reference",
        },
        "collapse_score_by_primitive": {
            name: round(1.0 - correct[name] / max(totals[name], 1), 6)
            for name in names
        },
        "correct_by_primitive": correct,
        "total_by_primitive": totals,
        "raw_rows": raw_rows,
    }


def write_findings(payload: dict[str, Any], out_dir: Path) -> None:
    collapse = payload["evaluation_corpus"]["collapse_score_by_primitive"]
    structural = payload["structural_corpus"]
    lines = [
        "# FINDINGS 068 - Raw CF2227H Perturbation and Structural Matrices",
        "",
        "## Protocol",
        "",
        "- Correlation computed: `false`.",
        "- Structural corpus and evaluation corpus are separate objects.",
        "- Structural corpus: 100 topology-stratified graphs for recurrence metrics only.",
        "- Evaluation corpus: 160 CF2227H records for primitive collapse only.",
        "- Star topology is flagged as a known confound: high multiplicity, zero entropy, depth 1.",
        "",
        "## Evaluation Collapse Matrix",
        "",
        "| Primitive | collapse_score |",
        "|---|---:|",
    ]
    for name in payload["evaluation_corpus"]["protocol"]["primitive_names"]:
        lines.append(f"| {name} | {collapse[name]:.6f} |")
    lines.extend([
        "",
        "## Structural Metrics",
        "",
        f"- Aggregated shallow fraction `max_collision_multiplicity <= 2`: `{structural['aggregated']['shallow_fraction_max_le_2']}`",
        f"- Aggregated mean collision multiplicity: `{structural['aggregated']['mean_collision_multiplicity']}`",
        f"- Aggregated convergence entropy: `{structural['aggregated']['convergence_entropy']}`",
        "",
        "| Topology | Graphs | Max collision distribution | Mean collision | Convergence entropy |",
        "|---|---:|---|---:|---:|",
    ])
    for cls, summary in structural["by_class"].items():
        lines.append(
            f"| {cls} | {summary['graphs']} | "
            f"`{json.dumps(summary['max_collision_multiplicity_distribution'], sort_keys=True)}` | "
            f"{summary['mean_collision_multiplicity']:.6f} | {summary['convergence_entropy']:.6f} |"
        )
    lines.extend([
        "",
        "## Raw Artifacts",
        "",
        f"- `{ROOT_RAW_MATRIX_ARTIFACT}`",
        f"- `{out_dir / 'raw_matrices.json'}`",
        f"- `{out_dir / 'evaluation_raw_rows.json'}`",
        "- `phase5/cf2227h_raw_perturbation_068.py`",
    ])
    FINDINGS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=FROZEN_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    if args.seed != FROZEN_SEED:
        raise SystemExit("FINDINGS_066 freezes seed 42 for this run")

    run_identity_check()
    structural = compute_structural_payload(args.seed)
    evaluation = compute_evaluation_payload(args.seed)
    raw_rows = evaluation.pop("raw_rows")
    payload = {
        "protocol": {
            "correlation_computed": False,
            "seed": args.seed,
            "structural_and_evaluation_corpora_separate": True,
        },
        "structural_corpus": structural,
        "evaluation_corpus": evaluation,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    matrix_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    ROOT_RAW_MATRIX_ARTIFACT.write_text(matrix_text, encoding="utf-8")
    (args.output_dir / "raw_matrices.json").write_text(matrix_text, encoding="utf-8")
    (args.output_dir / "evaluation_raw_rows.json").write_text(json.dumps(raw_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_findings(payload, args.output_dir)
    print(f"wrote {FINDINGS_PATH} and {ROOT_RAW_MATRIX_ARTIFACT}")


if __name__ == "__main__":
    main()
