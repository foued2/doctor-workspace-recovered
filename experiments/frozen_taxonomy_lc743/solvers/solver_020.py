"""LC743 frozen solver s020: F2 family.
Mechanism: doubles weights during graph construction
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s020 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
