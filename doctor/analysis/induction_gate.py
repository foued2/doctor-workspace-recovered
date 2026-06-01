"""Induction gate — evaluates unrecognized candidates for induction."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class InductionResult:
    eligible: bool
    rejection_reason: Optional[str] = None
    candidate_artifact: Optional[dict] = field(default_factory=dict)


def evaluate_induction_candidate(
    statement: str,
    source_code: str,
    spec_hypothesis: dict,
    oracle_state: dict,
    recognized: bool = False,
) -> InductionResult:
    """
    Evaluate whether an unrecognized candidate is eligible for induction.

    Returns InductionResult with eligibility and optional artifact.
    """
    if recognized:
        return InductionResult(
            eligible=False,
            rejection_reason="already_recognized",
        )

    if not source_code or not source_code.strip():
        return InductionResult(
            eligible=False,
            rejection_reason="no_source_code",
        )

    completeness = spec_hypothesis.get("completeness_score", 0.0)
    if completeness < 0.3:
        return InductionResult(
            eligible=False,
            rejection_reason="low_completeness",
        )

    oracle_decidability = str(oracle_state.get("decidability", "")).lower()
    if oracle_decidability == "undecidable":
        return InductionResult(
            eligible=False,
            rejection_reason="undecidable_problem",
        )

    candidate_type = "induction_candidate"

    return InductionResult(
        eligible=True,
        rejection_reason=None,
        candidate_artifact={
            "candidate_type": candidate_type,
            "statement": statement,
            "source_code": source_code,
            "spec_hypothesis": spec_hypothesis,
        },
    )
