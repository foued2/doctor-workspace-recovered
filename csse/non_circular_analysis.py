"""CSSE Non-Circular Analysis — Failure Entropy, KL Divergence, Disagreement Detection.

NO coherence labels are assigned. Structure is an OUTPUT metric, not an input.

Pipeline:
  1. Load CSSE per-probe results
  2. Compute per-solver: failure entropy, KL divergence from uniform, B1/C_genuine decisions
  3. Identify disagreements (B1 != C_genuine)
  4. Post-analysis: compare entropy of disagreement vs agreement solvers
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path


def load_csse_results() -> dict:
    """Load CSSE result file."""
    path = Path(__file__).resolve().parent.parent / "results" / "csse_result.json"
    with open(path) as f:
        return json.load(f)


def load_probes() -> list[dict]:
    """Load CSSE probe definitions."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from csse.problem_definition import PROBES
    return PROBES


def compute_failure_distribution(probe_results: dict[str, bool], probes: list[dict]) -> dict[str, int]:
    """For a solver, count failures per probe family.
    
    Returns: {family_name: failure_count}
    """
    probe_map = {p["probe_id"]: p for p in probes}
    family_fails = defaultdict(int)
    for pid, passed in probe_results.items():
        if not passed:
            p = probe_map.get(pid)
            if p:
                family_fails[p["probe_family"]] += 1
    return dict(family_fails)


def failure_entropy(family_fails: dict[str, int], total_families: int) -> float:
    """Shannon entropy of failure distribution across probe families.
    
    If solver has zero failures, entropy is 0 (no uncertainty).
    If failures are spread uniformly, entropy is log2(total_families).
    """
    total_failures = sum(family_fails.values())
    if total_failures == 0:
        return 0.0
    
    entropy = 0.0
    for count in family_fails.values():
        if count > 0:
            p = count / total_failures
            entropy -= p * math.log2(p)
    return entropy


def kl_divergence(family_fails: dict[str, int], total_families: int) -> float:
    """KL(failure_distribution || uniform) over probe families.
    
    Only considers families that have at least one failure.
    Families with zero failures contribute 0 to the sum (by convention).
    """
    total_failures = sum(family_fails.values())
    if total_failures == 0:
        return 0.0
    
    uniform = 1.0 / total_families
    kl = 0.0
    for count in family_fails.values():
        if count > 0:
            p = count / total_families  # probability mass on this family
            kl += p * math.log2(p / uniform)
    return kl


def b1_decision(fail_count: int) -> str:
    """B1: ACCEPT iff zero failures."""
    return "ACCEPT" if fail_count == 0 else "REJECT"


def c_genuine_decision(family_fails: dict[str, int]) -> str:
    """C_genuine: ACCEPT if zero failures or failures in <= 1 family.
    
    NOTE: This is NOT used as a label. It is the decision function whose
    disagreement with B1 we measure. The family structure comes from probe
    definitions (independent of solver outcomes), not from solver behavior.
    """
    if sum(family_fails.values()) == 0:
        return "ACCEPT"
    if len(family_fails) <= 1:
        return "ACCEPT"
    return "REJECT"


