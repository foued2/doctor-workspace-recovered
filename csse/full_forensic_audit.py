"""Full forensic audit: every disagreement between C_genuine and best count-threshold."""
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


def c_count_decision(obs_fails, threshold):
    return "ACCEPT" if obs_fails <= threshold else "REJECT"


def find_best_threshold_and_disagreements(solver_evals, phi, probe_ids, ground_truth):
    """Find T* and all disagreements with C_genuine."""
    genuine_decisions = {}
    fail_counts = {}
    for sid, results in solver_evals.items():
        obs_fails = sum(1 for pid in probe_ids if not results.get(pid, True))
        fail_counts[sid] = obs_fails
        family_fails = defaultdict(int)
        for pid in probe_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1
        genuine_decisions[sid] = c_genuine_decision(dict(family_fails))

    max_fails = max(fail_counts.values()) if fail_counts else 0

    best_T = 0
    best_agreement = -1.0
    for T in range(0, max_fails + 2):
        count_decisions = {sid: c_count_decision(fail_counts[sid], T) for sid in fail_counts}
        agreements = sum(1 for sid in genuine_decisions if genuine_decisions[sid] == count_decisions[sid])
        agreement_rate = agreements / len(genuine_decisions)
        if agreement_rate > best_agreement:
            best_agreement = agreement_rate
            best_T = T

    count_decisions = {sid: c_count_decision(fail_counts[sid], best_T) for sid in fail_counts}

    disagreements = []
    for sid in sorted(solver_evals.keys()):
        if genuine_decisions[sid] != count_decisions[sid]:
            results = solver_evals[sid]
            obs_fails = fail_counts[sid]
            family_fails = defaultdict(int)
            for pid in probe_ids:
                if not results.get(pid, True):
                    fam = phi.get(pid, "unknown")
                    family_fails[fam] += 1

            losses = {}
            for lam in [10, 50, 100]:
                loss_b1 = decision_loss_single(b1_decision(obs_fails), ground_truth[sid], 1.0, float(lam))
                loss_cgen = decision_loss_single(genuine_decisions[sid], ground_truth[sid], 1.0, float(lam))
                loss_ccons = decision_loss_single(count_decisions[sid], ground_truth[sid], 1.0, float(lam))
                losses[lam] = {"b1": loss_b1, "cgen": loss_cgen, "ccons": loss_ccons}

            disagreements.append({
                "sid": sid,
                "obs_fails": obs_fails,
                "family_fails": dict(family_fails),
                "n_families_with_failures": len([f for f, c in family_fails.items() if c > 0]),
                "b1": b1_decision(obs_fails),
                "cgen": genuine_decisions[sid],
                "ccons": count_decisions[sid],
                "gt_correct": ground_truth[sid],
                "losses": losses,
            })

    genuine_accepts = sum(1 for v in genuine_decisions.values() if v == "ACCEPT")
    return best_T, best_agreement, genuine_accepts, len(genuine_decisions), disagreements, genuine_decisions


def run_audit():
    configs = [
        ("lc322", lc322_to_input, lc322_oracle, "single"),
        ("lc3946", lc3946_to_input, lc3946_oracle, "single"),
    ]

    all_results = {}

    for pc, to_input, oracle_fn, style in configs:
        print("=" * 70)
        print(f"  FORENSIC AUDIT: {pc.upper()}")
        print("=" * 70)

        probes = load_probes(pc)
        phi = extract_canonical_phi(probes)
        obs, tgt = load_observed_target_split(pc)
        solver_evals = evaluate_frozen_solvers(pc, to_input, oracle_fn, style)
        ground_truth = load_ground_truth_from_json(pc)

        T_star, agreement, n_accept, n_total, disagreements, genuine_dec = \
            find_best_threshold_and_disagreements(solver_evals, phi, obs, ground_truth)

        print(f"\n  T* = {T_star}")
        print(f"  Agreement = {agreement:.4f} ({int(agreement * n_total)}/{n_total})")
        print(f"  C_genuine accept rate = {n_accept}/{n_total} = {n_accept/n_total:.4f}")
        print(f"  Disagreements = {len(disagreements)}")

        if not disagreements:
            print(f"\n  No disagreements. C_count(T*={T_star}) perfectly replicates C_genuine.")
            all_results[pc] = {
                "T_star": T_star,
                "agreement": agreement,
                "n_disagreements": 0,
                "disagreements": [],
            }
            continue

        print(f"\n  {'='*60}")
        print(f"  DISAGREEMENT DETAILS")
        print(f"  {'='*60}")

        for d in disagreements:
            print(f"\n  --- {d['sid']} ---")
            print(f"  Ground truth: {'ACCEPT (correct)' if d['gt_correct'] else 'REJECT (incorrect)'}")
            print(f"  obs_fails = {d['obs_fails']}, families with failures = {d['n_families_with_failures']}")
            print(f"  Family distribution: {d['family_fails']}")
            print(f"  B1={d['b1']}, C_genuine={d['cgen']}, C_conservative={d['ccons']}")
            for lam in [10, 50, 100]:
                l = d["losses"][lam]
                print(f"  lambda={lam:>3}: B1={l['b1']:.1f} C_genuine={l['cgen']:.1f} C_conservative={l['ccons']:.1f} "
                      f"residual(Ccons-Cgen)={l['ccons']-l['cgen']:+.1f}")

        # Aggregate residual
        print(f"\n  {'='*60}")
        print(f"  AGGREGATE RESIDUAL")
        print(f"  {'='*60}")
        for lam in [10, 50, 100]:
            total_residual = sum(d["losses"][lam]["ccons"] - d["losses"][lam]["cgen"] for d in disagreements)
            print(f"  lambda={lam:>3}: total residual from disagreements = {total_residual:+.1f} "
                  f"(per solver: {total_residual/n_total:+.4f})")

        all_results[pc] = {
            "T_star": T_star,
            "agreement": agreement,
            "n_disagreements": len(disagreements),
            "disagreements": disagreements,
        }

        print()

    # Final summary
    print("=" * 70)
    print("  CROSS-PROBLEM SUMMARY")
    print("=" * 70)
    for pc, res in all_results.items():
        n_dis = res["n_disagreements"]
        print(f"\n  {pc.upper()}:")
        print(f"    T*={res['T_star']}, agreement={res['agreement']:.4f}, disagreements={n_dis}")
        if n_dis == 0:
            print(f"    Family structure contributes zero decision information.")
        else:
            for d in res["disagreements"]:
                direction = "C_genuine better" if d["cgen"] == "REJECT" and d["gt_correct"] == False else \
                            "C_conservative better" if d["ccons"] != d["cgen"] and d["cgen"] != "REJECT" else \
                            "C_genuine better" if d["ccons"] != d["cgen"] else "same"
                # Simpler: just say who the ground truth supports
                if d["gt_correct"]:
                    correct_decision = "ACCEPT"
                    who_got_it_right = "C_conservative" if d["ccons"] == correct_decision else "C_genuine"
                else:
                    correct_decision = "REJECT"
                    who_got_it_right = "C_genuine" if d["cgen"] == correct_decision else "C_conservative"

                print(f"    {d['sid']}: gt={'ACCEPT' if d['gt_correct'] else 'REJECT'}, "
                      f"obs_fails={d['obs_fails']}, families={d['n_families_with_failures']}, "
                      f"correct_decision={correct_decision}, got_it_right={who_got_it_right}")

    out_path = ROOT / "results" / "mechanism_separation_audit.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Audit saved to {out_path}")


if __name__ == "__main__":
    run_audit()
