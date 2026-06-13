"""LC743 frozen solver s001: F1 family.
Mechanism: reachability check uses reverse graph
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s001 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
