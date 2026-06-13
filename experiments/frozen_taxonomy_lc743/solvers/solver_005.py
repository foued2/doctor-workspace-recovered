"""LC743 frozen solver s005: F1 family.
Mechanism: returns min distance instead of max
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s005 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
