"""Runner for LC49 ingestion gate (Group Anagrams).

Perturbation family ``ordering_invariant``: shuffles word order in input
list.  Individual word strings never modified.  Comparator
``multiset_of_multisets`` handles order-independent group comparison.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Callable

from doctor.adversarial.lc49_ingestion_gate import lc49_ingestion_gate


# ---------------------------------------------------------------------------
# Reference oracle
# ---------------------------------------------------------------------------

def lc49_oracle(strs: list[str]) -> list[list[str]]:
    """Group anagrams via sorted-character signature."""
    groups: dict[str, list[str]] = {}
    for s in strs:
        key = "".join(sorted(s))
        if key not in groups:
            groups[key] = []
        groups[key].append(s)
    return list(groups.values())


# ---------------------------------------------------------------------------
# Solvers under test
# ---------------------------------------------------------------------------

def solver_defaultdict(strs: list[str]) -> list[list[str]]:
    """Default dict grouping."""
    groups: dict[str, list[str]] = defaultdict(list)
    for s in strs:
        groups["".join(sorted(s))].append(s)
    return list(groups.values())


def solver_sorted_groupby(strs: list[str]) -> list[list[str]]:
    """Sort by signature then group."""
    from itertools import groupby
    sorted_strs = sorted(strs, key=lambda s: "".join(sorted(s)))
    result: list[list[str]] = []
    for _, group in groupby(sorted_strs, key=lambda s: "".join(sorted(s))):
        result.append(list(group))
    return result


def solver_tuple_counter(strs: list[str]) -> list[list[str]]:
    """Use tuple of char counts as key instead of sorted string."""
    groups: dict[tuple[int, ...], list[str]] = {}
    for s in strs:
        counts = [0] * 26
        for ch in s:
            counts[ord(ch) - ord("a")] += 1
        key = tuple(counts)
        if key not in groups:
            groups[key] = []
        groups[key].append(s)
    return list(groups.values())


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def solver_empty(strs: list[str]) -> list[list[str]]:
    """Always returns empty list. Expect rejection."""
    return []


def solver_single_bucket(strs: list[str]) -> list[list[str]]:
    """Puts all words in one group — wrong. Expect rejection."""
    return [list(strs)]


# ---------------------------------------------------------------------------
# Reference tests
# ---------------------------------------------------------------------------

REFERENCE_TESTS: list[dict[str, list[str] | list[list[str]]]] = [
    {"strs": ["eat", "tea", "tan", "ate", "nat", "bat"], "expected": [
        ["eat", "tea", "ate"], ["tan", "nat"], ["bat"],
    ]},
    {"strs": [""], "expected": [[""]]},
    {"strs": ["a"], "expected": [["a"]]},
    {"strs": ["abc", "cba", "bac", "xyz", "zyx"], "expected": [
        ["abc", "cba", "bac"], ["xyz", "zyx"],
    ]},
    {"strs": ["rat", "tar", "art", "car", "arc"], "expected": [
        ["rat", "tar", "art"], ["car", "arc"],
    ]},
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_suite(
    solvers: list[Callable[[list[str]], list[list[str]]]],
    label: str,
) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc49_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc49_oracle,
        reference_tests=REFERENCE_TESTS,
    )
    ingest = result["ingest"]
    reason = result["reason"]
    metrics = result.get("metrics", {})
    print(f"  ingest: {ingest}")
    print(f"  reason: {reason}")
    if metrics:
        os_ = metrics.get("oracle_alignment", "N/A")
        ps_ = metrics.get("avg_perturbation_stability", "N/A")
        print(f"  oracle_alignment: {os_}")
        print(f"  avg_stability: {ps_}")
        per_solver = metrics.get("perturbation_stability", {}).get("per_solver", {})
        for sname, stab in per_solver.items():
            print(f"  {sname}: stability={stab}")
    return {"ingest": ingest, "reason": reason}


def main() -> int:
    print("=" * 60)
    print("LC49 Ingestion Gate — Group Anagrams")
    print("=" * 60)

    good_solvers = [solver_defaultdict, solver_sorted_groupby, solver_tuple_counter]
    good_result = run_suite(good_solvers, "Good solvers (should PASS)")

    bad_solvers = [solver_empty, solver_single_bucket]
    bad_result = run_suite(bad_solvers, "Negative controls (must FAIL)")

    print("\n" + "=" * 60)
    verdict = (
        good_result["ingest"] is True and bad_result["ingest"] is False
    )
    print(f"Good solvers ingested: {good_result['ingest']}")
    print(f"Bad solvers rejected: {not bad_result['ingest']} (reason: {bad_result['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print("=" * 60)

    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
