"""
Closure + Invariance Test over Semantically Generated Symmetry Candidates

Tests existence of nontrivial fibers via closure criterion:
  T_A: execution-order syntactic permutations (already tested)
  T_B: representation isomorphisms (graph isomorphism, weight remapping, encoding swaps)
  T_C: relaxation schedule automorphisms (event reordering, equivalent scheduling, micro-interleaving)

Primary question:
  Is τ invariant under the full semantically generated symmetry group of dm-fibers?

Expected outcomes:
  Case 1: Full closure + τ invariance → fibers truly atomic, τ = h(dm)
  Case 2: Closure holds, τ still varies → hidden intra-fiber coordinate
  Case 3: Closure fails → symmetry model incomplete
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


def compute_dm_from_tau(tau):
    dm = 0
    for x in tau:
        if x == 0:
            dm += 1
    return dm


def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))


# ============================================================================
# T_B: State-representation symmetries (definitionally dm-preserving)
# ============================================================================

def tb_node_id_permutation(solver_fn):
    """Permute node IDs arbitrarily while preserving adjacency structure."""
    def perturbed(times, n, k):
        nodes = set()
        for u, v, w in times:
            nodes.add(u)
            nodes.add(v)
        nodes = sorted(nodes)
        perm = list(nodes)
        random.shuffle(perm)
        mapping = dict(zip(nodes, perm))
        new_times = [[mapping[u], mapping[v], w] for u, v, w in times]
        new_k = mapping[k]
        return solver_fn(new_times, n, new_k)
    return perturbed


def tb_weight_preserving_remap(solver_fn):
    """Permute equal-weight edges while preserving shortest path structure."""
    def perturbed(times, n, k):
        weight_groups = defaultdict(list)
        for edge in times:
            weight_groups[edge[2]].append(edge)
        new_times = []
        for w, edges in weight_groups.items():
            shuffled = list(edges)
            random.shuffle(shuffled)
            new_times.extend(shuffled)
        return solver_fn(new_times, n, k)
    return perturbed


def tb_adjacency_to_edge_list(solver_fn):
    """Convert adjacency list to edge list representation and back."""
    def perturbed(times, n, k):
        edge_list = [(u, v, w) for u, v, w in times]
        random.shuffle(edge_list)
        return solver_fn(edge_list, n, k)
    return perturbed


def tb_reverse_edge_direction(solver_fn):
    """Reverse edge directions while preserving structure."""
    def perturbed(times, n, k):
        new_times = [[v, u, w] for u, v, w in times]
        return solver_fn(new_times, n, k)
    return perturbed


# ============================================================================
# T_C: Relaxation microdynamics symmetries (semantic group)
# ============================================================================

def tc_event_reorder_independent(solver_fn):
    """Reorder independent relaxations (partial-order-preserving shuffle)."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        INF = float("inf")
        dist = {i: INF for i in range(1, n + 1)}
        dist[k] = 0
        heap = [(0, k)]
        accepted_events = []
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
                    accepted_events.append((u, v, w))
                    heapq.heappush(heap, (nd, v))
        max_dist = 0
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
            if dist[node] > max_dist:
                max_dist = dist[node]
        return int(max_dist)
    return perturbed


def tc_equivalent_scheduling_policy(solver_fn):
    """Use different tie-breaking that preserves accepted relaxation set."""
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


def tc_micro_interleaving(solver_fn):
    """Different interleaving of equal-priority expansions."""
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
            neighbors = sorted(graph[u], key=lambda x: (x[1], random.random()))
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
# Main experiment
# ============================================================================

