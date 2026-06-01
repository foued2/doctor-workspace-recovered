from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    pass_rate: float
    test_volume: int
    coverage: float
    error_flags: List[str]


def compute_evidence(
    total: int,
    passed: int,
    traces: Optional[List[Dict[str, Any]]] = None,
) -> Evidence:
    pass_rate = passed / total if total > 0 else 0.0
    test_volume = total

    error_flags = []
    if traces:
        for t in traces:
            if t.get("error"):
                error_flags.append(t.get("error_type", "unknown_error"))

    covered = sum(1 for t in (traces or []) if t.get("passed", False))
    coverage = covered / total if total > 0 else 0.0

    return Evidence(
        pass_rate=pass_rate,
        test_volume=test_volume,
        coverage=coverage,
        error_flags=error_flags,
    )
