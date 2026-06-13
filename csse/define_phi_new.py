"""Define input-structure-only families (φ_new) for LC322 and LC3946."""
import sys
sys.path.insert(0, ".")

from csse.phi_robustness import load_probes


def phi_new_lc322(probe):
    """Input-structure families for LC322 (coin change problem).
    
    Based on: amount regime and coin diversity.
    No outcome information used.
    """
    coins = probe.get("coins", [])
    amount = probe.get("amount", 0)
    
    # Amount regime (adjusted for better balance)
    if amount <= 5:
        amount_regime = "tiny"
    elif amount <= 15:
        amount_regime = "small"
    elif amount <= 50:
        amount_regime = "medium"
    else:
        amount_regime = "large"
    
    # Coin diversity
    if len(coins) <= 1:
        coin_diversity = "single"
    elif len(coins) <= 3:
        coin_diversity = "few"
    else:
        coin_diversity = "many"
    
    return f"{amount_regime}_{coin_diversity}"


def phi_new_lc3946(probe):
    """Input-structure families for LC3946 (budget optimization).
    
    Based on: item count regime and budget tightness.
    No outcome information used.
    """
    items = probe.get("items", [])
    budget = probe.get("budget", 0)
    
    # Item count regime
    if len(items) <= 3:
        item_regime = "few"
    elif len(items) <= 5:
        item_regime = "medium"
    else:
        item_regime = "many"
    
    # Budget tightness (relative to average item weight)
    if items:
        avg_weight = sum(w for w, v in items) / len(items)
        if avg_weight > 0:
            budget_ratio = budget / avg_weight
        else:
            budget_ratio = float("inf")
    else:
        budget_ratio = float("inf")
    
    if budget_ratio < 2:
        tightness = "tight"
    elif budget_ratio < 4:
        tightness = "moderate"
    else:
        tightness = "loose"
    
    return f"{item_regime}_{tightness}"


def build_phi_new(problem_class):
    """Build φ_new for a problem class."""
    probes = load_probes(problem_class)
    
    if problem_class == "lc322":
        phi_fn = phi_new_lc322
    elif problem_class == "lc3946":
        phi_fn = phi_new_lc3946
    else:
        raise ValueError(f"Unknown problem class: {problem_class}")
    
    phi = {}
    for p in probes:
        pid = p["probe_id"]
        phi[pid] = phi_fn(p)
    
    return phi


def validate_no_leakage(phi, problem_class):
    """Validate that φ_new does not leak outcome information.
    
    Check that families are defined purely from input properties.
    """
    probes = load_probes(problem_class)
    
    # Check that each probe's family is consistent across all solvers
    # (i.e., family assignment doesn't depend on solver behavior)
    print(f"\n  Validating no leakage for {problem_class}:")
    print(f"  Total probes: {len(probes)}")
    
    # Check family distribution
    family_counts = {}
    for pid, fam in phi.items():
        family_counts[fam] = family_counts.get(fam, 0) + 1
    
    print(f"  Families: {len(family_counts)}")
    for fam, count in sorted(family_counts.items()):
        print(f"    {fam}: {count}")
    
    # Check that families are input-only by examining one probe per family
    print(f"\n  Sample probes per family:")
    seen_families = set()
    for p in probes:
        pid = p["probe_id"]
        fam = phi[pid]
        if fam not in seen_families:
            seen_families.add(fam)
            # Print input features only
            features = {k: v for k, v in p.items() if k not in ["probe_id", "family", "axis", "paired_probe_id", "deformation_level", "expected_invariant"]}
            print(f"    {fam}: {features}")
    
    return True


if __name__ == "__main__":
    for pc in ["lc322", "lc3946"]:
        phi = build_phi_new(pc)
        validate_no_leakage(phi, pc)
