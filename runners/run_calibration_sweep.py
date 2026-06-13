#!/usr/bin/env python3
"""
Calibration Stability Protocol v1.2 - Parameter sweep.

Runs the protocol across multiple calibration ratios to get
meaningful entropy variation within the fixed 30-solver population.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runners.load_calibration_data import load_lc322_data, load_lc3946_data
from doctor.protocols.calibration_stability_protocol import (
    run_protocol,
    compute_event_entropy,
    compute_solver_entropy,
    derive_t_star,
    compute_agreement,
)
import random


def run_sweep(solver_evals, phi, problem_class, K=20, n_solvers=30, seed_base=1):
    """Run protocol across calibration ratios, varying subset sizes."""
    results = {}

    # Sweep calibration ratios
    cal_ratios = [0.5, 0.6, 0.7, 0.8, 0.9]

    for cal_ratio in cal_ratios:
        result = run_protocol(
            solver_evals=solver_evals,
            phi=phi,
            K=K,
            n_solvers=n_solvers,
            cal_ratio=cal_ratio,
            seed_base=seed_base,
            invert_pass_fail=(problem_class == "lc3946"),
        )
        results[f"cal_ratio_{cal_ratio}"] = result

    # Also sweep n_solvers
    for n_sol in [10, 15, 20, 25, 30]:
        result = run_protocol(
            solver_evals=solver_evals,
            phi=phi,
            K=K,
            n_solvers=n_sol,
            cal_ratio=0.7,
            seed_base=seed_base,
            invert_pass_fail=(problem_class == "lc3946"),
        )
        results[f"n_solvers_{n_sol}"] = result

    return results


def run_subsample_sweep(solver_evals, phi, problem_class, K=20, seed_base=1):
    """
    Run protocol with subsampled populations to get entropy variation.

    For each fold, draw n_sub solvers from the population (without
    replacement), then run the protocol on that subsample.
    This creates variation in entropy across folds.
    """
    all_sids = list(solver_evals.keys())
    fold_results = []

    for k in range(K):
        seed = seed_base + k
        rng = random.Random(seed)

        # Draw a subsample of varying size
        n_sub = rng.randint(10, 30)
        sample = rng.sample(all_sids, n_sub)

        # Get subsample evals
        sub_evals = {sid: solver_evals[sid] for sid in sample}

        # Compute entropy for subsample
        event_entropy = compute_event_entropy(sub_evals, phi)
        solver_entropy = compute_solver_entropy(sub_evals, phi)

        # Split into calibration and test
        cal_size = int(len(sample) * 0.7)
        cal_sids = sample[:cal_size]
        test_sids = sample[cal_size:]

        cal_evals = {sid: solver_evals[sid] for sid in cal_sids}
        test_evals = {sid: solver_evals[sid] for sid in test_sids}

        # Derive T_star on calibration set
        T_star = derive_t_star(cal_evals, phi)

        # Compute agreement on test set
        agreement = compute_agreement(test_evals, phi, T_star)

        fold_results.append({
            "fold": k + 1,
            "seed": seed,
            "n_sub": n_sub,
            "n_cal": len(cal_sids),
            "n_test": len(test_sids),
            "T_star": T_star,
            "agreement": agreement,
            "event_entropy": event_entropy,
            "solver_entropy": solver_entropy,
        })

    # Summary statistics
    agreements = [f["agreement"] for f in fold_results]
    event_entropies = [f["event_entropy"] for f in fold_results]
    solver_entropies = [f["solver_entropy"] for f in fold_results]

    mean_a = sum(agreements) / len(agreements)
    std_a = (sum((a - mean_a) ** 2 for a in agreements) / len(agreements)) ** 0.5

    mean_ee = sum(event_entropies) / len(event_entropies)
    mean_se = sum(solver_entropies) / len(solver_entropies)

    cov_a_ee = sum(
        (a - mean_a) * (ee - mean_ee)
        for a, ee in zip(agreements, event_entropies)
    ) / len(agreements)

    cov_a_se = sum(
        (a - mean_a) * (se - mean_se)
        for a, se in zip(agreements, solver_entropies)
    ) / len(agreements)

    return {
        "fold_results": fold_results,
        "summary": {
            "K": K,
            "n_solvers_range": [10, 30],
            "cal_ratio": 0.7,
            "mean_agreement": mean_a,
            "std_agreement": std_a,
            "mean_event_entropy": mean_ee,
            "mean_solver_entropy": mean_se,
            "cov_agreement_event_entropy": cov_a_ee,
            "cov_agreement_solver_entropy": cov_a_se,
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Calibration Stability sweep")
    parser.add_argument(
        "problem_class",
        choices=["lc322", "lc3946"],
        help="Problem class to run",
    )
    parser.add_argument("--sweep", choices=["cal_ratio", "subsample"], default="subsample")
    args = parser.parse_args()

    if args.problem_class == "lc322":
        solver_evals, phi = load_lc322_data()
    else:
        solver_evals, phi = load_lc3946_data()

    print(f"Loaded {len(solver_evals)} solvers, {len(phi)} probes")

    if args.sweep == "cal_ratio":
        results = run_sweep(solver_evals, phi, args.problem_class)
    else:
        results = run_subsample_sweep(solver_evals, phi, args.problem_class)

    output_path = REPO_ROOT / "results" / "calibration_stability"
    output_path.mkdir(parents=True, exist_ok=True)
    out_file = output_path / f"calibration_stability_{args.problem_class}_{args.sweep}.json"

    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    if args.sweep == "subsample":
        s = results["summary"]
        print(f"\n=== Subsample Sweep ({args.problem_class.upper()}) ===")
        print(f"K={s['K']}, n_solvers_range={s['n_solvers_range']}")
        print(f"Agreement: {s['mean_agreement']:.4f} +/- {s['std_agreement']:.4f}")
        print(f"Event entropy: {s['mean_event_entropy']:.4f}")
        print(f"Solver entropy: {s['mean_solver_entropy']:.4f}")
        print(f"Cov(A, event_entropy): {s['cov_agreement_event_entropy']:.6f}")
        print(f"Cov(A, solver_entropy): {s['cov_agreement_solver_entropy']:.6f}")

        print(f"\n--- Per-fold results ---")
        for f in results["fold_results"]:
            print(f"Fold {f['fold']:2d}: A={f['agreement']:.3f}, "
                  f"ee={f['event_entropy']:.3f}, se={f['solver_entropy']:.3f}, "
                  f"T*={f['T_star']}, n_sub={f['n_sub']}")
    else:
        for key, val in results.items():
            s = val["summary"]
            print(f"\n{key}: A={s['mean_agreement']:.4f}+/-{s['std_agreement']:.4f}, "
                  f"Cov_ee={s['cov_agreement_event_entropy']:.6f}")

    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
