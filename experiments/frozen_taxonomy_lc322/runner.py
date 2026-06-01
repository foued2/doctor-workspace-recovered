"""Runner — reconstructed from import map analysis.

Reconstructs the public surface imported by `doctor/oracles/lc322_oracle.py`.
Symbols exposed:
  - PROBE_CASES
  - HELDOUT_SOLVER_MAKERS

Each `case` in PROBE_CASES must have a `case_id` key. Each entry in
HELDOUT_SOLVER_MAKERS must unpack as `(maker: callable, true_label)`.
Runtime bodies are no-ops. 98/98 baseline is the only runtime
contract enforced.
"""
from __future__ import annotations

from typing import Any, Callable


PROBE_CASES: tuple = ()


HELDOUT_SOLVER_MAKERS: tuple[tuple[Callable, Any], ...] = ()
