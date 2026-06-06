# doctor/identity_resolution.py
# Phase C-3a: Per-Solver Identity Resolution
# Implements D (disagreement support), A (advantage asymmetry),
# aggregate-consistency check, and three-case decision rule.
# No new estimators. No new probes. Infrastructure only.

from __future__ import annotations

VALID_VERDICTS = {"ACCEPT", "REJECT"}


def misclassified_set(
    decisions: list[str],
    ground_truth: list[str],
) -> set[int]:
    """Return the set of solver indices where decision != ground_truth."""
    if len(decisions) == 0:
        raise ValueError("decisions must not be empty.")
    if len(decisions) != len(ground_truth):
        raise ValueError(
            f"decisions and ground_truth must have the same length. "
            f"Got {len(decisions)} and {len(ground_truth)}."
        )
    for d in decisions:
        if d not in VALID_VERDICTS:
            raise ValueError(f"Invalid decision: {d!r}. Must be ACCEPT or REJECT.")
    for g in ground_truth:
        if g not in VALID_VERDICTS:
            raise ValueError(f"Invalid ground_truth: {g!r}. Must be ACCEPT or REJECT.")

    return {i for i, (d, g) in enumerate(zip(decisions, ground_truth)) if d != g}


def compute_D(
    decisions_C: list[str],
    decisions_B1: list[str],
    ground_truth: list[str],
) -> int:
    """Disagreement support size: |M_C △ M_B1|.

    D = 0 → C and B1 misclassify identical solver sets (full equivalence candidate).
    D > 0 → at least one solver is misclassified by one but not the other.
    Integer-valued. Threshold = 0 (no floating-point fuzz needed).
    """
    M_C  = misclassified_set(decisions_C,  ground_truth)
    M_B1 = misclassified_set(decisions_B1, ground_truth)
    return len(M_C.symmetric_difference(M_B1))


def compute_A(
    decisions_C: list[str],
    decisions_B1: list[str],
    ground_truth: list[str],
    lambda_sweep: list[float],
    lambda_A: float = 1.0,
) -> int:
    """Advantage asymmetry: max over λ, max over solver i of |cost_C(i,λ) - cost_B1(i,λ)|.

    A = 0 → identical per-solver costs at every λ.
    A > 0 → at least one solver at at least one λ is priced differently.
    Integer-valued under the freeze (costs are λ_R, λ_A=1, or 0).
    Threshold = 0.
    """
    if len(lambda_sweep) == 0:
        return 0

    n = len(ground_truth)
    if len(decisions_C) != n or len(decisions_B1) != n:
        raise ValueError("decisions_C, decisions_B1, and ground_truth must have the same length.")

    max_diff = 0

    for lambda_R in lambda_sweep:
        for i, (dc, db1, g) in enumerate(zip(decisions_C, decisions_B1, ground_truth)):
            cost_C  = _per_solver_cost(dc,  g, lambda_R, lambda_A)
            cost_B1 = _per_solver_cost(db1, g, lambda_R, lambda_A)
            diff = abs(cost_C - cost_B1)
            if diff > max_diff:
                max_diff = diff

    return int(max_diff)


def _per_solver_cost(
    decision: str,
    ground_truth: str,
    lambda_R: float,
    lambda_A: float,
) -> float:
    """Per-solver cost under asymmetric cost model."""
    if decision not in VALID_VERDICTS:
        raise ValueError(f"Invalid decision: {decision!r}.")
    if ground_truth not in VALID_VERDICTS:
        raise ValueError(f"Invalid ground_truth: {ground_truth!r}.")

    if decision == ground_truth:
        return 0.0
    if decision == "ACCEPT" and ground_truth == "REJECT":
        return float(lambda_A)
    return float(lambda_R)


def apply_three_case_rule(D: int, A: int) -> str:
    """Apply the pre-declared three-case decision rule.

    Case 1 — D = 0:          FULL_EQUIVALENCE
    Case 2 — D > 0, A = 0:   MASKED_DIVERGENCE
    Case 3 — D > 0, A > 0:   DIRECTIONAL_SUPERIORITY
    """
    if D < 0 or A < 0:
        raise ValueError(f"D and A must be non-negative integers. Got D={D}, A={A}.")
    if D == 0:
        return "FULL_EQUIVALENCE"
    if A == 0:
        return "MASKED_DIVERGENCE"
    return "DIRECTIONAL_SUPERIORITY"


def check_aggregate_consistency(
    decisions: list[str],
    ground_truth: list[str],
    expected_wrong_accepts: int,
    expected_wrong_rejects: int,
    estimator_name: str,
    population_id: str,
) -> None:
    """Verify per-solver decisions are consistent with stored (WA, WR) aggregates.

    Raises ValueError if inconsistent. This is a hard stop condition per C-3a spec §8.
    Must be called for every estimator before recording any result.
    """
    if len(decisions) != len(ground_truth):
        raise ValueError(
            f"[{population_id}/{estimator_name}] decisions and ground_truth length mismatch: "
            f"{len(decisions)} vs {len(ground_truth)}."
        )

    actual_WA = sum(
        1 for d, g in zip(decisions, ground_truth)
        if d == "ACCEPT" and g == "REJECT"
    )
    actual_WR = sum(
        1 for d, g in zip(decisions, ground_truth)
        if d == "REJECT" and g == "ACCEPT"
    )

    if actual_WA != expected_wrong_accepts or actual_WR != expected_wrong_rejects:
        raise ValueError(
            f"[{population_id}/{estimator_name}] Aggregate consistency check FAILED.\n"
            f"  Expected: WA={expected_wrong_accepts}, WR={expected_wrong_rejects}\n"
            f"  Actual:   WA={actual_WA}, WR={actual_WR}\n"
            f"  Stop condition triggered. Surface to Foued before proceeding."
        )
