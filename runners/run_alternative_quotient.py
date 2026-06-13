"""Alternative Quotient Test.

Construct trace-functionals independent of dm and test partition equivalence.

The oracle partition is: label = 1 if dm > 0, else 0.
dm is a sufficient statistic for this partition.
But is dm unique? Is dm minimal?

Test: construct alternative functionals h(trace) that:
1. Are NOT functions of dm (two solvers with same dm can have different h)
2. Induce the SAME oracle partition (h > 0 iff dm > 0)

If such h exist, dm is one coordinate among many quotient representations.
If no such h exist, dm is canonically distinguished.
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
from doctor.solvers.lc756.lc_756_solvers import SOLVER_REGISTRY


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


def compute_trace_functionals(solver_fn):
    """Compute multiple trace-functionals for a solver."""
    dm = 0
    error_magnitudes = []
    f1_mismatches = 0
    f2_mismatches = 0
    f3_mismatches = 0
    f4_mismatches = 0
    solver_returns_neg1 = 0
    oracle_returns_neg1 = 0
    both_neg1 = 0
    solver_reachable_oracle_unreachable = 0
    solver_unreachable_oracle_reachable = 0
    per_case_dm = []

    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        _, oracle_result = compute_full_distances(case["times"], case["n"], case["k"])

        is_mismatch = solver_result != oracle_result
        per_case_dm.append(1 if is_mismatch else 0)

        if is_mismatch:
            dm += 1

        # Error magnitude
        if solver_result == -1 and oracle_result == -1:
            error_mag = 0.0
        elif solver_result == -1:
            error_mag = float(oracle_result)
        elif oracle_result == -1:
            error_mag = float(solver_result)
        else:
            error_mag = abs(solver_result - oracle_result)
        error_magnitudes.append(error_mag)

        # Direction-specific counts
        if solver_result == -1:
            solver_returns_neg1 += 1
        if oracle_result == -1:
            oracle_returns_neg1 += 1
        if solver_result == -1 and oracle_result == -1:
            both_neg1 += 1
        if solver_result != -1 and oracle_result == -1:
            solver_reachable_oracle_unreachable += 1
        if solver_result == -1 and oracle_result != -1:
            solver_unreachable_oracle_reachable += 1

        # Family-specific mismatches
        label = case["label"]
        if is_mismatch:
            if label.startswith("f1") or label.startswith("f2_multihop") or label.startswith("f3_hop_count") or label.startswith("f4_high_weight"):
                f1_mismatches += 1
            elif label.startswith("f2_"):
                f2_mismatches += 1
            elif label.startswith("f3_"):
                f3_mismatches += 1
            elif label.startswith("f4_"):
                f4_mismatches += 1

    return {
        "dm": dm,
        "per_case_dm": tuple(per_case_dm),
        "error_magnitudes": error_magnitudes,
        "max_error": max(error_magnitudes),
        "sum_error": sum(error_magnitudes),
        "avg_error": sum(error_magnitudes) / len(error_magnitudes),
        "f1_mismatches": f1_mismatches,
        "f2_mismatches": f2_mismatches,
        "f3_mismatches": f3_mismatches,
        "f4_mismatches": f4_mismatches,
        "solver_returns_neg1": solver_returns_neg1,
        "oracle_returns_neg1": oracle_returns_neg1,
        "both_neg1": both_neg1,
        "solver_reachable_oracle_unreachable": solver_reachable_oracle_unreachable,
        "solver_unreachable_oracle_reachable": solver_unreachable_oracle_reachable,
    }


def oracle_partition(functional_values):
    """Compute oracle partition from functional values.
    
    Oracle partition: label = 1 if any value > 0, else 0.
    """
    return tuple(1 if v > 0 else 0 for v in functional_values)


def main():
    print("=" * 70)
    print("ALTERNATIVE QUOTIENT TEST")
    print("=" * 70)

    # Phase 1: Compute all trace-functionals
    print("\nPhase 1: Computing trace-functionals for all 30 solvers...")
    solvers = {}
    for sid, meta in SOLVER_REGISTRY.items():
        fn = meta["fn"]
        functionals = compute_trace_functionals(fn)
        solvers[sid] = {
            "functionals": functionals,
            "direction": meta["direction"],
        }
        print(f"  {sid}: dm={functionals['dm']}, "
              f"f1={functionals['f1_mismatches']}, f2={functionals['f2_mismatches']}, "
              f"f3={functionals['f3_mismatches']}, f4={functionals['f4_mismatches']}, "
              f"max_err={functionals['max_error']:.1f}")

    # Phase 2: Define alternative functionals
    print("\nPhase 2: Defining alternative trace-functionals...")
    
    # Functional definitions
    functional_defs = {
        "dm": lambda f: f["dm"],
        "f1_only": lambda f: f["f1_mismatches"],
        "f2_only": lambda f: f["f2_mismatches"],
        "f3_only": lambda f: f["f3_mismatches"],
        "f4_only": lambda f: f["f4_mismatches"],
        "max_error": lambda f: f["max_error"],
        "sum_error": lambda f: f["sum_error"],
        "solver_neg1_count": lambda f: f["solver_returns_neg1"],
        "oracle_neg1_count": lambda f: f["oracle_returns_neg1"],
        "reachable_oracle_unreachable": lambda f: f["solver_reachable_oracle_unreachable"],
        "unreachable_oracle_reachable": lambda f: f["solver_unreachable_oracle_reachable"],
        "f1_or_f4": lambda f: f["f1_mismatches"] + f["f4_mismatches"],
        "any_disconnect": lambda f: f["solver_unreachable_oracle_reachable"] + f["solver_reachable_oracle_unreachable"],
    }

    # Phase 3: Compute functional values for all solvers
    print("\nPhase 3: Computing functional values...")
    functional_values = {}
    for name, fn_def in functional_defs.items():
        values = {}
        for sid, data in solvers.items():
            values[sid] = fn_def(data["functionals"])
        functional_values[name] = values

    # Phase 4: Compute oracle partitions
    print("\nPhase 4: Computing oracle partitions...")
    oracle_partitions = {}
    for name, values in functional_values.items():
        partition = oracle_partition(list(values.values()))
        oracle_partitions[name] = partition
        print(f"  {name}: partition = {partition}")

    # Phase 5: Check partition equivalence
    print("\nPhase 5: Checking partition equivalence...")
    dm_partition = oracle_partitions["dm"]
    
    equivalence_results = {}
    for name, partition in oracle_partitions.items():
        is_equivalent = partition == dm_partition
        equivalence_results[name] = is_equivalent
        if is_equivalent and name != "dm":
            print(f"  {name}: EQUIVALENT to dm")
        elif not is_equivalent:
            print(f"  {name}: NOT equivalent to dm")

    # Phase 6: Check if equivalent functionals are functions of dm
    print("\nPhase 6: Checking if equivalent functionals are functions of dm...")
    dm_values = functional_values["dm"]
    
    independence_results = {}
    for name, values in functional_values.items():
        if not equivalence_results[name]:
            continue
        if name == "dm":
            continue

        # Check if this functional is a function of dm
        # Two solvers with same dm must have same functional value
        is_function_of_dm = True
        for s1 in SOLVER_REGISTRY:
            for s2 in SOLVER_REGISTRY:
                if s1 >= s2:
                    continue
                if dm_values[s1] == dm_values[s2]:
                    if values[s1] != values[s2]:
                        is_function_of_dm = False
                        break
            if not is_function_of_dm:
                break

        independence_results[name] = not is_function_of_dm
        if is_function_of_dm:
            print(f"  {name}: IS a function of dm")
        else:
            print(f"  {name}: is NOT a function of dm (independent quotient coordinate)")

    # Phase 7: Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    equivalent_independent = [name for name, is_ind in independence_results.items() if is_ind]
    equivalent_dependent = [name for name, is_ind in independence_results.items() if not is_ind]
    not_equivalent = [name for name, is_eq in equivalence_results.items() if not is_eq]

    print(f"  Functionals equivalent to dm: {len(equivalence_results) - 1}")
    print(f"    Independent of dm: {equivalent_independent}")
    print(f"    Dependent on dm: {equivalent_dependent}")
    print(f"  Functionals NOT equivalent to dm: {not_equivalent}")

    # Verdict
    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")

    if len(equivalent_independent) > 0:
        verdict = "MULTIPLE_QUOTIENTS"
        explanation = (f"dm is NOT unique: {len(equivalent_independent)} independent functionals "
                      f"induce the same oracle partition. dm is one coordinate among many "
                      f"quotient representations.")
    else:
        verdict = "CANONICAL"
        explanation = "dm appears canonically distinguished: no independent alternative quotients found."

    print(f"  Verdict: {verdict}")
    print(f"  {explanation}")

    # Concrete examples
    if equivalent_independent:
        print(f"\n  Concrete examples of independent equivalent functionals:")
        for name in equivalent_independent[:3]:
            print(f"    {name}:")
            for sid in ["s001", "s027", "s004", "s012"]:
                if sid in functional_values[name]:
                    print(f"      {sid}: {functional_values[name][sid]}")

    # Save
    output = {
        "phase": "alternative_quotient_test",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "canonical_test_suite": "24-case",
            "oracle": "LC743",
        },
        "functional_definitions": list(functional_defs.keys()),
        "oracle_partitions": {name: list(part) for name, part in oracle_partitions.items()},
        "equivalence_to_dm": equivalence_results,
        "independence_from_dm": independence_results,
        "equivalent_independent": equivalent_independent,
        "equivalent_dependent": equivalent_dependent,
        "not_equivalent": not_equivalent,
        "verdict": verdict,
        "explanation": explanation,
    }

    for base in [ROOT, ROOT.parent]:
        out_path = base / "results" / "alternative_quotient_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
