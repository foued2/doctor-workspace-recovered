"""LC743 frozen solver s018: F2 family.
Mechanism: adds node count to every edge weight
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s018 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
