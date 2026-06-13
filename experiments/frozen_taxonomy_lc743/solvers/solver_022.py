"""LC743 frozen solver s022: F3 family.
Mechanism: returns distance to node 1 instead of max
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s022 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
