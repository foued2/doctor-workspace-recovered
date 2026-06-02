"""Operator sensitivity profile for the LC45 evaluation operator.

FRAMEWORK: OPTION B (instrument framing).

The LC45 system is a constructed artifact, not an observed system:
  - the 9 BUGGY solvers were designed (failure classes per handoff v3)
  - the SURVIVOR was chosen
  - the brute-force oracle was authored
  - the 4-projection evaluation operator (P1..P4) was defined
  - the test cases were chosen
  - the random sample is generated from a fixed seed

Every "observation" in this file is a property of *this construction*, not
a fact about an independent solver space. The tests do not assert that LC45
reveals a stable property of "jumping games". They assert that under the
specific operator (P1..P4) we have defined, the following discriminability
signature is observed on the specific sample we generated:

  - P1  {SUCCESS, FAILURE, UNREACHABLE}   loses discriminability for ONE
         specific pair: {reachable_boolean_confusion, frontier_off_by_one}.
         This is an *operator sensitivity observation*, not a solver claim:
         the binary-correctness projection does not distinguish a solver
         that always returns 5 from a solver that always returns 4 when
         both are wrong on every reachable input.
  - P2  {NEAR, FAR, UNREACHABLE}          preserves discriminability
         across all pairs in the population.
  - P3  {SUCCESS, NEAR-wrong, FAR-wrong,  preserves discriminability
        UNREACHABLE}                       across all pairs in the population.
  - P4  value-level                        preserves discriminability
                                            across all pairs in the population.
  - SURVIVOR is distinguishable from every BUGGY under P1 and P3.

INTERPRETATION CONSTRAINTS:
  1. These observations are *K-local* to the constructed LC45 system. They
     are not portable claims about "jumping games" or "solver populations
     in general".
  2. Transfer of these discriminability observations to a different problem
     (e.g. LC322) is a *transfer stress test of the operator*, not a
     transfer test of solver behavior. If P1 on LC322 dissolves a different
     pair, that is an operator-property finding, not an LC322 property
     finding.
  3. Any change to the operator (definitions of P1..P4), the sample
     (size, seed, distribution), or the solver population that alters the
     discriminability signature is an operator-behavior change, not a
     solver-behavior change.

Determinism: the operator-sensitivity tests use a fixed-seed random sample
of 1000 reachable arrays. The seed is hardcoded; the sample is reproducible.

P1-COUNT IS NOT A PROPERTY OF LC45 PROBLEM STRUCTURE.
The P1 dissolved-pair count of 1 is a property of THIS specific 9-BUGGY
solver basis (the failure classes chosen and their alignments) under
THIS sampling protocol. It is not stable under:
  - solver basis permutation (adding/removing/regrouping BUGGY)
  - instance distribution changes
  - sampling parameter changes
The count is degeneracy of the ensemble under the P1 quotient, not a
feature of LC45.

TEST-LAYER OBSERVATION SUBSTRATE: per-sample classifications in this
file are also populated as `doctor.core.observation.Observation`
instances. The Observation is test-layer instrumentation; production
modules in `doctor/adversarial/` etc. MUST NOT import it. The rationale
is recorded in `doctor/core/observation.py`.
"""
import os
import random
import sys
import unittest
from collections import Counter

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.observation import Observation, from_brute_force

from doctor.adversarial.lc45_candidates import (
    lc45_bfs_depth_cutoff,
    lc45_farthest_landing_path,
    lc45_first_window_max_then_greedy,
    lc45_frontier_off_by_one,
    lc45_max_landing_value,
    lc45_naive_greedy,
    lc45_reachable_boolean_confusion,
    lc45_three_step_window_dp,
    lc45_uniform_formula_generalizer,
    lc45_zero_dead_end_panic,
)
from doctor.adversarial.lc45_ground_truth import lc45_brute_force

SURVIVOR = lc45_bfs_depth_cutoff
ALL_BUGGY = [
    lc45_naive_greedy,
    lc45_max_landing_value,
    lc45_farthest_landing_path,
    lc45_zero_dead_end_panic,
    lc45_reachable_boolean_confusion,
    lc45_three_step_window_dp,
    lc45_frontier_off_by_one,
    lc45_uniform_formula_generalizer,
    lc45_first_window_max_then_greedy,
]
BUGGY_NAMES = [f.__name__ for f in ALL_BUGGY]

