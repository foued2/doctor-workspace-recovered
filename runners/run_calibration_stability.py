#!/usr/bin/env python3
"""
Runner for Calibration Stability Protocol v1.2.

Loads solver evaluations and phi mapping, runs the protocol,
saves results.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from doctor.protocols.calibration_stability_protocol import run_protocol


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Calibration Stability Protocol v1.2 runner"
    )
    parser.add_argument(
        "--solver-evals",
        required=True,
        help="Path to solver_evals JSON: {sid: {probe_id: bool}}",
    )
    parser.add_argument(
        "--phi",
        required=True,
        help="Path to phi JSON: {probe_id: family_name}",
    )
    parser.add_argument(
        "--output-dir",
        default="results/calibration_stability",
        help="Output directory",
    )
    parser.add_argument("--K", type=int, default=20, help="Number of folds")
    parser.add_argument("--n-solvers", type=int, default=30, help="Solvers per fold")
    parser.add_argument("--seed-base", type=int, default=1, help="Starting seed")
    args = parser.parse_args()

    # Load data
    with open(args.solver_evals) as f:
        solver_evals = json.load(f)
    with open(args.phi) as f:
        phi = json.load(f)

    print(f"Loaded {len(solver_evals)} solvers, {len(phi)} probes")

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
    out_file = output_path / "calibration_stability_result.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)

    # Print summary
    s = result["summary"]
    print(f"\n=== Calibration Stability Protocol v1.2 ===")
    print(f"K={s['K']}, n_solvers={s['n_solvers']}")
    print(f"Agreement: {s['mean_agreement']:.4f} +/- {s['std_agreement']:.4f}")
    print(f"Event entropy: {s['mean_event_entropy']:.4f}")
    print(f"Solver entropy: {s['mean_solver_entropy']:.4f}")
    print(f"Cov(A, event_entropy): {s['cov_agreement_event_entropy']:.6f}")
    print(f"Cov(A, solver_entropy): {s['cov_agreement_solver_entropy']:.6f}")
    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
