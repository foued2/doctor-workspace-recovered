"""LC3946 Joint Distribution: P(disagreement | ObsF=k, entropy=e).

Computes the full joint distribution of ObsF, entropy, and decision divergence
for all 30 LC3946 solvers.
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
    per_probe = load_json(REPO / "data" / "midweather_fingerprint_lc3946_per_probe.json")
    probe_index = load_json(REPO / "data" / "midweather_fingerprint_lc3946_probe_index.json")
    result = load_json(REPO / "data" / "midweather_fingerprint_lc3946.json")
    freeze = load_json(REPO / "MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json")

    probe_family = {p["probe_id"]: p["family"] for p in probe_index["probes"]}
    observed_ids = freeze["observation_budget"]["observed_probe_ids"]

    # Compute per-solver metrics
    rows = []
    for sid in sorted(per_probe.keys()):
        probes = per_probe[sid]

        obs_fails = sum(1 for pid in observed_ids if not probes.get(pid, True))

        # Observed failure distribution
        obs_family_fails = defaultdict(int)
        for pid in observed_ids:
            if not probes.get(pid, True):
                fam = probe_family.get(pid, "unknown")
                obs_family_fails[fam] += 1

        obs_ent = failure_entropy(dict(obs_family_fails))

        # B1 and C_genuine decisions
        b1 = "ACCEPT" if obs_fails == 0 else "REJECT"
        if obs_fails == 0:
            c_gen = "ACCEPT"
        else:
            c_gen = "ACCEPT" if len(obs_family_fails) <= 1 else "REJECT"

        disagree = 1 if b1 != c_gen else 0

        rows.append({
            "sid": sid,
            "obs_fails": obs_fails,
            "entropy": round(obs_ent, 4),
            "b1": b1,
            "c_gen": c_gen,
            "disagree": disagree,
        })

    # ── Joint distribution table ───────────────────────────────────────────
    print("=" * 80)
    print("LC3946 JOINT DISTRIBUTION: P(disagree | ObsF, entropy)")
    print("=" * 80)
    print()

    # Group by (obs_fails, entropy)
    joint = defaultdict(lambda: {"total": 0, "disagree": 0})
    for r in rows:
        key = (r["obs_fails"], r["entropy"])
        joint[key]["total"] += 1
        joint[key]["disagree"] += r["disagree"]

    print(f"{'ObsF':<6} {'Entropy':<10} {'N':<5} {'Disagree':<10} {'P(disagree)'}")
    print("-" * 50)
    for (obs_f, ent), counts in sorted(joint.items()):
        p_dis = counts["disagree"] / counts["total"] if counts["total"] > 0 else 0
        print(f"{obs_f:<6} {ent:<10.4f} {counts['total']:<5} {counts['disagree']:<10} {p_dis:.4f}")
    print()

    # ── Marginal: P(disagree | ObsF = k) ──────────────────────────────────
    print("MARGINAL: P(disagree | ObsF = k)")
    print("-" * 50)
    obsf_counts = defaultdict(lambda: {"total": 0, "disagree": 0})
    for r in rows:
        obsf_counts[r["obs_fails"]]["total"] += 1
        obsf_counts[r["obs_fails"]]["disagree"] += r["disagree"]

    print(f"{'ObsF':<6} {'N':<5} {'Disagree':<10} {'P(disagree)'}")
    print("-" * 50)
    for k in sorted(obsf_counts.keys()):
        c = obsf_counts[k]
        p = c["disagree"] / c["total"] if c["total"] > 0 else 0
        print(f"{k:<6} {c['total']:<5} {c['disagree']:<10} {p:.4f}")
    print()

    # ── Marginal: P(disagree | entropy = e) ────────────────────────────────
    print("MARGINAL: P(disagree | entropy = e)")
    print("-" * 50)
    ent_counts = defaultdict(lambda: {"total": 0, "disagree": 0})
    for r in rows:
        ent_counts[r["entropy"]]["total"] += 1
        ent_counts[r["entropy"]]["disagree"] += r["disagree"]

    print(f"{'Entropy':<10} {'N':<5} {'Disagree':<10} {'P(disagree)'}")
    print("-" * 50)
    for e in sorted(ent_counts.keys()):
        c = ent_counts[e]
        p = c["disagree"] / c["total"] if c["total"] > 0 else 0
        print(f"{e:<10.4f} {c['total']:<5} {c['disagree']:<10} {p:.4f}")
    print()

    # ── Full per-solver table ──────────────────────────────────────────────
    print("FULL PER-SOLVER TABLE")
    print("-" * 80)
    print(f"{'Solver':<14} {'ObsF':<6} {'Entropy':<10} {'B1':<8} {'C_gen':<8} {'Disagree'}")
    print("-" * 80)
    for r in rows:
        marker = " <--" if r["disagree"] else ""
        print(f"{r['sid']:<14} {r['obs_fails']:<6} {r['entropy']:<10.4f} "
              f"{r['b1']:<8} {r['c_gen']:<8} {r['disagree']}{marker}")
    print("=" * 80)


if __name__ == "__main__":
    main()
