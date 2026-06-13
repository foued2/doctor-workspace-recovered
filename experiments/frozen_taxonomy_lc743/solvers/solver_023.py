"""LC743 frozen solver s023: F3 family.
Mechanism: subtracts 1 from each edge weight
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s023 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
