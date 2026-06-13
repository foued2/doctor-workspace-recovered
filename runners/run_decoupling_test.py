"""Decoupling Test — Identifiability Hinge.

Can two solvers with identical dm trajectories have different oracle outputs?

dm trajectory = length-24 binary vector (pass/fail per test case)
Oracle output = binary label: label = 1 if dm > 0 else 0

Mathematical fact: two solvers with identical dm trajectories have identical
dm counts, hence identical labels. The binary label is trivially determined
by the trajectory.

Non-trivial question: does the dm trajectory determine phi(s) (continuous
features) and perturbation response? If not, dm is a coarse sufficient
statistic, not a complete quotient coordinate.

Test design:
  Phase 1: Compute per-case dm trajectories for all 30 solvers
  Phase 2: Find groups with identical trajectories
  Phase 3: For each group, compare phi(s) values
  Phase 4: For each group, compare perturbation responses
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

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
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


def compute_dm_trajectory(solver_fn):
    """Compute per-case pass/fail vector (length 24)."""
    trajectory = []
    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        _, oracle_result = compute_full_distances(case["times"], case["n"], case["k"])
        trajectory.append(1 if solver_result != oracle_result else 0)
    return tuple(trajectory)


def compute_continuous_features(solver_fn):
    abs_errors = []
    norm_errors = []
    reach_agrees = []
    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        oracle_dist, oracle_result = compute_full_distances(case["times"], case["n"], case["k"])

        if solver_result == -1 and oracle_result == -1:
            abs_error = 0.0
        elif solver_result == -1:
            abs_error = float(oracle_result)
        elif oracle_result == -1:
            abs_error = float(solver_result)
        else:
            abs_error = abs(solver_result - oracle_result)

        if oracle_result == -1 or oracle_result == 0:
            norm_error = abs_error
        else:
            norm_error = abs_error / oracle_result

        if solver_result == -1 and oracle_result == -1:
            reach = 1.0
        elif solver_result == -1 or oracle_result == -1:
            reach = 0.0
        else:
            reach = 1.0

        abs_errors.append(abs_error)
        norm_errors.append(norm_error)
        reach_agrees.append(reach)

    avg_abs = sum(abs_errors) / len(abs_errors)
    max_abs = max(abs_errors)
    avg_norm = sum(norm_errors) / len(norm_errors)
    max_norm = max(norm_errors)
    avg_reach = sum(reach_agrees) / len(reach_agrees)

    max_dist_errors = []
    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        _, oracle_result = compute_full_distances(case["times"], case["n"], case["k"])
        if solver_result == -1 and oracle_result == -1:
            max_dist_errors.append(0.0)
        elif solver_result == -1:
            max_dist_errors.append(float(oracle_result))
        elif oracle_result == -1:
            max_dist_errors.append(float(solver_result))
        else:
            max_dist_errors.append(abs(solver_result - oracle_result))

    avg_max_dist = sum(max_dist_errors) / len(max_dist_errors)

    return [avg_abs, max_abs, avg_norm, max_norm, avg_reach, avg_max_dist]


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def perturb_weight_condition(condition_type):
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
            for v, w in graph[u]:
                if condition_type == "skip_heavy" and w > 1:
                    continue
                if condition_type == "skip_light" and w <= 1:
                    continue
                if condition_type == "skip_medium" and not (1 < w <= 5):
                    continue
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


def perturb_early_stop(stop_node):
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
            if u == stop_node:
                break
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


def perturb_dijkstra_variant(variant):
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        INF = float("inf")
        dist = {i: INF for i in range(1, n + 1)}
        dist[k] = 0

        if variant == "no_decrease_key":
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
        elif variant == "bfs_no_weights":
            from collections import deque
            queue = deque([k])
            visited = {k}
            while queue:
                u = queue.popleft()
                for v, w in graph[u]:
                    if v not in visited:
                        visited.add(v)
                        dist[v] = dist[u] + 1
                        queue.append(v)
        elif variant == "reversed_relaxation":
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


def compute_perturbation_response(solver_fn, baseline_label, baseline_features):
    """Compute perturbation response profile for a solver."""
    responses = []

    # Weight conditions
    for cond in ["skip_heavy", "skip_light", "skip_medium"]:
        pf = perturb_weight_condition(cond)
        dm = sum(1 for case in CANONICAL_TEST_SUITE
                 if (pf(case["times"], case["n"], case["k"]))
                 != compute_full_distances(case["times"], case["n"], case["k"])[1])
        features = compute_continuous_features(pf)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(baseline_features, features)
        responses.append({
            "perturbation": f"weight_{cond}",
            "dm": dm,
            "label": label,
            "label_changed": label != baseline_label,
            "delta_phi": round(delta_phi, 4),
        })

    # Early stops
    for stop_node in [3, 5, 7]:
        pf = perturb_early_stop(stop_node)
        dm = sum(1 for case in CANONICAL_TEST_SUITE
                 if (pf(case["times"], case["n"], case["k"]))
                 != compute_full_distances(case["times"], case["n"], case["k"])[1])
        features = compute_continuous_features(pf)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(baseline_features, features)
        responses.append({
            "perturbation": f"early_stop_{stop_node}",
            "dm": dm,
            "label": label,
            "label_changed": label != baseline_label,
            "delta_phi": round(delta_phi, 4),
        })

    # Dijkstra variants
    for variant in ["no_decrease_key", "bfs_no_weights", "reversed_relaxation"]:
        pf = perturb_dijkstra_variant(variant)
        dm = sum(1 for case in CANONICAL_TEST_SUITE
                 if (pf(case["times"], case["n"], case["k"]))
                 != compute_full_distances(case["times"], case["n"], case["k"])[1])
        features = compute_continuous_features(pf)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(baseline_features, features)
        responses.append({
            "perturbation": f"variant_{variant}",
            "dm": dm,
            "label": label,
            "label_changed": label != baseline_label,
            "delta_phi": round(delta_phi, 4),
        })

    return responses


def main():
    print("=" * 70)
    print("DECOUPLING TEST — IDENTIFIABILITY HINGE")
    print("=" * 70)

    # Phase 1: Compute dm trajectories for all 30 solvers
    print("\nPhase 1: Computing dm trajectories...")
    solvers = {}
    for sid, meta in SOLVER_REGISTRY.items():
        fn = meta["fn"]
        trajectory = compute_dm_trajectory(fn)
        dm = sum(trajectory)
        label = 1 if dm > 0 else 0
        features = compute_continuous_features(fn)
        solvers[sid] = {
            "trajectory": trajectory,
            "dm": dm,
            "label": label,
            "features": features,
            "direction": meta["direction"],
        }
        print(f"  {sid}: dm={dm}, label={label}, direction={meta['direction']}, "
              f"trajectory_sum={sum(trajectory)}")

    # Phase 2: Find groups with identical dm trajectories
    print("\nPhase 2: Finding groups with identical trajectories...")
    trajectory_groups = {}
    for sid, data in solvers.items():
        key = data["trajectory"]
        if key not in trajectory_groups:
            trajectory_groups[key] = []
        trajectory_groups[key].append(sid)

    print(f"  Total unique trajectories: {len(trajectory_groups)}")
    print(f"  Groups with >1 solver:")
    for traj, sids in sorted(trajectory_groups.items(), key=lambda x: -len(x[1])):
        if len(sids) > 1:
            directions = [solvers[s]["direction"] for s in sids]
            print(f"    trajectory (dm={sum(traj)}): {sids} ({directions})")

    # Phase 3: Compare phi(s) values within each group
    print("\nPhase 3: Comparing phi(s) within trajectory groups...")
    phi_divergence_results = []
    for traj, sids in trajectory_groups.items():
        if len(sids) < 2:
            continue
        group_features = {s: solvers[s]["features"] for s in sids}
        # Compute pairwise feature distances
        max_dist = 0.0
        min_dist = float("inf")
        avg_dist = 0.0
        n_pairs = 0
        for i, s1 in enumerate(sids):
            for s2 in sids[i + 1:]:
                d = euclidean(group_features[s1], group_features[s2])
                max_dist = max(max_dist, d)
                min_dist = min(min_dist, d)
                avg_dist += d
                n_pairs += 1
        avg_dist /= n_pairs if n_pairs > 0 else 1

        # Compute pairwise cosine similarity
        cos_sims = []
        for i, s1 in enumerate(sids):
            for s2 in sids[i + 1:]:
                c = cosine_similarity(group_features[s1], group_features[s2])
                cos_sims.append(c)

        result = {
            "trajectory_dm": sum(traj),
            "solvers": sids,
            "directions": [solvers[s]["direction"] for s in sids],
            "pairwise_euclidean": {
                "max": round(max_dist, 4),
                "min": round(min_dist, 4),
                "avg": round(avg_dist, 4),
            },
            "pairwise_cosine": [round(c, 4) for c in cos_sims],
            "feature_vectors": {s: [round(v, 4) for v in group_features[s]] for s in sids},
        }
        phi_divergence_results.append(result)
        print(f"  trajectory (dm={sum(traj)}): {sids}")
        print(f"    euclidean: max={max_dist:.4f}, min={min_dist:.4f}, avg={avg_dist:.4f}")
        print(f"    cosine: {[f'{c:.4f}' for c in cos_sims]}")
        print(f"    features: {dict((s, [f'{v:.4f}' for v in group_features[s]]) for s in sids)}")

    # Phase 4: Compare perturbation responses within each group
    print("\nPhase 4: Comparing perturbation responses...")
    perturbation_comparison = []
    for result in phi_divergence_results:
        sids = result["solvers"]
        if len(sids) < 2:
            continue

        responses = {}
        for s in sids:
            data = solvers[s]
            resp = compute_perturbation_response(
                SOLVER_REGISTRY[s]["fn"], data["label"], data["features"]
            )
            responses[s] = resp

        # Compare label changes across solvers in group
        label_change_agreement = True
        for i, s1 in enumerate(sids):
            for s2 in sids[i + 1:]:
                for r1, r2 in zip(responses[s1], responses[s2]):
                    if r1["label_changed"] != r2["label_changed"]:
                        label_change_agreement = False
                        break

        # Compare delta_phi distributions
        delta_phis = {}
        for s in sids:
            delta_phis[s] = [r["delta_phi"] for r in responses[s]]

        perturbation_comparison.append({
            "trajectory_dm": result["trajectory_dm"],
            "solvers": sids,
            "label_change_agreement": label_change_agreement,
            "delta_phi_by_solver": {s: [round(d, 4) for d in delta_phis[s]] for s in sids},
        })
        print(f"  trajectory (dm={result['trajectory_dm']}): {sids}")
        print(f"    label_change_agreement: {label_change_agreement}")
        for s in sids:
            print(f"    {s} delta_phis: {[f'{d:.4f}' for d in delta_phis[s]]}")

    # Phase 5: Cross-family trajectory comparison
    print("\nPhase 5: Cross-family trajectory analysis...")
    families = defaultdict(list)
    for sid, data in solvers.items():
        families[data["direction"]].append(sid)

    # Check if any two solvers from different families have identical trajectories
    cross_family_identical = []
    all_sids = list(solvers.keys())
    for i, s1 in enumerate(all_sids):
        for s2 in all_sids[i + 1:]:
            if solvers[s1]["trajectory"] == solvers[s2]["trajectory"]:
                if solvers[s1]["direction"] != solvers[s2]["direction"]:
                    cross_family_identical.append((s1, s2))

    print(f"  Cross-family identical trajectories: {len(cross_family_identical)}")
    for s1, s2 in cross_family_identical:
        print(f"    {s1} ({solvers[s1]['direction']}) == {s2} ({solvers[s2]['direction']})")

    # Phase 6: Summary statistics
    print("\nPhase 6: Summary statistics...")
    print(f"  Total solvers: {len(solvers)}")
    print(f"  Unique trajectories: {len(trajectory_groups)}")
    print(f"  Groups with >1 solver: {sum(1 for g in trajectory_groups.values() if len(g) > 1)}")
    print(f"  Cross-family identical: {len(cross_family_identical)}")

    # Check if dm trajectory determines label
    trajectory_label_map = {}
    for sid, data in solvers.items():
        traj = data["trajectory"]
        if traj not in trajectory_label_map:
            trajectory_label_map[traj] = data["label"]
        else:
            assert trajectory_label_map[traj] == data["label"], \
                f"dm trajectory does NOT determine label: {sid} has label {data['label']} but trajectory already mapped to {trajectory_label_map[traj]}"

    print(f"  dm trajectory determines label: YES (trivially)")

    # Check if dm trajectory determines phi(s)
    phi_determined = True
    for result in phi_divergence_results:
        if result["pairwise_euclidean"]["max"] > 1e-6:
            phi_determined = False
            print(f"  dm trajectory does NOT determine phi(s): "
                  f"trajectory (dm={result['trajectory_dm']}) has max_euclidean={result['pairwise_euclidean']['max']:.4f}")

    if phi_determined:
        print(f"  dm trajectory determines phi(s): YES")
    else:
        print(f"  dm trajectory determines phi(s): NO")

    # Check if dm trajectory determines perturbation response
    response_determined = True
    for comp in perturbation_comparison:
        if not comp["label_change_agreement"]:
            response_determined = False
            print(f"  dm trajectory does NOT determine perturbation response: "
                  f"trajectory (dm={comp['trajectory_dm']}) has disagreement")

    if response_determined:
        print(f"  dm trajectory determines perturbation response: YES")
    else:
        print(f"  dm trajectory determines perturbation response: NO")

    # Verdict
    print(f"\n{'=' * 70}")
    print("DECOUPLING TEST VERDICT")
    print(f"{'=' * 70}")

    if phi_determined and response_determined:
        verdict = "COUPLED"
        explanation = "dm trajectory determines both phi(s) and perturbation response: dm is a complete quotient coordinate"
    elif phi_determined and not response_determined:
        verdict = "PARTIAL_DECOUPLED"
        explanation = "dm trajectory determines phi(s) but not perturbation response: dm captures continuous structure but not dynamic behavior"
    elif not phi_determined and response_determined:
        verdict = "PARTIAL_DECOUPLED"
        explanation = "dm trajectory determines perturbation response but not phi(s): dm captures dynamic behavior but not continuous structure"
    else:
        verdict = "FULLY_DECOUPLED"
        explanation = "dm trajectory determines neither phi(s) nor perturbation response: dm is a coarse sufficient statistic, not a complete quotient coordinate"

    print(f"  Verdict: {verdict}")
    print(f"  {explanation}")

    # Save
    output = {
        "phase": "decoupling_test",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "canonical_test_suite": "24-case",
            "oracle": "LC743",
        },
        "summary": {
            "total_solvers": len(solvers),
            "unique_trajectories": len(trajectory_groups),
            "cross_family_identical": len(cross_family_identical),
            "phi_determined_by_trajectory": phi_determined,
            "response_determined_by_trajectory": response_determined,
        },
        "trajectory_groups": [
            {
                "trajectory_dm": result["trajectory_dm"],
                "solvers": result["solvers"],
                "directions": result["directions"],
                "pairwise_euclidean": result["pairwise_euclidean"],
                "pairwise_cosine": result["pairwise_cosine"],
                "feature_vectors": result["feature_vectors"],
            }
            for result in phi_divergence_results
        ],
        "perturbation_comparison": perturbation_comparison,
        "cross_family_identical": [
            {"s1": s1, "s2": s2,
             "s1_direction": solvers[s1]["direction"],
             "s2_direction": solvers[s2]["direction"]}
            for s1, s2 in cross_family_identical
        ],
        "verdict": verdict,
        "explanation": explanation,
    }

    for base in [ROOT, ROOT.parent]:
        out_path = base / "results" / "decoupling_test_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
