"""Operator-invariance test: does the LC45-discriminability signature transfer
to LC322 under the same operator class?

FRAMEWORK: OPTION B (instrument framing) — see test_lc45_solver_population.py
for the framework declaration. This file is the LC322 instantiation.

KEY DIFFERENCES FROM LC45 (by design, not by oversight):
  1. P1-P4 are RECONSTRUCTED as LC322-native, not ported from LC45. The
     structural roles (coarse / intermediate / fine) are preserved; the
     predicates are re-derived from LC322 semantics (coin combinations
     vs. path reachability). "UNREACHABLE" is NOT structurally identical
     between the two problems: LC45 brute raises on unreachable, LC322
     brute returns -1. The projection family is re-derived accordingly.

  2. The sample distribution is LC322-native (coins + amount, not jump
     arrays). Seed and sample SIZE match LC45 for direct comparability,
     but the parameterization is independent.

  3. The P1 dissolved-pair set is NOT pre-committed. This is the actual
     invariance measurement: P1-collapse-count(LC45) vs
     P1-collapse-count(LC322). If LC322's P1 dissolves zero pairs, that
     is a real finding (operator is problem-class-dependent in a
     specific direction), not a test failure.

WHAT THIS TEST ASSERTS:
  - P2, P3, P4 preserve discriminability across the BUGGY population
    (resolution consistency under refinement).
  - SURVIVOR does not dissolve with any BUGGY under P1 or P3.

WHAT THIS TEST DOES NOT ASSERT:
  - P1 dissolves exactly N pairs (N is reported, not pre-committed).
  - The dissolved pair set is the same as LC45's.
  - Any cross-problem property of solvers (only operator properties
    are tested).

Determinism: the discriminability tests use a fixed-seed random sample
of 1000 reachable LC322 instances (coins + amount). The seed matches
LC45's seed for direct comparability.

P1-COUNT IS NOT A PROPERTY OF LC322 PROBLEM STRUCTURE.
The P1 dissolved-pair count of 6 is a property of THIS specific 9-BUGGY
solver basis (the failure classes chosen and their alignments) under
THIS sampling protocol. It is not stable under:
  - solver basis permutation (adding/removing/regrouping BUGGY)
  - instance distribution changes
  - sampling parameter changes
The count is degeneracy of the ensemble under the P1 quotient, not a
feature of LC322.

THE "1 vs 6" SCALAR IS NOT A MEANINGFUL COMPARISON.
LC45 P1-count and LC322 P1-count cannot be compared as a scalar because
the two measurements are taken under different joint distributions
(problem x solver-flavor basis x instance generator x sampling scheme).
The three surviving invariants (monotonicity, SURVIVOR separability,
finite-sample stability) hold in both; everything else is interpretive
load.
"""
from __future__ import annotations

import os
import random
import sys
import unittest
from collections import Counter

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.observation import Observation, from_brute_force

from doctor.adversarial.lc322_candidates import (
    lc322_dp,
    lc322_bfs_coin_count_cutoff,
    lc322_greedy,
    lc322_lookahead_one,
    lc322_memo_collision,
    lc322_modulo_memo_alias,
    lc322_ordering_commitment,
    lc322_reachability_lookahead,
    lc322_smallest_first,
    lc322_transition_asymmetric_forward_dp,
)
from doctor.adversarial.lc322_ground_truth import lc322_brute_force

# 5-case oracle: pinned canonical cases for the LC322 population.
ORACLE_CASES = [
    ([1, 2, 5, 11], 3),
    ([1, 3, 4, 6], 2),
    ([1, 5, 10, 25, 30], 2),
    ([2, 3], "unreachable"),
    ([1, 2, 5, 100], 20),
]

# The 10-solver population: 1 SURVIVOR + 9 BUGGY, calibrated against the
# 5-case oracle. Each BUGGY fails on >=1 case.
SURVIVOR = lc322_dp
ALL_BUGGY = [
    lc322_greedy,
    lc322_smallest_first,
    lc322_memo_collision,
    lc322_lookahead_one,
    lc322_bfs_coin_count_cutoff,
    lc322_modulo_memo_alias,
    lc322_reachability_lookahead,
    lc322_ordering_commitment,
    lc322_transition_asymmetric_forward_dp,
]
BUGGY_NAMES = [f.__name__ for f in ALL_BUGGY]