NEAR_THRESHOLD = 1
RANDOM_SAMPLE_SIZE = 1000
RANDOM_SEED = 20260602

ORACLE_CASES = [
    ([2, 3, 1, 1, 4], 2),
    ([2, 3, 0, 1, 4], 2),
    ([1, 1, 1, 1], 3),
    ([3, 0, 0, 0, 1], "unreachable"),
    ([1, 2, 3], 2),
]


def _safe(fn, nums):
    try:
        return ("ok", fn(nums))
    except Exception as e:
        return ("raise", type(e).__name__)


def _project_p1(solver_out, brute_out):
    if brute_out[0] == "raise":
        return "UNREACHABLE"
    if solver_out[0] == "raise":
        return "FAILURE"
    return "SUCCESS" if solver_out[1] == brute_out[1] else "FAILURE"


def _project_p2(solver_out, brute_out):
    if brute_out[0] == "raise":
        return "UNREACHABLE"
    if solver_out[0] == "raise":
        return "FAR"
    return "NEAR" if abs(solver_out[1] - brute_out[1]) <= NEAR_THRESHOLD else "FAR"


def _project_p3(solver_out, brute_out):
    if brute_out[0] == "raise":
        return "UNREACHABLE"
    if solver_out[0] == "raise":
        return "FAR-wrong"
    if solver_out[1] == brute_out[1]:
        return "SUCCESS"
    return "NEAR-wrong" if abs(solver_out[1] - brute_out[1]) <= NEAR_THRESHOLD else "FAR-wrong"


def _project_p4(solver_out, brute_out):
    if brute_out[0] == "raise":
        return "UNREACHABLE"
    if solver_out[0] == "raise":
        return "RAISE"
    return f"V{solver_out[1]}"


def _generate_reachable_sample(n, seed):
    """Generate a deterministic sample of n unique reachable random arrays."""
    rng = random.Random(seed)
    sample, seen = [], set()
    attempts = 0
    while len(sample) < n and attempts < n * 10:
        attempts += 1
        size = rng.randint(2, 20)
        nums = [rng.randint(0, 5) for _ in range(size)]
        h = tuple(nums)
        if h in seen:
            continue
        seen.add(h)
        try:
            lc45_brute_force(nums)
            sample.append(nums)
        except Exception:
            pass
    return sample


class TestOracle(unittest.TestCase):
    def test_survivor_passes_all_oracle(self):
        for nums, claimed in ORACLE_CASES:
            if claimed == "unreachable":
                with self.assertRaises(Exception):
                    SURVIVOR(nums)
            else:
                self.assertEqual(
                    SURVIVOR(nums),
                    claimed,
                    f"SURVIVOR failed on {nums}: expected {claimed}, got {SURVIVOR(nums)}",
                )


class TestBuggyFailsOracle(unittest.TestCase):
    def test_each_buggy_fails_at_least_one_oracle_case(self):
        for solver in ALL_BUGGY:
            failures = 0
            for nums, claimed in ORACLE_CASES:
                b = _safe(lc45_brute_force, nums)
                s = _safe(solver, nums)
                if b[0] == "raise" and s[0] == "raise":
                    continue
                if b[0] == "raise" or s[0] == "raise":
                    failures += 1
                    continue
                if s[1] != b[1]:
                    failures += 1
            self.assertGreaterEqual(
                failures,
                1,
                f"{solver.__name__} passed all 5 oracle cases — failure class miscalibrated",
            )


