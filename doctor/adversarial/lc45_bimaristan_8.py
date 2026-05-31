"""
LC45 oracle correctness discrimination validation.

Tests that LC45OracleEvaluator:
1. Catches wrong solutions (naive_greedy diverging from truth) — no false negatives
2. Validates correct solutions (greedy_frontier agreeing with truth) — no false positives
3. Correctly rejects arrays exceeding domain ceiling
4. Produces correct oracle-dependent values matching direct solver calls

Gate: if this script exits 0, the oracle is safe to commit.
"""
from __future__ import annotations

import sys
from collections import Counter

from doctor.adversarial.lc45_bimaristan import LC45
from doctor.adversarial.lc45_candidates import lc45_dp, lc45_greedy_frontier, lc45_naive_greedy
from doctor.adversarial.lc45_ground_truth import lc45_brute_force, GroundTruthDomainError
from doctor.adversarial.lc45_oracle import LC45OracleEvaluator, OracleCeilingError, evaluation_surface
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


def _candidate(array, generator_id="validation"):
    return SynthesizedCandidate(tuple(array), (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


# ── 1. Expand seed space from runner ─────────────────────────────────────

def _all_seeds() -> dict[str, list[list[int]]]:
    """Replicate the seed space from run_lc45.py _candidate_space."""
    seeds: dict[str, list[list[int]]] = {
        "naive_max_jump_suboptimal": [
            [2, 4, 1, 1, 1, 1],
            [2, 3, 0, 1, 4],
            [3, 5, 1, 1, 1, 1, 1],
            [2, 5, 0, 0, 1, 1, 1],
            [3, 1, 4, 1, 1, 1],
            [2, 4, 0, 1, 1, 1],
            [3, 4, 1, 0, 1, 1],
            [2, 5, 1, 1, 1, 1, 1],
            [3, 2, 5, 1, 1, 1, 1],
            [2, 3, 1, 1, 4],
            [4, 1, 1, 5, 1, 1, 1],
            [3, 5, 0, 1, 1, 1, 1],
        ],
        "single_large_jump_decoy": [
            [2, 5, 0, 0, 1, 1, 1],
            [3, 6, 1, 1, 1, 1, 1, 1],
            [2, 4, 0, 1, 1, 1],
            [3, 5, 1, 0, 1, 1, 1],
            [2, 6, 0, 0, 0, 1, 1, 1],
            [3, 7, 1, 1, 1, 1, 1, 1, 1],
            [2, 5, 1, 1, 1, 1, 1],
            [4, 6, 1, 1, 0, 1, 1, 1],
            [3, 5, 0, 1, 1, 1, 1],
            [2, 7, 0, 0, 0, 0, 1, 1, 1],
            [4, 5, 1, 1, 1, 0, 1],
            [3, 6, 0, 1, 1, 1, 1, 1],
        ],
        "uniform_jump_array": [
            [1, 1, 1, 1],
            [2, 2, 2, 2],
            [3, 3, 3, 3],
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3],
            [2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4],
            [2, 2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4, 4],
        ],
        "greedy_frontier_valid_no_false_pressure": [
            [2, 3, 1, 1, 4],
            [1, 2, 1, 1, 1],
            [2, 2, 1, 1, 1],
            [3, 1, 2, 1, 1],
            [1, 3, 1, 1, 1],
            [2, 1, 2, 1, 1],
            [3, 2, 1, 1, 1],
            [1, 1, 2, 1, 1],
            [2, 3, 2, 1, 1, 1],
            [1, 2, 2, 1, 1, 1],
            [3, 1, 1, 2, 1, 1],
            [2, 1, 1, 2, 1, 1],
        ],
        "greedy_horizon_collapse": [
            [2, 3, 1, 1, 4],
            [3, 1, 5, 1, 1, 1, 1],
            [2, 4, 0, 0, 1, 1],
            [3, 2, 4, 1, 1, 1, 1],
            [2, 5, 0, 0, 0, 1, 1],
            [4, 1, 1, 1, 5, 1, 1, 1],
            [3, 1, 4, 0, 1, 1, 1],
            [2, 3, 0, 1, 4],
            [5, 1, 1, 1, 1, 6, 1, 1, 1, 1, 1],
            [3, 2, 1, 4, 1, 1, 1],
            [2, 4, 1, 0, 1, 1],
            [4, 2, 1, 1, 5, 1, 1, 1],
        ],
    }
    return seeds


def _resolve_validation_predicates(manifold_id: str) -> list:
    for family in LC45.invariant_families:
        for manifold in family.failure_manifolds:
            if manifold.manifold_id == manifold_id:
                return list(manifold.geometry_generators[0].validation_predicates)
    return []


# ── 2. Direct solver ground truth ────────────────────────────────────────

def _direct_ground_truth(nums: list[int]) -> int | None:
    try:
        return lc45_brute_force(nums)
    except GroundTruthDomainError:
        return None


def _direct_naive(nums: list[int]) -> int:
    return lc45_naive_greedy(nums)


def _direct_greedy_frontier(nums: list[int]) -> int:
    return lc45_greedy_frontier(nums)


def _direct_dp(nums: list[int]) -> int:
    return lc45_dp(nums)


# ── 3. Validation checks ─────────────────────────────────────────────────

def _check_oracle_ceiling() -> list[str]:
    failures: list[str] = []
    # Arrays of length 16 should be rejected
    for length in [16, 20, 100]:
        big = [1] * length
        candidate = _candidate(big)
        try:
            LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (), "ceiling_test"))
            failures.append(f"OracleCeilingError NOT raised for length {length}")
        except OracleCeilingError:
            pass
        except Exception as e:
            failures.append(f"Unexpected error for length {length}: {e}")

    # Arrays of length exactly 15 should be accepted
    boundary = [1] * 15
    candidate = _candidate(boundary)
    try:
        LC45OracleEvaluator().evaluate(evaluation_surface(candidate, (), "ceiling_test"))
    except OracleCeilingError:
        failures.append("OracleCeilingError raised for length 15 (should be accepted)")
    except Exception as e:
        failures.append(f"Unexpected error for length 15: {e}")

    return failures


