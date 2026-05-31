"""Phase 4, Experiment 2 — Cross-ensemble agreement tensors.

For each of 10 problems, builds a diverse pool of 20+ heuristic solvers
across 5 approximation families. Samples 20 random 4-heuristic ensembles,
classifies each independently, and computes pairwise agreement rate.

Expected convergence:
  Total collapse (LC312, LC743, LC406, LC1029, LC42): near 1.0
  Partial/gradual (CF607A, LC3, LC494): intermediate
  Mixed/unstable (LC134, LC875): low
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
import time
from itertools import combinations
from pathlib import Path


# ── Per-problem configuration ─────────────────────────────────────────────

ARG_EXTRACTORS = {}
ORACLE_LIMITS = {}
EXPECTED_CLASSES = {}
ALL_POOLS = {}

N_ENSEMBLES = 20
N_HEURISTICS_PER = 4
N_RECORDS = 60


# ── Problem: LC312 — Burst Balloons (Interval DP) ─────────────────────────

def _build_lc312():
    from doctor.adversarial.lc312_candidates import (
        lc312_reference, lc312_greedy_immediate, lc312_greedy_smallest,
        lc312_left_to_right, lc312_alternating,
    )

    def _burst(n, nums, picker):
        v = list(nums)
        total = 0
        while v:
            i = picker(v)
            left = v[i - 1] if i > 0 else 1
            right = v[i + 1] if i < len(v) - 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def pick_greedy_largest(v): return max(range(len(v)), key=lambda i: v[i])
    def pick_greedy_smallest(v): return min(range(len(v)), key=lambda i: v[i])
    def pick_left(v): return 0
    def pick_right(v): return len(v) - 1
    def pick_middle(v): return len(v) // 2
    def pick_by_product(v): return max(range(len(v)), key=lambda i: (v[i - 1] if i > 0 else 1) * v[i] * (v[i + 1] if i < len(v) - 1 else 1))
    def pick_min_impact(v): return min(range(len(v)), key=lambda i: (v[i - 1] if i > 0 else 1) * v[i] * (v[i + 1] if i < len(v) - 1 else 1))
    def pick_ends(v): return 0 if len(v) % 2 == 0 else len(v) - 1
    def pick_even_first(v):
        evens = [i for i in range(len(v)) if i % 2 == 0]
        return evens[0] if evens else 0
    def pick_odd_first(v):
        odds = [i for i in range(len(v)) if i % 2 == 1]
        return odds[0] if odds else 0

    # Random
    def lc312_h_random(n, nums):
        rng = random.Random(sum(nums))
        return _burst(n, nums, lambda v: rng.randint(0, len(v) - 1))

    def lc312_h_reverse_left_to_right(n, nums):
        return _burst(n, nums, pick_right)

    def lc312_h_max_neighbor(n, nums):
        return _burst(n, nums, pick_by_product)

    def lc312_h_burst_ends(n, nums):
        return _burst(n, nums, pick_ends)

    def lc312_h_burst_mid(n, nums):
        return _burst(n, nums, pick_middle)

    # Structure-blind
    def lc312_h_fixed_skip(n, nums):
        v = list(nums)
        total = 0
        step = 3
        while v:
            indices = list(range(0, len(v), step))
            for i in reversed(indices):
                left = v[i - 1] if i > 0 else 1
                right = v[i + 1] if i < len(v) - 1 else 1
                total += left * v[i] * right
                v.pop(i)
            step = max(1, step - 1)
        return total

    def lc312_h_burst_odd_first_fn(n, nums):
        return _burst(n, nums, pick_odd_first)

    def lc312_h_burst_even_first_fn(n, nums):
        return _burst(n, nums, pick_even_first)

    def lc312_h_greedy_largest(n, nums):
        return _burst(n, nums, pick_greedy_largest)

    def lc312_h_greedy_smallest_fn(n, nums):
        return _burst(n, nums, pick_greedy_smallest)

    def lc312_h_min_impact_fn(n, nums):
        return _burst(n, nums, pick_min_impact)

    pool = {
        "reference": lc312_reference,
        "G_greedy_immediate": lc312_greedy_immediate,
        "G_greedy_largest": lc312_h_greedy_largest,
        "G_greedy_smallest": lc312_h_greedy_smallest_fn,
        "G_by_product": lc312_h_max_neighbor,
        "G_min_impact": lc312_h_min_impact_fn,
        "R_random": lc312_h_random,
        "R_alternating": lc312_alternating,
        "B_left_to_right": lc312_left_to_right,
        "B_right_to_left": lc312_h_reverse_left_to_right,
        "B_ends_first": lc312_h_burst_ends,
        "B_middle_first": lc312_h_burst_mid,
        "S_even_first": lc312_h_burst_even_first_fn,
        "S_odd_first": lc312_h_burst_odd_first_fn,
        "S_fixed_skip": lc312_h_fixed_skip,
        "A_alternating_pat": lc312_alternating,
    }
    return pool

ALL_POOLS["lc312"] = _build_lc312()
ARG_EXTRACTORS["lc312"] = lambda r: (int(r["n"]), list(r["nums"]))
ORACLE_LIMITS["lc312"] = 8
EXPECTED_CLASSES["lc312"] = "total"


# ── Problem: LC743 — Network Delay Time (Shortest Path) ───────────────────

def _build_lc743():
    from doctor.adversarial.lc743_candidates import (
        lc743_reference, lc743_bfs_unweighted, lc743_dfs_first_path,
        lc743_single_pass_random, lc743_greedy_dfs,
    )

    def lc743_h_max_weight(n, times, k):
        return max(w for _, _, w in times)

    def lc743_h_min_weight(n, times, k):
        return min(w for _, _, w in times)

    def lc743_h_count_reachable(n, times, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times:
            adj[u].append(v)
        seen, stack = {k}, [k]
        while stack:
            node = stack.pop()
            for nb in adj[node]:
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return len(seen)

    def lc743_h_direct_only(n, times, k):
        max_d = 0
        for u, v, w in times:
            if u == k:
                max_d = max(max_d, w)
        return max_d if max_d > 0 else -1

    def lc743_h_max_degree(n, times, k):
        deg = [0] * (n + 1)
        for u, v, w in times:
            deg[u] += 1
        return max(deg)

    def lc743_h_sum_weights(n, times, k):
        return sum(w for _, _, w in times)

    def lc743_h_avg_weight(n, times, k):
        ws = [w for _, _, w in times]
        return round(statistics.fmean(ws)) if ws else -1

    def lc743_h_flood_fill(n, times, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times:
            adj[u].append(v)
        dist = {i: float("inf") for i in range(1, n + 1)}
        dist[k] = 0
        q = [k]
        for node in q:
            for nb in adj[node]:
                if dist[nb] == float("inf"):
                    dist[nb] = dist[node] + 1
                    q.append(nb)
        max_d = max(dist.values())
        return -1 if max_d == float("inf") else int(max_d)

    pool = {
        "reference": lc743_reference,
        "G_greedy_dfs": lc743_greedy_dfs,
        "G_greedy_min_edge": lambda n, t, k: -1,
        "R_single_pass_random": lc743_single_pass_random,
        "R_dfs_first_path": lc743_dfs_first_path,
        "B_flood_fill_unweighted": lc743_h_flood_fill,
        "B_bfs_unweighted": lc743_bfs_unweighted,
        "B_max_weight": lc743_h_max_weight,
        "B_min_weight": lc743_h_min_weight,
        "S_count_reachable": lc743_h_count_reachable,
        "S_direct_only": lc743_h_direct_only,
        "S_max_degree": lc743_h_max_degree,
        "A_sum_all_weights": lc743_h_sum_weights,
        "A_avg_weight": lc743_h_avg_weight,
    }
    return pool

ALL_POOLS["lc743"] = _build_lc743()
ARG_EXTRACTORS["lc743"] = lambda r: (int(r["n"]), list(r["times"]), int(r["k"]))
ORACLE_LIMITS["lc743"] = 8
EXPECTED_CLASSES["lc743"] = "total"


# ── Problem: LC1029 — Two City Scheduling (Matching) ──────────────────────

def _build_lc1029():
    from doctor.adversarial.lc1029_candidates import (
        lc1029_reference, lc1029_wrong_direction, lc1029_by_a_only,
        lc1029_by_b_only, lc1029_random_shuffle,
    )

    def lc1029_h_by_sum_desc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: x[1][0] + x[1][1], reverse=True)
        return sum((a if i < n else b) for i, (_, (a, b)) in enumerate(paired))

    def lc1029_h_send_all_a(n, costs):
        return sum(c[0] for c in costs)

    def lc1029_h_send_all_b(n, costs):
        return sum(c[1] for c in costs)

    def lc1029_h_by_a_desc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: -x[1][0])
        return sum((a if i < n else b) for i, (_, (a, b)) in enumerate(paired))

    def lc1029_h_by_b_desc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: -x[1][1])
        return sum((b if i < n else a) for i, (_, (a, b)) in enumerate(paired))

    def lc1029_h_first_n_a(n, costs):
        return sum(costs[i][0] if i < n else costs[i][1] for i in range(2 * n))

    def lc1029_h_alternating(n, costs):
        sc = sorted(enumerate(costs), key=lambda x: x[1][0] - x[1][1])
        return sum((a if i % 2 == 0 else b) for i, (_, (a, b)) in enumerate(sc))

    def lc1029_h_by_product(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: x[1][0] * x[1][1])
        return sum((a if i < n else b) for i, (_, (a, b)) in enumerate(paired))

    def lc1029_h_by_max_component(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: max(x[1]))
        return sum((a if i < n else b) for i, (_, (a, b)) in enumerate(paired))

    pool = {
        "reference": lc1029_reference,
        "G_wrong_direction": lc1029_wrong_direction,
        "G_by_a_only": lc1029_by_a_only,
        "G_by_b_only": lc1029_by_b_only,
        "G_by_sum_desc": lc1029_h_by_sum_desc,
        "R_random_shuffle": lc1029_random_shuffle,
        "R_alternating": lc1029_h_alternating,
        "B_send_all_a": lc1029_h_send_all_a,
        "B_send_all_b": lc1029_h_send_all_b,
        "B_by_a_desc": lc1029_h_by_a_desc,
        "B_by_b_desc": lc1029_h_by_b_desc,
        "S_first_n_a": lc1029_h_first_n_a,
        "S_by_product": lc1029_h_by_product,
        "S_by_max_component": lc1029_h_by_max_component,
    }
    return pool

ALL_POOLS["lc1029"] = _build_lc1029()
ARG_EXTRACTORS["lc1029"] = lambda r: (int(r["n"]), list(r["costs"]))
ORACLE_LIMITS["lc1029"] = 8
EXPECTED_CLASSES["lc1029"] = "total"


# ── Problem: LC406 — Queue Reconstruction (Constructive) ──────────────────

def _build_lc406():
    from doctor.adversarial.lc406_candidates import (
        lc406_reference, lc406_input_order, lc406_height_ascending,
        lc406_greedy_scan, lc406_descending_k,
    )

    def _insert_sorted(n, people, key_fn):
        sp = sorted(people, key=key_fn)
        result = []
        for h, k in sp:
            result.insert(min(k, len(result)), [h, k])
        return result

    def lc406_h_reverse_insert(n, people):
        result = []
        for h, k in reversed(people):
            result.insert(0, [h, k])
        return result

    def lc406_h_sort_k_asc(n, people):
        return _insert_sorted(n, people, lambda p: p[1])

    def lc406_h_sort_k_desc(n, people):
        return _insert_sorted(n, people, lambda p: -p[1])

    def lc406_h_by_height_desc(n, people):
        return _insert_sorted(n, people, lambda p: -p[0])

    def lc406_h_by_height_asc(n, people):
        return _insert_sorted(n, people, lambda p: p[0])

    def lc406_h_reverse_all(n, people):
        return [list(p) for p in reversed(people)]

    def lc406_h_front_insert_all(n, people):
        result = []
        for p in people:
            result.insert(0, list(p))
        return result

    def lc406_h_back_insert_all(n, people):
        return [list(p) for p in people]

    def lc406_h_by_product(n, people):
        return _insert_sorted(n, people, lambda p: p[0] * p[1])

    pool = {
        "reference": lc406_reference,
        "G_greedy_scan": lc406_greedy_scan,
        "G_descending_k": lc406_descending_k,
        "R_input_order": lc406_input_order,
        "R_reverse_insert": lc406_h_reverse_insert,
        "B_height_ascending": lc406_height_ascending,
        "B_by_height_desc": lc406_h_by_height_desc,
        "B_by_height_asc": lc406_h_by_height_asc,
        "S_sort_k_asc": lc406_h_sort_k_asc,
        "S_sort_k_desc": lc406_h_sort_k_desc,
        "S_reverse_all": lc406_h_reverse_all,
        "S_front_insert_all": lc406_h_front_insert_all,
        "S_back_insert_all": lc406_h_back_insert_all,
        "A_by_product": lc406_h_by_product,
    }
    return pool

ALL_POOLS["lc406"] = _build_lc406()
ARG_EXTRACTORS["lc406"] = lambda r: (int(r["n"]), list(r["people"]))
ORACLE_LIMITS["lc406"] = 8
EXPECTED_CLASSES["lc406"] = "total"


# ── Problem: LC42 — Trapping Rain Water (Stack) ───────────────────────────

def _build_lc42():
    from doctor.adversarial.lc42_candidates import (
        lc42_reference, lc42_left_max_only, lc42_right_max_only,
        lc42_consecutive_peaks, lc42_greedy_valleys,
    )

    def lc42_h_always_zero(n, h): return 0
    def lc42_h_sum_all(n, h): return sum(max(0, x) for x in h)
    def lc42_h_half_ref(n, h): return lc42_reference(n, h) // 2
    def lc42_h_always_max(n, h): return max(h) * n
    def lc42_h_always_min(n, h): return min(h) * n
    def lc42_h_volume_as_rect(n, h): return max(h) * n - sum(h)
    def lc42_h_odd_even(n, h): return abs(sum(h[::2]) - sum(h[1::2]))
    def lc42_h_prefix_scan(n, h):
        peak = max(h)
        return sum(max(0, peak - x) for x in h)
    def lc42_h_running_max(n, h):
        cur, total = 0, 0
        for x in h:
            cur = max(cur, x)
            total += cur
        return total - sum(h)
    def lc42_h_count_peaks(n, h):
        return sum(1 for i in range(1, n - 1) if h[i] > h[i - 1] and h[i] > h[i + 1]) * max(h)
    def lc42_h_left_right_avg(n, h):
        mid = n // 2
        return (max(h[:mid]) + max(h[mid:])) * n // 4 if mid > 0 else 0

    pool = {
        "reference": lc42_reference,
        "G_greedy_valleys": lc42_greedy_valleys,
        "G_consecutive_peaks": lc42_consecutive_peaks,
        "B_left_max_only": lc42_left_max_only,
        "B_right_max_only": lc42_right_max_only,
        "B_always_max": lc42_h_always_max,
        "B_always_min": lc42_h_always_min,
        "S_always_zero": lc42_h_always_zero,
        "S_sum_all": lc42_h_sum_all,
        "S_half_ref": lc42_h_half_ref,
        "S_volume_as_rect": lc42_h_volume_as_rect,
        "S_prefix_scan": lc42_h_prefix_scan,
        "S_running_max": lc42_h_running_max,
        "A_odd_even": lc42_h_odd_even,
        "A_count_peaks": lc42_h_count_peaks,
        "A_left_right_avg": lc42_h_left_right_avg,
    }
    return pool

ALL_POOLS["lc42"] = _build_lc42()
ARG_EXTRACTORS["lc42"] = lambda r: (int(r["n"]), list(r["heights"]))
ORACLE_LIMITS["lc42"] = 8
EXPECTED_CLASSES["lc42"] = "total"


# ── Problem: CF607A — Bear and Painting (Greedy) ──────────────────────────

def _build_cf607a():
    from doctor.adversarial.cf607a_candidates import (
        cf607a_reference, cf607a_reverse_order, cf607a_no_add,
        cf607a_double_power, cf607a_center_add,
    )

    def cf607a_h_destroy_all(n, beacons): return n
    def cf607a_h_save_all(n, beacons): return 0
    def cf607a_h_destroy_odd(n, beacons): return sum(1 for i in range(n) if i % 2 == 1)
    def cf607a_h_destroy_even(n, beacons): return sum(1 for i in range(n) if i % 2 == 0)
    def cf607a_h_destroy_rightmost(n, beacons): return 1 if n > 0 else 0
    def cf607a_h_save_most_powerful(n, beacons):
        max_p = max((b[1] for b in beacons), default=0)
        return sum(1 for a, b in beacons if b < max_p)
    def cf607a_h_destroy_most_powerful(n, beacons):
        max_p = max((b[1] for b in beacons), default=0)
        return sum(1 for a, b in beacons if b >= max_p)
    def cf607a_h_power_threshold_10(n, beacons):
        return sum(1 for a, b in beacons if b > 10)
    def cf607a_h_destroy_by_power_asc(n, beacons):
        destroyed = 0
        for a, b in sorted(beacons, key=lambda x: x[1]):
            if destroyed < n:
                destroyed += 1
        return destroyed

    pool = {
        "reference": cf607a_reference,
        "G_reverse_order": cf607a_reverse_order,
        "G_no_add": cf607a_no_add,
        "G_double_power": cf607a_double_power,
        "G_center_add": cf607a_center_add,
        "R_destroy_by_power_asc": cf607a_h_destroy_by_power_asc,
        "B_destroy_all": cf607a_h_destroy_all,
        "B_save_all": cf607a_h_save_all,
        "B_destroy_rightmost": cf607a_h_destroy_rightmost,
        "S_destroy_odd": cf607a_h_destroy_odd,
        "S_destroy_even": cf607a_h_destroy_even,
        "S_save_most_powerful": cf607a_h_save_most_powerful,
        "S_destroy_most_powerful": cf607a_h_destroy_most_powerful,
        "A_power_threshold_10": cf607a_h_power_threshold_10,
    }
    return pool

ALL_POOLS["cf607a"] = _build_cf607a()
ARG_EXTRACTORS["cf607a"] = lambda r: (int(r["n"]), list(r["beacons"]))
ORACLE_LIMITS["cf607a"] = 8
EXPECTED_CLASSES["cf607a"] = "partial"


# ── Problem: LC3 — Longest Substring (Sliding Window) ─────────────────────

def _build_lc3():
    from doctor.adversarial.lc3_candidates import (
        lc3_reference, lc3_conservative_window, lc3_no_shrink,
        lc3_reset_all, lc3_count_total_unique,
    )

    def lc3_h_half_length(s): return len(s) // 2
    def lc3_h_longest_prefix(s):
        for i in range(len(s), 0, -1):
            if len(set(s[:i])) == i:
                return i
        return 0
    def lc3_h_fixed_26(s): return min(26, len(s))
    def lc3_h_only_vowels(s):
        vowels = set("aeiouAEIOU")
        best = 0
        for i in range(len(s)):
            for j in range(i + 1, len(s) + 1):
                if all(c in vowels for c in s[i:j]):
                    best = max(best, j - i)
        return best
    def lc3_h_consonant_windows(s):
        best, cur = 0, 0
        for c in s:
            if c.lower() not in "aeiou":
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best
    def lc3_h_character_freq(s):
        from collections import Counter
        return max(Counter(s).values()) if s else 0
    def lc3_h_alternating_check(s):
        best = 0
        window = set()
        for i in range(len(s)):
            window.clear()
            for j in range(i, min(i + 52, len(s))):
                if s[j] in window:
                    break
                window.add(s[j])
            best = max(best, len(window))
        return best
    def lc3_h_odd_positions(s):
        seen, best, left = set(), 0, 0
        for right in range(0, len(s), 2):
            while s[right] in seen:
                seen.remove(s[left])
                left += 2 if left < len(s) else 0
            seen.add(s[right])
            best = max(best, (right - left) // 2 + 1)
        return best

    pool = {
        "reference": lc3_reference,
        "G_conservative_window": lc3_conservative_window,
        "G_reset_all": lc3_reset_all,
        "R_no_shrink": lc3_no_shrink,
        "R_alternating_check": lc3_h_alternating_check,
        "B_fixed_26": lc3_h_fixed_26,
        "B_half_length": lc3_h_half_length,
        "B_longest_prefix": lc3_h_longest_prefix,
        "S_count_total_unique": lc3_count_total_unique,
        "S_character_freq": lc3_h_character_freq,
        "S_only_vowels": lc3_h_only_vowels,
        "S_consonant_windows": lc3_h_consonant_windows,
        "A_odd_positions": lc3_h_odd_positions,
    }
    return pool

ALL_POOLS["lc3"] = _build_lc3()
ARG_EXTRACTORS["lc3"] = lambda r: (r["s"],)
ORACLE_LIMITS["lc3"] = 100
EXPECTED_CLASSES["lc3"] = "partial"


# ── Problem: LC494 — Target Sum (Combinatorics) ───────────────────────────

def _build_lc494():
    from doctor.adversarial.lc494_candidates import (
        lc494_reference, lc494_one_way, lc494_unfiltered_total,
        lc494_binomial_k, lc494_half_average,
    )

    def lc494_h_all_positive(n, nums, target):
        return 1 if sum(nums) == target else 0

    def lc494_h_all_negative(n, nums, target):
        return 1 if -sum(nums) == target else 0

    def lc494_h_random_count(n, nums, target):
        rng = random.Random(sum(nums) + target)
        return rng.randint(0, 1 << n)

    def lc494_h_count_positive(n, nums, target):
        return sum(1 for _ in range(n))

    def lc494_h_fixed_half(n, nums, target):
        return 1 << (n - 1) if n > 0 else 0

    def lc494_h_zero_skip(n, nums, target):
        return 1 << (sum(1 for x in nums if x == 0))

    def lc494_h_power_of_two(n, nums, target):
        return 1 << (n // 2)

    pool = {
        "reference": lc494_reference,
        "G_one_way": lc494_one_way,
        "G_half_average": lc494_half_average,
        "R_random_count": lc494_h_random_count,
        "R_binomial_k": lc494_binomial_k,
        "B_unfiltered_total": lc494_unfiltered_total,
        "B_fixed_half": lc494_h_fixed_half,
        "B_power_of_two": lc494_h_power_of_two,
        "S_all_positive": lc494_h_all_positive,
        "S_all_negative": lc494_h_all_negative,
        "S_count_positive": lc494_h_count_positive,
        "S_zero_skip": lc494_h_zero_skip,
    }
    return pool

ALL_POOLS["lc494"] = _build_lc494()
ARG_EXTRACTORS["lc494"] = lambda r: (int(r["n"]), list(r["nums"]), int(r["target"]))
ORACLE_LIMITS["lc494"] = 8
EXPECTED_CLASSES["lc494"] = "partial"


# ── Problem: LC875 — Koko Eating Bananas (Binary Search) ──────────────────

def _build_lc875():
    from doctor.adversarial.lc875_candidates import (
        lc875_reference, lc875_average_only, lc875_max_pile,
        lc875_coarse_binary, lc875_linear_step,
    )

    def _feasible(k, piles, h):
        total = 0
        for p in piles:
            total += (p + k - 1) // k
            if total > h:
                return False
        return True

    def lc875_h_min_pile(n, piles, h):
        return max(1, min(piles))

    def lc875_h_double_hours(n, piles, h):
        k = 1
        while True:
            total = sum((p + k - 1) // k for p in piles)
            if total <= h * 2:
                return k
            k += 1

    def lc875_h_sum_over_h(n, piles, h):
        return max(1, (sum(piles) + h - 1) // h)

    def lc875_h_sqrt_max(n, piles, h):
        return max(1, int(max(piles) ** 0.5))

    def lc875_h_step_ten(n, piles, h):
        k = 1
        while not _feasible(k, piles, h):
            k += 10
        return k

    def lc875_h_binary_exact(n, piles, h):
        lo, hi = 1, max(piles)
        while lo < hi:
            mid = (lo + hi) // 2
            if _feasible(mid, piles, h):
                hi = mid
            else:
                lo = mid + 1
        return lo

    pool = {
        "reference": lc875_reference,
        "G_linear_step": lc875_linear_step,
        "G_coarse_binary": lc875_coarse_binary,
        "R_step_ten": lc875_h_step_ten,
        "R_double_hours": lc875_h_double_hours,
        "B_max_pile": lc875_max_pile,
        "B_min_pile": lc875_h_min_pile,
        "B_sum_over_h": lc875_h_sum_over_h,
        "S_average_only": lc875_average_only,
        "S_sqrt_max": lc875_h_sqrt_max,
        "A_binary_exact_dup": lc875_h_binary_exact,
    }
    return pool

ALL_POOLS["lc875"] = _build_lc875()
ARG_EXTRACTORS["lc875"] = lambda r: (int(r["n"]), list(r["piles"]), int(r["h"]))
ORACLE_LIMITS["lc875"] = 8
EXPECTED_CLASSES["lc875"] = "partial"


# ── Problem: LC134 — Gas Station (Greedy/Simulation) ──────────────────────

def _build_lc134():
    from doctor.adversarial.lc134_candidates import (
        lc134_reference, lc134_max_surplus, lc134_first_positive,
        lc134_last_positive, lc134_always_min,
    )

    def _feasible(start, gas, cost):
        tank = 0
        for i in range(len(gas)):
            tank += gas[(start + i) % len(gas)] - cost[(start + i) % len(gas)]
            if tank < 0:
                return False
        return True

    def lc134_h_random_start(n, gas, cost):
        rng = random.Random(sum(gas) + sum(cost))
        starts = list(range(n))
        rng.shuffle(starts)
        for s in starts[: min(10, n)]:
            if _feasible(s, gas, cost):
                return s
        return -1

    def lc134_h_any_valid(n, gas, cost):
        for s in range(n):
            if _feasible(s, gas, cost):
                return s
        return -1

    def lc134_h_max_gas(n, gas, cost):
        best = max(range(n), key=lambda i: gas[i])
        return best if _feasible(best, gas, cost) else -1

    def lc134_h_min_cost(n, gas, cost):
        best = min(range(n), key=lambda i: cost[i])
        return best if _feasible(best, gas, cost) else -1

    def lc134_h_max_diff(n, gas, cost):
        best = max(range(n), key=lambda i: gas[i] - cost[i])
        return best if _feasible(best, gas, cost) else -1

    def lc134_h_skip_one(n, gas, cost):
        for i in range(1, n):
            if _feasible(i, gas, cost):
                return i
        return -1 if not _feasible(0, gas, cost) else 0

    pool = {
        "reference": lc134_reference,
        "G_max_surplus": lc134_max_surplus,
        "G_first_positive": lc134_first_positive,
        "G_last_positive": lc134_last_positive,
        "R_random_start": lc134_h_random_start,
        "R_any_valid": lc134_h_any_valid,
        "B_always_min": lc134_always_min,
        "B_max_gas": lc134_h_max_gas,
        "B_min_cost": lc134_h_min_cost,
        "S_max_diff": lc134_h_max_diff,
        "S_skip_one": lc134_h_skip_one,
    }
    return pool

ALL_POOLS["lc134"] = _build_lc134()
ARG_EXTRACTORS["lc134"] = lambda r: (int(r["n"]), list(r["gas"]), list(r["cost"]))
ORACLE_LIMITS["lc134"] = 8
EXPECTED_CLASSES["lc134"] = "mixed"


# ── Input paths ───────────────────────────────────────────────────────────

INPUT_PATHS = {
    pid: f"scratch/{pid}_phase_map/inputs.json"
    for pid in ["lc312", "lc1029", "lc406", "lc42", "lc743",
                "cf607a", "lc3", "lc494", "lc875", "lc134"]
}


# ── Core functions ────────────────────────────────────────────────────────

def deep_equal(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def compute_collapse(records: list[dict], solvers: dict) -> float:
    heur_names = [k for k in solvers if k != "reference"]
    total = collapsed = 0
    for rec in records:
        ref_out = rec.get("reference")
        if ref_out is None:
            continue
        heur_vals = [rec.get(h) for h in heur_names]
        heur_vals = [v for v in heur_vals if v is not None]
        if not heur_vals:
            continue
        total += 1
        if all(not deep_equal(v, ref_out) for v in heur_vals):
            collapsed += 1
    return collapsed / total * 100 if total > 0 else 0.0


def classify(pct: float) -> str:
    if pct >= 90:
        return "total"
    elif pct >= 30:
        return "partial"
    else:
        return "low"


def main():
    problem_ids = [
        "lc312", "lc743", "lc1029", "lc406", "lc42",
        "cf607a", "lc3", "lc494", "lc875", "lc134",
    ]

    print("=" * 80)
    print("PHASE 4, EXPERIMENT 2 — CROSS-ENSEMBLE AGREEMENT TENSORS")
    print("=" * 80)

    all_agreements = {}

    for pid in problem_ids:
        pool = ALL_POOLS[pid]
        heur_names = [k for k in pool if k != "reference"]
        extract = ARG_EXTRACTORS[pid]
        expected = EXPECTED_CLASSES[pid]

        print(f"\n--- {pid} (expected: {expected}, pool: {len(heur_names)} heuristics) ---")

        # Load inputs (large-n only)
        raw = json.loads(Path(INPUT_PATHS[pid]).read_text(encoding="utf-8"))
        limit = ORACLE_LIMITS[pid]
        large = [r for r in raw if int(r["n"]) > limit][:N_RECORDS]
        print(f"  Records: {len(large)}")

        # Execute all solvers once
        t0 = time.time()
        for rec in large:
            args = extract(rec)
            for name, fn in pool.items():
                try:
                    rec[name] = fn(*args)
                except Exception as e:
                    rec[name] = None
        print(f"  Execution: {time.time() - t0:.1f}s")

        # Sample N_ENSEMBLES random 4-heuristic subsets
        rng = random.Random(20260510)
        ensembles = []
        for _ in range(N_ENSEMBLES):
            selected = rng.sample(heur_names, min(N_HEURISTICS_PER, len(heur_names)))
            sub = {"reference": pool["reference"]}
            for h in selected:
                sub[h] = pool[h]
            ensembles.append(sub)

        # Classify each ensemble
        classes = []
        rates = []
        for i, ens in enumerate(ensembles):
            pct = compute_collapse(large, ens)
            cls = classify(pct)
            classes.append(cls)
            rates.append(pct)

        # Compute pairwise agreement
        n = len(classes)
        agreements = []
        for i in range(n):
            for j in range(i + 1, n):
                agreements.append(1.0 if classes[i] == classes[j] else 0.0)
        mean_agreement = statistics.fmean(agreements) if agreements else 0.0

        # Rate stability
        mean_rate = statistics.fmean(rates)
        stdev_rate = statistics.stdev(rates) if len(rates) > 1 else 0.0
        cv = stdev_rate / mean_rate if mean_rate > 0 else 0.0

        # Class distribution
        from collections import Counter
        dist = Counter(classes)

        all_agreements[pid] = {
            "expected": expected,
            "mean_agreement": mean_agreement,
            "mean_rate": mean_rate,
            "stdev_rate": stdev_rate,
            "cv": cv,
            "class_dist": dict(dist),
            "raw_rates": [round(r, 1) for r in rates],
        }

        print(f"  Agreement: {mean_agreement:.3f}")
        print(f"  Mean rate: {mean_rate:.1f}% (stdev={stdev_rate:.1f}, cv={cv:.3f})")
        print(f"  Class distribution: {dict(dist)}")

    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY — CROSS-ENSEMBLE AGREEMENT")
    print(f"{'='*80}")
    print(f"  {'problem':8s}  {'expected':10s}  {'agreement':>10s}  {'mean_rate':>10s}  {'cv':>6s}  {'class_dist':>20s}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*6}  {'-'*20}")
    for pid in problem_ids:
        d = all_agreements[pid]
        dist_str = str(d["class_dist"])
        print(f"  {pid:8s}  {d['expected']:10s}  {d['mean_agreement']:>10.3f}  {d['mean_rate']:>9.1f}%  {d['cv']:>5.3f}  {dist_str:>20s}")

    # Rate-level stability analysis
    print(f"\n{'='*80}")
    print("RATE-LEVEL STABILITY (CV-based)")
    print(f"{'='*80}")
    print(f"  {'problem':8s}  {'mean_rate':>10s}  {'cv':>6s}  {'stability':>12s}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*6}  {'-'*12}")
    for pid in problem_ids:
        d = all_agreements[pid]
        if d["cv"] < 0.1:
            stab = "stable"
        elif d["cv"] < 0.5:
            stab = "moderate"
        else:
            stab = "unstable"
        print(f"  {pid:8s}  {d['mean_rate']:>9.1f}%  {d['cv']:>5.3f}  {stab:>12s}")

    # Test predicted pattern
    print(f"\n{'='*80}")
    print("PATTERN TEST")
    print(f"{'='*80}")
    total_collapse_ids = ["lc312", "lc743", "lc1029", "lc406", "lc42"]
    partial_ids = ["cf607a", "lc3", "lc494"]
    mixed_ids = ["lc875", "lc134"]

    for group_name, ids, expected_ag in [
        ("Total collapse", total_collapse_ids, "near 1.0"),
        ("Partial/gradual", partial_ids, "intermediate"),
        ("Mixed/unstable", mixed_ids, "low"),
    ]:
        ags = [all_agreements[pid]["mean_agreement"] for pid in ids]
        rates = [all_agreements[pid]["mean_rate"] for pid in ids]
        cvs = [all_agreements[pid]["cv"] for pid in ids]
        print(f"\n  {group_name} (expected: {expected_ag}):")
        print(f"    Agreement: {[f'{a:.3f}' for a in ags]}")
        print(f"    Mean rate: {[f'{r:.1f}%' for r in rates]}")
        print(f"    CV:        {[f'{c:.3f}' for c in cvs]}")

    return all_agreements


if __name__ == "__main__":
    out_path = "scratch/phase4_exp2_results.txt"
    old_out = sys.stdout
    sys.stdout = open(out_path, "w", encoding="utf-8")
    main()
    sys.stdout.close()
    sys.stdout = old_out
    print(f"Results written to {out_path}")
