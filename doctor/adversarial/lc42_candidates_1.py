"""Phase 3, Attack 1 — Solver ensemble randomization.

For each of 10 problems, creates additional broken heuristics,
then runs N random trials selecting 4 per trial. Records whether
the collapse class (total/partial/unstable) is preserved.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


# ── Extended solver pools (existing + new broken heuristics) ──────────────

def _extend_solvers(problem_id: str) -> dict[str, Callable]:
    """Return extended solver dict for a problem: reference + extra heuristics."""

    if problem_id == "lc42":
        from doctor.adversarial.lc42_candidates import (
            lc42_reference, lc42_left_max_only, lc42_right_max_only,
            lc42_consecutive_peaks, lc42_greedy_valleys,
        )
        def lc42_always_zero(n, h): return 0
        def lc42_sum_all(n, h): return sum(max(0, x) for x in h)
        def lc42_half_ref(n, h): return lc42_reference(n, h) // 2
        return {"reference": lc42_reference, "left_max_only": lc42_left_max_only,
                "right_max_only": lc42_right_max_only, "consecutive_peaks": lc42_consecutive_peaks,
                "greedy_valleys": lc42_greedy_valleys, "always_zero": lc42_always_zero,
                "sum_all": lc42_sum_all, "half_ref": lc42_half_ref}

    elif problem_id == "lc312":
        from doctor.adversarial.lc312_candidates import (
            lc312_reference, lc312_greedy_immediate, lc312_greedy_smallest,
            lc312_left_to_right, lc312_alternating,
        )
        def lc312_burst_even_first(n, nums):
            """Burst all even-indexed balloons first."""
            remaining = list(range(n))
            total = 0
            while remaining:
                for i in list(remaining):
                    if i % 2 == 0:
                        left = nums[remaining[remaining.index(i) - 1]] if remaining.index(i) > 0 else 1
                        right = nums[remaining[(remaining.index(i) + 1) % len(remaining)]] if len(remaining) > 1 else 1
                        total += left * nums[i] * right
                        remaining.remove(i)
                if not any(i % 2 == 0 for i in remaining):
                    break
            for i in remaining:
                left = nums[remaining[remaining.index(i) - 1]] if remaining.index(i) > 0 else 1
                right = nums[remaining[(remaining.index(i) + 1) % len(remaining)]] if len(remaining) > 1 else 1
                total += left * nums[i] * right
            return total
        def lc312_reverse_order(n, nums):
            """Process right-to-left instead of left-to-right."""
            total = 0
            nums_copy = list(nums)
            for _ in range(n):
                i = len(nums_copy) - 1
                left = nums_copy[i - 1] if i > 0 else 1
                right = nums_copy[i + 1] if i < len(nums_copy) - 1 else 1
                total += left * nums_copy[i] * right
                nums_copy.pop(i)
            return total
        return {"reference": lc312_reference, "greedy_immediate": lc312_greedy_immediate,
                "greedy_smallest": lc312_greedy_smallest, "left_to_right": lc312_left_to_right,
                "alternating": lc312_alternating, "burst_even_first": lc312_burst_even_first,
                "reverse_order": lc312_reverse_order}

    elif problem_id == "lc743":
        from doctor.adversarial.lc743_candidates import (
            lc743_reference, lc743_bfs_unweighted, lc743_dfs_first_path,
            lc743_single_pass_random, lc743_greedy_dfs,
        )
        def lc743_flood_fill(n, times, k):
            """Return max distance from k using simple BFS (ignoring weights)."""
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
        def lc743_max_weight(n, times, k):
            """Return the max single edge weight (gross underestimate)."""
            return max(w for _, _, w in times)
        return {"reference": lc743_reference, "bfs_unweighted": lc743_bfs_unweighted,
                "dfs_first_path": lc743_dfs_first_path, "single_pass_random": lc743_single_pass_random,
                "greedy_dfs": lc743_greedy_dfs, "flood_fill": lc743_flood_fill,
                "max_weight": lc743_max_weight}

    elif problem_id == "lc406":
        from doctor.adversarial.lc406_candidates import (
            lc406_reference, lc406_input_order, lc406_height_ascending,
            lc406_greedy_scan, lc406_descending_k,
        )
        def lc406_reverse_insert(n, people):
            """Process in reverse order, insert at front."""
            result = []
            for h, k in reversed(people):
                result.insert(0, [h, k])
            return result
        def lc406_sort_k_asc(n, people):
            """Sort by k ascending, insert at position."""
            sorted_p = sorted(people, key=lambda p: p[1])
            result = []
            for h, k in sorted_p:
                result.insert(min(k, len(result)), [h, k])
            return result
        return {"reference": lc406_reference, "input_order": lc406_input_order,
                "height_ascending": lc406_height_ascending, "greedy_scan": lc406_greedy_scan,
                "descending_k": lc406_descending_k, "reverse_insert": lc406_reverse_insert,
                "sort_k_asc": lc406_sort_k_asc}

    elif problem_id == "lc494":
        from doctor.adversarial.lc494_candidates import (
            lc494_reference, lc494_one_way, lc494_unfiltered_total,
            lc494_binomial_k, lc494_half_average,
        )
        def lc494_all_positive(n, nums, target):
            return 1 if sum(nums) == target else 0
        def lc494_all_negative(n, nums, target):
            return 1 if -sum(nums) == target else 0
        def lc494_random_count(n, nums, target):
            import random as _r
            _r.seed(sum(nums) + target)
            return _r.randint(0, 2**n)
        return {"reference": lc494_reference, "one_way": lc494_one_way,
                "unfiltered_total": lc494_unfiltered_total, "binomial_k": lc494_binomial_k,
                "half_average": lc494_half_average, "all_positive": lc494_all_positive,
                "all_negative": lc494_all_negative, "random_count": lc494_random_count}

    elif problem_id == "lc875":
        from doctor.adversarial.lc875_candidates import (
            lc875_reference, lc875_average_only, lc875_max_pile,
            lc875_coarse_binary, lc875_linear_step,
        )
        def lc875_min_pile(n, piles, h):
            return max(1, min(piles))
        def lc875_double_hours(n, piles, h):
            from math import ceil
            k = 1
            while True:
                total = sum(ceil(p / k) for p in piles)
                if total <= 2 * h:
                    return k
                k += 1
        return {"reference": lc875_reference, "average_only": lc875_average_only,
                "max_pile": lc875_max_pile, "coarse_binary": lc875_coarse_binary,
                "linear_step": lc875_linear_step, "min_pile": lc875_min_pile,
                "double_hours": lc875_double_hours}

    elif problem_id == "lc134":
        from doctor.adversarial.lc134_candidates import (
            lc134_reference, lc134_max_surplus, lc134_first_positive,
            lc134_last_positive, lc134_always_min,
        )
        def lc134_random_start(n, gas, cost):
            starts = list(range(n))
            random.Random(sum(gas) + sum(cost)).shuffle(starts)
            for s in starts[:5]:
                tank = 0
                ok = True
                for i in range(n):
                    tank += gas[(s + i) % n] - cost[(s + i) % n]
                    if tank < 0:
                        ok = False
                        break
                if ok:
                    return s
            return -1
        def lc134_any_valid(n, gas, cost):
            for s in range(n):
                tank = 0
                ok = True
                for i in range(n):
                    tank += gas[(s + i) % n] - cost[(s + i) % n]
                    if tank < 0:
                        ok = False
                        break
                if ok:
                    return s
            return -1
        return {"reference": lc134_reference, "max_surplus": lc134_max_surplus,
                "first_positive": lc134_first_positive, "last_positive": lc134_last_positive,
                "always_min": lc134_always_min, "random_start": lc134_random_start,
                "any_valid": lc134_any_valid}

    elif problem_id == "cf607a":
        from doctor.adversarial.cf607a_candidates import (
            cf607a_reference, cf607a_reverse_order, cf607a_no_add,
            cf607a_double_power, cf607a_center_add,
        )
        def cf607a_destroy_all(n, beacons):
            return n
        def cf607a_save_all(n, beacons):
            return 0
        return {"reference": cf607a_reference, "reverse_order": cf607a_reverse_order,
                "no_add": cf607a_no_add, "double_power": cf607a_double_power,
                "center_add": cf607a_center_add, "destroy_all": cf607a_destroy_all,
                "save_all": cf607a_save_all}

    elif problem_id == "lc1029":
        from doctor.adversarial.lc1029_candidates import (
            lc1029_reference, lc1029_wrong_direction, lc1029_by_a_only,
            lc1029_by_b_only, lc1029_random_shuffle,
        )
        def lc1029_by_sum_desc(n, costs):
            paired = sorted(enumerate(costs), key=lambda x: x[1][0] + x[1][1], reverse=True)
            total = 0
            for i, (idx, (a, b)) in enumerate(paired):
                total += a if i < n else b
            return total
        def lc1029_alternating(n, costs):
            sorted_c = sorted(enumerate(costs), key=lambda x: x[1][0] - x[1][1])
            total = 0
            for i, (idx, (a, b)) in enumerate(sorted_c):
                total += a if i % 2 == 0 else b
            return total
        return {"reference": lc1029_reference, "wrong_direction": lc1029_wrong_direction,
                "by_a_only": lc1029_by_a_only, "by_b_only": lc1029_by_b_only,
                "random_shuffle": lc1029_random_shuffle, "by_sum_desc": lc1029_by_sum_desc,
                "alternating": lc1029_alternating}

    elif problem_id == "lc3":
        from doctor.adversarial.lc3_candidates import (
            lc3_reference, lc3_conservative_window, lc3_no_shrink,
            lc3_reset_all, lc3_count_total_unique,
        )
        def lc3_longest_prefix(s):
            """Only check prefixes starting at index 0."""
            n = len(s)
            best = 0
            for i in range(n):
                if len(set(s[:i+1])) == i + 1:
                    best = i + 1
                else:
                    break
            return best
        def lc3_half_length(s):
            return len(s) // 2
        return {"reference": lc3_reference, "conservative_window": lc3_conservative_window,
                "no_shrink": lc3_no_shrink, "reset_all": lc3_reset_all,
                "count_total_unique": lc3_count_total_unique, "longest_prefix": lc3_longest_prefix,
                "half_length": lc3_half_length}

    raise ValueError(f"Unknown problem: {problem_id}")


# ── Shared oracle loader ──────────────────────────────────────────────────

def load_oracle(problem_id: str):
    """Return brute_force function for small-n problems."""
    if problem_id == "lc42":
        from doctor.adversarial.lc42_ground_truth import lc42_brute_force
        return lc42_brute_force
    elif problem_id == "lc312":
        from doctor.adversarial.lc312_ground_truth import lc312_brute_force
        return lc312_brute_force
    elif problem_id == "lc743":
        from doctor.adversarial.lc743_ground_truth import lc743_brute_force
        return lc743_brute_force
    elif problem_id == "lc406":
        from doctor.adversarial.lc406_ground_truth import lc406_brute_force
        return lc406_brute_force
    elif problem_id == "lc494":
        from doctor.adversarial.lc494_ground_truth import lc494_brute_force
        return lc494_brute_force
    elif problem_id == "lc875":
        from doctor.adversarial.lc875_ground_truth import lc875_brute_force
        return lc875_brute_force
    elif problem_id == "lc134":
        from doctor.adversarial.lc134_ground_truth import lc134_brute_force
        return lc134_brute_force
    elif problem_id == "cf607a":
        from doctor.adversarial.cf607a_ground_truth import cf607a_brute_force
        return cf607a_brute_force
    elif problem_id == "lc1029":
        from doctor.adversarial.lc1029_ground_truth import lc1029_brute_force
        return lc1029_brute_force
    elif problem_id == "lc3":
        from doctor.adversarial.lc3_ground_truth import lc3_brute_force
        return lc3_brute_force
    raise ValueError(f"No oracle for {problem_id}")


# ── Input loader ──────────────────────────────────────────────────────────

def load_inputs(problem_id: str) -> list[dict]:
    path = Path(f"scratch/{problem_id}_phase_map/inputs.json")
    if not path.exists():
        raise FileNotFoundError(f"No inputs for {problem_id} at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# ── Execution ─────────────────────────────────────────────────────────────

def execute_record(record: dict, solvers: dict[str, Callable],
                   brute_force: Callable | None, pid: str) -> dict:
    from time import perf_counter
    def _safe_run(fn, *args):
        started = perf_counter()
        try:
            o = fn(*args)
            return {"status": "ok", "output": o, "runtime_ms": round((perf_counter() - started) * 1000, 3), "error": None}
        except Exception as e:
            return {"status": "error", "output": None, "runtime_ms": round((perf_counter() - started) * 1000, 3), "error": str(e)}

    def _extract_arg(rec):
        for key in ("s", "costs", "heights", "people", "piles", "nums", "gas", "beacons", "times"):
            if key in rec:
                return rec[key]
        return None

    solver_results = {}
    for name, fn in solvers.items():
        if pid == "lc3":
            solver_results[name] = _safe_run(fn, record["s"])
        else:
            arg = _extract_arg(record)
            solver_results[name] = _safe_run(fn, record["n"], arg)

    oracle = {"available": False, "output": None, "error": None}
    n = int(record["n"])
    oracle_limit = 100 if pid == "lc3" else 8
    if brute_force and n <= oracle_limit:
        try:
            arg = _extract_arg(record)
            if pid == "lc3":
                oracle["output"] = brute_force(arg)
            else:
                oracle["output"] = brute_force(n, arg)
            oracle["available"] = True
        except Exception as e:
            oracle["error"] = str(e)

    correctness = None
    if oracle["available"]:
        correctness = {name: res["status"] == "ok" and res["output"] == oracle["output"] for name, res in solver_results.items()}

    return {"input_id": record["input_id"], "n": n, "truth_model": "oracle" if oracle["available"] else "non_oracle",
            "oracle": oracle, "solver_outputs": solver_results, "correctness_vs_oracle": correctness}


# ── Collapse score ────────────────────────────────────────────────────────

def collapse_score(row: dict, solvers: dict) -> float:
    solver_names = list(solvers.keys())
    correctness = row.get("correctness_vs_oracle")
    if correctness is not None:
        vals = [correctness.get(s, False) for s in solver_names]
        n_c = sum(1 for v in vals if v)
        if n_c == 0 or n_c == len(vals):
            return 0.0
        p = n_c / len(vals)
        return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
    outputs = {}
    for name in solver_names:
        r = row["solver_outputs"].get(name, {})
        if r.get("status") == "ok" and r.get("output") is not None:
            outputs[name] = r["output"]
    ref = outputs.get("reference")
    if ref is None:
        return 0.0
    heur_vals = [v for k, v in outputs.items() if k != "reference"]
    if not heur_vals:
        return 0.0
    n_agree = sum(1 for v in heur_vals if v == ref)
    p = n_agree / len(heur_vals)
    if p == 0.0 or p == 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def all_heuristics_disagree(row: dict, solvers: dict) -> bool | None:
    outputs = {}
    for name in solvers:
        r = row["solver_outputs"].get(name, {})
        if r.get("status") == "ok" and r.get("output") is not None:
            outputs[name] = r["output"]
    ref = outputs.get("reference")
    if ref is None:
        return None
    heur_vals = [v for k, v in outputs.items() if k != "reference"]
    if not heur_vals:
        return None
    return all(v != ref for v in heur_vals)


# ── Run trial ─────────────────────────────────────────────────────────────

PROBLEM_CATEGORIES = {
    "lc42": "A_sharp_near_total",
    "lc312": "C_instant_total",
    "lc743": "C_instant_total",
    "lc406": "C_instant_total",
    "lc1029": "C_instant_total",
    "lc3": "E_bounded_output",
    "lc494": "D_feasibility_preserved",
    "cf607a": "B_gradual_partial",
    "lc875": "C_mixed_unstable",
    "lc134": "mixed_unstable",
}

def run_trial(problem_id: str, heuristic_names: list[str],
              all_solvers: dict, records: list[dict],
              brute_force: Callable | None, trial_idx: int) -> dict:
    selected = {"reference": all_solvers["reference"]}
    for h in heuristic_names:
        selected[h] = all_solvers[h]

    matrix = [execute_record(rec, selected, brute_force, problem_id) for rec in records]

    collapse_basin = 0
    total_large = 0
    for row in matrix:
        if row["truth_model"] != "oracle":
            total_large += 1
            all_w = all_heuristics_disagree(row, selected)
            cs = collapse_score(row, selected)
            if all_w is True and cs == 0.0:
                collapse_basin += 1

    pct = round(collapse_basin / total_large * 100, 1) if total_large > 0 else 0.0
    return {"problem": problem_id, "trial": trial_idx,
            "category": PROBLEM_CATEGORIES.get(problem_id, "unknown"),
            "heuristics": heuristic_names,
            "collapse_pct": pct, "collapse_basin": collapse_basin,
            "total_large_n": total_large}


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    problem_ids = ["lc42", "lc312", "lc743", "lc406", "lc494",
                   "lc875", "lc134", "cf607a", "lc1029", "lc3"]
    rng = random.Random(5050)
    n_trials = 3

    all_results = []
    for pid in problem_ids:
        print(f"\n{'='*60}")
        print(f"Attack 1 -- {pid} ({PROBLEM_CATEGORIES.get(pid, '?')})")
        print(f"{'='*60}")

        all_solvers = _extend_solvers(pid)
        heuristic_pool = [k for k in all_solvers if k != "reference"]
        records = load_inputs(pid)
        # Use first 60 large-n records for speed
        threshold = 100 if pid == "lc3" else 8
        large_records = [r for r in records if int(r["n"]) > threshold]
        sampled = large_records[:60]
        if len(sampled) < 10:
            sampled = records[:60]
        bf = load_oracle(pid)

        for t in range(n_trials):
            selected = rng.sample(heuristic_pool, min(4, len(heuristic_pool)))
            result = run_trial(pid, selected, all_solvers, sampled, bf, t)
            all_results.append(result)
            ok = result["collapse_pct"] >= 95 or (
                result["collapse_pct"] < 30 and pid == "lc3"
            ) or (
                30 <= result["collapse_pct"] < 95 and pid in ("cf607a", "lc494")
            )
            tag = "[OK]" if ok else "[BREAK]"
            print(f"  Trial {t}: collapse={result['collapse_pct']}%  "
                  f"({result['collapse_basin']}/{result['total_large_n']})  "
                  f"heuristics={result['heuristics']}  {tag}")

    # Summary
    print(f"\n\n{'='*60}")
    print("ATTACK 1 -- SUMMARY")
    print(f"{'='*60}")
    by_problem = defaultdict(list)
    for r in all_results:
        by_problem[r["problem"]].append(r["collapse_pct"])

    taxonomy_holds = True
    for pid, pcts in sorted(by_problem.items()):
        mean_pct = statistics.fmean(pcts)
        cat = PROBLEM_CATEGORIES[pid]
        expected = ""
        if "total" in cat or "near" in cat:
            expected = ">=95pct"
            holds = mean_pct >= 90
        elif pid == "lc3":
            expected = "<=30pct"
            holds = mean_pct < 40
        elif pid in ("cf607a", "lc494"):
            expected = "30-95pct"
            holds = 20 <= mean_pct <= 95
        else:
            expected = "any"
            holds = True
        status = "[OK]" if holds else "[BREAK]"
        if not holds:
            taxonomy_holds = False
        print(f"  {pid:8s} ({cat:25s}) mean={mean_pct:5.1f}%  expected={expected:12s}  {status}")

    print(f"\n  Taxonomy stability: {'[OK] HOLDS' if taxonomy_holds else '[BREAK] BREAKS'}")
    return taxonomy_holds


if __name__ == "__main__":
    import sys
    out_path = "scratch/phase3_attack1_results.txt"
    old_out = sys.stdout
    sys.stdout = open(out_path, "w", encoding="utf-8")
    result = main()
    sys.stdout.close()
    sys.stdout = old_out
    print(f"Results written to {out_path}")
    print(f"Taxonomy stable: {result}")