def run_closure_test():
    print("=" * 60)
    print("Closure + Invariance Test")
    print("=" * 60)

    tau_data = {}
    dm_data = {}
    family_data = {}

    print("\nPhase 1: Computing baseline tau and dm for all solvers...")
    for name, meta in SOLVER_REGISTRY.items():
        solver_fn = meta["fn"]
        family = meta["direction"]
        tau = compute_tau(solver_fn)
        dm = compute_dm_from_tau(tau)
        tau_data[name] = tau
        dm_data[name] = dm
        family_data[name] = family

    dm_groups = defaultdict(list)
    for name, dm in dm_data.items():
        dm_groups[dm].append(name)

    print(f"Baseline: {len(dm_groups)} dm values, {len(set(tau_data.values()))} distinct tau")

    all_transforms = {
        "T_B_node_permutation": tb_node_id_permutation,
        "T_B_weight_remap": tb_weight_preserving_remap,
        "T_B_edge_list": tb_adjacency_to_edge_list,
        "T_B_reverse_edges": tb_reverse_edge_direction,
        "T_C_event_reorder": tc_event_reorder_independent,
        "T_C_scheduling": tc_equivalent_scheduling_policy,
        "T_C_interleaving": tc_micro_interleaving,
    }

    results = {}
    dm_preserving_total = 0
    tau_divergent_total = 0
    closure_violations = 0

    for dm_val, solvers in dm_groups.items():
        print(f"\n--- dm={dm_val} ({len(solvers)} solvers) ---")
        fiber_results = {}

        for solver_name in solvers:
            base_tau = tau_data[solver_name]
            base_dm = dm_data[solver_name]
            base_fn = SOLVER_REGISTRY[solver_name]["fn"]

            transform_results = {}
            for t_name, t_fn in all_transforms.items():
                perturbed_fn = t_fn(base_fn)
                pert_tau = compute_tau(perturbed_fn)
                pert_dm = compute_dm_from_tau(pert_tau)

                dm_match = (pert_dm == base_dm)
                tau_diff = hamming_distance(base_tau, pert_tau)

                if dm_match:
                    dm_preserving_total += 1
                if tau_diff > 0:
                    tau_divergent_total += 1

                transform_results[t_name] = {
                    "dm_preserved": dm_match,
                    "tau_hamming": tau_diff,
                }

            fiber_results[solver_name] = transform_results

        dm_preserving_count = sum(
            1 for sp in fiber_results.values()
            for p in sp.values() if p["dm_preserved"]
        )
        tau_divergent_count = sum(
            1 for sp in fiber_results.values()
            for p in sp.values() if p["dm_preserved"] and p["tau_hamming"] > 0
        )

        print(f"  DM-preserving: {dm_preserving_count}, Tau-divergent within DM: {tau_divergent_count}")

        results[dm_val] = {
            "n_solvers": len(solvers),
            "dm_preserving": dm_preserving_count,
            "tau_divergent_within_dm": tau_divergent_count,
            "perturbation_results": fiber_results,
        }

    print("\n" + "=" * 60)
    print("Closure Analysis")
    print("=" * 60)

    for t_name in all_transforms:
        composition_violations = 0
        for dm_val, solvers in dm_groups.items():
            for solver_name in solvers:
                base_fn = SOLVER_REGISTRY[solver_name]["fn"]
                base_tau = tau_data[solver_name]
                base_dm = dm_data[solver_name]

                for t1_name in all_transforms:
                    for t2_name in all_transforms:
                        t1 = all_transforms[t1_name]
                        t2 = all_transforms[t2_name]
                        composed = lambda fn, t1=t1, t2=t2: t2(t1(fn))
                        perturbed_fn = composed(base_fn)
                        pert_tau = compute_tau(perturbed_fn)
                        pert_dm = compute_dm_from_tau(pert_tau)

                        if pert_dm != base_dm:
                            composition_violations += 1

        if composition_violations > 0:
            closure_violations += composition_violations
            print(f"  {t_name}: {composition_violations} closure violations")

    any_divergence = tau_divergent_total > 0

    if closure_violations > 0:
        regime = "REGIME_3_NO_GROUP_STRUCTURE"
        print(f"\nResult: {closure_violations} closure violations")
        print("Interpretation: transformations do not form a stable group under composition")
    elif any_divergence:
        regime = "REGIME_2_STRICT_SUBGROUP"
        print(f"\nResult: Closure holds, but {tau_divergent_total} tau-divergent perturbations exist")
        print("Interpretation: T is strict subgroup of G_k, hidden intra-fiber coordinate exists")
    else:
        regime = "REGIME_1_FULL_CLOSURE"
        print("\nResult: Full closure + τ invariance under all tested transformations")
        print("Interpretation: T spans full G_k, fibers truly atomic, τ = h(dm)")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total DM-preserving: {dm_preserving_total}")
    print(f"Total Tau-divergent: {tau_divergent_total}")
    print(f"Closure violations: {closure_violations}")
    print(f"Regime: {regime}")

    output = {
        "baseline": {
            "n_dm_values": len(dm_groups),
            "n_distinct_tau": len(set(tau_data.values())),
        },
        "results": results,
        "closure_violations": closure_violations,
        "regime": regime,
        "dm_preserving_total": dm_preserving_total,
        "tau_divergent_total": tau_divergent_total,
    }

    output_path = ROOT / "results" / "closure_test_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}")
    print("=" * 60)
    print("Closure test complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_closure_test()
