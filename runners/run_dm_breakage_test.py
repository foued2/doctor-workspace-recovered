"""
Active breakage test: construct solvers that force same dm, different tau.

Strategy: build parametric solvers that wrap the oracle with conditional
bugs, then sweep parameters to find dm-collisions with tau-divergence.
"""
import sys
from pathlib import Path
from itertools import product

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE, lc743_oracle


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


def compute_dm(tau):
    return sum(tau)


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


def make_conditional_solver(error_map):
    """Build a solver that applies specific errors on specific test case indices.

    error_map: dict mapping case_index -> return_value (to use instead of oracle)
    For cases not in error_map, runs correct Dijkstra.
    """
    from collections import defaultdict
    import heapq

    def solver(times, n, k):
        # We need to know which case index this is. Since we can't pass
        # case index through the solver interface, we use a closure trick:
        # match input signature to identify the case.
        for idx, case in enumerate(CANONICAL_TEST_SUITE):
            if case["times"] == times and case["n"] == n and case["k"] == k:
                if idx in error_map:
                    return error_map[idx]
                break

        # Correct Dijkstra
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
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
        return int(max(dist[node] for node in range(1, n + 1)))

    return solver


def make_parametric_solver(family, param):
    """Build a solver with a specific bug pattern controlled by param.

    family controls the type of bug, param controls which cases it affects.
    """
    from collections import defaultdict
    import heapq

    def solver(times, n, k):
        # Identify case index
        case_idx = None
        for idx, case in enumerate(CANONICAL_TEST_SUITE):
            if case["times"] == times and case["n"] == n and case["k"] == k:
                case_idx = idx
                break

        # Build graph
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

        # Apply bug based on family and param
        if family == "return_wrong_on_cases":
            # If case_idx is in param set, return wrong answer
            if case_idx in param:
                return 0  # Return 0 (almost always wrong)
            # Otherwise correct
            for node in range(1, n + 1):
                if dist[node] == INF:
                    return -1
            return int(max(dist[node] for node in range(1, n + 1)))

        elif family == "flip_disconnected":
            # On disconnected graphs, flip the result
            has_unreachable = any(dist[node] == INF for node in range(1, n + 1))
            if has_unreachable:
                if param == "return_0":
                    return 0
                elif param == "return_n":
                    return n
                elif param == "return_positive":
                    # Return max reachable distance
                    max_d = 0
                    for node in range(1, n + 1):
                        if dist[node] < INF and dist[node] > max_d:
                            max_d = dist[node]
                    return int(max_d)
            for node in range(1, n + 1):
                if dist[node] == INF:
                    return -1
            return int(max(dist[node] for node in range(1, n + 1)))

        elif family == "skip_weight_threshold":
            # Skip edges with weight > param
            graph2 = defaultdict(list)
            for u, v, w in times:
                if w <= param:
                    graph2[u].append((v, w))
            dist2 = {i: INF for i in range(1, n + 1)}
            dist2[k] = 0
            heap2 = [(0, k)]
            while heap2:
                d, u = heapq.heappop(heap2)
                if d > dist2[u]:
                    continue
                for v, w in graph2[u]:
                    nd = d + w
                    if nd < dist2[v]:
                        dist2[v] = nd
                        heapq.heappush(heap2, (nd, v))
            for node in range(1, n + 1):
                if dist2[node] == INF:
                    return -1
            return int(max(dist2[node] for node in range(1, n + 1)))

        elif family == "multiply_weight":
            # Multiply weights by param
            graph3 = defaultdict(list)
            for u, v, w in times:
                graph3[u].append((v, w * param))
            dist3 = {i: INF for i in range(1, n + 1)}
            dist3[k] = 0
            heap3 = [(0, k)]
            while heap3:
                d, u = heapq.heappop(heap3)
                if d > dist3[u]:
                    continue
                for v, w in graph3[u]:
                    nd = d + w
                    if nd < dist3[v]:
                        dist3[v] = nd
                        heapq.heappush(heap3, (nd, v))
            for node in range(1, n + 1):
                if dist3[node] == INF:
                    return -1
            return int(max(dist3[node] for node in range(1, n + 1)))

        elif family == "early_stop_at_node":
            # Stop BFS when we reach node with ID == param
            while heap:
                d, u = heapq.heappop(heap)
                if d > dist[u]:
                    continue
                if u == param:
                    break
                for v, w in graph[u]:
                    nd = d + w
                    if nd < dist[v]:
                        dist[v] = nd
                        heapq.heappush(heap, (nd, v))
            for node in range(1, n + 1):
                if dist[node] == INF:
                    return -1
            return int(max(dist[node] for node in range(1, n + 1)))

        # Default: correct
        for node in range(1, n + 1):
            if dist[node] == INF:
                return -1
        return int(max(dist[node] for node in range(1, n + 1)))

    return solver