class TestFailureClassInstantiation(unittest.TestCase):
    """Each BUGGY solver's failure is instantiated on a canonical case in the way
    its labeled failure class predicts."""

    def test_local_max_jump_horizon_naive(self):
        self.assertEqual(lc45_brute_force([2, 3, 1, 1, 4]), 2)
        self.assertEqual(lc45_naive_greedy([2, 3, 1, 1, 4]), 3)

    def test_local_value_horizon_max(self):
        self.assertEqual(lc45_brute_force([2, 1, 1, 1, 4]), 3)
        self.assertEqual(lc45_max_landing_value([2, 1, 1, 1, 4]), 4)

    def test_local_reach_horizon_farthest(self):
        self.assertEqual(lc45_brute_force([1, 1, 1, 1, 1]), 4)
        self.assertEqual(lc45_farthest_landing_path([1, 1, 1, 1, 1]), -1)

    def test_reachability_dead_end_overgeneralization_zero_panic(self):
        self.assertEqual(lc45_brute_force([2, 3, 0, 1, 4]), 2)
        self.assertEqual(lc45_zero_dead_end_panic([2, 3, 0, 1, 4]), -1)

    def test_reachability_boolean_count_confusion(self):
        self.assertEqual(lc45_brute_force([2, 3, 1, 1, 4]), 2)
        self.assertEqual(lc45_reachable_boolean_confusion([2, 3, 1, 1, 4]), 5)

    def test_bounded_transition_window_three_step_dp(self):
        # On [5,1,1,1,1,1,1,1,1,1]: truth=5, three_step_window_dp returns 7 (FAR-wrong).
        self.assertEqual(lc45_brute_force([5, 1, 1, 1, 1, 1, 1, 1, 1, 1]), 5)
        self.assertEqual(lc45_three_step_window_dp([5, 1, 1, 1, 1, 1, 1, 1, 1, 1]), 7)

    def test_counting_boundary_error_frontier(self):
        self.assertEqual(lc45_brute_force([1, 1, 1, 1]), 3)
        self.assertEqual(lc45_frontier_off_by_one([1, 1, 1, 1]), 4)

    def test_uniform_pattern_overgeneralizer_passes_on_uniform_fails_otherwise(self):
        self.assertEqual(lc45_brute_force([1, 1, 1, 1]), 3)
        self.assertEqual(lc45_uniform_formula_generalizer([1, 1, 1, 1]), 3)
        self.assertEqual(lc45_brute_force([1, 2, 3]), 2)
        self.assertEqual(lc45_uniform_formula_generalizer([1, 2, 3]), 1)

    def test_local_max_jump_horizon_first_window(self):
        self.assertEqual(lc45_brute_force([2, 1, 1, 1, 4]), 3)
        self.assertEqual(lc45_first_window_max_then_greedy([2, 1, 1, 1, 4]), 4)

    def test_first_window_distinct_from_max_value_on_canonical_case(self):
        # [1,3,1,1,1,4]: max_landing_value returns 5 (FAR), first_window returns 3 (SUCCESS).
        self.assertEqual(lc45_brute_force([1, 3, 1, 1, 1, 4]), 3)
        self.assertEqual(lc45_max_landing_value([1, 3, 1, 1, 1, 4]), 5)
        self.assertEqual(lc45_first_window_max_then_greedy([1, 3, 1, 1, 1, 4]), 3)


def _make_signatures(project_fn, sample, include_survivor=False):
    solvers = [SURVIVOR] + ALL_BUGGY if include_survivor else ALL_BUGGY
    sig = {}
    for solver in solvers:
        sig[solver.__name__] = [
            project_fn(_safe(solver, nums), _safe(lc45_brute_force, nums))
            for nums in sample
        ]
    return sig


