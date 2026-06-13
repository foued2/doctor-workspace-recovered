"""
Kernel Analysis of dm over tau-space

Computes raw oracle trajectories tau(s) in {0,1}^{24} for all 30 solvers,
groups them by dm value, and analyzes the structure within each fiber.

This is the only non-redundant move that keeps tau(s) as the primary object.
"""
from __future__ import annotations

import heapq
import json
import math
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
    """Compute raw oracle trajectory tau(s) in {0,1}^{24}.

    Each entry: 1 if solver passes (matches oracle), 0 if solver fails.
    """
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
    """Compute dm from raw trajectory.

    dm = #zeros + 2 * #ones in the trajectory, but applied to the
    complementary representation (1-failure, 0-pass).
    """
    dm = 0
    for x in tau:
        if x > 0:
            dm += 1
        elif x < 0:
            dm += 2
    return dm


def compute_dm_from_trajectory(trajectory):
    """Compute dm from trajectory (1=fail, 0=pass representation)."""
    dm = 0
    for x in trajectory:
        if x > 0:
            dm += 1
        elif x < 0:
            dm += 2
    return dm


def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))


def run_kernel_analysis():
    print("=" * 60)
    print("Kernel Analysis of dm over tau-space")
    print("=" * 60)

    # Phase 1: Compute tau(s) for all solvers
    print("\nPhase 1: Computing tau(s) for all 30 solvers...")

    tau_data = {}
    trajectory_data = {}
    dm_data = {}
    label_data = {}
    family_data = {}

    for name, meta in SOLVER_REGISTRY.items():
        solver_fn = meta["fn"]
        family = meta["direction"]

        tau = compute_tau(solver_fn)
        trajectory = tuple(1 - x for x in tau)  # 1=fail, 0=pass representation
        dm = compute_dm_from_trajectory(trajectory)
        label = 1 if dm > 0 else 0

        tau_data[name] = tau
        trajectory_data[name] = trajectory
        dm_data[name] = dm
        label_data[name] = label
        family_data[name] = family

        print(f"  {name} ({family}): dm={dm}, label={label}, tau={tau}")

    # Phase 2: Group by dm value
    print("\nPhase 2: Grouping by dm value...")
    dm_groups = defaultdict(list)
    for name, dm in dm_data.items():
        dm_groups[dm].append(name)

    for dm_val in sorted(dm_groups.keys()):
        solvers = dm_groups[dm_val]
        taus = [tau_data[s] for s in solvers]
        trajectories = [trajectory_data[s] for s in solvers]

        n_distinct_tau = len(set(taus))
        n_distinct_traj = len(set(trajectories))

        if n_distinct_tau > 1:
            hamming_dists_tau = []
            for i in range(len(taus)):
                for j in range(i + 1, len(taus)):
                    hamming_dists_tau.append(hamming_distance(taus[i], taus[j]))
            avg_hamming_tau = sum(hamming_dists_tau) / len(hamming_dists_tau)
            max_hamming_tau = max(hamming_dists_tau)
        else:
            avg_hamming_tau = 0
            max_hamming_tau = 0

        print(f"\n  dm={dm_val} ({len(solvers)} solvers, {n_distinct_tau} distinct tau, {n_distinct_traj} distinct traj):")
        print(f"    Solvers: {solvers}")
        print(f"    Families: {[family_data[s] for s in solvers]}")
        print(f"    Avg Hamming (tau): {avg_hamming_tau:.2f}, Max Hamming (tau): {max_hamming_tau}")

    # Phase 3: Analyze kernel structure
    print("\nPhase 3: Kernel structure analysis...")

    kernel_summary = {}
    for dm_val, solvers in dm_groups.items():
        taus = [tau_data[s] for s in solvers]
        distinct_taus = list(set(taus))

        # Count how many solvers map to each distinct tau
        tau_to_solvers = defaultdict(list)
        for s in solvers:
            tau_to_solvers[tau_data[s]].append(s)

        # Compression ratio: solvers / distinct tau
        compression_ratio = len(solvers) / len(distinct_taus) if len(distinct_taus) > 0 else 0

        # Diversity of families within each tau-fiber
        family_diversity = {}
        for tau_val, fiber_solvers in tau_to_solvers.items():
            families = [family_data[s] for s in fiber_solvers]
            family_diversity[str(tau_val)] = {
                "n_solvers": len(fiber_solvers),
                "families": families,
                "n_distinct_families": len(set(families)),
            }

        kernel_summary[dm_val] = {
            "n_solvers": len(solvers),
            "n_distinct_tau": len(distinct_taus),
            "compression_ratio": compression_ratio,
            "tau_fibers": family_diversity,
        }

    # Phase 4: Cross-fiber analysis
    print("\nPhase 4: Cross-fiber analysis...")

    # For each pair of dm values, check if tau values are Hamming-close
    dm_vals = sorted(dm_groups.keys())
    cross_fiber_hamming = {}
    for i, dm_a in enumerate(dm_vals):
        for dm_b in dm_vals[i + 1:]:
            taus_a = [tau_data[s] for s in dm_groups[dm_a]]
            taus_b = [tau_data[s] for s in dm_groups[dm_b]]
            min_hamming = float("inf")
            for ta in taus_a:
                for tb in taus_b:
                    h = hamming_distance(ta, tb)
                    if h < min_hamming:
                        min_hamming = h
            cross_fiber_hamming[(dm_a, dm_b)] = min_hamming

    print("  Minimum Hamming distance between fibers:")
    for (dm_a, dm_b), min_h in cross_fiber_hamming.items():
        print(f"    dm={dm_a} <-> dm={dm_b}: {min_h}")

    # Phase 5: Compression summary
    print("\nPhase 5: Compression summary...")

    total_solvers = len(tau_data)
    total_distinct_tau = len(set(tau_data.values()))
    total_distinct_traj = len(set(trajectory_data.values()))
    total_distinct_dm = len(dm_groups)

    print(f"  Total solvers: {total_solvers}")
    print(f"  Distinct tau(s) vectors: {total_distinct_tau}")
    print(f"  Distinct trajectories: {total_distinct_traj}")
    print(f"  Distinct dm values: {total_distinct_dm}")
    print(f"  tau-compression ratio: {total_solvers / total_distinct_tau:.2f}")
    print(f"  dm-compression ratio: {total_solvers / total_distinct_dm:.2f}")

    # Information loss: what does dm erase?
    print("\n  Information loss (what dm erases):")
    for dm_val, summary in sorted(kernel_summary.items()):
        if summary["n_distinct_tau"] > 1:
            print(f"    dm={dm_val}: collapses {summary['n_solvers']} solvers into {summary['n_distinct_tau']} distinct tau-fibers")
            for tau_val, fiber in summary["tau_fibers"].items():
                print(f"      Fiber {tau_val}: {fiber['n_solvers']} solvers, families={fiber['families']}")

    # Save results
    result = {
        "tau_data": {k: list(map(int, v)) for k, v in tau_data.items()},
        "trajectory_data": {k: list(map(int, v)) for k, v in trajectory_data.items()},
        "dm_data": {k: int(v) for k, v in dm_data.items()},
        "label_data": {k: int(v) for k, v in label_data.items()},
        "family_data": family_data,
        "dm_groups": {str(k): v for k, v in dm_groups.items()},
        "kernel_summary": {str(k): v for k, v in kernel_summary.items()},
        "cross_fiber_hamming": {f"{a}-{b}": h for (a, b), h in cross_fiber_hamming.items()},
        "compression": {
            "total_solvers": total_solvers,
            "distinct_tau": total_distinct_tau,
            "distinct_traj": total_distinct_traj,
            "distinct_dm": total_distinct_dm,
            "tau_compression_ratio": total_solvers / total_distinct_tau,
            "dm_compression_ratio": total_solvers / total_distinct_dm,
        },
    }

    output_path = ROOT / "results" / "kernel_analysis_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print("=" * 60)
    print("Kernel analysis complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_kernel_analysis()