# Same protocol constants as LC45 for direct comparability.
RANDOM_SAMPLE_SIZE = 1000
RANDOM_SEED = 20260602
NEAR_THRESHOLD = 1


def _safe(fn, coins, amount):
    try:
        return ("ok", fn([*coins, amount]))
    except Exception as e:
        return ("raise", type(e).__name__)


# =========================================================================
# LC322-NATIVE PROJECTION FUNCTIONS
# Re-derived from LC322 semantics; not ported from LC45.
# Structural roles preserved: P1 coarse, P2 distance, P3 typed, P4 fine.
# =========================================================================

def _project_lc322_p1(solver_out, brute_out):
    """P1 (coarse, 3 states): SUCCESS / FAILURE / UNREACHABLE.

    LC322-native predicate (not LC45 port):
      - UNREACHABLE: brute=-1 AND solver=-1 (mutual agreement on infeasible)
      - FAILURE: brute=-1 XOR solver=-1, OR both reachable but disagree
      - SUCCESS: both reachable and agree on coin count

    LC45's P1 used `raise` as the unreachable signal; LC322 uses -1.
    LC45's P1 collapsed "solver says reachable when brute is unreachable"
    into UNREACHABLE (masking disagreement). The LC322-native P1
    surfaces that disagreement as FAILURE for full discriminability.
    """
    s_val = solver_out[1] if solver_out[0] == "ok" else None
    b_val = brute_out[1] if brute_out[0] == "ok" else None
    if b_val == -1 and s_val == -1:
        return "UNREACHABLE"
    if b_val == -1 or s_val == -1:
        return "FAILURE"
    return "SUCCESS" if s_val == b_val else "FAILURE"


def _project_lc322_p2(solver_out, brute_out):
    """P2 (intermediate, distance-based): NEAR / FAR / UNREACHABLE.

    LC322-native: NEAR iff |solver - brute| <= 1 and both reachable.
    """
    s_val = solver_out[1] if solver_out[0] == "ok" else None
    b_val = brute_out[1] if brute_out[0] == "ok" else None
    if b_val == -1 and s_val == -1:
        return "UNREACHABLE"
    if b_val == -1 or s_val == -1:
        return "FAR"
    return "NEAR" if abs(s_val - b_val) <= NEAR_THRESHOLD else "FAR"


def _project_lc322_p3(solver_out, brute_out):
    """P3 (intermediate, typed): SUCCESS / NEAR-wrong / FAR-wrong / UNREACHABLE.

    LC322-native: distinguishes exact match from distance <=1 from further.
    """
    s_val = solver_out[1] if solver_out[0] == "ok" else None
    b_val = brute_out[1] if brute_out[0] == "ok" else None
    if b_val == -1 and s_val == -1:
        return "UNREACHABLE"
    if b_val == -1 or s_val == -1:
        return "FAR-wrong"
    if s_val == b_val:
        return "SUCCESS"
    return "NEAR-wrong" if abs(s_val - b_val) <= NEAR_THRESHOLD else "FAR-wrong"


def _project_lc322_p4(solver_out, brute_out):
    """P4 (fine, value-level): V{n} per specific coin count, plus UNREACHABLE.

    LC322-native: each specific min-coin-count is its own label.
    """
    s_val = solver_out[1] if solver_out[0] == "ok" else None
    b_val = brute_out[1] if brute_out[0] == "ok" else None
    if b_val == -1 and s_val == -1:
        return "UNREACHABLE"
    if b_val == -1 or s_val == -1:
        return "MISMATCH"
    return f"V{s_val}"


# =========================================================================
# SAMPLE GENERATION (LC322-native)
# =========================================================================

def _generate_lc322_reachable_sample(n, seed):
    """Generate a deterministic sample of n unique reachable LC322 instances.

    Each instance is (coins, amount) where:
      - 2-6 positive coin denominations from 1-25
      - amount in 1-30
      - brute_force returns >= 0 (reachable, excluding the trivial amount=0)
    """
    rng = random.Random(seed)
    sample = []
    seen = set()
    attempts = 0
    while len(sample) < n and attempts < n * 30:
        attempts += 1
        size = rng.randint(2, 6)
        coins = sorted({rng.randint(1, 25) for _ in range(size)})
        if not coins or len(coins) < 2:
            continue
        amount = rng.randint(1, 30)
        key = (tuple(coins), amount)
        if key in seen:
            continue
        seen.add(key)
        try:
            t = lc322_brute_force(coins, amount)
        except Exception:
            continue
        if t < 0:
            continue
        sample.append((coins, amount))
    return sample


