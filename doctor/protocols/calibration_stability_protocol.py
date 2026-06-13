"""
Calibration Stability Protocol v1.2

Tests whether C_conservative (thresholded count) is a stable surrogate
of C_genuine (per-solver local decision functional) under IID resampling.

Core question:
    Is agreement between C_genuine and C_conservative stable under
    distribution shift in solver populations, and is stability
    explained by failure-distribution entropy?

Objects:
    C_genuine(s, phi): per-solver local functional
        ACCEPT iff failures span <= 1 family under phi
    C_count(T, s): thresholded count
        ACCEPT iff obs_fails(s) <= T
    T_star(S_cal): argmin_T mismatch on calibration set
        Tie-breaking: smallest T
    A_k: agreement on test set
    entropy_k: failure distribution entropy for sample

Dependency class: A (per-solver local, conditionally IID)
"""

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


# ══════════════════════════════════════════════════════════════════════════
# Core decision functions
# ══════════════════════════════════════════════════════════════════════════

def c_genuine_decision(family_fails: dict[str, int]) -> str:
    """C_genuine: per-solver local functional.
    ACCEPT iff 0 failures or all failures in <= 1 family.
    """
    if sum(family_fails.values()) == 0:
        return "ACCEPT"
    if len(family_fails) <= 1:
        return "ACCEPT"
    return "REJECT"


def c_count_decision(obs_fails: int, T: int) -> str:
    """C_count: thresholded count functional.
    ACCEPT iff obs_fails <= T.
    """
    return "ACCEPT" if obs_fails <= T else "REJECT"


# ══════════════════════════════════════════════════════════════════════════
# Entropy computation
# ══════════════════════════════════════════════════════════════════════════