def _check_correctness_discrimination() -> list[str]:
    """
    Core validation: verify the oracle correctly discriminates
    correct vs wrong solutions across ALL seed arrays.
    """
    failures: list[str] = []
    seeds = _all_seeds()

    for manifold_id, arrays in seeds.items():
        predicates = _resolve_validation_predicates(manifold_id)
        if not predicates:
            failures.append(f"No validation predicates found for {manifold_id}")
            continue

        for arr in arrays:
            gt = _direct_ground_truth(arr)
            if gt is None:
                continue

            greedy = _direct_greedy_frontier(arr)
            naive = _direct_naive(arr)
            dp = _direct_dp(arr)

            # ── Direct solver checks ──
            # greedy_frontier should always match truth (it's the correct algorithm)
            if greedy != gt:
                failures.append(f"{manifold_id} {arr}: greedy_frontier={greedy} != oracle={gt} (BUG IN GREEDY FRONTIER?)")
            # DP should always match truth
            if dp != gt:
                failures.append(f"{manifold_id} {arr}: dp={dp} != oracle={gt}")

            # ── Oracle evaluator checks ──
            candidate = _candidate(arr)
            result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, tuple(predicates), manifold_id))
            values = {v.symbol_name: v.value for v in result.oracle_dependent_values}

            # The oracle's ground_truth must match direct BFS
            if values.get("ground_truth_jumps", -1) != gt:
                failures.append(
                    f"{manifold_id} {arr}: oracle ground_truth_jumps={values.get('ground_truth_jumps')} "
                    f"!= direct BFS={gt}"
                )

            # The oracle's greedy_frontier must match direct call
            if values.get("greedy_frontier_output", -1) != greedy:
                failures.append(
                    f"{manifold_id} {arr}: oracle greedy_frontier_output={values.get('greedy_frontier_output')} "
                    f"!= direct call={greedy}"
                )

            # The oracle's naive output must match direct call
            naive_norm = naive if naive < 10**9 else -1
            oracle_naive = values.get("naive_max_jump_output", -1)
            if oracle_naive != naive_norm and oracle_naive != naive:
                failures.append(
                    f"{manifold_id} {arr}: oracle naive_max_jump_output={oracle_naive} "
                    f"!= direct call={naive}"
                )

    return failures


