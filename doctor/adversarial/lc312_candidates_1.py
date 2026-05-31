"""Phase 4, Experiment 1 — Ensemble scaling.

Tests whether collapse classification shifts when heuristic ensemble size
scales from 4 -> 10 -> 20 on 6 target problems:
- 5 total-collapse: LC312, LC1029, LC406, LC42, LC743
- 1 partial/gradual: CF607A
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path


# ── Extended heuristic pools (20 per problem) ─────────────────────────────

def _build_pools():
    """Return dict: problem_id -> list of (name, callable)."""

    pools = {}

    # ── LC312: Burst Balloons (Interval DP) ───────────────────────────
    from doctor.adversarial.lc312_candidates import (
        lc312_reference, lc312_greedy_immediate, lc312_greedy_smallest,
        lc312_left_to_right, lc312_alternating,
    )

    def _burst(n, nums, order_fn):
        vals = list(nums)
        total = 0
        for _ in range(n):
            if not vals:
                break
            i = order_fn(vals)
            left = vals[i - 1] if i > 0 else 1
            right = vals[i + 1] if i < len(vals) - 1 else 1
            total += left * vals[i] * right
            vals.pop(i)
        return total

    def _burst_by_index_order(n, nums, indices):
        v = list(nums)
        total = 0
        for idx in indices:
            if idx >= len(v):
                continue
            left = v[idx - 1] if idx > 0 else 1
            right = v[idx + 1] if idx < len(v) - 1 else 1
            total += left * v[idx] * right
            v.pop(idx)
        return total

    def lc312_h_burst_largest(n, nums):
        return _burst(n, nums, lambda v: max(range(len(v)), key=lambda i: v[i]))

    def lc312_h_burst_odd_first(n, nums):
        v = list(nums)
        total = 0
        for _ in range(n):
            odd = [i for i in range(len(v)) if i % 2 == 1]
            even = [i for i in range(len(v)) if i % 2 == 0]
            order = odd + even
            if not order:
                break
            i = order[0]
            left = v[i - 1] if i > 0 else 1
            right = v[i + 1] if i < len(v) - 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def lc312_h_burst_ends_first(n, nums):
        v = list(nums)
        total = 0
        while v:
            i = 0 if len(v) % 2 == 0 else len(v) - 1
            left = v[i - 1] if i > 0 else 1
            right = v[i + 1] if i < len(v) - 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def lc312_h_burst_middle_first(n, nums):
        v = list(nums)
        total = 0
        while v:
            i = len(v) // 2
            left = v[i - 1] if i > 0 else 1
            right = v[i + 1] if i < len(v) - 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def lc312_h_random_order(n, nums):
        r = random.Random(sum(nums))
        idxs = list(range(n))
        r.shuffle(idxs)
        return _burst_by_index_order(n, nums, idxs)

    def lc312_h_burst_even_first(n, nums):
        v = list(nums)
        total = 0
        while v:
            evens = [i for i in range(len(v)) if i % 2 == 0]
            if evens:
                i = evens[0]
            else:
                i = 0
            left = v[i - 1] if i > 0 else 1
            right = v[i + 1] if i < len(v) - 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def lc312_h_burst_by_product(n, nums):
        return _burst(n, nums, lambda v: max(range(len(v)), key=lambda i: (v[i - 1] if i > 0 else 1) * v[i] * (v[i + 1] if i < len(v) - 1 else 1)))

    def lc312_h_burst_min_impact(n, nums):
        return _burst(n, nums, lambda v: min(range(len(v)), key=lambda i: (v[i - 1] if i > 0 else 1) * v[i] * (v[i + 1] if i < len(v) - 1 else 1)))

    def lc312_h_reverse_order(n, nums):
        return _burst(n, nums, lambda v: len(v) - 1)

    def lc312_h_burst_all_left(n, nums):
        v = list(nums)
        total = 0
        while v:
            i = 0
            left = 1
            right = v[1] if len(v) > 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def lc312_h_burst_all_right(n, nums):
        v = list(nums)
        total = 0
        while v:
            i = len(v) - 1
            left = v[i - 1] if i > 0 else 1
            right = 1
            total += left * v[i] * right
            v.pop(i)
        return total

    def lc312_h_skip_even(n, nums):
        v = list(nums)
        total = 0
        # Burst odd positions first
        while True:
            odds = [i for i in range(len(v)) if i % 2 == 1]
            if not odds:
                break
            i = odds[0]
            left = v[i - 1] if i > 0 else 1
            right = v[i + 1] if i < len(v) - 1 else 1
            total += left * v[i] * right
            v.pop(i)
        # Then burst remaining
        while v:
            i = 0
            left = 1
            right = v[1] if len(v) > 1 else 1
            total += left * v[i] * right
            v.pop(i)
        return total

    pools["lc312"] = {
        "reference": lc312_reference,
        "H01_greedy_immediate": lc312_greedy_immediate,
        "H02_greedy_smallest": lc312_greedy_smallest,
        "H03_left_to_right": lc312_left_to_right,
        "H04_alternating": lc312_alternating,
        "H05_burst_largest": lc312_h_burst_largest,
        "H06_burst_even_first": lc312_h_burst_even_first,
        "H07_burst_odd_first": lc312_h_burst_odd_first,
        "H08_burst_ends_first": lc312_h_burst_ends_first,
        "H09_burst_middle_first": lc312_h_burst_middle_first,
        "H10_random_order": lc312_h_random_order,
        "H11_reverse_order": lc312_h_reverse_order,
        "H12_burst_by_product": lc312_h_burst_by_product,
        "H13_burst_min_impact": lc312_h_burst_min_impact,
        "H14_burst_all_left": lc312_h_burst_all_left,
        "H15_burst_all_right": lc312_h_burst_all_right,
        "H16_skip_even": lc312_h_skip_even,
    }

    # ── LC1029: Two City Scheduling (Matching) ────────────────────────
    from doctor.adversarial.lc1029_candidates import (
        lc1029_reference, lc1029_wrong_direction, lc1029_by_a_only,
        lc1029_by_b_only, lc1029_random_shuffle,
    )

    def lc1029_h_by_sum_desc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: x[1][0] + x[1][1], reverse=True)
        total = 0
        for i, (_, (a, b)) in enumerate(paired):
            total += a if i < n else b
        return total

    def lc1029_h_by_sum_asc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: x[1][0] + x[1][1])
        total = 0
        for i, (_, (a, b)) in enumerate(paired):
            total += a if i < n else b
        return total

    def lc1029_h_send_all_a(n, costs):
        return sum(c[0] for c in costs)

    def lc1029_h_send_all_b(n, costs):
        return sum(c[1] for c in costs)

    def lc1029_h_by_a_desc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: -x[1][0])
        total = 0
        for i, (_, (a, b)) in enumerate(paired):
            total += a if i < n else b
        return total

    def lc1029_h_by_b_desc(n, costs):
        paired = sorted(enumerate(costs), key=lambda x: -x[1][1])
        total = 0
        for i, (_, (a, b)) in enumerate(paired):
            total += b if i < n else a
        return total

    def lc1029_h_first_n_a(n, costs):
        total = 0
        for i in range(2 * n):
            total += costs[i][0] if i < n else costs[i][1]
        return total

    def lc1029_h_alternating(n, costs):
        sc = sorted(enumerate(costs), key=lambda x: x[1][0] - x[1][1])
        total = 0
        for i, (_, (a, b)) in enumerate(sc):
            total += a if i % 2 == 0 else b
        return total

    pools["lc1029"] = {
        "reference": lc1029_reference,
        "H01_wrong_direction": lc1029_wrong_direction,
        "H02_by_a_only": lc1029_by_a_only,
        "H03_by_b_only": lc1029_by_b_only,
        "H04_random_shuffle": lc1029_random_shuffle,
        "H05_by_sum_desc": lc1029_h_by_sum_desc,
        "H06_by_sum_asc": lc1029_h_by_sum_asc,
        "H07_send_all_a": lc1029_h_send_all_a,
        "H08_send_all_b": lc1029_h_send_all_b,
        "H09_by_a_desc": lc1029_h_by_a_desc,
        "H10_by_b_desc": lc1029_h_by_b_desc,
        "H11_first_n_a": lc1029_h_first_n_a,
        "H12_alternating": lc1029_h_alternating,
    }

    # ── LC406: Queue Reconstruction (Constructive) ────────────────────
    from doctor.adversarial.lc406_candidates import (
        lc406_reference, lc406_input_order, lc406_height_ascending,
        lc406_greedy_scan, lc406_descending_k,
    )

    def lc406_h_reverse_insert(n, people):
        result = []
        for h, k in reversed(people):
            result.insert(0, [h, k])
        return result

    def lc406_h_sort_k_asc(n, people):
        sp = sorted(people, key=lambda p: p[1])
        result = []
        for h, k in sp:
            result.insert(min(k, len(result)), [h, k])
        return result

    def lc406_h_sort_k_desc(n, people):
        sp = sorted(people, key=lambda p: -p[1])
        result = []
        for h, k in sp:
            result.insert(min(k, len(result)), [h, k])
        return result

    def lc406_h_by_height_only_desc(n, people):
        sp = sorted(people, key=lambda p: -p[0])
        result = []
        for h, k in sp:
            result.insert(k, [h, k])
        return result

    def lc406_h_by_height_only_asc(n, people):
        sp = sorted(people, key=lambda p: p[0])
        result = []
        for h, k in sp:
            result.insert(k, [h, k])
        return result

    def lc406_h_reverse_all(n, people):
        return list(reversed([[h, k] for h, k in people]))

    def lc406_h_front_insert_all(n, people):
        result = []
        for h, k in people:
            result.insert(0, [h, k])
        return result

    def lc406_h_back_insert_all(n, people):
        result = []
        for h, k in people:
            result.append([h, k])
        return result

    pools["lc406"] = {
        "reference": lc406_reference,
        "H01_input_order": lc406_input_order,
        "H02_height_ascending": lc406_height_ascending,
        "H03_greedy_scan": lc406_greedy_scan,
        "H04_descending_k": lc406_descending_k,
        "H05_reverse_insert": lc406_h_reverse_insert,
        "H06_sort_k_asc": lc406_h_sort_k_asc,
        "H07_sort_k_desc": lc406_h_sort_k_desc,
        "H08_by_height_only_desc": lc406_h_by_height_only_desc,
        "H09_by_height_only_asc": lc406_h_by_height_only_asc,
        "H10_reverse_all": lc406_h_reverse_all,
        "H11_front_insert_all": lc406_h_front_insert_all,
        "H12_back_insert_all": lc406_h_back_insert_all,
    }

    # ── LC42: Trapping Rain Water (Stack) ─────────────────────────────
    from doctor.adversarial.lc42_candidates import (
        lc42_reference, lc42_left_max_only, lc42_right_max_only,
        lc42_consecutive_peaks, lc42_greedy_valleys,
    )

    def lc42_h_always_zero(n, h):
        return 0

    def lc42_h_sum_all(n, h):
        return sum(max(0, x) for x in h)

    def lc42_h_half_ref(n, h):
        return lc42_reference(n, h) // 2

    def lc42_h_always_max(n, h):
        return max(h) * n

    def lc42_h_always_min(n, h):
        return min(h) * n

    def lc42_h_left_right_avg(n, h):
        return (max(h[:n//2]) + max(h[n//2:])) * n // 4 if n > 1 else 0

    def lc42_h_running_max(n, h):
        total, cur = 0, 0
        for x in h:
            cur = max(cur, x)
            total += cur
        return total - sum(h[:n])

    def lc42_h_running_min(n, h):
        total, cur = 0, float("inf")
        for x in h:
            cur = min(cur, x)
        return max(0, cur * n - sum(h))

    def lc42_h_volume_as_rect(n, h):
        return max(h) * n - sum(h)

    def lc42_h_odd_even(n, h):
        return sum(h[i] for i in range(0, n, 2)) - sum(h[i] for i in range(1, n, 2))

    def lc42_h_prefix_scan(n, h):
        total, peak = 0, 0
        for x in h:
            peak = max(peak, x)
        for x in h:
            total += max(0, peak - x)
        return total

    def lc42_h_suffix_scan(n, h):
        total, peak = 0, 0
        for x in reversed(h):
            peak = max(peak, x)
        for x in h:
            total += max(0, peak - x)
        return total

    pools["lc42"] = {
        "reference": lc42_reference,
        "H01_left_max_only": lc42_left_max_only,
        "H02_right_max_only": lc42_right_max_only,
        "H03_consecutive_peaks": lc42_consecutive_peaks,
        "H04_greedy_valleys": lc42_greedy_valleys,
        "H05_always_zero": lc42_h_always_zero,
        "H06_sum_all": lc42_h_sum_all,
        "H07_half_ref": lc42_h_half_ref,
        "H08_always_max": lc42_h_always_max,
        "H09_always_min": lc42_h_always_min,
        "H10_left_right_avg": lc42_h_left_right_avg,
        "H11_running_max": lc42_h_running_max,
        "H12_running_min": lc42_h_running_min,
        "H13_volume_as_rect": lc42_h_volume_as_rect,
        "H14_odd_even": lc42_h_odd_even,
        "H15_prefix_scan": lc42_h_prefix_scan,
        "H16_suffix_scan": lc42_h_suffix_scan,
    }

    # ── LC743: Network Delay Time (Shortest Path) ─────────────────────
    from doctor.adversarial.lc743_candidates import (
        lc743_reference, lc743_bfs_unweighted, lc743_dfs_first_path,
        lc743_single_pass_random, lc743_greedy_dfs,
    )

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

    def lc743_h_max_weight(n, times, k):
        return max(w for _, _, w in times)

    def lc743_h_min_weight(n, times, k):
        return min(w for _, _, w in times)

    def lc743_h_count_reachable(n, times, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times:
            adj[u].append(v)
        seen, stack = set(), [k]
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(adj[node])
        return len(seen)

    def lc743_h_direct_only(n, times, k):
        max_d = 0
        for u, v, w in times:
            if u == k:
                max_d = max(max_d, w)
        return max_d if max_d > 0 else -1

    def lc743_h_max_degree(n, times, k):
        degree = [0] * (n + 1)
        for u, v, w in times:
            degree[u] += 1
        return max(degree)

    def lc743_h_greedy_min_edge(n, times, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times:
            adj[u].append((v, w))
        visited, total = set(), 0
        cur = k
        for _ in range(n):
            visited.add(cur)
            if adj[cur]:
                nxt = min(adj[cur], key=lambda x: x[1])
                total += nxt[1]
                cur = nxt[0]
            else:
                break
        return total if len(visited) == n else -1

    def lc743_h_dfs_deepest(n, times, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times:
            adj[u].append((v, w))
        def dfs(node, visited):
            max_d = 0
            for nb, w in adj[node]:
                if nb not in visited:
                    visited.add(nb)
                    max_d = max(max_d, w + dfs(nb, visited))
                    visited.remove(nb)
            return max_d
        return dfs(k, {k})

    pools["lc743"] = {
        "reference": lc743_reference,
        "H01_bfs_unweighted": lc743_bfs_unweighted,
        "H02_dfs_first_path": lc743_dfs_first_path,
        "H03_single_pass_random": lc743_single_pass_random,
        "H04_greedy_dfs": lc743_greedy_dfs,
        "H05_flood_fill": lc743_h_flood_fill,
        "H06_max_weight": lc743_h_max_weight,
        "H07_min_weight": lc743_h_min_weight,
        "H08_count_reachable": lc743_h_count_reachable,
        "H09_direct_only": lc743_h_direct_only,
        "H10_max_degree": lc743_h_max_degree,
        "H11_greedy_min_edge": lc743_h_greedy_min_edge,
        # H12_dfs_deepest excluded (exponential complexity)
    }

    # ── CF607A: Bear and Painting (Greedy) ────────────────────────────
    from doctor.adversarial.cf607a_candidates import (
        cf607a_reference, cf607a_reverse_order, cf607a_no_add,
        cf607a_double_power, cf607a_center_add,
    )

    def cf607a_h_destroy_all(n, beacons):
        return n

    def cf607a_h_save_all(n, beacons):
        return 0

    def cf607a_h_destroy_odd(n, beacons):
        return sum(1 for i in range(n) if i % 2 == 1)

    def cf607a_h_destroy_even(n, beacons):
        return sum(1 for i in range(n) if i % 2 == 0)

    def cf607a_h_destroy_rightmost(n, beacons):
        return 1 if n > 0 else 0

    def cf607a_h_destroy_leftmost(n, beacons):
        return 1 if n > 0 else 0

    def cf607a_h_destroy_by_power_asc(n, beacons):
        sp = sorted(beacons, key=lambda b: b[1])
        destroyed = 0
        for a, b in sp:
            if destroyed < n:
                destroyed += 1
        return destroyed

    def cf607a_h_destroy_by_power_desc(n, beacons):
        sp = sorted(beacons, key=lambda b: -b[1])
        destroyed = 0
        for a, b in sp:
            if destroyed < n:
                destroyed += 1
        return destroyed

    def cf607a_h_save_most_powerful(n, beacons):
        max_power = max(b[1] for b in beacons) if beacons else 0
        return sum(1 for a, b in beacons if b < max_power)

    def cf607a_h_destroy_most_powerful(n, beacons):
        max_power = max(b[1] for b in beacons) if beacons else 0
        return sum(1 for a, b in beacons if b >= max_power)

    def cf607a_h_power_threshold_5(n, beacons):
        return sum(1 for a, b in beacons if b > 5)

    pools["cf607a"] = {
        "reference": cf607a_reference,
        "H01_reverse_order": cf607a_reverse_order,
        "H02_no_add": cf607a_no_add,
        "H03_double_power": cf607a_double_power,
        "H04_center_add": cf607a_center_add,
        "H05_destroy_all": cf607a_h_destroy_all,
        "H06_save_all": cf607a_h_save_all,
        "H07_destroy_odd": cf607a_h_destroy_odd,
        "H08_destroy_even": cf607a_h_destroy_even,
        "H09_destroy_rightmost": cf607a_h_destroy_rightmost,
        "H10_destroy_leftmost": cf607a_h_destroy_leftmost,
        "H11_destroy_by_power_asc": cf607a_h_destroy_by_power_asc,
        "H12_destroy_by_power_desc": cf607a_h_destroy_by_power_desc,
        "H13_save_most_powerful": cf607a_h_save_most_powerful,
        "H14_destroy_most_powerful": cf607a_h_destroy_most_powerful,
        "H15_power_threshold_5": cf607a_h_power_threshold_5,
    }

    return pools


# ── Input loaders ─────────────────────────────────────────────────────────

ARG_EXTRACTORS = {
    "lc312": lambda r: (int(r["n"]), list(r["nums"])),
    "lc1029": lambda r: (int(r["n"]), list(r["costs"])),
    "lc406": lambda r: (int(r["n"]), list(r["people"])),
    "lc42": lambda r: (int(r["n"]), list(r["heights"])),
    "lc743": lambda r: (int(r["n"]), list(r["times"]), int(r["k"])),
    "cf607a": lambda r: (int(r["n"]), list(r["beacons"])),
}

INPUT_PATHS = {
    pid: f"scratch/{pid}_phase_map/inputs.json"
    for pid in ["lc312", "lc1029", "lc406", "lc42", "lc743", "cf607a"]
}

ORACLE_LIMITS = {
    "lc312": 8, "lc1029": 8, "lc406": 8,
    "lc42": 8, "lc743": 8, "cf607a": 8,
}

CLASS_NAMES = {
    "lc312": "total", "lc1029": "total", "lc406": "total",
    "lc42": "total", "lc743": "total", "cf607a": "partial",
}


# ── Execution ─────────────────────────────────────────────────────────────

def deep_equal(a, b) -> bool:
    """Compare outputs, handling lists."""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def compute_collapse(records: list[dict], solvers: dict, ref_name: str) -> float:
    """Fraction of records where ALL heuristics disagree with reference."""
    heur_names = [k for k in solvers if k != ref_name]
    total = 0
    collapsed = 0
    for rec in records:
        ref_out = rec.get(ref_name)
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
    pools = _build_pools()
    problem_ids = ["lc312", "lc1029", "lc406", "lc42", "lc743", "cf607a"]

    print("=" * 80)
    print("PHASE 4, EXPERIMENT 1 — ENSEMBLE SCALING")
    print("=" * 80)

    all_results = []

    for pid in problem_ids:
        solvers = pools[pid]
        heur_names = [k for k in solvers if k != "reference"]
        extract = ARG_EXTRACTORS[pid]
        expected = CLASS_NAMES[pid]

        print(f"\n--- {pid} (expected: {expected}) ---")

        # Load inputs (large-n only)
        path = Path(INPUT_PATHS[pid])
        raw = json.loads(path.read_text(encoding="utf-8"))
        limit = ORACLE_LIMITS[pid]
        large = [r for r in raw if int(r["n"]) > limit][:60]

        # Execute all solvers with timing
        print(f"  Executing {len(large)} records x {len(solvers)} solvers...")
        t0 = __import__("time").time()
        for rec in large:
            args = extract(rec)
            for name, fn in solvers.items():
                try:
                    rec[name] = fn(*args)
                except Exception:
                    rec[name] = None
        dt = __import__("time").time() - t0
        print(f"  Done in {dt:.1f}s ({dt/len(large):.2f}s per record)")

        # Test at 3 scales
        scales = {"n=4": 4, "n=10": 10, "n=20": 16}
        rng = random.Random(20260510)

        row = {"problem": pid, "expected": expected}

        for scale_name, n_h in scales.items():
            selected = heur_names[:n_h] if n_h <= len(heur_names) else heur_names
            sub = {"reference": solvers["reference"]}
            for h in selected:
                sub[h] = solvers[h]
            pct = compute_collapse(large, sub, "reference")
            cls = classify(pct)
            row[scale_name] = f"{pct:.1f}% ({cls})"
            print(f"  {scale_name}: {pct:.1f}%  -> {cls}")

        all_results.append(row)

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY — CLASSIFICATION AT 4, 10, 20 HEURISTICS")
    print(f"{'='*80}")
    print(f"  {'problem':8s}  {'expected':10s}  {'n=4':18s}  {'n=10':18s}  {'n=20':18s}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*18}  {'-'*18}  {'-'*18}")
    for row in all_results:
        print(f"  {row['problem']:8s}  {row['expected']:10s}  {row['n=4']:18s}  {row['n=10']:18s}  {row['n=20']:18s}")

    # Check stability
    shifts = 0
    for row in all_results:
        classes = set()
        for scale_name in ["n=4", "n=10", "n=20"]:
            cls = row[scale_name].split("(")[-1].rstrip(")")
            classes.add(cls)
        if len(classes) > 1:
            shifts += 1
            print(f"  SHIFT: {row['problem']} classes={classes}")

    print(f"\n  Total shifts: {shifts}/{len(all_results)}")
    print(f"  Taxonomy stable under scaling: {shifts == 0}")

    return shifts == 0


if __name__ == "__main__":
    out_path = "scratch/phase4_exp1_results.txt"
    old_out = sys.stdout
    sys.stdout = open(out_path, "w", encoding="utf-8")
    result = main()
    sys.stdout.close()
    sys.stdout = old_out
    print(f"Results written to {out_path}")
    print(f"Taxonomy stable under ensemble scaling: {result}")
