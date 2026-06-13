"""LC743 frozen solver s004: F2 family.
Mechanism: adds source node ID to every edge weight
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s004 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
