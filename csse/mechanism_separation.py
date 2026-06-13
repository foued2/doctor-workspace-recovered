"""Mechanism Separation Experiment — MECHANISM_SEPARATION_SPEC v1.0

Separates conservatism from family-structure as mechanism for ΔU > 0.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, extract_canonical_phi, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    b1_decision, c_genuine_decision, decision_loss_single,
    SEED, N_BOOTSTRAP,
    lc322_to_input, lc322_oracle,
    lc3946_to_input, lc3946_oracle,
)


# ══════════════════════════════════════════════════════════════════════════
# C_conservative: best count-threshold approximation to C_genuine
# ══════════════════════════════════════════════════════════════════════════

def find_best_count_threshold(solver_evals, phi, probe_ids, ground_truth):
    """Find count threshold T* that best approximates C_genuine decisions.

    Returns (T*, agreement_rate, confusion_matrix, all_T_results, genuine_decisions).
    """
    genuine_decisions = {}
    for sid, results in solver_evals.items():
        obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
        family_fails = defaultdict(int)
        for pid in probe_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1
        genuine_decisions[sid] = c_genuine_decision(dict(family_fails))

    fail_counts = {}
    for sid, results in solver_evals.items():
        fail_counts[sid] = sum(1 for pid in probe_ids if not results.get(pid, True))

    max_fails = max(fail_counts.values()) if fail_counts else 0

    best_T = 0
    best_agreement = -1.0
    results_by_T = {}

    for T in range(0, max_fails + 2):
        count_decisions = {
            sid: ("ACCEPT" if fail_counts[sid] <= T else "REJECT")
            for sid in fail_counts
        }
        agreements = sum(
            1 for sid in genuine_decisions
            if genuine_decisions[sid] == count_decisions[sid]
        )
        agreement_rate = agreements / len(genuine_decisions)

        tp = sum(1 for sid in genuine_decisions
                 if genuine_decisions[sid] == "ACCEPT" and count_decisions[sid] == "ACCEPT")
        fp = sum(1 for sid in genuine_decisions
                 if genuine_decisions[sid] == "REJECT" and count_decisions[sid] == "ACCEPT")
        fn = sum(1 for sid in genuine_decisions
                 if genuine_decisions[sid] == "ACCEPT" and count_decisions[sid] == "REJECT")
        tn = sum(1 for sid in genuine_decisions
                 if genuine_decisions[sid] == "REJECT" and count_decisions[sid] == "REJECT")

        results_by_T[T] = {
            "agreement_rate": agreement_rate,
            "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "count_accepts": sum(1 for v in count_decisions.values() if v == "ACCEPT"),
        }

        if agreement_rate > best_agreement:
            best_agreement = agreement_rate
            best_T = T

    return (best_T, results_by_T[best_T]["agreement_rate"],
            results_by_T[best_T]["confusion"], results_by_T, genuine_decisions)


# ══════════════════════════════════════════════════════════════════════════
# Three-way deltaU computation
# ══════════════════════════════════════════════════════════════════════════

def c_count_decision(obs_fails, threshold):
    """C_count(T): ACCEPT if obs_fails <= T, else REJECT."""
    return "ACCEPT" if obs_fails <= threshold else "REJECT"


def compute_deltaU_two_classifiers(solver_evals, phi, probe_ids, ground_truth,
                                    dec_a_fn, dec_b_fn,
                                    wrong_accept_cost, wrong_reject_cost):
    """Compute deltaU = mean[loss(A,s) - loss(B,s)] for two classifiers."""
    losses_a = []
    losses_b = []
    for sid, results in solver_evals.items():
        if sid not in ground_truth:
            continue
        is_correct = ground_truth[sid]
        obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
        family_fails = defaultdict(int)
        for pid in probe_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1

        dec_a = dec_a_fn(obs_fails, dict(family_fails))
        dec_b = dec_b_fn(obs_fails, dict(family_fails))

        losses_a.append(decision_loss_single(dec_a, is_correct, wrong_accept_cost, wrong_reject_cost))
        losses_b.append(decision_loss_single(dec_b, is_correct, wrong_accept_cost, wrong_reject_cost))

    if not losses_a:
        return 0.0
    return (sum(losses_a) - sum(losses_b)) / len(losses_a)


def bootstrap_ci_two_classifiers(solver_evals, phi, probe_ids, ground_truth,
                                  dec_a_fn, dec_b_fn,
                                  wrong_accept_cost, wrong_reject_cost,
                                  n_bootstrap=1000):
    """Bootstrap CI for deltaU between two classifiers."""
    import random
    rng = random.Random(SEED)
    sids = list(solver_evals.keys())
    point = compute_deltaU_two_classifiers(
        solver_evals, phi, probe_ids, ground_truth,
        dec_a_fn, dec_b_fn, wrong_accept_cost, wrong_reject_cost
    )
    boot_deltas = []
    for _ in range(n_bootstrap):
        sample = rng.choices(sids, k=len(sids))
        sub_evals = {sid: solver_evals[sid] for sid in sample}
        d = compute_deltaU_two_classifiers(
            sub_evals, phi, probe_ids, ground_truth,
            dec_a_fn, dec_b_fn, wrong_accept_cost, wrong_reject_cost
        )
        boot_deltas.append(d)
    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * n_bootstrap)]
    ci_hi = boot_deltas[int(0.975 * n_bootstrap)]
    return point, ci_lo, ci_hi


# ══════════════════════════════════════════════════════════════════════════
# Validation checkpoint: LC3946 only
# ══════════════════════════════════════════════════════════════════════════

def run_validation():
    print("=" * 70)
    print("  MECHANISM SEPARATION — LC322 at lambda=10, 50, 100")
    print("=" * 70)

    pc = "lc322"
    probes = load_probes(pc)
    phi = extract_canonical_phi(probes)
    obs, tgt = load_observed_target_split(pc)
    solver_evals = evaluate_frozen_solvers(pc, lc322_to_input, lc322_oracle, "single")
    ground_truth = load_ground_truth_from_json(pc)

    print(f"\n  Frozen solvers: {len(solver_evals)}")
    print(f"  Observed probes: {len(obs)}")

    # Step 1: find best threshold
    T_star, agreement, confusion, all_T, genuine_dec = find_best_count_threshold(
        solver_evals, phi, obs, ground_truth
    )

    print(f"\n  C_genuine decisions:")
    for sid in sorted(genuine_dec.keys()):
        print(f"    {sid}: {genuine_dec[sid]}")

    genuine_accepts = sum(1 for v in genuine_dec.values() if v == "ACCEPT")
    print(f"\n  C_genuine accept rate: {genuine_accepts}/{len(genuine_dec)} = {genuine_accepts/len(genuine_dec):.4f}")

    print(f"\n  Best threshold T*: {T_star}")
    print(f"  Agreement rate: {agreement:.4f}")
    print(f"  Confusion matrix: {confusion}")

    if agreement < 0.70:
        print(f"\n  STOP: Agreement rate {agreement:.4f} < 0.70. Comparison invalid.")
        return

    # Step 2: three-way comparison at lambda=10, 50, 100
    def b1_fn(obs_fails, family_fails):
        return b1_decision(obs_fails)

    def cgen_fn(obs_fails, family_fails):
        return c_genuine_decision(family_fails)

    def ccons_fn(obs_fails, family_fails):
        return c_count_decision(obs_fails, T_star)

    three_way = {}
    for lam in [10, 50, 100]:
        wa = 1.0
        wr = float(lam)

        du_b1_cgen, lo_b1_cgen, hi_b1_cgen = bootstrap_ci_two_classifiers(
            solver_evals, phi, obs, ground_truth, b1_fn, cgen_fn, wa, wr
        )
        du_b1_ccons, lo_b1_ccons, hi_b1_ccons = bootstrap_ci_two_classifiers(
            solver_evals, phi, obs, ground_truth, b1_fn, ccons_fn, wa, wr
        )
        du_ccons_cgen, lo_ccons_cgen, hi_ccons_cgen = bootstrap_ci_two_classifiers(
            solver_evals, phi, obs, ground_truth, ccons_fn, cgen_fn, wa, wr
        )

        b1_vs_ccons_excludes_zero = (lo_b1_ccons > 0) or (hi_b1_ccons < 0)
        ccons_vs_cgen_excludes_zero = (lo_ccons_cgen > 0) or (hi_ccons_cgen < 0)

        if b1_vs_ccons_excludes_zero and not ccons_vs_cgen_excludes_zero:
            pattern = "A"
        elif not b1_vs_ccons_excludes_zero and ccons_vs_cgen_excludes_zero:
            pattern = "B"
        elif b1_vs_ccons_excludes_zero and ccons_vs_cgen_excludes_zero:
            pattern = "C"
        else:
            pattern = "ambiguous"

        key = f"lambda_{lam}"
        three_way[key] = {
            "deltaU_b1_cgen": du_b1_cgen,
            "ci": [lo_b1_cgen, hi_b1_cgen],
            "deltaU_b1_ccons": du_b1_ccons,
            "ci": [lo_b1_ccons, hi_b1_ccons],
            "deltaU_ccons_cgen": du_ccons_cgen,
            "ci": [lo_ccons_cgen, hi_ccons_cgen],
            "b1_vs_ccons_excludes_zero": b1_vs_ccons_excludes_zero,
            "ccons_vs_cgen_excludes_zero": ccons_vs_cgen_excludes_zero,
            "pattern": pattern,
        }

        print(f"\n  lambda={lam}:")
        print(f"    deltaU(B1 vs C_genuine):              {du_b1_cgen:.6f}  [{lo_b1_cgen:.6f}, {hi_b1_cgen:.6f}]")
        print(f"    deltaU(B1 vs C_conservative):         {du_b1_ccons:.6f}  [{lo_b1_ccons:.6f}, {hi_b1_ccons:.6f}]")
        print(f"    deltaU(C_conservative vs C_genuine):  {du_ccons_cgen:.6f}  [{lo_ccons_cgen:.6f}, {hi_ccons_cgen:.6f}]")
        print(f"    Pattern: {pattern}")

    result = {
        "problem": "LC322",
        "lambda_values": [10, 50, 100],
        "c_genuine_decisions": genuine_dec,
        "c_genuine_accept_rate": genuine_accepts / len(genuine_dec),
        "best_threshold_T": T_star,
        "agreement_rate": agreement,
        "confusion_matrix": confusion,
        "three_way": three_way,
    }

    out_path = ROOT / "results" / "mechanism_separation_results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Results saved to {out_path}")

    return result


if __name__ == "__main__":
    run_validation()
