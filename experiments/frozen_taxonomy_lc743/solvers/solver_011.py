"""LC743 frozen solver s011: F2 family.
Mechanism: relaxes edges in reverse direction
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s011 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
