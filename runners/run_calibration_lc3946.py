#!/usr/bin/env python3
"""
Quick runner for Calibration Stability Protocol on LC3946.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runners.load_calibration_data import load_lc3946_data
from doctor.protocols.calibration_stability_protocol import run_protocol


def main():
    solver_evals, phi = load_lc3946_data()
    print(f"Loaded {len(solver_evals)} solvers, {len(phi)} probes")

    result = run_protocol(
        solver_evals=solver_evals,
        phi=phi,
        K=20,
        n_solvers=30,
        cal_ratio=0.7,
        seed_base=1,
        invert_pass_fail=True,  # LC3946 uses True=pass, protocol expects True=fail
    )

    output_path = REPO_ROOT / "results" / "calibration_stability"
    output_path.mkdir(parents=True, exist_ok=True)
    out_file = output_path / "calibration_stability_lc3946.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)

    s = result["summary"]
    print(f"\n=== Calibration Stability Protocol v1.2 (LC3946) ===")
    print(f"K={s['K']}, n_solvers={s['n_solvers']}")
    print(f"Agreement: {s['mean_agreement']:.4f} +/- {s['std_agreement']:.4f}")
    print(f"Event entropy: {s['mean_event_entropy']:.4f}")
    print(f"Solver entropy: {s['mean_solver_entropy']:.4f}")
    print(f"Cov(A, event_entropy): {s['cov_agreement_event_entropy']:.6f}")
    print(f"Cov(A, solver_entropy): {s['cov_agreement_solver_entropy']:.6f}")

    # Print per-fold results
    print(f"\n--- Per-fold results ---")
    for f in result["fold_results"]:
        print(f"Fold {f['fold']:2d}: A={f['agreement']:.3f}, "
              f"ee={f['event_entropy']:.3f}, se={f['solver_entropy']:.3f}, "
              f"T*={f['T_star']}")

    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
