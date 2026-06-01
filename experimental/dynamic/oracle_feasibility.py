"""experimental.dynamic.oracle_feasibility — stub.

Reconstructed from import map. `assess_oracle_feasibility` returns
an `OracleFeasibility` enum member; `.value` is accessed at the
call site, so the enum inherits from `str`.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class OracleFeasibility(str, Enum):
    UNKNOWN = "unknown"
    SOLVER_REQUIRED = "solver_required"
    SOLVER_OPTIONAL = "solver_optional"


def assess_oracle_feasibility(schema: Any) -> OracleFeasibility:
    return OracleFeasibility.UNKNOWN
