"""LC743 frozen solver s030: F4 family.
Mechanism: returns 0 on disconnect
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s030 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
