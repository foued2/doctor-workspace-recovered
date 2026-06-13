"""LC743 frozen solver s012: F2 family.
Mechanism: uses ceil(w/2) instead of w
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s012 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
