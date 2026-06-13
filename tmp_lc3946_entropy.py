"""LC3946 Entropy Analysis — Per-solver failure distribution.

Loads per-probe pass/fail data, computes failure entropy across probe families,
identifies B1/C_genuine disagreements, and reports the per-solver table.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parent


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def failure_entropy(family_fails: dict[str, int]) -> float:
    """Shannon entropy of failure distribution across probe families."""
    total = sum(family_fails.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in family_fails.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def main():
    # Load data
    per_probe = load_json(REPO / "data" / "midweather_fingerprint_lc3946_per_probe.json")
    probe_index = load_json(REPO / "data" / "midweather_fingerprint_lc3946_probe_index.json")
    result = load_json(REPO / "data" / "midweather_fingerprint_lc3946.json")

    # Build probe_id -> family map
    probe_family = {p["probe_id"]: p["family"] for p in probe_index["probes"]}

    # Build per-solver B1 and C_genuine decisions
    # B1 and C_genuine are in the estimator_table
    b1_preds = {}
    c_gen_preds = {}
    for est_row in result["estimator_table"]:
        if est_row["estimator"] == "B1_count":
            # predictions are stripped from the stored file, need to recompute
            pass
        if est_row["estimator"] == "C_genuine":
            pass

    # Since predictions are stripped, recompute from pass_results
    # B1: ACCEPT iff zero observed failures
    # We need observed_ids and target_ids from the freeze
    freeze = load_json(REPO / "MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json")
    observed_ids = freeze["observation_budget"]["observed_probe_ids"]
    target_ids = freeze["observation_budget"]["target_probe_ids"]

    # Load the oracle to recompute decisions
    # B1 decision: ACCEPT iff zero failures on observed probes
    # C_genuine decision: ACCEPT iff zero failures OR failures span <= 1 family (on observed probes)

    # Get ground truth per solver
    ground = {}
    for sid, data in result["per_solver_ground_truth"].items():
        ground[sid] = data

    # Compute per-solver metrics
    solver_ids = sorted(per_probe.keys())
    rows = []
    for sid in solver_ids:
        probes = per_probe[sid]  # {probe_id: bool}

        # Total failures (across all probes)
        total_fails = sum(1 for v in probes.values() if not v)
        total = len(probes)

        # Observed failures
        obs_fails = sum(1 for pid in observed_ids if not probes.get(pid, True))
        obs_n = len(observed_ids)

        # Target failures
        tgt_fails = sum(1 for pid in target_ids if not probes.get(pid, True))
        tgt_n = len(target_ids)

        # B1 decision (on observed probes): ACCEPT iff obs_fails == 0
        b1 = "ACCEPT" if obs_fails == 0 else "REJECT"

        # C_genuine decision (on observed probes)
        if obs_fails == 0:
            c_gen = "ACCEPT"
        else:
            obs_families = set()
            for pid in observed_ids:
                if not probes.get(pid, True):
                    fam = probe_family.get(pid, "unknown")
                    obs_families.add(fam)
            c_gen = "ACCEPT" if len(obs_families) <= 1 else "REJECT"

        # Failure distribution across ALL probes (for entropy)
        family_fails = defaultdict(int)
        for pid, passed in probes.items():
            if not passed:
                fam = probe_family.get(pid, "unknown")
                family_fails[fam] += 1

        # Failure distribution across OBSERVED probes only (for C_genuine context)
        obs_family_fails = defaultdict(int)
        for pid in observed_ids:
            if not probes.get(pid, True):
                fam = probe_family.get(pid, "unknown")
                obs_family_fails[fam] += 1

        ent = failure_entropy(dict(family_fails))
        obs_ent = failure_entropy(dict(obs_family_fails))

        truth_label = ground.get(sid, {}).get("truth_label", "UNKNOWN")

        rows.append({
            "sid": sid,
            "truth": truth_label,
            "total_fails": total_fails,
            "total": total,
            "obs_fails": obs_fails,
            "obs_n": obs_n,
            "tgt_fails": tgt_fails,
            "tgt_n": tgt_n,
            "b1": b1,
            "c_gen": c_gen,
            "entropy_all": ent,
            "entropy_obs": obs_ent,
            "family_fails_all": dict(family_fails),
            "family_fails_obs": dict(obs_family_fails),
            "disagree": b1 != c_gen,
        })

    # ── Print disagreement table ───────────────────────────────────────────
    disagreements = [r for r in rows if r["disagree"]]

    print("=" * 110)
    print("LC3946 B1/C_genuine DISAGREEMENT TABLE")
    print("=" * 110)
    print(f"Total solvers: {len(rows)}")
    print(f"Disagreements: {len(disagreements)}")
    print()

    if disagreements:
        print(f"{'Solver':<14} {'Truth':<8} {'TgtF':<5} {'ObsF':<5} {'B1':<8} {'C_gen':<8} {'Ent(all)':<9} {'Ent(obs)':<9} {'Failure Families (observed probes)'}")
        print("-" * 110)
        for r in disagreements:
            obs_dist = ", ".join(f"{k}:{v}" for k, v in sorted(r["family_fails_obs"].items()))
            print(f"{r['sid']:<14} {r['truth']:<8} {r['tgt_fails']:<5} {r['obs_fails']:<5} "
                  f"{r['b1']:<8} {r['c_gen']:<8} {r['entropy_all']:<9.4f} {r['entropy_obs']:<9.4f} {obs_dist}")
    else:
        print("No disagreements found.")
    print()

    # ── Full table ─────────────────────────────────────────────────────────
    print("FULL SOLVER TABLE")
    print("-" * 110)
    print(f"{'Solver':<14} {'Truth':<8} {'TgtF':<5} {'ObsF':<5} {'B1':<8} {'C_gen':<8} {'Ent(all)':<9} {'Ent(obs)':<9} {'Disagree'}")
    print("-" * 110)
    for r in rows:
        marker = " <--" if r["disagree"] else ""
        print(f"{r['sid']:<14} {r['truth']:<8} {r['tgt_fails']:<5} {r['obs_fails']:<5} "
              f"{r['b1']:<8} {r['c_gen']:<8} {r['entropy_all']:<9.4f} {r['entropy_obs']:<9.4f} {r['disagree']}{marker}")
    print()

    # ── Summary statistics ─────────────────────────────────────────────────
    dis = [r for r in rows if r["disagree"]]
    agr = [r for r in rows if not r["disagree"]]

    print("ENTROPY SUMMARY")
    print("-" * 110)
    if dis:
        print(f"Disagreement solvers (n={len(dis)}):")
        print(f"  Mean entropy (all probes): {sum(r['entropy_all'] for r in dis)/len(dis):.4f}")
        print(f"  Mean entropy (obs probes): {sum(r['entropy_obs'] for r in dis)/len(dis):.4f}")
    if agr:
        print(f"Agreement solvers (n={len(agr)}):")
        print(f"  Mean entropy (all probes): {sum(r['entropy_all'] for r in agr)/len(agr):.4f}")
        print(f"  Mean entropy (obs probes): {sum(r['entropy_obs'] for r in agr)/len(agr):.4f}")
    print("=" * 110)


if __name__ == "__main__":
    main()
