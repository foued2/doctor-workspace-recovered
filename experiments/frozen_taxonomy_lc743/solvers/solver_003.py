"""LC743 frozen solver s003: F1 family.
Mechanism: returns node count instead of max distance
"""
from __future__ import annotations
from doctor.solvers.lc_743_solvers import s003 as _impl

def solve(times, n, k):
    return _impl(times, n, k)
