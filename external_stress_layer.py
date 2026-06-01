"""external_stress_layer — reconstructed from import map analysis.

Reconstructs the public surface imported by `doctor/enhanced_evaluator.py`.
Symbols exposed:
  - StressMetrics
  - StressKind

StressMetrics is constructed with no args and returned as the type
annotation of a function returning a metrics object. StressKind is
imported but no attribute access is observed at the call site.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class StressKind(Enum):
    pass


class StressMetrics:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass
