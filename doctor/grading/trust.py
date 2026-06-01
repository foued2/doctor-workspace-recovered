"""Grading trust — computes trust type and risk level."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def compute_trust_v1(
    E: int,
    evidence: Any,
    c: float,
) -> dict:
    """
    Compute trust type and risk level.

    E: execution correctness (1=correct, 0=incorrect)
    evidence: evidence dataclass with pass_rate, test_volume, coverage, error_flags
    c: model confidence (0.0-1.0)

    Returns:
        {"type": str, "risk": str}
    """
    pass_rate = getattr(evidence, "pass_rate", 0.0)
    test_volume = getattr(evidence, "test_volume", 0)
    error_flags = getattr(evidence, "error_flags", [])

    if E == 1 and pass_rate >= 0.9:
        trust_type = "HIGH"
        risk = "LOW"
    elif E == 1 and pass_rate < 0.9:
        trust_type = "MEDIUM"
        risk = "MEDIUM"
    elif E == 0 and pass_rate < 0.1:
        trust_type = "LOW"
        risk = "HIGH"
    else:
        trust_type = "MEDIUM"
        risk = "MEDIUM"

    if error_flags:
        risk = "HIGH"
        if trust_type == "HIGH":
            trust_type = "MEDIUM"

    if test_volume < 2:
        if trust_type == "HIGH":
            trust_type = "MEDIUM"
        risk = "MEDIUM"

    return {"type": trust_type, "risk": risk}
