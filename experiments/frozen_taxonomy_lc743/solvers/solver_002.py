"""LC743 frozen solver s002: F1 family.
Mechanism: only explores direct neighbors of source
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s002 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
