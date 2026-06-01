"""Oracle feasibility — assesses whether oracle verification is possible."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OracleState:
    problem_id: Optional[str]
    decidability: str  # "decidable", "undecidable", "unknown"
    constructibility: str  # "constructible", "non_constructible", "unknown"
    oracle_available: bool
    reason: Optional[str] = None


def default_oracle_state() -> dict[str, str]:
    """Return default oracle state when no oracle is available."""
    return {
        "decidability": "unknown",
        "constructibility": "unknown",
        "oracle_available": "false",
    }


def assess_oracle_feasibility(problem_id: Optional[str]) -> OracleState:
    """Assess whether oracle verification is feasible for a problem."""
    if problem_id is None:
        return OracleState(
            problem_id=None,
            decidability="unknown",
            constructibility="unknown",
            oracle_available=False,
            reason="no_problem_id",
        )

    # Known problems with brute-force oracles
    _ORACLE_PROBLEMS = {
        "lc42", "lc312", "lc743", "lc406", "lc494",
        "lc875", "lc134", "cf607a", "lc1029", "lc3",
        "lc322",
        "two_sum", "arrange_numbers_divisible",
    }

    if problem_id in _ORACLE_PROBLEMS:
        return OracleState(
            problem_id=problem_id,
            decidability="decidable",
            constructibility="constructible",
            oracle_available=True,
        )

    return OracleState(
        problem_id=problem_id,
        decidability="unknown",
        constructibility="unknown",
        oracle_available=False,
        reason="not_in_oracle_set",
    )


def interpret_oracle_state(state: OracleState) -> dict:
    """Interpret oracle state into pipeline action."""
    if state.oracle_available:
        return {"proceed": True, "block_reason": None}
    if state.decidability == "unknown":
        return {"proceed": True, "block_reason": None}
    return {"proceed": True, "block_reason": None}


def serialize_oracle_state(state: OracleState) -> dict:
    """Serialize oracle state for trace."""
    return {
        "decidability": state.decidability,
        "constructibility": state.constructibility,
        "oracle_available": str(state.oracle_available).lower(),
        "problem_id": state.problem_id,
        "reason": state.reason,
    }