def _make_observation_signatures(
    projection_level, project_fn, sample, include_survivor=False
):
    """Observation-substrate view of the per-sample classification.

    Returns: dict[solver_name -> list[Observation]]
    Each Observation wraps a single classification with explicit
    problem_id, candidate_id, projection_level, evaluation_layer, seed,
    sample_size. The multiset of observation.canonical_form[0] values must
    equal the multiset of classification strings produced by
    `_make_signatures` for the same projection.
    """
    solvers = [SURVIVOR] + ALL_BUGGY if include_survivor else ALL_BUGGY
    sig = {}
    for solver in solvers:
        observations = []
        for nums in sample:
            s_out = _safe(solver, nums)
            b_out = _safe(lc45_brute_force, nums)
            classification = project_fn(s_out, b_out)
            obs = from_brute_force(
                problem_id="lc45",
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
    """Under an operator, two solvers are 'dissolved' iff their operator-signatures
    are identical across the sample. This is a discriminability failure of the
    operator, not a behavioral claim about the solvers."""
    dissolved = []
    for i, s1 in enumerate(names):
        for s2 in names[i + 1 :]:
            if sig[s1] == sig[s2]:
                dissolved.append((s1, s2))
    return dissolved


class TestOperatorSensitivity(unittest.TestCase):
    """Pin the discriminability signature of the 4-projection operator on a
    fixed-seed random sample of reachable arrays.

    These tests assert operator behavior, not solver behavior. A change in
    the dissolved-pair set is an operator-sensitivity change, not a
    solver-property change.
    """

    P1_DISSOLVED_PAIR = {
        frozenset(("lc45_reachable_boolean_confusion", "lc45_frontier_off_by_one"))
    }

    @classmethod
    def setUpClass(cls):
        cls.sample = _generate_reachable_sample(RANDOM_SAMPLE_SIZE, RANDOM_SEED)
        assert len(cls.sample) == RANDOM_SAMPLE_SIZE, (
            f"Failed to generate {RANDOM_SAMPLE_SIZE} reachable arrays (got {len(cls.sample)})"
        )

    def test_sample_size(self):
        self.assertEqual(len(self.sample), RANDOM_SAMPLE_SIZE)

    def test_p1_dissolved_pair(self):
        sig = _make_signatures(_project_p1, self.sample)
        actual = {frozenset(p) for p in _find_dissolved_pairs(sig, BUGGY_NAMES)}
        self.assertEqual(
            actual,
            self.P1_DISSOLVED_PAIR,
            f"P1 dissolved-pair set changed. Operator sensitivity drifted. "
            f"Expected exactly {self.P1_DISSOLVED_PAIR}, got {actual}.",
        )

        obs_sig = _make_observation_signatures(1, _project_p1, self.sample)
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.problem_id, "lc45")
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 1)
                self.assertEqual(obs.evaluation_layer, "brute_force")
                self.assertEqual(obs.seed, RANDOM_SEED)
                self.assertEqual(obs.sample_size, RANDOM_SAMPLE_SIZE)
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                Counter(sig[name]),
                f"Observation canonical_form multiset diverges from string "
                f"signature for {name} under P1",
            )

    def test_p2_discriminability_preserved(self):
        sig = _make_signatures(_project_p2, self.sample)
        dissolved = _find_dissolved_pairs(sig, BUGGY_NAMES)
        self.assertEqual(
            dissolved,
            [],
            f"P2 lost discriminability. The pair(s) {dissolved} are no longer "
            f"distinguishable under the NEAR/FAR/UNREACHABLE projection.",
        )

        obs_sig = _make_observation_signatures(2, _project_p2, self.sample)
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.problem_id, "lc45")
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 2)
                self.assertEqual(obs.evaluation_layer, "brute_force")
                self.assertEqual(obs.seed, RANDOM_SEED)
                self.assertEqual(obs.sample_size, RANDOM_SAMPLE_SIZE)
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                Counter(sig[name]),
                f"Observation canonical_form multiset diverges from string "
                f"signature for {name} under P2",
            )

    def test_p3_discriminability_preserved(self):
        sig = _make_signatures(_project_p3, self.sample)
        dissolved = _find_dissolved_pairs(sig, BUGGY_NAMES)
        self.assertEqual(
            dissolved,
            [],
            f"P3 lost discriminability. The pair(s) {dissolved} are no longer "
            f"distinguishable under the SUCCESS/NEAR-wrong/FAR-wrong/UNREACHABLE projection.",
        )

        obs_sig = _make_observation_signatures(3, _project_p3, self.sample)
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.problem_id, "lc45")
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 3)
                self.assertEqual(obs.evaluation_layer, "brute_force")
                self.assertEqual(obs.seed, RANDOM_SEED)
                self.assertEqual(obs.sample_size, RANDOM_SAMPLE_SIZE)
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                Counter(sig[name]),
                f"Observation canonical_form multiset diverges from string "
                f"signature for {name} under P3",
            )

    def test_p4_discriminability_preserved(self):
        sig = _make_signatures(_project_p4, self.sample)
        dissolved = _find_dissolved_pairs(sig, BUGGY_NAMES)
        self.assertEqual(
            dissolved,
            [],
            f"P4 (value-level) lost discriminability. The pair(s) {dissolved} "
            f"now produce identical value-signatures across the sample.",
        )

        obs_sig = _make_observation_signatures(4, _project_p4, self.sample)
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.problem_id, "lc45")
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 4)
                self.assertEqual(obs.evaluation_layer, "brute_force")
                self.assertEqual(obs.seed, RANDOM_SEED)
                self.assertEqual(obs.sample_size, RANDOM_SAMPLE_SIZE)
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                Counter(sig[name]),
                f"Observation canonical_form multiset diverges from string "
                f"signature for {name} under P4",
            )

    def test_p1_dissolved_pair_resolved_by_p2(self):
        """The P1 dissolved pair has identical P1 signatures but distinct P2
        signatures. This documents that the loss-of-discriminability under P1
        is an operator property, not a behavioral equivalence of the solvers."""
        sig_p1 = _make_signatures(_project_p1, self.sample)
        sig_p2 = _make_signatures(_project_p2, self.sample)
        self.assertEqual(
            sig_p1["lc45_reachable_boolean_confusion"],
            sig_p1["lc45_frontier_off_by_one"],
        )
        self.assertNotEqual(
            sig_p2["lc45_reachable_boolean_confusion"],
            sig_p2["lc45_frontier_off_by_one"],
        )

        obs_p1 = _make_observation_signatures(1, _project_p1, self.sample)
        obs_p2 = _make_observation_signatures(2, _project_p2, self.sample)
        pair = ("lc45_reachable_boolean_confusion", "lc45_frontier_off_by_one")
        for obs in obs_p1[pair[0]] + obs_p1[pair[1]]:
            self.assertEqual(obs.projection_level, 1)
            self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(obs.problem_id, "lc45")
        for obs in obs_p2[pair[0]] + obs_p2[pair[1]]:
            self.assertEqual(obs.projection_level, 2)
            self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(obs.problem_id, "lc45")
        self.assertEqual(
            Counter(o.canonical_form[0] for o in obs_p1[pair[0]]),
            Counter(o.canonical_form[0] for o in obs_p1[pair[1]]),
        )
        self.assertNotEqual(
            Counter(o.canonical_form[0] for o in obs_p2[pair[0]]),
            Counter(o.canonical_form[0] for o in obs_p2[pair[1]]),
        )


