"""Run CF2227H solvers over unlabeled trees and record bounded truth separately."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from doctor.adversarial.cf2227h_candidates import cf2227h_reference
from doctor.adversarial.cf2227h_ground_truth import GroundTruthDomainError, cf2227h_brute_force


DEFAULT_INPUT = Path("scratch/cf2227h_regime_discovery/inputs.json")
DEFAULT_OUTPUT = Path("scratch/cf2227h_regime_discovery/execution_matrix.json")

def _build_adj(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u - 1].append(v - 1)
        adj[v - 1].append(u - 1)
    return adj


def _find_leaves(adj: list[list[int]]) -> list[int]:
    return [i for i, row in enumerate(adj) if len(row) == 1]


def _distances_from(start: int, adj: list[list[int]]) -> list[int]:
    dist = [-1] * len(adj)
    dist[start] = 0
    queue = [start]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def _leaf_distances(leaves: list[int], adj: list[list[int]]) -> dict[int, list[int]]:
    return {leaf: _distances_from(leaf, adj) for leaf in leaves}


def cf2227h_greedy_nearest_fast(n: int, edges: list[tuple[int, int]]) -> int:
    adj = _build_adj(n, edges)
    leaves = _find_leaves(adj)
    dist = _leaf_distances(leaves, adj)
    remaining = set(leaves)
    total = 0
    while len(remaining) >= 2:
        best = 10**9
        best_pair = None
        rlist = list(remaining)
        for i in range(len(rlist)):
            for j in range(i + 1, len(rlist)):
                d = dist[rlist[i]][rlist[j]]
                if d < best:
                    best = d
                    best_pair = (rlist[i], rlist[j])
        total += best
        remaining.discard(best_pair[0])
        remaining.discard(best_pair[1])
    return total


def cf2227h_pair_center_fast(n: int, edges: list[tuple[int, int]]) -> int:
    adj = _build_adj(n, edges)
    leaves = _find_leaves(adj)
    dist = _leaf_distances(leaves, adj)
    center = min(range(n), key=lambda u: max(dist[u][v] for v in leaves))
    center_dists = {v: dist[v][center] for v in leaves}
    remaining = set(leaves)
    total = 0
    while len(remaining) >= 2:
        rlist = sorted(remaining, key=lambda v: center_dists[v])
        u, v = rlist[0], rlist[1]
        total += dist[u][v]
        remaining.discard(u)
        remaining.discard(v)
    return total


def cf2227h_dfs_order_fast(n: int, edges: list[tuple[int, int]]) -> int:
    adj = _build_adj(n, edges)
    leaves = _find_leaves(adj)
    leaf_set = set(leaves)
    dist = _leaf_distances(leaves, adj)
    order: list[int] = []
    visited = [False] * n
    stack = [0]
    while stack:
        u = stack.pop()
        if visited[u]:
            continue
        visited[u] = True
        if u in leaf_set:
            order.append(u)
        for v in adj[u]:
            if not visited[v]:
                stack.append(v)
    return sum(dist[order[i]][order[i + 1]] for i in range(0, len(order) - 1, 2))


def cf2227h_greedy_farthest_fast(n: int, edges: list[tuple[int, int]]) -> int:
    adj = _build_adj(n, edges)
    leaves = _find_leaves(adj)
    dist = _leaf_distances(leaves, adj)
    remaining = set(leaves)
    total = 0
    while len(remaining) >= 2:
        best = -1
        best_pair = None
        rlist = list(remaining)
        for i in range(len(rlist)):
            for j in range(i + 1, len(rlist)):
                d = dist[rlist[i]][rlist[j]]
                if d > best:
                    best = d
                    best_pair = (rlist[i], rlist[j])
        total += best
        remaining.discard(best_pair[0])
        remaining.discard(best_pair[1])
    return total


SOLVERS: dict[str, Callable[[int, list[tuple[int, int]]], int]] = {
    "reference": cf2227h_reference,
    "greedy_nearest": cf2227h_greedy_nearest_fast,
    "pair_center": cf2227h_pair_center_fast,
    "dfs_order": cf2227h_dfs_order_fast,
    "greedy_farthest": cf2227h_greedy_farthest_fast,
}


def _normalize_edges(edges: list[list[int]] | list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(int(u), int(v)) for u, v in edges]


def _safe_run(fn: Callable[[int, list[tuple[int, int]]], int], n: int, edges: list[tuple[int, int]]) -> dict:
    started = perf_counter()
    try:
        output = fn(n, edges)
        return {
            "status": "ok",
            "output": output,
            "runtime_ms": round((perf_counter() - started) * 1000, 3),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - failures are part of the matrix.
        return {
            "status": "error",
            "output": None,
            "runtime_ms": round((perf_counter() - started) * 1000, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }


def execute_record(record: dict[str, Any]) -> dict[str, Any]:
    n = int(record["n"])
    edges = _normalize_edges(record["edges"])
    solver_results = {name: _safe_run(fn, n, edges) for name, fn in SOLVERS.items()}

    oracle = {"available": False, "output": None, "error": None}
    if n <= 12:
        try:
            oracle["output"] = cf2227h_brute_force(n, edges)
            oracle["available"] = True
        except GroundTruthDomainError as exc:
            oracle["error"] = str(exc)

    pairwise: dict[str, bool | None] = {}
    names = list(SOLVERS)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            lres = solver_results[left]
            rres = solver_results[right]
            key = f"{left}__vs__{right}"
            if lres["status"] != "ok" or rres["status"] != "ok":
                pairwise[key] = None
            else:
                pairwise[key] = lres["output"] != rres["output"]

    correctness = None
    if oracle["available"]:
        correctness = {
            name: result["status"] == "ok" and result["output"] == oracle["output"]
            for name, result in solver_results.items()
        }

    ref_output = solver_results["reference"]["output"]
    proxy_mismatches = {
        name: (
            None
            if name == "reference" or ref_output is None or result["status"] != "ok"
            else result["output"] != ref_output
        )
        for name, result in solver_results.items()
    }

    return {
        "input_id": record["input_id"],
        "n": n,
        "edges": edges,
        "truth_model": "oracle" if oracle["available"] else "non_oracle_disagreement_only",
        "oracle": oracle,
        "solver_outputs": solver_results,
        "ref_output": ref_output,
        "correctness_vs_oracle": correctness,
        "pairwise_disagreements": pairwise,
        "proxy_mismatches_vs_reference": proxy_mismatches,
        "any_disagreement": any(value is True for value in pairwise.values()),
        "any_failure": any(result["status"] != "ok" for result in solver_results.values()),
        "runtime_ms_total": round(
            math.fsum(result["runtime_ms"] for result in solver_results.values()), 3
        ),
    }


def execute_matrix(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [execute_record(record) for record in records]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    records = json.loads(args.input.read_text(encoding="utf-8"))
    matrix = execute_matrix(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    disagreements = sum(1 for row in matrix if row["any_disagreement"])
    oracle_rows = sum(1 for row in matrix if row["truth_model"] == "oracle")
    print(
        f"Wrote {len(matrix)} executions to {args.output} "
        f"({oracle_rows} oracle rows, {disagreements} disagreement rows)"
    )


if __name__ == "__main__":
    main()