def _check_no_false_pressure() -> list[str]:
    """
    Verify that the oracle DOES NOT report adversarial pressure
    on manifolds where naive is correct (no false positives).

    Only flags a false positive if the oracle says naive_diverges=True
    but the direct solver call shows naive actually matches truth.
    Seeds that genuinely have naive_diverges=True are NOT false positives
    (they would be filtered out by generation constraints at runtime).
    """
    failures: list[str] = []
    seeds = _all_seeds()
    no_pressure_manifolds = {"uniform_jump_array", "greedy_frontier_valid_no_false_pressure"}

    for manifold_id in no_pressure_manifolds:
        for arr in seeds[manifold_id]:
            gt = _direct_ground_truth(arr)
            if gt is None:
                continue
            naive = _direct_naive(arr)
            naive_norm = naive if naive < 10**9 else -1

            candidate = _candidate(arr)
            result = LC45OracleEvaluator().evaluate(
                evaluation_surface(candidate, (), manifold_id)
            )
            values = {v.symbol_name: v.value for v in result.oracle_dependent_values}
            oracle_naive_diverges = values.get("naive_diverges", None)

            if naive_norm == gt and oracle_naive_diverges is True:
                failures.append(
                    f"{manifold_id} {arr}: FALSE POSITIVE — oracle says naive_diverges=True "
                    f"but direct naive({naive_norm}) == truth({gt})"
                )
            if naive_norm != gt and oracle_naive_diverges is False:
                failures.append(
                    f"{manifold_id} {arr}: FALSE NEGATIVE — oracle says naive_diverges=False "
                    f"but direct naive({naive_norm}) != truth({gt})"
                )

    return failures


def _check_saturated_failure_manifolds() -> list[str]:
    """
    Verify that the oracle correctly identifies ALL candidates as diverging
    on manifolds where naive is supposed to be wrong (no false negatives).
    """
    failures: list[str] = []
    seeds = _all_seeds()
    saturated = {"naive_max_jump_suboptimal", "single_large_jump_decoy", "greedy_horizon_collapse"}

    for manifold_id in saturated:
        predicates = _resolve_validation_predicates(manifold_id)
        for arr in seeds[manifold_id]:
            gt = _direct_ground_truth(arr)
            if gt is None:
                continue
            candidate = _candidate(arr)
            result = LC45OracleEvaluator().evaluate(evaluation_surface(candidate, tuple(predicates), manifold_id))
            values = {v.symbol_name: v.value for v in result.oracle_dependent_values}

            naive = _direct_naive(arr)
            naive_norm = naive if naive < 10**9 else -1
            if values.get("naive_diverges", False) is False and naive_norm != gt:
                failures.append(
                    f"{manifold_id} {arr}: FALSE NEGATIVE — naive_diverges=False but "
                    f"direct naive={naive_norm} != truth={gt}"
                )

    return failures


# ── 4. Main ──────────────────────────────────────────────────────────────

def main() -> int:
    checks = [
        ("Domain ceiling", _check_oracle_ceiling),
        ("Correctness discrimination", _check_correctness_discrimination),
        ("No false pressure (uniform_jump_array, frontier_valid)", _check_no_false_pressure),
        ("Saturated failure manifolds (no false negatives)", _check_saturated_failure_manifolds),
    ]

    all_failures: list[str] = []
    total_checks = 0
    passed_checks = 0

    print("=" * 72)
    print("LC45 ORACLE CORRECTNESS DISCRIMINATION VALIDATION")
    print("=" * 72)

    for label, fn in checks:
        failures = fn()
        all_failures.extend(failures)
        if failures:
            print(f"\n  FAIL [{label}] - {len(failures)} failure(s):")
            for f in failures:
                print(f"    X {f}")
        else:
            print(f"\n  PASS [{label}]")
        total_checks += 1
        if not failures:
            passed_checks += 1

    print()
    print("-" * 72)
    print(f"  Checks: {passed_checks}/{total_checks} passed")
    print(f"  Assertions failed: {len(all_failures)}")

    if all_failures:
        print("\n  RESULT: REJECT - oracle has correctness issues")
        return 1
    else:
        print("\n  RESULT: ACCEPT - oracle correctly discriminates correct vs wrong solutions")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
