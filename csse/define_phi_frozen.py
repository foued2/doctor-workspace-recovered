"""Frozen exogenous phi definitions (no tuning allowed).

These are defined ONCE using only static input properties.
No reference to failure patterns, solver behavior, or outcomes.
No further edits allowed after this point.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import load_probes


def phi_frozen_lc322(probe):
    """Frozen exogenous phi for LC322.
    
    Based ONLY on: amount (input length).
    No solver behavior, no failure patterns, no outcome information.
    """
    amount = probe.get("amount", 0)
    
    if amount <= 5:
        return "tiny"
    elif amount <= 20:
        return "small"
    elif amount <= 100:
        return "medium"
    else:
        return "large"


def phi_frozen_lc3946(probe):
    """Frozen exogenous phi for LC3946.
    
    Based ONLY on: number of items (input length).
    No solver behavior, no failure patterns, no outcome information.
    """
    items = probe.get("items", [])
    n_items = len(items)
    
    if n_items <= 3:
        return "few"
    elif n_items <= 5:
        return "medium"
    else:
        return "many"


def phi_frozen_lc45(probe):
    """Frozen exogenous phi for LC45.
    
    Based ONLY on: array length (input size).
    No solver behavior, no failure patterns, no outcome information.
    """
    nums = probe.get("nums", [])
    n = len(nums)
    
    if n <= 4:
        return "short"
    elif n <= 7:
        return "medium"
    else:
        return "long"


def build_phi_frozen(problem_class):
    """Build frozen exogenous phi for a problem class."""
    probes = load_probes(problem_class)
    
    if problem_class == "lc322":
        phi_fn = phi_frozen_lc322
    elif problem_class == "lc3946":
        phi_fn = phi_frozen_lc3946
    elif problem_class == "lc45":
        phi_fn = phi_frozen_lc45
    else:
        raise ValueError(f"Unknown problem class: {problem_class}")
    
    phi = {}
    for p in probes:
        pid = p["probe_id"]
        phi[pid] = phi_fn(p)
    
    return phi


if __name__ == "__main__":
    for pc in ["lc322", "lc3946"]:
        phi = build_phi_frozen(pc)
        family_counts = {}
        for fam in phi.values():
            family_counts[fam] = family_counts.get(fam, 0) + 1
        print(f"{pc}: {len(family_counts)} families: {family_counts}")