# =========================================================================
# SIGNATURE PROTOCOL (multiset over sample)
# =========================================================================

def _make_multiset_signatures(project_fn, sample, solvers):
    """Compute multiset signature per solver under a projection.

    Returns: dict[solver_name -> Counter of classifications over sample].

    Two solvers "dissolve" under projection P iff their multiset signatures
    are identical. This is the operator-discriminability observation.
    """
    sig = {}
    for solver in solvers:
        classifications = []
        for coins, amount in sample:
            s_out = _safe(solver, coins, amount)
            b_val = lc322_brute_force(coins, amount)
            b_out = ("ok", b_val) if b_val != -1 else ("ok", -1)
            classifications.append(project_fn(s_out, b_out))
        sig[solver.__name__] = Counter(classifications)
    return sig


def _make_observation_signatures(projection_level, project_fn, sample, solvers):
    """Observation-substrate view of the per-sample classification.

    Returns: dict[solver_name -> list[Observation]]
    Each Observation wraps a single classification with explicit
    problem_id, candidate_id, projection_level, evaluation_layer, seed,
    sample_size. The multiset of observation.canonical_form[0] values
    must equal the Counter from `_make_multiset_signatures`.
    """
    sig = {}
    for solver in solvers:
        observations = []
        for coins, amount in sample:
            s_out = _safe(solver, coins, amount)
            b_val = lc322_brute_force(coins, amount)
            b_out = ("ok", b_val) if b_val != -1 else ("ok", -1)
            classification = project_fn(s_out, b_out)
            obs = from_brute_force(
                problem_id="lc322",
                candidate_id=solver.__name__,
                projection_level=projection_level,
                classification=classification,
                seed=RANDOM_SEED,
                sample_size=RANDOM_SAMPLE_SIZE,
            )
            observations.append(obs)
        sig[solver.__name__] = observations
    return sig


def _find_dissolved_pairs(sig, names):
    """Find all pairs (a, b) with a < b such that sig[a] == sig[b]."""
    dissolved = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if sig[a] == sig[b]:
                dissolved.append((a, b))
    return dissolved


# =========================================================================
# TESTS
# =========================================================================

class TestOracle(unittest.TestCase):
    def test_survivor_passes_all_oracle(self):
        for nums, claimed in ORACLE_CASES:
            coins = nums[:-1]
            amount = nums[-1]
            if claimed == "unreachable":
                self.assertEqual(
                    SURVIVOR(nums), -1,
                    f"SURVIVOR failed unreachable on {nums}",
                )
            else:
                self.assertEqual(
                    SURVIVOR(nums), claimed,
                    f"SURVIVOR failed on {nums}: expected {claimed}, got {SURVIVOR(nums)}",
                )


class TestBuggyFailsOracle(unittest.TestCase):
    def test_each_buggy_fails_at_least_one_oracle_case(self):
        for solver in ALL_BUGGY:
            failures = 0
            for nums, claimed in ORACLE_CASES:
                coins = nums[:-1]
                amount = nums[-1]
                bf = lc322_brute_force(coins, amount)
                s_out = _safe(solver, coins, amount)
                if claimed == "unreachable":
                    if bf == -1 and s_out[1] != -1:
                        failures += 1
                    elif bf != -1 and s_out[1] == -1:
                        failures += 1
                    elif bf != -1 and s_out[1] != bf:
                        failures += 1
                else:
                    if s_out[1] != claimed:
                        failures += 1
            self.assertGreaterEqual(
                failures, 1,
                f"{solver.__name__} passed all 5 oracle cases — failure class miscalibrated",
            )


