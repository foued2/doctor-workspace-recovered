#!/usr/bin/env python3
"""
Doctor probe runner: Smallest Unique Subarray.

This is a prepared-envelope measurement only. Doctor does not autonomously
understand the problem — the envelope was constructed manually from a
user-provided problem statement.

Usage:
    py -3 runners/run_doctor_probe_smallest_unique_subarray.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from doctor.adversarial.smallest_unique_subarray_candidates import (
    reference_oracle_wrapper,
    wrong_adjacent_pair_only,
    wrong_distinct_cover_window,
    wrong_set_count_no_order,
    wrong_singleton_unique_only,
)
from doctor.adversarial.smallest_unique_subarray_oracle import (
    DEFAULT_MAX_N,
    brute_force_smallest_unique_subarray,
)

OUTPUT_PATH = ROOT / "data" / "smallest_unique_subarray_doctor_probe.json"
FINDINGS_PATH = ROOT / "findings" / "FINDINGS_SMALLEST_UNIQUE_SUBARRAY.md"

# ── Test cases ──────────────────────────────────────────────────────────────

PROBE_CASES: list[dict] = [
    # Examples from problem statement
    {"nums": [3, 3, 3], "expected": 3, "tag": "example_all_same"},
    {"nums": [2, 1, 2, 3, 3], "expected": 1, "tag": "example_singleton_unique"},
    {"nums": [1, 1, 2, 2, 1], "expected": 2, "tag": "example_pair_unique"},
    # All same
    {"nums": [5, 5, 5, 5], "expected": 4, "tag": "all_same_four"},
    {"nums": [7, 7], "expected": 2, "tag": "all_same_two"},
    {"nums": [9], "expected": 1, "tag": "single_element"},
    # Singleton unique exists
    {"nums": [2, 1, 2, 3, 3], "expected": 1, "tag": "singleton_exists"},
    {"nums": [4, 4, 4, 5], "expected": 1, "tag": "singleton_at_end"},
    {"nums": [6, 7, 7, 7], "expected": 1, "tag": "singleton_at_start"},
    # No singleton unique but pair unique
    {"nums": [1, 1, 2, 2, 1], "expected": 2, "tag": "pair_unique_length2"},
    {"nums": [1, 2, 1, 2], "expected": 2, "tag": "alternating_pair_unique"},
    {"nums": [3, 3, 1, 1, 3, 3], "expected": 2, "tag": "pair_unique_middle"},
    # Longer unique subarrays
    {"nums": [1, 2, 3, 1, 2, 3], "expected": 2, "tag": "repeated_triplet"},
    {"nums": [1, 1, 2, 2, 3, 3], "expected": 2, "tag": "pair_unique_pairs"},
    # Repeated periodic
    {"nums": [1, 2, 1, 2, 1, 2], "expected": 4, "tag": "periodic_alternating"},
    {"nums": [1, 1, 1, 2, 2, 2], "expected": 2, "tag": "periodic_blocks"},
    # Subarrays with same values but different order
    {"nums": [1, 2, 2, 1], "expected": 2, "tag": "order_matters"},
    {"nums": [1, 2, 1, 2, 2, 1], "expected": 2, "tag": "order_matters_longer"},
    # Palindrome/reversal traps
    {"nums": [1, 2, 3, 2, 1, 2, 3, 2, 1], "expected": 3, "tag": "palindrome_pattern"},
    # Edge: all distinct values
    {"nums": [1, 2, 3, 4, 5], "expected": 1, "tag": "all_distinct"},
    # Edge: two elements
    {"nums": [1, 1], "expected": 2, "tag": "two_same"},
    {"nums": [1, 2], "expected": 1, "tag": "two_distinct"},
    # Random small arrays
    {"nums": [1, 2, 3, 1, 2], "expected": 1, "tag": "random_small_1"},
    {"nums": [2, 2, 1, 2, 2], "expected": 1, "tag": "random_small_2"},
]

# Exhaustive tiny: all arrays of length n with values in {1, 2, 3}
EXHAUSTIVE_MAX_N = 5
EXHAUSTIVE_MAX_VAL = 3

CANDIDATES = {
    "reference_oracle_wrapper": reference_oracle_wrapper,
    "wrong_singleton_unique_only": wrong_singleton_unique_only,
    "wrong_distinct_cover_window": wrong_distinct_cover_window,
    "wrong_adjacent_pair_only": wrong_adjacent_pair_only,
    "wrong_set_count_no_order": wrong_set_count_no_order,
}


def generate_exhaustive_cases() -> list[dict]:
    """Generate all arrays of length 1..EXHAUSTIVE_MAX_N over {1..EXHAUSTIVE_MAX_VAL}."""
    cases = []
    for n in range(1, EXHAUSTIVE_MAX_N + 1):
        stack = [(0, [])]
        while stack:
            idx, arr = stack.pop()
            if idx == n:
                expected = brute_force_smallest_unique_subarray(arr)
                cases.append({
                    "nums": list(arr),
                    "expected": expected,
                    "tag": f"exhaustive_n{n}_v{EXHAUSTIVE_MAX_VAL}",
                })
            else:
                for v in range(1, EXHAUSTIVE_MAX_VAL + 1):
                    stack.append((idx + 1, arr + [v]))
    return cases


def run_probes() -> dict:
    all_cases = list(PROBE_CASES)
    exhaustive = generate_exhaustive_cases()
    all_cases.extend(exhaustive)

    results = []
    candidate_stats: dict[str, dict] = {name: {"pass": 0, "fail": 0, "total": 0}
                                        for name in CANDIDATES}

    for case in all_cases:
        nums = case["nums"]
        expected = case["expected"]
        tag = case["tag"]

        row = {
            "nums": nums,
            "expected": expected,
            "tag": tag,
            "candidate_results": {},
        }

        for name, func in CANDIDATES.items():
            try:
                actual = func(nums)
                passed = actual == expected
            except Exception as e:
                actual = None
                passed = False

            row["candidate_results"][name] = {
                "actual": actual,
                "passed": passed,
            }
            candidate_stats[name]["total"] += 1
            if passed:
                candidate_stats[name]["pass"] += 1
            else:
                candidate_stats[name]["fail"] += 1

        results.append(row)

    n_total = len(all_cases)
    n_exhaustive = len(exhaustive)
    n_probe = len(PROBE_CASES)
    n_ok = sum(1 for r in results if r["candidate_results"]["reference_oracle_wrapper"]["passed"])

    # Provenance: every row has exactly one oracle ground-truth source
    provenance_count = n_total  # one oracle call per case
    invalid_rows = n_total - n_ok  # reference oracle should pass all

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "harness": "runners/run_doctor_probe_smallest_unique_subarray.py",
        "oracle": "doctor/adversarial/smallest_unique_subarray_oracle.py::brute_force_smallest_unique_subarray",
        "oracle_bound_n": DEFAULT_MAX_N,
        "candidates": list(CANDIDATES.keys()),
        "total_cases": n_total,
        "probe_cases": n_probe,
        "exhaustive_cases": n_exhaustive,
        "exhaustive_config": {
            "max_n": EXHAUSTIVE_MAX_N,
            "max_val": EXHAUSTIVE_MAX_VAL,
        },
        "provenance_count": provenance_count,
        "invalid_rows": invalid_rows,
        "blocked_rows": 0,
        "comparator": "exact int (==)",
        "claim": "prepared-envelope measurement only. Doctor does not autonomously understand the problem.",
        "candidate_pass_rates": {
            name: {
                "pass": stats["pass"],
                "fail": stats["fail"],
                "total": stats["total"],
                "pass_rate": round(stats["pass"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
            }
            for name, stats in candidate_stats.items()
        },
        "per_case": results,
    }


def write_report(data: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Written {OUTPUT_PATH}")

    # Generate findings markdown
    cr = data["candidate_pass_rates"]
    lines = [
        "# FINDINGS_SMALLEST_UNIQUE_SUBARRAY: Doctor Probe Results",
        "",
        "## Summary",
        "",
        f"- **Problem:** Smallest Unique Subarray (prepared envelope)",
        f"- **Total cases:** {data['total_cases']} ({data['probe_cases']} hand-written, {data['exhaustive_cases']} exhaustive n<={EXHAUSTIVE_MAX_N})",
        f"- **Oracle bound:** n <= {data['oracle_bound_n']}",
        f"- **Comparator:** {data['comparator']}",
        f"- **Provenance count:** {data['provenance_count']}",
        f"- **Invalid/blocked rows:** {data['invalid_rows']} / {data['blocked_rows']}",
        "",
        "## Candidate Pass Rates",
        "",
        "| Candidate | Pass | Fail | Total | Pass Rate |",
        "|-----------|-----:|-----:|------:|----------:|",
    ]
    for name, stats in sorted(cr.items()):
        lines.append(
            f"| {name} | {stats['pass']} | {stats['fail']} | {stats['total']} | {stats['pass_rate']:.2%} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "This is a **prepared-envelope Doctor measurement** only.",
        "Doctor does not autonomously understand URLs or problem statements.",
        "",
        "- The reference oracle wrapper should pass all cases.",
        "- All wrong candidates should fail at least one case.",
        "- Candidates that fail at lower rates are harder to distinguish;",
        "  they approximate the correct logic more closely.",
        "",
        "## Caveats",
        "",
        f"- Oracle is O(n^3) brute-force, bounded to n <= {data['oracle_bound_n']}.",
        "- No editorial solution was used as oracle.",
        "- No external tags were used as evidence.",
        "- No LLM/schema_classifier was involved.",
        "- This does not constitute autonomous problem understanding.",
    ])

    FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written {FINDINGS_PATH}")


def main():
    data = run_probes()
    write_report(data)

    cr = data["candidate_pass_rates"]
    for name, stats in sorted(cr.items()):
        print(f"  {name}: {stats['pass']}/{stats['total']} passed ({stats['pass_rate']:.2%})")


if __name__ == "__main__":
    main()
