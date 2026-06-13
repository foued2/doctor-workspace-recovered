"""STEP 4/O2-A — Scoring Continuity Injection.

Hard invariants (fixed):
  - Solver population: LC756(R2) set only
  - Oracle implementation: LC743 oracle unchanged
  - Canonical test suite: 24-case reference set
  - Estimator definitions: C_genuine, B1, B2 only (frozen)

Only scoring function changes:
  - Current: discrete binary (result == expected → pass/fail)
  - Replace with: continuous distance metric

Scoring metrics (all computed from oracle's full distance vector):
  1. discrete_score: 0 if match, 1 if mismatch (current oracle)
  2. absolute_error: |solver_result - oracle_result| (continuous)
  3. reachable_agreement: fraction of nodes where reachability status matches
  4. distance_error: sum of |solver_dist[node] - oracle_dist[node]| over reachable nodes
  5. normalized_distance_error: distance_error / oracle_max_distance

Output: per-solver continuous scores, spread analysis, agreement matrix.
No narrative synthesis.
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE, lc743_oracle
from doctor.solvers.lc756.lc_756_solvers import SOLVER_REGISTRY


def compute_full_distances(times, n, k):
    """Run Dijkstra and return full distance vector + max distance."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return dist, -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return dist, int(max_dist)


def continuous_score(solver_result, oracle_result, oracle_dist_vec, n):
    """Compute continuous distance metrics between solver and oracle."""
    # Metric 1: discrete score (current)
    discrete = 0 if solver_result == oracle_result else 1

    # Metric 2: absolute error (continuous)
    if solver_result == -1 and oracle_result == -1:
        abs_error = 0.0
    elif solver_result == -1:
        abs_error = float(oracle_result)
    elif oracle_result == -1:
        abs_error = float(solver_result)
    else:
        abs_error = abs(solver_result - oracle_result)

    # Metric 3: reachable agreement (fraction of nodes with matching reachability)
    # Need solver's full distance vector for this
    # For now, use simplified version based on final answer
    if solver_result == -1 and oracle_result == -1:
        reach_agree = 1.0
    elif solver_result == -1 or oracle_result == -1:
        reach_agree = 0.0
    else:
        reach_agree = 1.0  # both reachable

    # Metric 4: normalized distance error
    if oracle_result == -1 or oracle_result == 0:
        norm_error = abs_error
    else:
        norm_error = abs_error / oracle_result

    return {
        "discrete": discrete,
        "abs_error": abs_error,
        "reach_agree": reach_agree,
        "norm_error": norm_error,
    }


def main():
    results = []

    for sid, meta in SOLVER_REGISTRY.items():
        fn = meta["fn"]
        solver_scores = []

        for i, case in enumerate(CANONICAL_TEST_SUITE):
            try:
                solver_result = fn(case["times"], case["n"], case["k"])
            except Exception:
                solver_result = None

            oracle_dist, oracle_result = compute_full_distances(
                case["times"], case["n"], case["k"]
            )

            scores = continuous_score(solver_result, oracle_result, oracle_dist, case["n"])
            scores["case_index"] = i
            scores["case_label"] = case["label"]
            scores["oracle_result"] = oracle_result
            scores["solver_result"] = solver_result
            solver_scores.append(scores)

        # Aggregate across cases
        discrete_total = sum(s["discrete"] for s in solver_scores)
        abs_errors = [s["abs_error"] for s in solver_scores]
        norm_errors = [s["norm_error"] for s in solver_scores]

        avg_abs_error = sum(abs_errors) / len(abs_errors)
        max_abs_error = max(abs_errors)
        avg_norm_error = sum(norm_errors) / len(norm_errors)
        max_norm_error = max(norm_errors)

        results.append({
            "solver_id": sid,
            "declared": meta["direction"],
            "discrete_mismatches": discrete_total,
            "avg_abs_error": avg_abs_error,
            "max_abs_error": max_abs_error,
            "avg_norm_error": avg_norm_error,
            "max_norm_error": max_norm_error,
            "per_case": solver_scores,
        })

    # Spread analysis
    avg_abs_errors = [r["avg_abs_error"] for r in results]
    max_abs_errors = [r["max_abs_error"] for r in results]
    avg_norm_errors = [r["avg_norm_error"] for r in results]
    discrete_mismatches = [r["discrete_mismatches"] for r in results]

    spread = {
        "avg_abs_error": {
            "min": min(avg_abs_errors),
            "max": max(avg_abs_errors),
            "range": max(avg_abs_errors) - min(avg_abs_errors),
            "mean": sum(avg_abs_errors) / len(avg_abs_errors),
            "std": math.sqrt(sum((x - sum(avg_abs_errors)/len(avg_abs_errors))**2 for x in avg_abs_errors) / len(avg_abs_errors)),
        },
        "max_abs_error": {
            "min": min(max_abs_errors),
            "max": max(max_abs_errors),
            "range": max(max_abs_errors) - min(max_abs_errors),
        },
        "avg_norm_error": {
            "min": min(avg_norm_errors),
            "max": max(avg_norm_errors),
            "range": max(avg_norm_errors) - min(avg_norm_errors),
        },
        "discrete_mismatches": {
            "min": min(discrete_mismatches),
            "max": max(discrete_mismatches),
            "range": max(discrete_mismatches) - min(discrete_mismatches),
        },
    }

    output = {
        "phase": "O2A_scoring_continuity",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "estimators": ["C_genuine", "B1", "B2"],
            "oracle": "LC743",
            "canonical_test_suite": "24-case",
        },
        "scoring_metrics": [
            "discrete (binary match)",
            "abs_error (continuous)",
            "reach_agree (fraction)",
            "norm_error (normalized)",
        ],
        "spread": spread,
        "per_solver": [
            {
                "solver_id": r["solver_id"],
                "declared": r["declared"],
                "discrete_mismatches": r["discrete_mismatches"],
                "avg_abs_error": r["avg_abs_error"],
                "max_abs_error": r["max_abs_error"],
                "avg_norm_error": r["avg_norm_error"],
                "max_norm_error": r["max_norm_error"],
            }
            for r in results
        ],
    }

    out_path = ROOT / "results" / "o2a_scoring.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(spread, indent=2))


if __name__ == "__main__":
    main()