class TestSurvivorDistinguishableFromBuggy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = _generate_reachable_sample(RANDOM_SAMPLE_SIZE, RANDOM_SEED)

    def test_survivor_does_not_dissolve_with_any_buggy_under_p1(self):
        sig = _make_signatures(_project_p1, self.sample, include_survivor=True)
        survivor_sig = sig[SURVIVOR.__name__]
        for name in BUGGY_NAMES:
            self.assertNotEqual(
                survivor_sig,
                sig[name],
                f"SURVIVOR dissolved with {name} under P1 — operator can no longer "
                f"separate SURVIVOR from this BUGGY under binary correctness.",
            )

        obs_sig = _make_observation_signatures(
            1, _project_p1, self.sample, include_survivor=True
        )
        for obs in obs_sig[SURVIVOR.__name__]:
            self.assertEqual(obs.candidate_id, SURVIVOR.__name__)
            self.assertEqual(obs.projection_level, 1)
            self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(obs.problem_id, "lc45")
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 1)
                self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                Counter(sig[name]),
            )

    def test_survivor_does_not_dissolve_with_any_buggy_under_p3(self):
        sig = _make_signatures(_project_p3, self.sample, include_survivor=True)
        survivor_sig = sig[SURVIVOR.__name__]
        for name in BUGGY_NAMES:
            self.assertNotEqual(
                survivor_sig,
                sig[name],
                f"SURVIVOR dissolved with {name} under P3 — operator can no longer "
                f"separate SURVIVOR from this BUGGY under ternary projection.",
            )

        obs_sig = _make_observation_signatures(
            3, _project_p3, self.sample, include_survivor=True
        )
        for obs in obs_sig[SURVIVOR.__name__]:
            self.assertEqual(obs.candidate_id, SURVIVOR.__name__)
            self.assertEqual(obs.projection_level, 3)
            self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(obs.problem_id, "lc45")
        for name in BUGGY_NAMES:
            for obs in obs_sig[name]:
                self.assertEqual(obs.candidate_id, name)
                self.assertEqual(obs.projection_level, 3)
                self.assertEqual(obs.evaluation_layer, "brute_force")
            self.assertEqual(
                Counter(o.canonical_form[0] for o in obs_sig[name]),
                Counter(sig[name]),
            )


if __name__ == "__main__":
    unittest.main()
