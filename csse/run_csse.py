"""CSSE Runner — Execute the Controlled Solver Separation Experiment.

Pipeline:
  1. Generate 20 solvers (pre-generated, frozen before evaluation)
  2. For each solver: run all 32 probes, record pass/fail
  3. Compute B1 decision (ACCEPT iff fail_count == 0)
  4. Compute C_genuine decision (ACCEPT iff failures span ≤ 1 probe family)
  5. Compute PAS (Partition Alignment Score)
  6. Output full results + binary outcome

Constraints enforced:
  - No solver modification after probe execution
  - No threshold tuning after results
  - No selective reporting
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from csse.problem_definition import oracle, PROBES, AXIS_SET, FAMILY_SET
from csse.solver_generation import get_solver_ids, get_solver


# ── Configuration ──────────────────────────────────────────────────────────

THRESHOLD_T = 0  # B1: ACCEPT iff fail_count == 0 (same as Doctor B1_count)
EPSILON = 0.1    # PAS threshold for Outcome A


# ── Solver Loading ─────────────────────────────────────────────────────────

def load_solver(sid: str):
    """Write solver code to temp file, load as module, return solve function."""
    family, s_axis, p_axis, code = get_solver(sid)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=str(Path(__file__).resolve().parent.parent)
    ) as f:
        f.write(code)
        tmp_path = f.name
    try:
        spec = importlib.util.spec_from_file_location(sid, tmp_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.solve
    finally:
        os.unlink(tmp_path)


# ── Probe Evaluation ───────────────────────────────────────────────────────

def probe_to_solver_input(probe: dict) -> dict:
    """Convert probe dict to solver input: {nums, target}."""
    return {"nums": list(probe["nums"]), "target": probe["target"]}


def evaluate_solver(solver_fn, probes: list[dict]) -> dict:
    """Run solver on all probes. Return {probe_id: bool}."""
    results = {}
    for probe in probes:
        solver_input = probe_to_solver_input(probe)
        truth = oracle(solver_input)
        try:
            observed = solver_fn(copy.deepcopy(solver_input["nums"]), solver_input["target"])
        except Exception:
            observed = "EXC"
        results[probe["probe_id"]] = (observed == truth)
    return results


# ── Decision Functions ─────────────────────────────────────────────────────

def b1_decision(fail_count: int, total: int) -> str:
    """B1: ACCEPT iff zero failures."""
    return "ACCEPT" if fail_count == 0 else "REJECT"


def c_genuine_decision(probe_results: dict, probes: list[dict]) -> str:
    """C_genuine: ACCEPT if zero failures OR all failures in ≤ 1 probe family."""
    failures = [pid for pid, passed in probe_results.items() if not passed]
    if len(failures) == 0:
        return "ACCEPT"

    probe_map = {p["probe_id"]: p for p in probes}
    failure_families = set()
    for pid in failures:
        p = probe_map.get(pid)
        if p:
            failure_families.add(p.get("probe_family", "unknown"))

    if len(failure_families) <= 1:
        return "ACCEPT"
    return "REJECT"


# ── PAS Computation ────────────────────────────────────────────────────────

def compute_pas(results: dict[str, dict[str, bool]], solver_meta: dict[str, tuple],
                probes: list[dict], threshold: int) -> dict:
    """Compute Partition Alignment Score and secondary metrics.

    PAS = P(C_genuine(s_i) != C_genuine(s_j) | B1(s_i) == B1(s_j) AND family(s_i) != family(s_j))

    Only pairs where B1 gives the SAME decision are considered.
    Among those, we count how often C_genuine disagrees, restricted to
    cross-family pairs.
    """
    solver_ids = sorted(results.keys())

    # Compute per-solver metrics
    per_solver = {}
    for sid in solver_ids:
        fail_count = sum(1 for passed in results[sid].values() if not passed)
        total = len(results[sid])
        b1 = b1_decision(fail_count, total)
        c_gen = c_genuine_decision(results[sid], probes)
        family = solver_meta[sid][0]
        per_solver[sid] = {
            "family": family,
            "fail_count": fail_count,
            "total": total,
            "fail_rate": fail_count / total if total > 0 else 0,
            "b1_decision": b1,
            "c_genuine_decision": c_gen,
        }

    # Compute PAS
    same_b1_pairs = 0
    cross_family_same_b1 = 0
    cross_family_disagree = 0

    for i in range(len(solver_ids)):
        for j in range(i + 1, len(solver_ids)):
            si, sj = solver_ids[i], solver_ids[j]
            b1_i = per_solver[si]["b1_decision"]
            b1_j = per_solver[sj]["b1_decision"]
            fam_i = per_solver[si]["family"]
            fam_j = per_solver[sj]["family"]

            if b1_i == b1_j:
                same_b1_pairs += 1
                if fam_i != fam_j:
                    cross_family_same_b1 += 1
                    c_i = per_solver[si]["c_genuine_decision"]
                    c_j = per_solver[sj]["c_genuine_decision"]
                    if c_i != c_j:
                        cross_family_disagree += 1

    pas = cross_family_disagree / cross_family_same_b1 if cross_family_same_b1 > 0 else 0.0

    return {
        "per_solver": per_solver,
        "pas": pas,
        "same_b1_pairs": same_b1_pairs,
        "cross_family_same_b1": cross_family_same_b1,
        "cross_family_disagree": cross_family_disagree,
        "total_solvers": len(solver_ids),
        "total_probes": len(probes),
    }


# ── Output Formatting ──────────────────────────────────────────────────────

def print_results(computed: dict, epsilon: float):
    """Print full results matrix and decision."""
    per_solver = computed["per_solver"]

    print("=" * 90)
    print("CSSE — CONTROLLED SOLVER SEPARATION EXPERIMENT")
    print("=" * 90)
    print(f"Total solvers: {computed['total_solvers']}")
    print(f"Total probes:  {computed['total_probes']}")
    print(f"Threshold T:   {THRESHOLD_T}")
    print(f"Epsilon:       {epsilon}")
    print()

    # Full solver table
    print(f"{'Solver':<10} {'Family':<6} {'S':<3} {'P':<3} {'Fails':<6} {'Rate':<7} {'B1':<8} {'C_gen':<8}")
    print("-" * 90)
    for sid in sorted(per_solver.keys()):
        r = per_solver[sid]
        print(f"{sid:<10} {r['family']:<6} {r['family'][1]:<3} "
              f"{'P0' if r['family'][0] == 'A' and r['family'][-1] == '2' else 'P1':<3} "
              f"{r['fail_count']:<6} {r['fail_rate']:<7.4f} {r['b1_decision']:<8} {r['c_genuine_decision']:<8}")
    print()

    # Family-wise summary
    families = defaultdict(lambda: {"b1_accept": 0, "b1_reject": 0, "c_accept": 0, "c_reject": 0, "total": 0})
    for sid, r in per_solver.items():
        fam = r["family"]
        families[fam]["total"] += 1
        if r["b1_decision"] == "ACCEPT":
            families[fam]["b1_accept"] += 1
        else:
            families[fam]["b1_reject"] += 1
        if r["c_genuine_decision"] == "ACCEPT":
            families[fam]["c_accept"] += 1
        else:
            families[fam]["c_reject"] += 1

    print("FAMILY-WISE SUMMARY")
    print("-" * 70)
    print(f"{'Family':<6} {'N':<4} {'B1_ACC':<8} {'B1_REJ':<8} {'C_ACC':<8} {'C_REJ':<8}")
    print("-" * 70)
    for fam in sorted(families.keys()):
        f = families[fam]
        print(f"{fam:<6} {f['total']:<4} {f['b1_accept']:<8} {f['b1_reject']:<8} "
              f"{f['c_accept']:<8} {f['c_reject']:<8}")
    print()

    # Failure distribution per family
    print("FAILURE DISTRIBUTION PER FAMILY")
    print("-" * 70)
    for fam in sorted(families.keys()):
        fam_solvers = [sid for sid, r in per_solver.items() if r["family"] == fam]
        fail_counts = [per_solver[sid]["fail_count"] for sid in fam_solvers]
        avg_fails = sum(fail_counts) / len(fail_counts) if fail_counts else 0
        print(f"{fam}: avg_fail_rate={avg_fails / computed['total_probes']:.4f} "
              f"fail_counts={sorted(fail_counts)}")
    print()

    # PAS
    print("PARTITION ALIGNMENT SCORE")
    print("-" * 70)
    print(f"Same B1 pairs:           {computed['same_b1_pairs']}")
    print(f"Cross-family same B1:    {computed['cross_family_same_b1']}")
    print(f"Cross-family disagree:   {computed['cross_family_disagree']}")
    print(f"PAS:                     {computed['pas']:.4f}")
    print()

    # Binary outcome
    if computed["pas"] > epsilon:
        outcome = "A"
        print(f"OUTCOME: A -- Positive Separation (PAS={computed['pas']:.4f} > epsilon={epsilon})")
        print("C_genuine is NOT reducible to B1. Doctor exhibits structural sensitivity.")
    else:
        outcome = "B"
        print(f"OUTCOME: B -- No Separation (PAS={computed['pas']:.4f} <= epsilon={epsilon})")
        print("C_genuine collapses to scalar failure model.")
    print("=" * 90)

    return outcome


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("Loading solvers...")
    solver_ids = get_solver_ids()
    solver_fns = {}
    solver_meta = {}
    for sid in solver_ids:
        solver_fns[sid] = load_solver(sid)
        solver_meta[sid] = get_solver(sid)[:3]  # (family, s_axis, p_axis)
    print(f"Loaded {len(solver_ids)} solvers.")
    print()

    print("Evaluating solvers on probes...")
    results = {}
    for sid in solver_ids:
        results[sid] = evaluate_solver(solver_fns[sid], PROBES)
    print("Evaluation complete.")
    print()

    print("Computing PAS...")
    computed = compute_pas(results, solver_meta, PROBES, THRESHOLD_T)
    print()

    outcome = print_results(computed, EPSILON)

    # Write raw results to JSON
    output_path = Path(__file__).resolve().parent.parent / "results" / "csse_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "experiment": "CSSE_v1",
            "threshold_T": THRESHOLD_T,
            "epsilon": EPSILON,
            "pas": computed["pas"],
            "outcome": outcome,
            "per_solver": computed["per_solver"],
            "summary": {
                "same_b1_pairs": computed["same_b1_pairs"],
                "cross_family_same_b1": computed["cross_family_same_b1"],
                "cross_family_disagree": computed["cross_family_disagree"],
            },
            "probes": [{"probe_id": p["probe_id"], "probe_family": p["probe_family"], "axis": p["axis"]} for p in PROBES],
            "solver_meta": {sid: {"family": solver_meta[sid][0], "s_axis": solver_meta[sid][1], "p_axis": solver_meta[sid][2]} for sid in solver_ids},
        }, f, indent=2)
    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()