def compute_event_entropy(solver_evals: dict, phi: dict[str, str]) -> float:
    """Entropy over failure events (family-weighted).
    H_events = -sum_f p_f log(p_f)
    where p_f = failures in family f / total failures
    """
    family_counts = defaultdict(int)
    for sid, results in solver_evals.items():
        for pid, passed in results.items():
            if not passed:
                fam = phi.get(pid, "unknown")
                family_counts[fam] += 1

    total = sum(family_counts.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in family_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log(p)

    return entropy


def compute_solver_entropy(solver_evals: dict, phi: dict[str, str]) -> float:
    """Solver-normalized entropy: mean of per-solver entropies.
    H_solvers = (1/n) sum_s H(s)
    where H(s) = entropy of solver s's failure distribution
    """
    entropies = []
    for sid, results in solver_evals.items():
        family_fails = defaultdict(int)
        for pid, passed in results.items():
            if not passed:
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1

        total = sum(family_fails.values())
        if total == 0:
            entropies.append(0.0)
            continue

        h = 0.0
        for count in family_fails.values():
            if count > 0:
                p = count / total
                h -= p * math.log(p)
        entropies.append(h)

    return sum(entropies) / len(entropies) if entropies else 0.0


# ══════════════════════════════════════════════════════════════════════════
# T_star derivation with tie-breaking
# ══════════════════════════════════════════════════════════════════════════

def derive_t_star(
    solver_evals_cal: dict,
    phi: dict[str, str],
    tie_break: str = "smallest"
) -> int:
    """Derive T_star on calibration set.
    Tie-breaking: 'smallest' (default) selects minimal T achieving min loss.
    """
    genuine_decisions = {}
    fail_counts = {}

    for sid, results in solver_evals_cal.items():
        family_fails = defaultdict(int)
        for pid, passed in results.items():
            if not passed:
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1
        genuine_decisions[sid] = c_genuine_decision(dict(family_fails))
        fail_counts[sid] = sum(1 for p, passed in results.items() if not passed)

    max_fails = max(fail_counts.values()) if fail_counts else 0

    best_T = 0
    best_loss = float("inf")

    for T in range(0, max_fails + 2):
        loss = 0
        for sid in solver_evals_cal:
            count_decision = c_count_decision(fail_counts[sid], T)
            if count_decision != genuine_decisions[sid]:
                loss += 1
        if loss < best_loss:
            best_loss = loss
            best_T = T

    return best_T


# ══════════════════════════════════════════════════════════════════════════
# Agreement computation
# ══════════════════════════════════════════════════════════════════════════

def compute_agreement(
    solver_evals_test: dict,
    phi: dict[str, str],
    T_star: int
) -> float:
    """Agreement: fraction of solvers where C_count(T_star) = C_genuine."""
    if not solver_evals_test:
        return 0.0

    agree_count = 0
    for sid, results in solver_evals_test.items():
        family_fails = defaultdict(int)
        for pid, passed in results.items():
            if not passed:
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1

        cg = c_genuine_decision(dict(family_fails))
        fail_count = sum(1 for p, passed in results.items() if not passed)
        cc = c_count_decision(fail_count, T_star)

        if cg == cc:
            agree_count += 1

    return agree_count / len(solver_evals_test)


# ══════════════════════════════════════════════════════════════════════════
# Main protocol
# ══════════════════════════════════════════════════════════════════════════

def run_protocol(
    solver_evals: dict,
    phi: dict[str, str],
    K: int = 20,
    n_solvers: int = 30,
    cal_ratio: float = 0.7,
    seed_base: int = 1,
    invert_pass_fail: bool = False,
) -> dict:
    """Run calibration stability protocol.

    Args:
        solver_evals: {sid: {probe_id: bool (True=pass)}}
        phi: {probe_id: family_name}
        K: number of folds
        cal_ratio: fraction for calibration
        seed_base: starting seed
        n_solvers: solvers to sample per fold
        invert_pass_fail: if True, invert booleans (True=pass -> True=fail)

    Returns:
        dict with fold results, summary statistics
    """
    # Invert if needed: protocol internally uses True=fail
    if invert_pass_fail:
        solver_evals = {
            sid: {pid: not passed for pid, passed in results.items()}
            for sid, results in solver_evals.items()
        }

    all_sids = list(solver_evals.keys())
    fold_results = []

    for k in range(K):
        seed = seed_base + k
        rng = random.Random(seed)

        # Draw IID sample
        sample = rng.sample(all_sids, min(n_solvers, len(all_sids)))

        # Compute entropy for this sample
        sample_evals = {sid: solver_evals[sid] for sid in sample}
        event_entropy = compute_event_entropy(sample_evals, phi)
        solver_entropy = compute_solver_entropy(sample_evals, phi)

        # Split into calibration and test
        cal_size = int(len(sample) * cal_ratio)
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

    # Covariance: Cov(A, event_entropy)
    cov_a_ee = sum(
        (a - mean_a) * (ee - mean_ee)
        for a, ee in zip(agreements, event_entropies)
    ) / len(agreements)

    # Covariance: Cov(A, solver_entropy)
    cov_a_se = sum(
        (a - mean_a) * (se - mean_se)
        for a, se in zip(agreements, solver_entropies)
    ) / len(agreements)

    return {
        "fold_results": fold_results,
        "summary": {
            "K": K,
            "n_solvers": n_solvers,
            "cal_ratio": cal_ratio,
            "mean_agreement": mean_a,
            "std_agreement": std_a,
            "mean_event_entropy": mean_ee,
            "mean_solver_entropy": mean_se,
            "cov_agreement_event_entropy": cov_a_ee,
            "cov_agreement_solver_entropy": cov_a_se,
        },
    }


# ══════════════════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Calibration Stability Protocol v1.2")
    parser.add_argument("--solver-evals", required=True, help="Path to solver_evals JSON")
    parser.add_argument("--phi", required=True, help="Path to phi (probe-to-family) JSON")
    parser.add_argument("--output-dir", default="results/calibration_stability")
    parser.add_argument("--K", type=int, default=20, help="Number of folds")
    parser.add_argument("--n-solvers", type=int, default=30, help="Solvers per fold")
    parser.add_argument("--seed-base", type=int, default=1, help="Starting seed")
    args = parser.parse_args()

    # Load data
    with open(args.solver_evals) as f:
        solver_evals = json.load(f)
    with open(args.phi) as f:
        phi = json.load(f)

    # Run protocol
    result = run_protocol(
        solver_evals=solver_evals,
        phi=phi,
        K=args.K,
        n_solvers=args.n_solvers,
        seed_base=args.seed_base,
    )

    # Save
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    with open(output_path / "calibration_stability_result.json", "w") as f:
        json.dump(result, f, indent=2)

    # Print summary
    s = result["summary"]
    print(f"K={s['K']}, n_solvers={s['n_solvers']}")
    print(f"Agreement: {s['mean_agreement']:.4f} +/- {s['std_agreement']:.4f}")
    print(f"Event entropy: {s['mean_event_entropy']:.4f}")
    print(f"Solver entropy: {s['mean_solver_entropy']:.4f}")
    print(f"Cov(A, event_entropy): {s['cov_agreement_event_entropy']:.6f}")
    print(f"Cov(A, solver_entropy): {s['cov_agreement_solver_entropy']:.6f}")


if __name__ == "__main__":
    main()
