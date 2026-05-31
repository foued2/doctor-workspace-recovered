"""Produce a human-readable report for CF2227H disagreement regimes."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase_maps.cf2227h_clustering import _distance
from execution_matrices.cf2227h_execution_matrix import execute_matrix
from phase_maps.cf2227h_fingerprint_extractor import extract_fingerprints
from doctor.adversarial.cf2227h_bimaristan import GENERATORS


DEFAULT_FINGERPRINTS = Path("scratch/cf2227h_regime_discovery/fingerprints.json")
DEFAULT_CLUSTERS = Path("scratch/cf2227h_regime_discovery/clusters.json")
DEFAULT_OUTPUT = Path("scratch/cf2227h_regime_discovery/regime_report.md")


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [row["posthoc_tree_metrics"][key] for row in rows]
    return round(statistics.fmean(values), 3) if values else 0.0


def _failure_rates(rows: list[dict[str, Any]]) -> dict[str, float]:
    counts: Counter[str] = Counter()
    for row in rows:
        mismatches = row["disagreement_summary"]["proxy_mismatches_vs_reference"]
        correctness = row["disagreement_summary"]["correctness_vs_oracle"]
        if correctness is not None:
            for solver, ok in correctness.items():
                if not ok:
                    counts[solver] += 1
        else:
            for solver, mismatched in mismatches.items():
                if mismatched:
                    counts[solver] += 1
    return {solver: round(count / len(rows) * 100, 2) for solver, count in counts.items()}


def _representative(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(rows, key=lambda row: (row["n"], len(row["edges"]), row["input_id"]))


def _cluster_centroids(clusters: dict, fingerprints_by_id: dict[str, dict]) -> dict[int, list[float]]:
    centroids: dict[int, list[float]] = {}
    for cluster in clusters["clusters"]:
        if cluster["kind"] != "regime":
            continue
        vectors = [fingerprints_by_id[input_id]["vector"] for input_id in cluster["input_ids"]]
        width = max(len(vector) for vector in vectors)
        centroids[cluster["cluster_id"]] = [
            statistics.fmean(vector[i] if i < len(vector) else 0.0 for vector in vectors)
            for i in range(width)
        ]
    return centroids


def _assign_old_manifolds(centroids: dict[int, list[float]]) -> dict[str, list[int]]:
    assignments: dict[str, list[int]] = defaultdict(list)
    records = []
    for manifold_id, generator in GENERATORS.items():
        for idx, (n, edges) in enumerate(generator()):
            records.append(
                {
                    "input_id": f"legacy_{manifold_id}_{idx:02d}",
                    "n": n,
                    "edges": edges,
                    "manifold_id": manifold_id,
                }
            )
    matrix = execute_matrix(records)
    fingerprints = extract_fingerprints(matrix)
    source_by_id = {record["input_id"]: record["manifold_id"] for record in records}
    for fp in fingerprints:
        if not centroids:
            assignments[source_by_id[fp["input_id"]]].append(-1)
            continue
        cluster_id, _ = min(
            ((cluster_id, _distance(fp["vector"], centroid)) for cluster_id, centroid in centroids.items()),
            key=lambda item: item[1],
        )
        assignments[source_by_id[fp["input_id"]]].append(cluster_id)
    return {key: sorted(set(value)) for key, value in assignments.items()}


def build_report(fingerprints: list[dict[str, Any]], clusters: dict) -> str:
    fingerprints_by_id = {fp["input_id"]: fp for fp in fingerprints}
    lines = [
        "# CF2227H Failure-Driven Regime Discovery",
        "",
        "Clustering input: solver disagreement vectors only. Tree structure is used only below as post-hoc interpretation.",
        "",
    ]

    for cluster in clusters["clusters"]:
        if cluster["kind"] != "regime":
            continue
        rows = [fingerprints_by_id[input_id] for input_id in cluster["input_ids"]]
        rep = _representative(rows)
        lines.extend(
            [
                f"## Regime {cluster['cluster_id']}",
                f"- Size: {len(rows)} inputs",
                f"- Truth models: {cluster['truth_models']}",
                f"- Solvers failing/disagreeing: {_failure_rates(rows)}",
                (
                    "- Post-hoc structural correlates: "
                    f"avg_leaf_ratio={_mean(rows, 'leaf_ratio')}, "
                    f"avg_max_degree={_mean(rows, 'max_degree')}, "
                    f"avg_diameter={_mean(rows, 'diameter')}"
                ),
                f"- Representative minimal input: n={rep['n']}, edges={rep['edges']}",
                "",
            ]
        )

    noise = next((cluster for cluster in clusters["clusters"] if cluster["kind"] == "noise"), None)
    if noise:
        lines.extend(["## Noise", f"- Size: {noise['size']} inputs", ""])

    assignments = _assign_old_manifolds(_cluster_centroids(clusters, fingerprints_by_id))
    lines.extend(["## Legacy Manifold Projection", ""])
    for manifold_id, cluster_ids in sorted(assignments.items()):
        lines.append(f"- {manifold_id}: regimes {cluster_ids}")

    cat = set(assignments.get("caterpillar", []))
    bal = set(assignments.get("balanced_binary", []))
    collapse = bool(cat and bal and cat == bal)
    lines.extend(
        [
            "",
            "## Verdict",
            (
                "Manual manifolds are obsolete for clustering input: the discovered regimes are formed without labels or tree metrics."
            ),
            (
                "Caterpillar and balanced_binary collapse into the same discovered regime."
                if collapse
                else "Caterpillar and balanced_binary do not fully collapse under this run; keep them only as post-hoc probes, not clustering features."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fingerprints", type=Path, default=DEFAULT_FINGERPRINTS)
    parser.add_argument("--clusters", type=Path, default=DEFAULT_CLUSTERS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    fingerprints = json.loads(args.fingerprints.read_text(encoding="utf-8"))
    clusters = json.loads(args.clusters.read_text(encoding="utf-8"))
    report = build_report(fingerprints, clusters)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote regime report to {args.output}")


if __name__ == "__main__":
    main()
