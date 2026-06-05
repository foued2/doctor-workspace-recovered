"""Tests for Week 8: bfs_agrees_rate encoder fix.

Guards against the encoder artifact regressing (bfs_agrees_rate becoming
informationally identical to pass_fail_rate again).
"""
from __future__ import annotations

from doctor.adversarial.problem_class_config import (
    lc45_raw_tensor_encoder,
    _bfs_reachable_count,
)


def test_bfs_reachable_count_helper():
    """The helper computes BFS reachable positions, not min-jump count."""
    assert _bfs_reachable_count([2, 3, 1, 1, 4]) == 5
    assert _bfs_reachable_count([1, 1, 1, 1]) == 4
    assert _bfs_reachable_count([0, 1]) == 1
    assert _bfs_reachable_count([]) == 0


def test_bfs_agrees_rate_is_not_pass_fail_rate():
    """The encoder artifact: bfs_agrees_rate must NOT equal pass_fail_rate.

    After Week 8 fix, bfs_agrees_rate compares candidate_output against the
    BFS reachable_count (number of positions BFS can reach from start), which
    is a different quantity from the min-jump count. No solver outputs the
    reachable count, so bfs_agrees_rate should be 0.0 for all solvers while
    pass_fail_rate varies for the passing solver.
    """
    obs_rows = [
        {"solver_id": "s1", "probe_id": "p1", "nums": [2, 3, 1, 1, 4],
         "candidate_output": 2, "expected_output": 2, "pass_fail": True},
        {"solver_id": "s1", "probe_id": "p2", "nums": [1, 1, 1, 1],
         "candidate_output": 3, "expected_output": 3, "pass_fail": True},
        {"solver_id": "s2", "probe_id": "p1", "nums": [2, 3, 1, 1, 4],
         "candidate_output": 3, "expected_output": 2, "pass_fail": False},
        {"solver_id": "s2", "probe_id": "p2", "nums": [1, 1, 1, 1],
         "candidate_output": 2, "expected_output": 3, "pass_fail": False},
    ]
    out = lc45_raw_tensor_encoder(obs_rows)
    s1 = out["s1"]
    s2 = out["s2"]
    assert s1[0] == 1.0
    assert s2[0] == 0.0
    # s1 passes all probes: pass_fail_rate=1.0, bfs_agrees_rate=0.0
    # (no solver outputs the BFS reachable count). These MUST differ.
    assert s1[1] != s1[0], "bfs_agrees_rate must not equal pass_fail_rate for passing solver"
    # s2 fails all probes: both are 0.0 (correct behavior — bfs_agrees
    # doesn't accidentally match pass_fail for failing solvers either).
    assert s1[1] == 0.0
    assert s2[1] == 0.0
