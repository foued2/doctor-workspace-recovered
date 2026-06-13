"""
Fiber Exploration Test — Constrained Search Over Solver Perturbations

Tests existence of nontrivial fibers:
  exists s != s' such that dm(s) = dm(s') and tau(s) != tau(s')

Perturbation families (in priority order):
  A: Control-flow permutation (adjacency order, tie-breaking)
  B: Cost-field isomorphisms (weight transforms preserving shortest paths)
  C: Relaxation-rule microvariations (high risk / high signal)

Correct experimental design:
  For fixed k:
    1. sample s in F_k
    2. apply T_i in {Family A/B/C}
    3. accept only if dm(T_i(s)) = k
    4. measure divergence: tau(s) vs tau(T_i(s))

Compute:
  - fiber entropy: H(tau | dm=k)
  - intra-fiber Hamming diameter
  - cluster fragmentation inside dm-level sets
"""
from __future__ import annotations

import heapq
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE, lc743_oracle
from doctor.solvers.lc756.lc_756_solvers import SOLVER_REGISTRY

random.seed(42)


def compute_full_distances(times, n, k):
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


def compute_tau(solver_fn):
    trajectory = []
    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        oracle_result = lc743_oracle(case["times"], case["n"], case["k"])
        trajectory.append(1 if solver_result == oracle_result else 0)
    return tuple(trajectory)


def compute_dm_from_trajectory(tau):
    """Compute dm from tau (1=pass, 0=fail).

    dm counts failures using the fail-count convention:
    dm = #zeros (failures) in tau representation.
    """
    dm = 0
    for x in tau:
        if x == 0:
            dm += 1
    return dm


def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))


# ============================================================================
# Family A: Control-flow permutations
# ============================================================================