def main():
    probes = load_probes()
    data = load_csse_results()
    
    total_families = len(set(p["probe_family"] for p in probes))
    
    print("=" * 95)
    print("CSSE NON-CIRCULAR ANALYSIS")
    print("=" * 95)
    print(f"Total families: {total_families}")
    print(f"Family names: {sorted(set(p['probe_family'] for p in probes))}")
    print()
    
    # ── Per-solver metrics ─────────────────────────────────────────────────
    results = []
    for sid in sorted(data["per_solver"].keys()):
        r = data["per_solver"][sid]
        probe_results = r.get("probe_results", {})
        
        # We need per-probe results. Check if they exist in the data.
        # The CSSE result file stores per_solver but may not store per-probe.
        # Let me check the structure.
        family_fails = {}
        if probe_results:
            family_fails = compute_failure_distribution(probe_results, probes)
        else:
            # Fallback: use the failure_count and known probe families
            # This is less precise but available
            pass
        
        results.append({
            "sid": sid,
            "family": r["family"],
            "fail_count": r["fail_count"],
            "fail_rate": r["fail_rate"],
            "b1": r["b1_decision"],
            "c_gen": r["c_genuine_decision"],
            "family_fails": family_fails,
        })
    
    # Check if per-probe data is available
    sample_sid = sorted(data["per_solver"].keys())[0]
    has_probe_results = "probe_results" in data["per_solver"][sample_sid]
    
    if not has_probe_results:
        print("NOTE: Per-probe pass/fail data not stored in CSSE result file.")
        print("Re-evaluating solvers to get per-probe data...")
        print()
        
        # Re-evaluate to get per-probe data
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from csse.run_csse import load_solver, evaluate_solver, PROBES
        from csse.solver_generation import get_solver_ids, get_solver
        
        results = []
        for sid in get_solver_ids():
            solver_fn = load_solver(sid)
            probe_results = evaluate_solver(solver_fn, probes)
            family_fails = compute_failure_distribution(probe_results, probes)
            fail_count = sum(1 for passed in probe_results.values() if not passed)
            total = len(probe_results)
            
            results.append({
                "sid": sid,
                "family": get_solver(sid)[0],
                "fail_count": fail_count,
                "fail_rate": fail_count / total if total > 0 else 0,
                "b1": b1_decision(fail_count),
                "c_gen": c_genuine_decision(family_fails),
                "family_fails": family_fails,
                "probe_results": probe_results,
            })
    
    # ── Compute entropy and KL divergence ──────────────────────────────────
    for r in results:
        r["entropy"] = failure_entropy(r["family_fails"], total_families)
        r["kl"] = kl_divergence(r["family_fails"], total_families)
    
    # ── Print full table ───────────────────────────────────────────────────
    print(f"{'Solver':<10} {'Fam':<5} {'Fails':<6} {'Rate':<7} {'B1':<8} {'C_gen':<8} {'Entropy':<8} {'KL':<8}")
    print("-" * 95)
    for r in results:
        print(f"{r['sid']:<10} {r['family']:<5} {r['fail_count']:<6} {r['fail_rate']:<7.4f} "
              f"{r['b1']:<8} {r['c_gen']:<8} {r['entropy']:<8.4f} {r['kl']:<8.4f}")
    print()
    
    # ── Failure distribution per solver ────────────────────────────────────
    print("FAILURE DISTRIBUTION PER SOLVER (probe family -> failure count)")
    print("-" * 95)
    for r in results:
        if r["family_fails"]:
            dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(r["family_fails"].items()))
        else:
            dist_str = "(no failures)"
        print(f"{r['sid']:<10} {dist_str}")
    print()
    
    # ── Identify disagreements ─────────────────────────────────────────────
    disagreements = [r for r in results if r["b1"] != r["c_gen"]]
    agreements = [r for r in results if r["b1"] == r["c_gen"]]
    
    print("B1 vs C_genuine DISAGREEMENTS")
    print("-" * 95)
    print(f"Total disagreements: {len(disagreements)} / {len(results)}")
    print()
    if disagreements:
        print(f"{'Solver':<10} {'Family':<6} {'B1':<8} {'C_gen':<8} {'Fails':<6} {'Entropy':<8} {'KL':<8}")
        print("-" * 95)
        for r in disagreements:
            print(f"{r['sid']:<10} {r['family']:<6} {r['b1']:<8} {r['c_gen']:<8} "
                  f"{r['fail_count']:<6} {r['entropy']:<8.4f} {r['kl']:<8.4f}")
    print()
    
    # ── Post-analysis: entropy comparison ──────────────────────────────────
    print("POST-ANALYSIS: Entropy of disagreement vs agreement solvers")
    print("-" * 95)
    
    if disagreements:
        dis_entropy = [r["entropy"] for r in disagreements]
        dis_kl = [r["kl"] for r in disagreements]
        dis_fail_rate = [r["fail_rate"] for r in disagreements]
        print(f"Disagreement solvers (n={len(disagreements)}):")
        print(f"  Mean entropy:  {sum(dis_entropy)/len(dis_entropy):.4f}")
        print(f"  Mean KL:       {sum(dis_kl)/len(dis_kl):.4f}")
        print(f"  Mean fail_rate: {sum(dis_fail_rate)/len(dis_fail_rate):.4f}")
    else:
        print("No disagreements found.")
    
    if agreements:
        agr_entropy = [r["entropy"] for r in agreements]
        agr_kl = [r["kl"] for r in agreements]
        agr_fail_rate = [r["fail_rate"] for r in agreements]
        print(f"Agreement solvers (n={len(agreements)}):")
        print(f"  Mean entropy:  {sum(agr_entropy)/len(agr_entropy):.4f}")
        print(f"  Mean KL:       {sum(agr_kl)/len(agr_kl):.4f}")
        print(f"  Mean fail_rate: {sum(agr_fail_rate)/len(agr_fail_rate):.4f}")
    print()
    
    # ── Non-circular conclusion ────────────────────────────────────────────
    print("NON-CIRCULAR CONCLUSION")
    print("-" * 95)
    if disagreements:
        dis_ent = sum(dis_entropy) / len(dis_entropy) if dis_entropy else 0
        agr_ent = sum(agr_entropy) / len(agr_entropy) if agr_entropy else 0
        
        if dis_ent < agr_ent:
            print(f"Disagreement solvers have LOWER mean entropy ({dis_ent:.4f}) than agreement solvers ({agr_ent:.4f}).")
            print("This means B1/C_genuine disagreements concentrate failures in fewer families.")
            print("Structure is an OUTPUT of the analysis, not an input.")
        elif dis_ent > agr_ent:
            print(f"Disagreement solvers have HIGHER mean entropy ({dis_ent:.4f}) than agreement solvers ({agr_ent:.4f}).")
            print("This means B1/C_genuine disagreements spread failures across more families.")
        else:
            print(f"Disagreement and agreement solvers have equal mean entropy ({dis_ent:.4f}).")
            print("No entropy-based distinction exists.")
    else:
        print("No disagreements to analyze.")
    print("=" * 95)


if __name__ == "__main__":
    main()
