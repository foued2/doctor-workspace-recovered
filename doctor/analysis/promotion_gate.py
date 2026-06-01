"""Promotion gate — decides whether to promote a candidate based on agreement."""
from __future__ import annotations

from typing import Any


def should_promote(agreement_result: Any) -> bool:
    """
    Decide whether to promote a candidate based on agreement result.

    agreement_result has .verdict attribute: "PASS", "INCONCLUSIVE", "FAIL"
    """
    verdict = getattr(agreement_result, "verdict", "FAIL")
    return verdict == "PASS"
