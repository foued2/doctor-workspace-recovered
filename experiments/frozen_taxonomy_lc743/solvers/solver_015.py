"""LC743 frozen solver s015: F2 family.
Mechanism: returns sum of all distances instead of max
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s015 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
