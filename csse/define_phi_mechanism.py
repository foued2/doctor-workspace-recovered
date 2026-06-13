"""Define mechanism-aligned phi_new for LC322 and LC3946.

These families correspond to hypothesized solver failure mechanisms,
not input syntax or output labels.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import load_probes


def is_canonical_coins(coins):
    """Check if coin set is canonical (greedy works for all amounts).
    
    Canonical sets: {1}, {1,5}, {1,5,10}, {1,5,10,25}, etc.
    Non-canonical: {1,3,4}, {1,5,6}, {3,5,7}, etc.
    """
    if not coins:
        return False
    if coins == [1]:
        return True
    if sorted(coins) == [1, 5]:
        return True
    if sorted(coins) == [1, 5, 10]:
        return True
    if sorted(coins) == [1, 5, 10, 25]:
        return True
    if sorted(coins) == [1, 2, 5, 10]:
        return True
    if sorted(coins) == [1, 2, 5, 10, 50]:
        return True
    return False


def phi_mechanism_lc322(probe):
    """Mechanism-aligned families for LC322 (coin change problem).
    
    Hypothesized failure mechanisms:
    1. greedy_tiny: Non-canonical coins, tiny amount (greedy fails, DP trivial)
    2. greedy_small: Non-canonical coins, small amount (greedy fails, DP easy)
    3. greedy_medium: Non-canonical coins, medium amount (greedy fails, DP moderate)
    4. greedy_large: Non-canonical coins, large amount (greedy fails, DP stressed)
    5. canonical_easy: Canonical coins, small amount (both work)
    6. canonical_stress: Canonical coins, large amount (DP stressed)
    7. boundary: Edge cases (single coin, amount=0)
    
    Each family maps to a distinct solver failure mode.
    """
    coins = probe.get("coins", [])
    amount = probe.get("amount", 0)
    
    # Check for boundary cases
    if amount == 0 or len(coins) <= 1:
        return "boundary"
    
    # Check for greedy-fragile cases (non-canonical coins)
    if not is_canonical_coins(coins):
        if amount <= 10:
            return "greedy_tiny"
        elif amount <= 20:
            return "greedy_small"
        elif amount <= 50:
            return "greedy_medium"
        else:
            return "greedy_large"
    
    # Canonical coins
    if amount > 100:
        return "canonical_stress"
    
    return "canonical_easy"


def phi_mechanism_lc3946(probe):
    """Mechanism-aligned families for LC3946 (budget optimization).
    
    Hypothesized failure mechanisms:
    1. factor_budget_tight: Tight budget where "free item" calculation is critical
    2. factor_budget_loose: Loose budget where "free item" calculation is easy
    3. subset_enumeration: Many items requiring careful subset selection
    4. greedy_price_error: Items with similar prices but different values
    5. easy_instance: Simple cases where basic approaches work
    
    Each family maps to a distinct solver failure mode.
    """
    items = probe.get("items", [])
    budget = probe.get("budget", 0)
    
    if not items:
        return "easy_instance"
    
    n_items = len(items)
    weights = [w for w, v in items]
    values = [v for w, v in items]
    
    total_weight = sum(weights)
    budget_tightness = budget / total_weight if total_weight > 0 else float("inf")
    
    # Subset enumeration complexity
    if n_items >= 5:
        return "subset_enumeration"
    
    # Factor budget complexity
    if budget_tightness < 0.5:
        return "factor_budget_tight"
    
    if budget_tightness < 1.0:
        return "factor_budget_loose"
    
    # Price error cases
    if n_items >= 3:
        avg_price = sum(weights) / n_items
        price_variance = sum((w - avg_price)**2 for w in weights) / n_items
        if price_variance > 5:
            return "greedy_price_error"
    
    return "easy_instance"


def build_phi_mechanism(problem_class):
    """Build mechanism-aligned phi for a problem class."""
    probes = load_probes(problem_class)
    
    if problem_class == "lc322":
        phi_fn = phi_mechanism_lc322
    elif problem_class == "lc3946":
        phi_fn = phi_mechanism_lc3946
    else:
        raise ValueError(f"Unknown problem class: {problem_class}")
    
    phi = {}
    for p in probes:
        pid = p["probe_id"]
        phi[pid] = phi_fn(p)
    
    return phi


def validate_mechanism_phi(phi, problem_class):
    """Validate mechanism-aligned phi."""
    probes = load_probes(problem_class)
    
    print(f"\n  Mechanism-aligned phi for {problem_class}:")
    
    # Family distribution
    family_counts = {}
    for pid, fam in phi.items():
        family_counts[fam] = family_counts.get(fam, 0) + 1
    
    print(f"  Families: {len(family_counts)}")
    for fam, count in sorted(family_counts.items()):
        print(f"    {fam}: {count}")
    
    # Sample probes per family
    print(f"\n  Sample probes per family:")
    seen_families = set()
    for p in probes:
        pid = p["probe_id"]
        fam = phi[pid]
        if fam not in seen_families:
            seen_families.add(fam)
            features = {k: v for k, v in p.items() if k not in ["probe_id", "family", "axis", "paired_probe_id", "deformation_level", "expected_invariant"]}
            print(f"    {fam}: {features}")
    
    return True


if __name__ == "__main__":
    for pc in ["lc322", "lc3946"]:
        phi = build_phi_mechanism(pc)
        validate_mechanism_phi(phi, pc)
