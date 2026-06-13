"""LC743 frozen solver s016: F3 family.
Mechanism: BFS on weighted graph (ignores weights)
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s016 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