def main():
    print("=" * 70)
    print("ACTIVE BREAKAGE TEST: Construct same-dm, different-tau solvers")
    print("=" * 70)

    # Step 1: Compute oracle results per case
    print("\n--- Per-case oracle results ---\n")
    oracle_results = []
    for i, case in enumerate(CANONICAL_TEST_SUITE):
        r = lc743_oracle(case["times"], case["n"], case["k"])
        oracle_results.append(r)
        print(f"  case {i:2d} ({case['label']:25s}): oracle={r}")

    # Step 2: Compute existing solver tau vectors
    print("\n--- Existing solver tau vectors ---\n")
    from doctor.solvers.lc756.lc_756_solvers import SOLVER_REGISTRY

    solver_taus = {}
    for name, meta in SOLVER_REGISTRY.items():
        tau = compute_tau(meta["fn"])
        dm = compute_dm(tau)
        solver_taus[name] = {"tau": tau, "dm": dm}
        tau_str = "".join(str(x) for x in tau)
        print(f"  {name} (dm={dm:2d}): {tau_str}")

    # Step 3: Identify which cases each solver gets right/wrong
    print("\n--- Per-case agreement breakdown ---\n")
    dm_groups = {}
    for name, data in solver_taus.items():
        dm = data["dm"]
        if dm not in dm_groups:
            dm_groups[dm] = []
        dm_groups[dm].append(name)

    for dm_val in sorted(dm_groups.keys()):
        members = dm_groups[dm_val]
        tau = solver_taus[members[0]]["tau"]
        right_cases = [i for i, v in enumerate(tau) if v == 1]
        wrong_cases = [i for i, v in enumerate(tau) if v == 0]
        print(f"  dm={dm_val}: right={right_cases}, wrong={wrong_cases}")

    # Step 4: Active breakage — construct solvers with same dm, different tau
    print("\n--- BREAKAGE ATTEMPT 1: Conditional error solvers ---\n")

    target_dm = 6  # Target: dm=6 group (11 solvers, tau=000000000000000000111111)
    target_tau = solver_taus["s004"]["tau"]
    target_right = [i for i, v in enumerate(target_tau) if v == 1]  # cases 18-23
    target_wrong = [i for i, v in enumerate(target_tau) if v == 0]  # cases 0-17

    print(f"  Target dm={target_dm}, target tau={target_tau}")
    print(f"  Target right cases: {target_right}")
    print(f"  Target wrong cases: {target_wrong}")

    # Strategy: build a solver that gets the SAME NUMBER of cases right (6)
    # but on a DIFFERENT set of cases.
    # Try: get cases 0-5 right, cases 6-23 wrong.
    swap_right = list(range(0, 6))  # F1 cases
    swap_wrong = list(range(6, 24))  # F2, F3, F4 cases

    print(f"\n  Attempt: construct solver with right={swap_right}, wrong={swap_wrong}")
    print(f"  (Same dm=6, different tau)")

    error_map = {i: 0 for i in swap_wrong}  # Return 0 on wrong cases
    constructed_solver = make_conditional_solver(error_map)
    constructed_tau = compute_tau(constructed_solver)
    constructed_dm = compute_dm(constructed_tau)

    tau_str = "".join(str(x) for x in constructed_tau)
    print(f"  Result: dm={constructed_dm}, tau={tau_str}")

    if constructed_dm == target_dm and constructed_tau != target_tau:
        print(f"  *** BREAKAGE SUCCESS: same dm={target_dm}, different tau ***")
        print(f"  Original tau: {''.join(str(x) for x in target_tau)}")
        print(f"  New tau:      {tau_str}")
        h = hamming(target_tau, constructed_tau)
        print(f"  Hamming distance: {h}")
    else:
        print(f"  No breakage (dm={constructed_dm}, same tau={constructed_tau == target_tau})")

    # Step 5: Systematic sweep of swap patterns
    print("\n--- BREAKAGE ATTEMPT 2: Systematic swap sweep ---\n")

    # For each dm value, try all ways to select `dm` cases from 24
    # and construct a solver that gets exactly those cases right.
    # We only need to find ONE collision.

    # Since C(24,6) is too large, use a smarter approach:
    # Pick pairs of cases to swap between "right" and "wrong" sets.

    found_any = False
    for dm_val in [6, 8, 11, 18]:
        members = dm_groups[dm_val]
        original_tau = solver_taus[members[0]]["tau"]
        original_right = set(i for i, v in enumerate(original_tau) if v == 1)
        original_wrong = set(i for i, v in enumerate(original_tau) if v == 0)

        print(f"  Testing dm={dm_val} (right={sorted(original_right)}, wrong={sorted(original_wrong)})")

        # Try swapping one case from right to wrong and one from wrong to right
        attempts = 0
        for r in sorted(original_right):
            for w in sorted(original_wrong):
                new_right = (original_right - {r}) | {w}
                new_wrong = (original_wrong - {w}) | {r}

                # Build error map: return 0 on new_wrong cases
                error_map = {i: 0 for i in new_wrong}
                test_solver = make_conditional_solver(error_map)
                test_tau = compute_tau(test_solver)
                test_dm = compute_dm(test_tau)

                if test_dm == dm_val and test_tau != original_tau:
                    print(f"    *** BREAKAGE FOUND ***")
                    print(f"    Swapped case {r} (right->wrong) with case {w} (wrong->right)")
                    print(f"    Original tau: {''.join(str(x) for x in original_tau)}")
                    print(f"    New tau:      {''.join(str(x) for x in test_tau)}")
                    print(f"    Hamming: {hamming(original_tau, test_tau)}")
                    found_any = True
                    break
                attempts += 1

            if found_any:
                break

        if not found_any:
            print(f"    No breakage found ({attempts} swaps tested)")

    # Step 6: Try different construction strategies
    print("\n--- BREAKAGE ATTEMPT 3: Skip-weight solvers ---\n")

    # Construct solvers that skip edges above a weight threshold
    # These naturally disagree with oracle on different cases than existing solvers
    for threshold in [0, 1, 2, 3, 5, 10, 50]:
        test_solver = make_parametric_solver("skip_weight_threshold", threshold)
        test_tau = compute_tau(test_solver)
        test_dm = compute_dm(test_tau)

        tau_str = "".join(str(x) for x in test_tau)
        print(f"  threshold={threshold:2d}: dm={test_dm:2d}, tau={tau_str}")

        # Check if this matches any existing dm but has different tau
        if test_dm in dm_groups:
            existing_tau = solver_taus[dm_groups[test_dm][0]]["tau"]
            if test_tau != existing_tau:
                print(f"    *** BREAKAGE: same dm={test_dm}, different tau ***")
                print(f"    Existing tau: {''.join(str(x) for x in existing_tau)}")
                print(f"    New tau:      {tau_str}")
                print(f"    Hamming: {hamming(existing_tau, test_tau)}")
                found_any = True

    # Step 7: Try multiply-weight solvers
    print("\n--- BREAKAGE ATTEMPT 4: Multiply-weight solvers ---\n")

    for factor in [1, 2, 3, 5, 10]:
        test_solver = make_parametric_solver("multiply_weight", factor)
        test_tau = compute_tau(test_solver)
        test_dm = compute_dm(test_tau)

        tau_str = "".join(str(x) for x in test_tau)
        print(f"  factor={factor}: dm={test_dm:2d}, tau={tau_str}")

        if test_dm in dm_groups:
            existing_tau = solver_taus[dm_groups[test_dm][0]]["tau"]
            if test_tau != existing_tau:
                print(f"    *** BREAKAGE: same dm={test_dm}, different tau ***")
                print(f"    Existing tau: {''.join(str(x) for x in existing_tau)}")
                print(f"    New tau:      {tau_str}")
                found_any = True

    # Step 8: Try early-stop solvers
    print("\n--- BREAKAGE ATTEMPT 5: Early-stop solvers ---\n")

    for stop_node in range(1, 6):
        test_solver = make_parametric_solver("early_stop_at_node", stop_node)
        test_tau = compute_tau(test_solver)
        test_dm = compute_dm(test_tau)

        tau_str = "".join(str(x) for x in test_tau)
        print(f"  stop_at_node={stop_node}: dm={test_dm:2d}, tau={tau_str}")

        if test_dm in dm_groups:
            existing_tau = solver_taus[dm_groups[test_dm][0]]["tau"]
            if test_tau != existing_tau:
                print(f"    *** BREAKAGE: same dm={test_dm}, different tau ***")
                print(f"    Existing tau: {''.join(str(x) for x in existing_tau)}")
                print(f"    New tau:      {tau_str}")
                found_any = True

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    if found_any:
        print("RESULT: BREAKAGE ACHIEVED — constructed solvers with same dm, different tau")
        print("This proves dm is lossy: it collapses distinct behavioral patterns.")
    else:
        print("RESULT: NO BREAKAGE — all constructions produce same dm AND same tau")
        print("Population is degenerate. Cannot conclude whether dm is lossy in general.")
        print("The current test suite + solver population does not provide enough")
        print("resolution to distinguish dm-collapse from tau-injectivity.")

    # Also compute all unique tau vectors from our constructions
    print("\n--- All discovered tau vectors ---\n")
    all_taus = set()
    for name, data in solver_taus.items():
        all_taus.add(data["tau"])

    # Re-collect from attempts
    for threshold in [0, 1, 2, 3, 5, 10, 50]:
        s = make_parametric_solver("skip_weight_threshold", threshold)
        all_taus.add(compute_tau(s))
    for factor in [1, 2, 3, 5, 10]:
        s = make_parametric_solver("multiply_weight", factor)
        all_taus.add(compute_tau(s))
    for stop_node in range(1, 6):
        s = make_parametric_solver("early_stop_at_node", stop_node)
        all_taus.add(compute_tau(s))

    print(f"  Total unique tau vectors discovered: {len(all_taus)}")
    for tau in sorted(all_taus):
        dm = compute_dm(tau)
        tau_str = "".join(str(x) for x in tau)
        print(f"  dm={dm:2d}: {tau_str}")


if __name__ == "__main__":
    main()
