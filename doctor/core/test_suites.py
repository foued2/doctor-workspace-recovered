"""Test suites — hardcoded test cases for known problems."""
from __future__ import annotations

from doctor.core.test_executor import TestCase

TEST_SUITES: dict[str, list[TestCase]] = {}

# ── two_sum ──────────────────────────────────────────────────────────────

TEST_SUITES["two_sum"] = [
    TestCase(input=([2, 7, 11, 15], 9), expected=[0, 1], label="basic"),
    TestCase(input=([3, 2, 4], 6), expected=[1, 2], label="middle"),
    TestCase(input=([3, 3], 6), expected=[0, 1], label="duplicates"),
    TestCase(input=([1, 2, 3, 4, 5], 9), expected=[3, 4], label="last_two"),
    TestCase(input=([0, 4, 3, 0], 0), expected=[0, 3], label="zeros"),
]

# ── lc42 — Trapping Rain Water ──────────────────────────────────────────

TEST_SUITES["lc42"] = [
    TestCase(input=([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), expected=6, label="classic"),
    TestCase(input=([4, 2, 0, 3, 2, 5],), expected=9, label="valley"),
    TestCase(input=([1],), expected=0, label="single"),
    TestCase(input=([1, 1],), expected=0, label="flat"),
    TestCase(input=([4, 3, 2, 1, 4],), expected=6, label="symmetric"),
    TestCase(input=([4, 2, 0, 3, 2, 5],), expected=9, label="deep_valley"),
]

# ── lc312 — Burst Balloons ──────────────────────────────────────────────

TEST_SUITES["lc312"] = [
    TestCase(input=([3, 1, 5, 8],), expected=167, label="example"),
    TestCase(input=([1],), expected=1, label="single"),
    TestCase(input=([1, 5],), expected=10, label="pair"),
    TestCase(input=([3, 1, 5],), expected=35, label="triple"),
    TestCase(input=([1, 2, 3, 4],), expected=20, label="sequential"),
]

# ── lc743 — Network Delay Time ──────────────────────────────────────────

TEST_SUITES["lc743"] = [
    TestCase(input=(3, [[2, 1, 1], [2, 3, 1], [3, 4, 1]], 2), expected=2, label="chain"),
    TestCase(input=(4, [[2, 1, 1], [2, 3, 1], [3, 4, 1]], 2), expected=3, label="long_chain"),
    TestCase(input=(1, [], 1), expected=0, label="single_node"),
]

# ── lc406 — Queue Reconstruction by Height ───────────────────────────────

TEST_SUITES["lc406"] = [
    TestCase(input=(4, [[7, 0], [4, 4], [7, 1], [5, 0], [6, 1], [5, 2]]),
             expected=[[5, 0], [7, 0], [5, 2], [6, 1], [4, 4], [7, 1]], label="example"),
    TestCase(input=(2, [[0, 0], [1, 0]]), expected=[[1, 0], [0, 0]], label="same_height"),
    TestCase(input=(1, [[4, 0]]), expected=[[4, 0]], label="single"),
]

# ── lc494 — Target Sum ──────────────────────────────────────────────────

TEST_SUITES["lc494"] = [
    TestCase(input=(5, [1, 1, 1, 1, 1], 3), expected=5, label="example"),
    TestCase(input=(1, [1], 1), expected=1, label="single_match"),
    TestCase(input=(1, [1], 2), expected=0, label="impossible"),
    TestCase(input=(2, [1, 1], 0), expected=2, label="zero_target"),
]

# ── lc875 — Koko Eating Bananas ─────────────────────────────────────────

TEST_SUITES["lc875"] = [
    TestCase(input=(4, [3, 6, 7, 11], 8), expected=4, label="example"),
    TestCase(input=(4, [30, 11, 23, 4, 20], 5), expected=30, label="large_pile"),
    TestCase(input=(1, [1000000000], 2), expected=500000000, label="huge"),
    TestCase(input=(3, [1, 1, 1], 3), expected=1, label="trivial"),
]

# ── lc134 — Gas Station ─────────────────────────────────────────────────

TEST_SUITES["lc134"] = [
    TestCase(input=(3, [1, 2, 3, 4, 5], [3, 4, 5, 1, 2]), expected=3, label="example"),
    TestCase(input=(2, [2, 3, 4], [3, 4, 3]), expected=-1, label="impossible"),
    TestCase(input=(1, [5], [4]), expected=0, label="single_ok"),
    TestCase(input=(1, [4], [5]), expected=-1, label="single_fail"),
]

# ── cf607a ───────────────────────────────────────────────────────────────

TEST_SUITES["cf607a"] = [
    TestCase(input=(5, [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]), expected=2, label="chain"),
    TestCase(input=(3, [(1, 10), (2, 5), (3, 1)]), expected=1, label="powerful_first"),
    TestCase(input=(1, [(1, 100)]), expected=0, label="single"),
]

# ── lc1029 — Two City Scheduling ────────────────────────────────────────

TEST_SUITES["lc1029"] = [
    TestCase(input=(2, [[10, 20], [30, 200], [400, 50], [30, 2]]), expected=110, label="example"),
    TestCase(input=(1, [[259, 770], [448, 54], [926, 667], [184, 139]]), expected=185, label="one_each"),
    TestCase(input=(2, [[515, 563], [451, 713], [537, 715], [122, 868], [180, 54], [211, 550]]),
             expected=351, label="six"),
]

# ── lc3 — Longest Substring Without Repeating Characters ────────────────

TEST_SUITES["lc3"] = [
    TestCase(input=("abcabcbb",), expected=3, label="abcabcbb"),
    TestCase(input=("bbbbb",), expected=1, label="bbbbb"),
    TestCase(input=("pwwkew",), expected=3, label="pwwkew"),
    TestCase(input=("",), expected=0, label="empty"),
    TestCase(input=(" ",), expected=1, label="space"),
    TestCase(input=("dvdf",), expected=3, label="dvdf"),
]

# ── arrange_numbers_divisible (referenced in tests) ──────────────────────

TEST_SUITES["arrange_numbers_divisible"] = [
    TestCase(input=([1, 2, 3, 4, 5], 3), expected=[3], label="sample"),
    TestCase(input=([1, 2, 3], 10), expected=[], label="impossible"),
    TestCase(input=([5, 6, 7], 1), expected=[5, 6, 7], label="trivial_k1"),
    TestCase(input=([10, 20, 30], 3), expected=[10, 20, 30], label="cross_boundary"),
]

# ── lc322 — Coin Change ─────────────────────────────────────────────────

TEST_SUITES["lc322"] = [
    TestCase(input=([1, 2, 5], 11), expected=3, label="example"),
    TestCase(input=([2], 3), expected=-1, label="impossible"),
    TestCase(input=([1], 0), expected=0, label="zero_amount"),
    TestCase(input=([1], 1), expected=1, label="single_coin"),
    TestCase(input=([1, 2, 5], 100), expected=20, label="large_amount"),
    TestCase(input=([1, 3, 4], 6), expected=2, label="greedy_trap"),
    TestCase(input=([1, 5, 10, 25], 41), expected=4, label="change"),
]
