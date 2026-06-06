# doctor/asymmetric_cost.py
# Phase C-1: Asymmetric-Cost Decision Utility
# Implements cost function, normalization, anti-degeneracy detection,
# and λ sweep runner.
# No new estimators. No new probes. Infrastructure only.

from __future__ import annotations

VALID_VERDICTS = {"ACCEPT", "REJECT"}


def compute_cost(
    decision: str,
    ground_truth: str,
    lambda_R: float,
    lambda_A: float,
) -> float:
    """Per-decision cost.

    decision=ACCEPT, ground_truth=REJECT  → false accept → cost = lambda_A
    decision=REJECT, ground_truth=ACCEPT  → false reject → cost = lambda_R
    decision == ground_truth              → correct      → cost = 0
    """
    if decision not in VALID_VERDICTS:
        raise ValueError(f"Invalid decision: {decision!r}. Must be ACCEPT or REJECT.")
    if ground_truth not in VALID_VERDICTS:
        raise ValueError(f"Invalid ground_truth: {ground_truth!r}. Must be ACCEPT or REJECT.")

    if decision == ground_truth:
        return 0.0
    if decision == "ACCEPT" and ground_truth == "REJECT":
        return float(lambda_A)
    # decision == "REJECT" and ground_truth == "ACCEPT"
    return float(lambda_R)


def compute_raw_cost(
    decisions: list[str],
    ground_truth: list[str],
    lambda_R: float,
    lambda_A: float,
) -> float:
    """Mean cost over population.

    raw_cost = mean(cost(d, g, lambda_R, lambda_A) for d, g in zip(decisions, ground_truth))
    """
    if len(decisions) == 0 or len(ground_truth) == 0:
        raise ValueError("decisions and ground_truth must not be empty.")
    if len(decisions) != len(ground_truth):
        raise ValueError(
            f"decisions and ground_truth must have the same length. "
            f"Got {len(decisions)} and {len(ground_truth)}."
        )

    total = sum(
        compute_cost(d, g, lambda_R, lambda_A)
        for d, g in zip(decisions, ground_truth)
    )
    return total / len(decisions)


def compute_normalized_utility(
    decisions: list[str],
    ground_truth: list[str],
    lambda_R: float,
    lambda_A: float,
) -> float:
    """Normalized utility per population.

    normalized_utility = 1 - raw_cost / lambda_A

    Per freeze file: lambda_A = 1 throughout.
    Normalization is per-population using that population's lambda_A.
    Can be negative when raw_cost > lambda_A.
    """
    raw = compute_raw_cost(decisions, ground_truth, lambda_R, lambda_A)
    return 1.0 - raw / float(lambda_A)


def is_degenerate(decisions: list[str]) -> bool:
    """Return True if all decisions are identical (all-ACCEPT or all-REJECT).

    Degenerate estimators are excluded from primary comparison at that lambda.
    They are recorded and reported, not silently dropped.
    """
    if len(decisions) == 0:
        raise ValueError("decisions must not be empty.")

    unique = set(decisions)
    return len(unique) == 1


def run_sweep(
    decisions: list[str],
    ground_truth: list[str],
    lambda_sweep: list[float],
    lambda_A: float = 1.0,
) -> list[dict]:
    """Run cost-weighted utility sweep over all lambda values.

    Returns one entry per lambda value. Each entry contains:
        lambda_R           : the tested ratio value
        raw_cost           : mean cost over population
        normalized_utility : 1 - raw_cost / lambda_A
        degenerate         : True if all decisions are identical

    Degenerate entries are included in the output for transparency.
    The caller is responsible for excluding degenerate entries from
    primary comparison.

    An empty lambda_sweep returns an empty list.
    """
    if len(lambda_sweep) == 0:
        return []

    results = []
    degenerate = is_degenerate(decisions)

    for lambda_R in lambda_sweep:
        raw = compute_raw_cost(decisions, ground_truth, lambda_R, lambda_A)
        nu = 1.0 - raw / float(lambda_A)
        results.append(
            {
                "lambda_R": lambda_R,
                "raw_cost": raw,
                "normalized_utility": nu,
                "degenerate": degenerate,
            }
        )

    return results


def run_sweep_aggregate(
    wrong_accepts: int,
    wrong_rejects: int,
    n_solvers: int,
    lambda_sweep: list[float],
    lambda_A: float = 1.0,
    *,
    degenerate_all_accept: bool = False,
    degenerate_all_reject: bool = False,
) -> list[dict]:
    """Apply cost sweep to aggregate (WA, WR) statistics.

    Under the PHASE_C1 freeze cost model, (WA, WR) is a sufficient statistic
    for total cost at any lambda. This function produces the same per-lambda
    raw_cost and normalized_utility that run_sweep would produce if the
    aggregate counts were expanded into per-solver decisions.

    Degeneracy is taken from the saved estimator_table flags
    (degenerate_all_accept, degenerate_all_reject), not derived from counts.
    The runner is responsible for passing the correct flags.

    The data files midweather_fingerprint_lc{322,45}.json persist per-estimator
    aggregate statistics only (wrong_accepts, wrong_rejects,
    degenerate_all_accept, degenerate_all_reject). They do not persist
    per-solver decision lists. This function is the aggregate-level entry
    point for the same sweep.
    """
    if n_solvers <= 0:
        raise ValueError(f"n_solvers must be positive, got {n_solvers}")
    if wrong_accepts < 0:
        raise ValueError(
            f"wrong_accepts must be non-negative, got {wrong_accepts}"
        )
    if wrong_rejects < 0:
        raise ValueError(
            f"wrong_rejects must be non-negative, got {wrong_rejects}"
        )
    if wrong_accepts + wrong_rejects > n_solvers:
        raise ValueError(
            f"wrong_accepts + wrong_rejects ({wrong_accepts + wrong_rejects}) "
            f"exceeds n_solvers ({n_solvers})"
        )
    if lambda_A <= 0:
        raise ValueError(f"lambda_A must be positive, got {lambda_A}")

    degenerate = degenerate_all_accept or degenerate_all_reject

    if len(lambda_sweep) == 0:
        return []

    results = []
    for lambda_R in lambda_sweep:
        if lambda_R <= 0:
            raise ValueError(
                f"lambda_R values must be positive, got {lambda_R}"
            )
        raw = (wrong_accepts * lambda_A + wrong_rejects * lambda_R) / n_solvers
        nu = 1.0 - raw / float(lambda_A)
        results.append(
            {
                "lambda_R": lambda_R,
                "raw_cost": raw,
                "normalized_utility": nu,
                "degenerate": degenerate,
            }
        )

    return results
