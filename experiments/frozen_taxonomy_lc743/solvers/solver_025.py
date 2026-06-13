"""LC743 frozen solver s025: F4 family.
Mechanism: returns max reachable, ignores unreachable
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s025 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
