#!/usr/bin/env python3
"""
Data loader for Calibration Stability Protocol v1.2.

Loads existing data files and converts them into the format
required by the protocol:
  - solver_evals: {sid: {probe_id: bool}} (True = passed)
  - phi: {probe_id: family_name}
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_lc3946_data():
    """Load LC3946 per-probe data and phi mapping."""
    per_probe_path = REPO_ROOT / "data" / "midweather_fingerprint_lc3946_per_probe.json"
    probe_index_path = REPO_ROOT / "data" / "midweather_fingerprint_lc3946_probe_index.json"

    with open(per_probe_path) as f:
        solver_evals = json.load(f)

    with open(probe_index_path) as f:
        probe_index = json.load(f)

    phi = {p["probe_id"]: p["family"] for p in probe_index["probes"]}

    return solver_evals, phi


def load_lc322_data():
    """Load LC322 per-probe data (must be generated first)."""
    per_probe_path = REPO_ROOT / "data" / "midweather_fingerprint_lc322_per_probe.json"
    probe_index_path = REPO_ROOT / "data" / "midweather_fingerprint_lc322_probe_index.json"

    if not per_probe_path.exists():
        print(
            f"ERROR: {per_probe_path} not found. "
            "Run: python runners/run_midweather_fingerprint_lc322.py --problem-class=lc322",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(per_probe_path) as f:
        solver_evals = json.load(f)

    with open(probe_index_path) as f:
        probe_index = json.load(f)

    phi = {p["probe_id"]: p["family"] for p in probe_index["probes"]}

    return solver_evals, phi


def load_data(problem_class: str):
    """Load data for the specified problem class."""
    if problem_class == "lc322":
        return load_lc322_data()
    elif problem_class == "lc3946":
        return load_lc3946_data()
    else:
        print(f"ERROR: unsupported problem class: {problem_class}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load data for calibration stability")
    parser.add_argument(
        "problem_class",
        choices=["lc322", "lc3946"],
        help="Problem class to load",
    )
    parser.add_argument("--output", help="Output path for loaded data (JSON)")
    args = parser.parse_args()

    solver_evals, phi = load_data(args.problem_class)
    print(f"Loaded {len(solver_evals)} solvers, {len(phi)} probes")

    if args.output:
        output = {
            "solver_evals": solver_evals,
            "phi": phi,
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Saved to {args.output}")
