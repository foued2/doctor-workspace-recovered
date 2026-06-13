"""LC743 frozen solver s024: F3 family.
Mechanism: returns min distance instead of max
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s024 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
