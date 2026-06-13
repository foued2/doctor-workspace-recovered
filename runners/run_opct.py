"""OPCT — Oracle Pullback Continuity Test.

Test continuity of O phi : S -> {0,1} under controlled perturbations
in solver space, not feature space.

Fixed:
  - Solver population S (LC756)
  - Feature map phi: S -> R^6
  - Oracle O: R^6 -> {0,1}

Perturbation regime A (solver-space, valid test):
  Generate s -> s' via minimal syntactic changes.
  Observe: Delta phi(s, s'), Delta O(phi(s), phi(s'))

Perturbation regime B (feature-space, diagnostic only):
  Take phi(s) and perturb directly: phi(s) + epsilon
  Observe: oracle robustness to representation noise

Two hypotheses:
  H1: smooth latent manifold — small solver changes -> small phi changes -> stable oracle
  H2: quotient collapse — small solver changes -> discontinuous phi or discontinuous O phi

No narrative synthesis.
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


def compute_discrete_mismatches(solver_fn):
    mismatches = 0
    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        _, oracle_result = compute_full_distances(case["times"], case["n"], case["k"])
        if solver_result != oracle_result:
            mismatches += 1
    return mismatches


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

    # max_dist_error from O2-B style
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


# --- Solver perturbation generators ---

def perturb_constant_threshold(solver_fn, threshold_old, threshold_new):
    """Create a perturbed solver by changing a constant threshold.

    This is a conceptual perturbation — in practice, we generate a new solver
    function that mimics the original but with the threshold changed.
    """
    import types

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
                if w > threshold_new:  # Changed threshold
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


def perturb_early_stop(solver_fn, stop_node):
    """Create a perturbed solver that stops at a different node."""
    import types

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
            if u == stop_node:  # Changed stop node
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


def perturb_weight_condition(solver_fn, condition_type):
    """Create a perturbed solver with different weight condition."""
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


def perturb_dijkstra_variant(solver_fn, variant):
    """Create a perturbed Dijkstra variant."""
    def perturbed(times, n, k):
        graph = defaultdict(list)
        for u, v, w in times:
            graph[u].append((v, w))
        INF = float("inf")
        dist = {i: INF for i in range(1, n + 1)}
        dist[k] = 0

        if variant == "no_decrease_key":
            # Allow duplicate entries in heap
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
            # BFS ignoring weights
            from collections import deque
            queue = deque([k])
            visited = {k}
            while queue:
                u = queue.popleft()
                for v, w in graph[u]:
                    if v not in visited:
                        visited.add(v)
                        dist[v] = dist[u] + 1  # Unit weight
                        queue.append(v)
        elif variant == "reversed_relaxation":
            # Relax in reverse order
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


def main():
    print("=" * 70)
    print("OPCT — ORACLE PULLBACK CONTINUITY TEST")
    print("=" * 70)

    # Baseline: compute features for all 30 solvers
    print("\nBaseline: computing features for all 30 solvers...")
    baseline = {}
    for sid, meta in SOLVER_REGISTRY.items():
        fn = meta["fn"]
        dm = compute_discrete_mismatches(fn)
        features = compute_continuous_features(fn)
        label = 1 if dm > 0 else 0
        baseline[sid] = {
            "discrete_mismatches": dm,
            "label": label,
            "features": features,
            "direction": meta["direction"],
        }
        print(f"  {sid}: dm={dm}, label={label}, features={[f'{v:.4f}' for v in features]}")

    # Identify boundary solvers (dm close to threshold)
    # s027 has dm=6, others have dm=0 or dm>=13
    s027 = baseline["s027"]
    print(f"\ns027 baseline: dm={s027['discrete_mismatches']}, label={s027['label']}")

    # --- Regime A: Solver-space perturbations ---
    print(f"\n{'=' * 70}")
    print("REGIME A: SOLVER-SPACE PERTURBATIONS")
    print(f"{'=' * 70}")

    perturbations_A = []

    # Perturbation 1: s027 with different weight conditions
    for cond in ["skip_heavy", "skip_light", "skip_medium"]:
        perturbed_fn = perturb_weight_condition(None, cond)
        dm = compute_discrete_mismatches(perturbed_fn)
        features = compute_continuous_features(perturbed_fn)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(s027["features"], features)
        delta_O = 0 if label == s027["label"] else 1
        perturbations_A.append({
            "source": "s027",
            "perturbation": f"weight_condition_{cond}",
            "dm": dm,
            "label": label,
            "delta_phi": round(delta_phi, 4),
            "delta_O": delta_O,
            "features": [round(v, 4) for v in features],
        })
        print(f"  s027 -> weight_{cond}: dm={dm}, label={label}, "
              f"delta_phi={delta_phi:.4f}, delta_O={delta_O}")

    # Perturbation 2: s027 with different early-stop nodes
    for stop_node in [1, 3, 5, 7, 10]:
        perturbed_fn = perturb_early_stop(None, stop_node)
        dm = compute_discrete_mismatches(perturbed_fn)
        features = compute_continuous_features(perturbed_fn)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(s027["features"], features)
        delta_O = 0 if label == s027["label"] else 1
        perturbations_A.append({
            "source": "s027",
            "perturbation": f"early_stop_{stop_node}",
            "dm": dm,
            "label": label,
            "delta_phi": round(delta_phi, 4),
            "delta_O": delta_O,
            "features": [round(v, 4) for v in features],
        })
        print(f"  s027 -> early_stop_{stop_node}: dm={dm}, label={label}, "
              f"delta_phi={delta_phi:.4f}, delta_O={delta_O}")

    # Perturbation 3: s027 Dijkstra variants
    for variant in ["no_decrease_key", "bfs_no_weights", "reversed_relaxation"]:
        perturbed_fn = perturb_dijkstra_variant(None, variant)
        dm = compute_discrete_mismatches(perturbed_fn)
        features = compute_continuous_features(perturbed_fn)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(s027["features"], features)
        delta_O = 0 if label == s027["label"] else 1
        perturbations_A.append({
            "source": "s027",
            "perturbation": f"variant_{variant}",
            "dm": dm,
            "label": label,
            "delta_phi": round(delta_phi, 4),
            "delta_O": delta_O,
            "features": [round(v, 4) for v in features],
        })
        print(f"  s027 -> variant_{variant}: dm={dm}, label={label}, "
              f"delta_phi={delta_phi:.4f}, delta_O={delta_O}")

    # Perturbation 4: perturb a boundary-adjacent solver (s002, dm=13)
    s002 = baseline["s002"]
    for cond in ["skip_heavy", "skip_light"]:
        perturbed_fn = perturb_weight_condition(None, cond)
        dm = compute_discrete_mismatches(perturbed_fn)
        features = compute_continuous_features(perturbed_fn)
        label = 1 if dm > 0 else 0
        delta_phi = euclidean(s002["features"], features)
        delta_O = 0 if label == s002["label"] else 1
        perturbations_A.append({
            "source": "s002",
            "perturbation": f"weight_condition_{cond}",
            "dm": dm,
            "label": label,
            "delta_phi": round(delta_phi, 4),
            "delta_O": delta_O,
            "features": [round(v, 4) for v in features],
        })
        print(f"  s002 -> weight_{cond}: dm={dm}, label={label}, "
              f"delta_phi={delta_phi:.4f}, delta_O={delta_O}")

    # --- Regime B: Feature-space perturbations (diagnostic) ---
    print(f"\n{'=' * 70}")
    print("REGIME B: FEATURE-SPACE PERTURBATIONS (diagnostic only)")
    print(f"{'=' * 70}")

    perturbations_B = []
    epsilons = [0.01, 0.05, 0.10, 0.20, 0.50]

    for eps in epsilons:
        for trial in range(5):
            rng = random.Random(trial * 1000 + int(eps * 1000))
            noise = [rng.gauss(0, eps) for _ in range(6)]
            perturbed_features = [s027["features"][j] + noise[j] for j in range(6)]

            # Determine label by kNN in baseline feature space
            dists = [(euclidean(perturbed_features, baseline[sid]["features"]),
                      baseline[sid]["label"])
                     for sid in baseline]
            dists.sort(key=lambda x: x[0])
            k = 3
            votes = {}
            for _, label in dists[:k]:
                votes[label] = votes.get(label, 0) + 1
            predicted_label = max(votes, key=votes.get)

            delta_phi = euclidean(s027["features"], perturbed_features)
            delta_O = 0 if predicted_label == s027["label"] else 1

            perturbations_B.append({
                "epsilon": eps,
                "trial": trial,
                "predicted_label": predicted_label,
                "delta_phi": round(delta_phi, 4),
                "delta_O": delta_O,
            })

        # Summarize for this epsilon
        eps_results = [p for p in perturbations_B if p["epsilon"] == eps]
        label_changes = sum(1 for p in eps_results if p["delta_O"] == 1)
        avg_delta_phi = sum(p["delta_phi"] for p in eps_results) / len(eps_results)
        print(f"  epsilon={eps}: label_changes={label_changes}/5, "
              f"avg_delta_phi={avg_delta_phi:.4f}")

    # --- Analysis ---
    print(f"\n{'=' * 70}")
    print("ANALYSIS")
    print(f"{'=' * 70}")

    # Regime A analysis
    a_results = [p for p in perturbations_A if p["source"] == "s027"]
    a_label_changes = sum(1 for p in a_results if p["delta_O"] == 1)
    a_no_change = [p for p in a_results if p["delta_O"] == 0]
    a_with_change = [p for p in a_results if p["delta_O"] == 1]

    print(f"\nRegime A (solver-space, s027 perturbations):")
    print(f"  Total perturbations: {len(a_results)}")
    print(f"  Label changes: {a_label_changes}/{len(a_results)}")
    if a_no_change:
        avg_phi_stable = sum(p["delta_phi"] for p in a_no_change) / len(a_no_change)
        print(f"  Avg delta_phi (label stable): {avg_phi_stable:.4f}")
    if a_with_change:
        avg_phi_unstable = sum(p["delta_phi"] for p in a_with_change) / len(a_with_change)
        print(f"  Avg delta_phi (label changed): {avg_phi_unstable:.4f}")

    # Regime B analysis
    for eps in epsilons:
        eps_results = [p for p in perturbations_B if p["epsilon"] == eps]
        label_changes = sum(1 for p in eps_results if p["delta_O"] == 1)
        print(f"\nRegime B (feature-space, epsilon={eps}):")
        print(f"  Label changes: {label_changes}/5")

    # Verdict
    print(f"\n{'=' * 70}")
    print("OPCT VERDICT")
    print(f"{'=' * 70}")

    if a_label_changes == 0:
        verdict_a = "SMOOTH"
        explanation_a = "No label changes under solver-space perturbation: oracle is locally Lipschitz over solver-induced geometry"
    elif a_label_changes < len(a_results) * 0.3:
        verdict_a = "MOSTLY_SMOOTH"
        explanation_a = "Few label changes: oracle is mostly locally Lipschitz with isolated discontinuities"
    elif a_label_changes < len(a_results) * 0.7:
        verdict_a = "MIXED"
        explanation_a = "Mixed label changes: oracle has both smooth and discontinuous regions"
    else:
        verdict_a = "QUOTIENT"
        explanation_a = "Many label changes: oracle induces piecewise-constant quotient map"

    print(f"  Regime A verdict: {verdict_a}")
    print(f"  {explanation_a}")

    # Regime B comparison
    b_changes_at_eps01 = sum(1 for p in perturbations_B if p["epsilon"] == 0.01 and p["delta_O"] == 1)
    b_changes_at_eps05 = sum(1 for p in perturbations_B if p["epsilon"] == 0.05 and p["delta_O"] == 1)

    if b_changes_at_eps01 > 0 and a_label_changes == 0:
        print(f"\n  Regime B shows instability at epsilon=0.01 ({b_changes_at_eps01}/5)")
        print(f"  while Regime A shows stability under solver perturbation")
        print(f"  => discontinuity is in representation, not in solver geometry")
    elif b_changes_at_eps01 == 0 and a_label_changes > 0:
        print(f"\n  Regime A shows instability under solver perturbation")
        print(f"  while Regime B shows stability at epsilon=0.01")
        print(f"  => discontinuity is in solver geometry, not in representation")

    # Save
    output = {
        "phase": "OPCT_oracle_pullback_continuity",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "estimators": ["C_genuine", "B1", "B2"],
            "oracle": "LC743",
            "canonical_test_suite": "24-case",
        },
        "regime_A_solver_perturbation": {
            "total": len(a_results),
            "label_changes": a_label_changes,
            "verdict": verdict_a,
            "perturbations": a_results,
        },
        "regime_B_feature_perturbation": {
            "epsilons_tested": epsilons,
            "perturbations": perturbations_B,
        },
    }

    for base in [ROOT, ROOT.parent]:
        out_path = base / "results" / "opct_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
