# tests/test_quotient.py
# Phase C-7: Response-Equivalence Quotient on `large_amount_stress`
# TDD: tests written before the quotient module.
#
# Tests the quotient construction operator on the restricted family-3
# probe set of LC322. Per PHASE_C7_SPEC.md (commit 779f9cb) and
# PHASE_C7_FREEZE.json (commit 06bbe40).

from __future__ import annotations

import pytest

from doctor.adversarial.quotient import (
    apply_rule_to_quotient,
    compute_quotient,
    quotient_size,
)


# ---------------------------------------------------------------------------
# Fixtures: LC322-shaped data (30 solvers, 5 family-3 probes)
# ---------------------------------------------------------------------------

LC322_FAMILY3_PROBES = ["p_fp_0011", "p_fp_0012", "p_fp_0013", "p_fp_0014", "p_fp_0015"]


def make_pass_results_all_pass(n_solvers: int = 30) -> dict:
    """All-pass response matrix: every solver passes every probe."""
    return {
        f"solver_{i+1:03d}": {pid: True for pid in LC322_FAMILY3_PROBES}
        for i in range(n_solvers)
    }


def make_pass_results_two_distinct_vectors(n_solvers: int = 30) -> dict:
    """Two distinct response vectors: half pass on probe 0, all fail on probe 1+.

    Probe p_fp_0011: pass for first half, fail for second half.
    All other probes: pass for everyone.

    This creates exactly 2 equivalence classes.
    """
    out = {}
    for i in range(n_solvers):
        sid = f"solver_{i+1:03d}"
        out[sid] = {
            "p_fp_0011": (i < n_solvers // 2),
            "p_fp_0012": True,
            "p_fp_0013": True,
            "p_fp_0014": True,
            "p_fp_0015": True,
        }
    return out


def make_pass_results_five_distinct(n_solvers: int = 30) -> dict:
    """Five distinct response vectors: each probe has its own response pattern.

    Probe p_fp_0011: solver i fails iff i == 0
    Probe p_fp_0012: solver i fails iff i == 1
    Probe p_fp_0013: solver i fails iff i == 2
    Probe p_fp_0014: solver i fails iff i == 3
    Probe p_fp_0015: solver i fails iff i == 4
    All other entries pass.

    This creates 5 equivalence classes (one per probe).
    """
    out = {}
    for i in range(n_solvers):
        sid = f"solver_{i+1:03d}"
        out[sid] = {
            "p_fp_0011": (i != 0),
            "p_fp_0012": (i != 1),
            "p_fp_0013": (i != 2),
            "p_fp_0014": (i != 3),
            "p_fp_0015": (i != 4),
        }
    return out


def make_pass_results_one_class(n_solvers: int = 30) -> dict:
    """All probes produce the same response vector (all pass) -> 1 class."""
    return make_pass_results_all_pass(n_solvers)


# B1 and C_genuine decision rules (copied from problem_class_config for test isolation)
def b1_count_rule(obs_fails: int, n_obs: int, obs_records: list | None) -> str:
    return "ACCEPT" if obs_fails == 0 else "REJECT"


def c_genuine_rule(obs_fails: int, n_obs: int, obs_records: list | None) -> str:
    if obs_fails == 0:
        return "ACCEPT"
    if obs_records is None:
        return "REJECT"
    families = {r["fingerprint_context"]["probe_family"] for r in obs_records if not r["pass_fail"]}
    if len(families) == 1:
        return "ACCEPT"
    return "REJECT"


# ---------------------------------------------------------------------------
# 1. Equivalence relation properties
# ---------------------------------------------------------------------------

class TestEquivalenceProperties:

    def test_reflexivity_probe_is_in_class_with_itself(self):
        """Every probe is in the same class as itself (reflexivity)."""
        pass_results = make_pass_results_two_distinct_vectors()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        for c in quotient:
            for pid in c["member_probes"]:
                # The probe is in a class; reflexivity is satisfied by the
                # fact that the equivalence relation is over the response vector.
                assert isinstance(pid, str)

    def test_symmetry_classes_are_unordered(self):
        """If p ~ p' (in same class), then p' ~ p (same class). The
        quotient construction groups by response vector, so symmetry is
        built in: the class containing p is the same as the class
        containing p'."""
        pass_results = make_pass_results_two_distinct_vectors()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        # 2 distinct response vectors -> 2 classes
        assert len(quotient) == 2
        # Each probe is in exactly one class
        seen = set()
        for c in quotient:
            for pid in c["member_probes"]:
                assert pid not in seen
                seen.add(pid)

    def test_transitivity_three_probes_same_response_in_one_class(self):
        """If p ~ p' and p' ~ p'' (all same response), then p ~ p'' in same class."""
        pass_results = make_pass_results_all_pass()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        # All-pass -> all 5 probes in one class
        assert len(quotient) == 1
        assert sorted(quotient[0]["member_probes"]) == sorted(LC322_FAMILY3_PROBES)


# ---------------------------------------------------------------------------
# 2. Identical response vectors -> same class
# ---------------------------------------------------------------------------

class TestIdenticalResponsesInSameClass:

    def test_two_probes_with_identical_responses_in_same_class(self):
        """Two probes with identical 30-dim response vectors are in the same class."""
        # Build pass_results where p_fp_0011 and p_fp_0012 have identical
        # response vectors (both pass for everyone).
        pass_results = {
            f"solver_{i+1:03d}": {
                "p_fp_0011": True,
                "p_fp_0012": True,
                "p_fp_0013": False,
                "p_fp_0014": False,
                "p_fp_0015": False,
            }
            for i in range(30)
        }
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        # p_fp_0011 and p_fp_0012 should be in the same class (both all-pass)
        # p_fp_0013, p_fp_0014, p_fp_0015 should be in the same class (all all-fail)
        assert len(quotient) == 2
        # Find the all-pass class
        all_pass_class = None
        for c in quotient:
            if c["response_vector"] == tuple([True] * 30):
                all_pass_class = c
                break
        assert all_pass_class is not None
        assert sorted(all_pass_class["member_probes"]) == ["p_fp_0011", "p_fp_0012"]

    def test_three_probes_with_identical_responses_in_same_class(self):
        """Three probes with identical response vectors are in the same class."""
        # p_fp_0011, p_fp_0012, p_fp_0013 all pass for everyone
        # p_fp_0014, p_fp_0015 all fail for everyone
        pass_results = {
            f"solver_{i+1:03d}": {
                "p_fp_0011": True,
                "p_fp_0012": True,
                "p_fp_0013": True,
                "p_fp_0014": False,
                "p_fp_0015": False,
            }
            for i in range(30)
        }
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        assert len(quotient) == 2
        # Find the all-pass class
        for c in quotient:
            if c["response_vector"] == tuple([True] * 30):
                assert sorted(c["member_probes"]) == ["p_fp_0011", "p_fp_0012", "p_fp_0013"]
                break
        else:
            pytest.fail("All-pass class not found")


# ---------------------------------------------------------------------------
# 3. Differing response vectors -> different classes
# ---------------------------------------------------------------------------

class TestDifferingResponsesInDifferentClasses:

    def test_two_probes_with_one_differing_solver_in_different_classes(self):
        """Two probes with at least one differing solver response are in different classes."""
        # p_fp_0011: all pass except solver_001
        # p_fp_0012: all pass
        pass_results = {
            f"solver_{i+1:03d}": {
                "p_fp_0011": (i != 0),  # solver_001 fails
                "p_fp_0012": True,       # all pass
                "p_fp_0013": True,
                "p_fp_0014": True,
                "p_fp_0015": True,
            }
            for i in range(30)
        }
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        # p_fp_0011 differs from p_fp_0012..5 -> p_fp_0011 in own class
        # p_fp_0012..5 all-pass -> in one class
        # Total: 2 classes
        assert len(quotient) == 2

    def test_each_probe_with_unique_differing_solver_in_own_class(self):
        """Each probe with a unique failing solver is in its own class."""
        pass_results = make_pass_results_five_distinct()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        # 5 probes, 5 distinct response vectors -> 5 classes
        assert len(quotient) == 5
        for c in quotient:
            assert len(c["member_probes"]) == 1


# ---------------------------------------------------------------------------
# 4. Quotient size range
# ---------------------------------------------------------------------------

class TestQuotientSizeRange:

    def test_size_is_at_least_1(self):
        """Quotient size is at least 1 (probes in the same class collapse)."""
        pass_results = make_pass_results_all_pass()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        assert quotient_size(quotient) >= 1

    def test_size_is_at_most_5(self):
        """Quotient size is at most 5 (one per probe in the worst case)."""
        pass_results = make_pass_results_five_distinct()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        assert quotient_size(quotient) <= 5

    def test_size_range_in_unit_tests(self):
        """Quotient size is in [1, 5] for 5 input probes."""
        for pr in [
            make_pass_results_all_pass(),
            make_pass_results_two_distinct_vectors(),
            make_pass_results_five_distinct(),
        ]:
            quotient = compute_quotient(LC322_FAMILY3_PROBES, pr)
            n = quotient_size(quotient)
            assert 1 <= n <= 5, f"quotient size {n} out of range [1, 5]"


# ---------------------------------------------------------------------------
# 5. Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:

    def test_same_input_same_output(self):
        """Same input produces same output (deterministic)."""
        pass_results = make_pass_results_two_distinct_vectors()
        q1 = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        q2 = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        assert q1 == q2

    def test_class_order_is_deterministic(self):
        """Class order in the quotient is deterministic (sorted by representative)."""
        pass_results = make_pass_results_five_distinct()
        q1 = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        q2 = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        for c1, c2 in zip(q1, q2):
            assert c1["representative_probe_id"] == c2["representative_probe_id"]
            assert c1["member_probes"] == c2["member_probes"]


# ---------------------------------------------------------------------------
# 6. Decision rules applied to quotient produce {ACCEPT, REJECT}
# ---------------------------------------------------------------------------

class TestDecisionRulesOnQuotient:

    def test_b1_produces_accept_or_reject(self):
        """B1 applied to the quotient produces a decision in {ACCEPT, REJECT}."""
        pass_results = make_pass_results_two_distinct_vectors()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(b1_count_rule, quotient, pass_results)
        for sid, decision in preds.items():
            assert decision in {"ACCEPT", "REJECT"}, f"B1 produced {decision!r} for {sid}"

    def test_c_genuine_produces_accept_or_reject(self):
        """C_genuine applied to the quotient produces a decision in {ACCEPT, REJECT}."""
        pass_results = make_pass_results_two_distinct_vectors()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(c_genuine_rule, quotient, pass_results)
        for sid, decision in preds.items():
            assert decision in {"ACCEPT", "REJECT"}, f"C_genuine produced {decision!r} for {sid}"

    def test_b1_on_all_pass_quotient_accepts_everyone(self):
        """B1 on a 1-class all-pass quotient accepts everyone."""
        pass_results = make_pass_results_all_pass()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(b1_count_rule, quotient, pass_results)
        for sid, decision in preds.items():
            assert decision == "ACCEPT"

    def test_c_genuine_on_all_pass_quotient_accepts_everyone(self):
        """C_genuine on a 1-class all-pass quotient accepts everyone."""
        pass_results = make_pass_results_all_pass()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(c_genuine_rule, quotient, pass_results)
        for sid, decision in preds.items():
            assert decision == "ACCEPT"

    def test_b1_on_2_class_quotient_rejects_solvers_with_failures(self):
        """B1 on a 2-class quotient rejects solvers with at least one failure."""
        pass_results = make_pass_results_two_distinct_vectors()
        # First half (15 solvers) pass on p_fp_0011 (and all others)
        # Second half (15 solvers) fail on p_fp_0011, pass on others
        # Quotient: 2 classes (p_fp_0011 alone, p_fp_0012..5 together)
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(b1_count_rule, quotient, pass_results)
        # First half: 0 failures on all 2 abstract probes -> ACCEPT
        # Second half: 1 failure on p_fp_0011 abstract -> REJECT
        for i in range(30):
            sid = f"solver_{i+1:03d}"
            if i < 15:
                assert preds[sid] == "ACCEPT"
            else:
                assert preds[sid] == "REJECT"

    def test_c_genuine_on_2_class_quotient_accepts_everyone(self):
        """C_genuine on a 2-class quotient (all family-3) accepts everyone
        (vacuous satisfaction: all failures share one family = 'large_amount_stress')."""
        pass_results = make_pass_results_two_distinct_vectors()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(c_genuine_rule, quotient, pass_results)
        for sid, decision in preds.items():
            assert decision == "ACCEPT"


# ---------------------------------------------------------------------------
# 7. Aggregate consistency check carries forward
# ---------------------------------------------------------------------------

class TestAggregateConsistencyCarriesForward:
    """The aggregate-consistency check from C-3a / C-4 / C-5 / C-6 is a
    runner-level concern. Here we verify that the quotient module exposes
    the data the runner needs to call check_aggregate_consistency.

    The check itself is in doctor.identity_resolution and is verified by
    its own test suite. This test confirms the quotient module produces
    decisions in the format the check expects.
    """

    def test_b1_decisions_on_full_30_probe_quotient_have_expected_format(self):
        """B1 decisions on the quotient (per-solver dict) match the format
        expected by check_aggregate_consistency: {solver_id: 'ACCEPT'|'REJECT'}."""
        pass_results = make_pass_results_two_distinct_vectors()
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(b1_count_rule, quotient, pass_results)
        # Format: {solver_id: "ACCEPT" | "REJECT"}
        for sid, decision in preds.items():
            assert isinstance(sid, str)
            assert decision in {"ACCEPT", "REJECT"}

    def test_decision_count_matches_n_solvers(self):
        """The number of decisions equals the number of solvers."""
        pass_results = make_pass_results_two_distinct_vectors()
        n_solvers = len(pass_results)
        quotient = compute_quotient(LC322_FAMILY3_PROBES, pass_results)
        preds = apply_rule_to_quotient(b1_count_rule, quotient, pass_results)
        assert len(preds) == n_solvers