def permute_adjacency_order(solver_fn):
    """Swap adjacency iteration order (BFS/DFS tie-breaking variation)."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        for u in graph:
            graph[u] = sorted(graph[u], key=lambda x: -x[1])
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
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def permute_random_tiebreak(solver_fn):
    """Random tie-breaking in priority queue."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        INF = float("inf")
        dist = {i: INF for i in range(1, n + 1)}
        dist[k] = 0
        heap = [(0, k)]
        counter = 0
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            neighbors = list(graph[u])
            random.shuffle(neighbors)
            for v, w in neighbors:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    counter += 1
                    heapq.heappush(heap, (nd + random.random() * 1e-9, v))
        max_dist = 0
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def permute_reverse_adjacency(solver_fn):
    """Reverse adjacency list order."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        for u in graph:
            graph[u] = list(reversed(graph[u]))
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
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def permute_node_order(solver_fn):
    """Process nodes in different order (reverse ID)."""
    def perturbed(times, n, k):
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
            neighbors = sorted(graph[u], key=lambda x: -x[0])
            for v, w in neighbors:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        max_dist = 0
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def permute_deterministic_seed(solver_fn):
    """Deterministic traversal ordering based on node properties."""
    def perturbed(times, n, k):
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
            neighbors = sorted(graph[u], key=lambda x: (x[1], x[0]))
            for v, w in neighbors:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        max_dist = 0
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


# ============================================================================
# Family B: Cost-field isomorphisms (weight transforms preserving shortest paths)
# ============================================================================

def weight_add_constant(solver_fn, c=1):
    """w -> w + c (preserves shortest path ordering)."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w + c))
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
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def weight_scale_positive(solver_fn, alpha=2.0):
    """w -> alpha * w (alpha > 0 preserves shortest path ordering)."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, int(w * alpha)))
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
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


# ============================================================================
# Family C: Relaxation-rule microvariations
# ============================================================================

def relaxation_update_order_reversed(solver_fn):
    """Process edges in reverse order."""
    def perturbed(times, n, k):
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
            edges = list(graph[u])
            edges.reverse()
            for v, w in edges:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        max_dist = 0
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def relaxation_queue_stability(solver_fn):
    """Perturb queue insertion with tiny noise to break stability."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        INF = float("inf")
        dist = {i: INF for i in range(1, n + 1)}
        dist[k] = 0
        counter = 0
        heap = [(0, counter, k)]
        while heap:
            d, _, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, w in graph[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    counter += 1
                    heapq.heappush(heap, (nd, counter, v))
        max_dist = 0
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


# ============================================================================
# Main experiment
# ============================================================================

def run_fiber_exploration():
    print("=" * 60)
    print("Fiber Exploration Test")
    print("=" * 60)

    tau_data = {}
    dm_data = {}
    family_data = {}

    print("\nPhase 1: Computing baseline tau and dm for all solvers...")
    for name, meta in SOLVER_REGISTRY.items():
        solver_fn = meta["fn"]
        family = meta["direction"]
        tau = compute_tau(solver_fn)
        dm = compute_dm_from_trajectory(tau)
        tau_data[name] = tau
        dm_data[name] = dm
        family_data[name] = family

    dm_groups = defaultdict(list)
    for name, dm in dm_data.items():
        dm_groups[dm].append(name)

    print(f"\nBaseline: {len(dm_groups)} dm values, {len(set(tau_data.values()))} distinct tau")

    perturbation_families = {
        "A1_adjacency_permute": permute_adjacency_order,
        "A2_random_tiebreak": permute_random_tiebreak,
        "A3_reverse_adjacency": permute_reverse_adjacency,
        "A4_node_order": permute_node_order,
        "A5_deterministic_seed": permute_deterministic_seed,
        "B1_weight_add1": lambda fn: weight_add_constant(fn, 1),
        "B2_weight_scale2": lambda fn: weight_scale_positive(fn, 2.0),
        "C1_reversal_edges": relaxation_update_order_reversed,
        "C2_queue_stability": relaxation_queue_stability,
    }

    results = {}
    total_perturbations = 0
    dm_preserving = 0
    tau_divergent = 0
    fiber_entropy_by_dm = {}

    for dm_val, solvers in dm_groups.items():
        print(f"\n--- dm={dm_val} ({len(solvers)} solvers) ---")
        fiber_results = {}

        for solver_name in solvers:
            base_tau = tau_data[solver_name]
            base_dm = dm_data[solver_name]
            base_fn = SOLVER_REGISTRY[solver_name]["fn"]

            solver_perturbations = []

            for pert_name, pert_fn in perturbation_families.items():
                total_perturbations += 1
                perturbed_fn = pert_fn(base_fn)
                pert_tau = compute_tau(perturbed_fn)
                pert_dm = compute_dm_from_trajectory(pert_tau)

                dm_match = (pert_dm == base_dm)
                tau_diff = hamming_distance(base_tau, pert_tau)

                if dm_match:
                    dm_preserving += 1
                if tau_diff > 0:
                    tau_divergent += 1
                if dm_match and tau_diff > 0:
                    print(f"  {solver_name} + {pert_name}: dm_preserved, tau_diff={tau_diff}")

                solver_perturbations.append({
                    "perturbation": pert_name,
                    "dm_preserved": dm_match,
                    "tau_hamming": tau_diff,
                    "pert_dm": pert_dm,
                })

            fiber_results[solver_name] = solver_perturbations

        dm_preserving_count = sum(
            1 for sp in fiber_results.values()
            for p in sp if p["dm_preserved"]
        )
        tau_divergent_count = sum(
            1 for sp in fiber_results.values()
            for p in sp if p["dm_preserved"] and p["tau_hamming"] > 0
        )
        max_tau_div = max(
            (p["tau_hamming"] for sp in fiber_results.values() for p in sp if p["dm_preserved"]),
            default=0
        )

        distinct_tau_in_fiber = set()
        for solver_name in solvers:
            distinct_tau_in_fiber.add(tau_data[solver_name])

        fiber_entropy_by_dm[dm_val] = {
            "n_solvers": len(solvers),
            "distinct_tau_baseline": len(distinct_tau_in_fiber),
            "dm_preserving_perturbations": dm_preserving_count,
            "tau_divergent_within_dm": tau_divergent_count,
            "max_tau_hamming_preserved": max_tau_div,
            "perturbation_results": fiber_results,
        }

        print(f"  DM-preserving: {dm_preserving_count}, Tau-divergent within DM: {tau_divergent_count}, Max tau hamming: {max_tau_div}")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total perturbations: {total_perturbations}")
    print(f"DM-preserving: {dm_preserving_count}")
    print(f"Tau-divergent: {tau_divergent_count}")
    print(f"Tau-divergent within DM: {sum(1 for v in fiber_entropy_by_dm.values() for p in v['perturbation_results'].values() for pp in p if pp['dm_preserved'] and pp['tau_hamming'] > 0)}")

    print("\nFiber entropy analysis:")
    for dm_val, info in sorted(fiber_entropy_by_dm.items()):
        print(f"  dm={dm_val}: {info['distinct_tau_baseline']} distinct tau, "
              f"{info['dm_preserving_perturbations']} DM-preserving, "
              f"{info['tau_divergent_within_dm']} tau-divergent")

    any_divergence = any(
        info["tau_divergent_within_dm"] > 0
        for info in fiber_entropy_by_dm.values()
    )

    if any_divergence:
        regime = "REGIME_2_HIDDEN_MULTIPLICITY"
        print("\nResult: H(tau | dm=k) > 0 under control-flow perturbations")
        print("Interpretation: dm is coarse over execution policy equivalence classes")
    else:
        regime = "REGIME_1_TRUE_ATOMIC_FIBERS"
        print("\nResult: H(tau | dm=k) approx 0, all perturbations collapse back")
        print("Interpretation: dm is effectively tau-isomorphic on current generator")

    result = {
        "baseline": {
            "n_dm_values": len(dm_groups),
            "n_distinct_tau": len(set(tau_data.values())),
        },
        "fiber_analysis": fiber_entropy_by_dm,
        "regime": regime,
        "total_perturbations": total_perturbations,
    }

    output_path = ROOT / "results" / "fiber_exploration_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}")
    print("=" * 60)
    print("Fiber exploration complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_fiber_exploration()