class TestOperatorInvariance(unittest.TestCase):
    """Pin the discriminability signature of the LC322-native operator
    (P1..P4 reconstructed from LC322 semantics) on a fixed-seed sample
    of 1000 reachable instances.

    Per the invariance spec: P2-P4 are checked for RESOLUTION CONSISTENCY
    (do they refine the P1 partition?), NOT for identity preservation
    (zero dissolved pairs globally). P1 dissolved-pair count is REPORTED
    for the comparison P1-count(LC45) vs P1-count(LC322).
    """

    REPORTED_P1_DISSOLVED_COUNT = None  # filled in by test_p1_signature_reported

    @classmethod
    def setUpClass(cls):
        cls.sample = _generate_lc322_reachable_sample(RANDOM_SAMPLE_SIZE, RANDOM_SEED)
        assert len(cls.sample) == RANDOM_SAMPLE_SIZE, (
            f"Failed to generate {RANDOM_SAMPLE_SIZE} reachable LC322 instances "
            f"(got {len(cls.sample)})"
        )

    def test_sample_size(self):
        self.assertEqual(len(self.sample), RANDOM_SAMPLE_SIZE)

    def test_p1_signature_reported(self):
        """P1 dissolved-pair count is REPORTED, not asserted. The actual
        invariance test is the comparison P1-count(LC45) vs P1-count(LC322)."""
        sig = _make_multiset_signatures(_project_lc322_p1, self.sample, ALL_BUGGY)
        dissolved = _find_dissolved_pairs(sig, BUGGY_NAMES)
        type(self).REPORTED_P1_DISSOLVED_COUNT = len(dissolved)
        print(
            f"\n[INVARIANCE MEASUREMENT] LC322 P1 dissolved-pair count: {len(dissolved)}"
        )
        if dissolved:
            for pair in dissolved:
                print(f"  dissolved: {pair[0]} == {pair[1]}")
        else:
            print("  (no dissolved pairs; P1 is fully discriminative on LC322)")

        obs_sig = _make_observation_signatures(1, _project_lc322_p1, self.sample, ALL_BUGGY)
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.problem_id, "lc322")
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 1)
                self.assertEqual(obs.evaluation_layer, "brute_force")
                self.assertEqual(obs.seed, RANDOM_SEED)
                self.assertEqual(obs.sample_size, RANDOM_SAMPLE_SIZE)
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                sig[name],
                f"Observation canonical_form Counter diverges from multiset "
                f"signature for {name} under LC322-P1",
            )

    def test_p2_p3_p4_monotone_non_increasing(self):
        """Resolution consistency: the dissolved-pair set is monotone
        non-increasing as the projection refines. Equivalently, no pair
        dissolved under a finer projection (P2/P3/P4) is un-dissolved
        under a coarser projection (P1).

        This is NOT a refinement-of-P1-dissolved test: P2-P4 may have
        additional dissolved pairs not in P1's set (those are reported
        but not asserted against). It is a hierarchy-coherence test:
        the coarser projections never make finer distinctions disappear.
        """
        sig_p1 = _make_multiset_signatures(_project_lc322_p1, self.sample, ALL_BUGGY)
        sig_p2 = _make_multiset_signatures(_project_lc322_p2, self.sample, ALL_BUGGY)
        sig_p3 = _make_multiset_signatures(_project_lc322_p3, self.sample, ALL_BUGGY)
        sig_p4 = _make_multiset_signatures(_project_lc322_p4, self.sample, ALL_BUGGY)

        p1_dissolved = {(a, b) for a, b in _find_dissolved_pairs(sig_p1, BUGGY_NAMES)}
        p2_dissolved = {(a, b) for a, b in _find_dissolved_pairs(sig_p2, BUGGY_NAMES)}
        p3_dissolved = {(a, b) for a, b in _find_dissolved_pairs(sig_p3, BUGGY_NAMES)}
        p4_dissolved = {(a, b) for a, b in _find_dissolved_pairs(sig_p4, BUGGY_NAMES)}

        # Monotone non-increasing: P1_dissolved ⊇ P2_dissolved ⊇ P3_dissolved ⊇ P4_dissolved
        p2_not_in_p1 = p2_dissolved - p1_dissolved
        p3_not_in_p2 = p3_dissolved - p2_dissolved
        p4_not_in_p3 = p4_dissolved - p3_dissolved

        self.assertEqual(
            p2_not_in_p1, set(),
            f"P2-dissolved pairs not in P1-dissolved: {p2_not_in_p1}. "
            f"Hierarchy violated: P2 should not dissolve pairs that P1 separates.",
        )
        self.assertEqual(
            p3_not_in_p2, set(),
            f"P3-dissolved pairs not in P2-dissolved: {p3_not_in_p2}. "
            f"Hierarchy violated: P3 should not dissolve pairs that P2 separates.",
        )
        self.assertEqual(
            p4_not_in_p3, set(),
            f"P4-dissolved pairs not in P3-dissolved: {p4_not_in_p3}. "
            f"Hierarchy violated: P4 should not dissolve pairs that P3 separates.",
        )

        print(
            f"\n[HIERARCHY] LC322 dissolved-pair counts: "
            f"P1={len(p1_dissolved)}, P2={len(p2_dissolved)}, "
            f"P3={len(p3_dissolved)}, P4={len(p4_dissolved)}"
        )

        obs_p1 = _make_observation_signatures(1, _project_lc322_p1, self.sample, ALL_BUGGY)
        obs_p2 = _make_observation_signatures(2, _project_lc322_p2, self.sample, ALL_BUGGY)
        obs_p3 = _make_observation_signatures(3, _project_lc322_p3, self.sample, ALL_BUGGY)
        obs_p4 = _make_observation_signatures(4, _project_lc322_p4, self.sample, ALL_BUGGY)
        for level, obs_sig in [(1, obs_p1), (2, obs_p2), (3, obs_p3), (4, obs_p4)]:
            for name in BUGGY_NAMES:
                for obs in obs_sig[name]:
                    self.assertEqual(obs.problem_id, "lc322")
                    self.assertEqual(obs.candidate_id, name)
                    self.assertEqual(obs.projection_level, level)
                    self.assertEqual(obs.evaluation_layer, "brute_force")
                    self.assertEqual(obs.seed, RANDOM_SEED)
                    self.assertEqual(obs.sample_size, RANDOM_SAMPLE_SIZE)
        canonical_sigs = {
            1: sig_p1, 2: sig_p2, 3: sig_p3, 4: sig_p4,
        }
        canonical_obs = {
            1: obs_p1, 2: obs_p2, 3: obs_p3, 4: obs_p4,
        }
        for level in (1, 2, 3, 4):
            for name in BUGGY_NAMES:
                self.assertEqual(
                    Counter(o.canonical_form[0] for o in canonical_obs[level][name]),
                    canonical_sigs[level][name],
                    f"Observation canonical_form Counter diverges from multiset "
                    f"signature for {name} under LC322-P{level}",
                )

    def test_survivor_does_not_dissolve_with_any_buggy_under_p1(self):
        sig = _make_multiset_signatures(
            _project_lc322_p1, self.sample, [SURVIVOR] + ALL_BUGGY
        )
        survivor_sig = sig[SURVIVOR.__name__]
        for name in BUGGY_NAMES:
            self.assertNotEqual(
                survivor_sig, sig[name],
                f"SURVIVOR dissolved with {name} under LC322-P1. "
                f"Operator can no longer separate SURVIVOR from this BUGGY.",
            )

        obs_sig = _make_observation_signatures(
            1, _project_lc322_p1, self.sample, [SURVIVOR] + ALL_BUGGY
        )
        for obs in obs_sig[SURVIVOR.__name__]:
            self.assertEqual(obs.candidate_id, SURVIVOR.__name__)
            self.assertEqual(obs.projection_level, 1)
            self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(obs.problem_id, "lc322")
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 1)
                self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                sig[name],
            )

    def test_survivor_does_not_dissolve_with_any_buggy_under_p3(self):
        sig = _make_multiset_signatures(
            _project_lc322_p3, self.sample, [SURVIVOR] + ALL_BUGGY
        )
        survivor_sig = sig[SURVIVOR.__name__]
        for name in BUGGY_NAMES:
            self.assertNotEqual(
                survivor_sig, sig[name],
                f"SURVIVOR dissolved with {name} under LC322-P3. "
                f"Operator can no longer separate SURVIVOR from this BUGGY.",
            )

        obs_sig = _make_observation_signatures(
            3, _project_lc322_p3, self.sample, [SURVIVOR] + ALL_BUGGY
        )
        for obs in obs_sig[SURVIVOR.__name__]:
            self.assertEqual(obs.candidate_id, SURVIVOR.__name__)
            self.assertEqual(obs.projection_level, 3)
            self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(obs.problem_id, "lc322")
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 3)
                self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                sig[name],
            )


if __name__ == "__main__":
    unittest.main()
