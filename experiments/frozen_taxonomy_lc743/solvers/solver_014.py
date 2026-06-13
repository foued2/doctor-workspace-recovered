"""LC743 frozen solver s014: F2 family.
Mechanism: max(a,b) instead of min(a,b) in relaxation
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s014 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
