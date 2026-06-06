"""Tests for the ``apply_estimator`` signature extension.

Verifies:
- Backward compatibility: the 8 estimator policies (B0..B6, C) produce
  identical preds with or without ``obs_records``.
- Schema: ``obs_records`` is in ``fingerprint_context`` shape
  (``probe_family`` not raw ``family``), matching
  ``midweather_fingerprint_features.encode_raw_tensor``.
- New: a feature-aware policy can read ``obs_records`` and discriminate.
"""
from __future__ import annotations

from runners.run_midweather_fingerprint_lc322 import (
    _probe_to_fingerprint_context,
    apply_estimator,
)
from doctor.adversarial.problem_class_config import (
    LC322_ESTIMATOR_POLICIES,
    LC45_ESTIMATOR_POLICIES,
)


SAMPLE_PROBE_INDEX = {
    "probes": [
        {
            "probe_id": "p1",
            "axis": "reachability",
            "family": "reachability_counterfactual",
            "deformation_level": 0,
            "paired_probe_id": "p2",
            "expected_invariant": "reachable",
        },
        {
            "probe_id": "p2",
            "axis": "order",
            "family": "non_canonical_coin_order",
            "deformation_level": 1,
            "paired_probe_id": "p1",
            "expected_invariant": "greedy_breaks",
        },
    ]
}
OBSERVED_IDS = ["p1", "p2"]
# pass_results includes a held-out target probe (t1) to verify the runner
# does not leak target context into obs_records.
PASS_RESULTS = {
    "s1": {"p1": True,  "p2": True,  "t1": False},
    "s2": {"p1": False, "p2": True,  "t1": True},
    "s3": {"p1": False, "p2": False, "t1": False},
}


def test_probe_to_fingerprint_context_renames_family_to_probe_family():
    """The only rename is family -> probe_family; other 4 keys pass through."""
    ctx = _probe_to_fingerprint_context(SAMPLE_PROBE_INDEX["probes"][0])
    assert ctx == {
        "axis": "reachability",
        "probe_family": "reachability_counterfactual",
        "deformation_level": 0,
        "paired_probe_id": "p2",
        "expected_invariant": "reachable",
    }
    assert "family" not in ctx


def test_apply_estimator_backward_compat_lc322_policies():
    """The 8 C-1 LC322 policies produce identical preds with or without obs_records.

    C_genuine is excluded: it intentionally uses obs_records (Phase C-4).
    See test_c_genuine_intentionally_breaks_backward_compat below.
    """
    c1_estimators = [e for e in LC322_ESTIMATOR_POLICIES if e != "C_genuine"]
    assert len(c1_estimators) == 8
    for est in c1_estimators:
        policy = LC322_ESTIMATOR_POLICIES[est]
        preds_without = apply_estimator(policy, PASS_RESULTS, OBSERVED_IDS)
        preds_with = apply_estimator(policy, PASS_RESULTS, OBSERVED_IDS, SAMPLE_PROBE_INDEX)
        assert preds_without == preds_with, (
            f"LC322.{est}: backward-compat broke: {preds_without!r} != {preds_with!r}"
        )


def test_apply_estimator_backward_compat_lc45_policies():
    """The 8 C-1 LC45 policies produce identical preds with or without obs_records.

    C_genuine is excluded: it intentionally uses obs_records (Phase C-4).
    See test_c_genuine_intentionally_breaks_backward_compat below.
    """
    c1_estimators = [e for e in LC45_ESTIMATOR_POLICIES if e != "C_genuine"]
    assert len(c1_estimators) == 8
    for est in c1_estimators:
        policy = LC45_ESTIMATOR_POLICIES[est]
        preds_without = apply_estimator(policy, PASS_RESULTS, OBSERVED_IDS)
        preds_with = apply_estimator(policy, PASS_RESULTS, OBSERVED_IDS, SAMPLE_PROBE_INDEX)
        assert preds_without == preds_with, (
            f"LC45.{est}: backward-compat broke: {preds_without!r} != {preds_with!r}"
        )


def test_c_genuine_intentionally_breaks_backward_compat():
    """C_genuine must produce different preds with obs_records than without.

    This is the defining property of a genuine structured policy (Phase C-4).
    If C_genuine produces identical preds with and without obs_records, it
    has collapsed to B1 behavior and the C-4 experiment cannot produce D > 0.
    """
    c_genuine = LC322_ESTIMATOR_POLICIES["C_genuine"]
    preds_without = apply_estimator(c_genuine, PASS_RESULTS, OBSERVED_IDS)
    preds_with = apply_estimator(c_genuine, PASS_RESULTS, OBSERVED_IDS, SAMPLE_PROBE_INDEX)
    assert preds_without != preds_with, (
        f"C_genuine must differ with vs. without obs_records; got identical: {preds_without!r}"
    )


def test_apply_estimator_obs_records_schema():
    """obs_records has fingerprint_context shape, one entry per observed probe only."""
    captured: list[list[dict]] = []

    def capture(obs_fails, n_obs, obs_records=None):
        captured.append(obs_records)
        return "ACCEPT"

    apply_estimator(capture, PASS_RESULTS, OBSERVED_IDS, SAMPLE_PROBE_INDEX)
    records = captured[0]
    assert records is not None
    assert len(records) == len(OBSERVED_IDS), (
        f"expected {len(OBSERVED_IDS)} records, got {len(records)}"
    )
    for r in records:
        assert set(r.keys()) == {"probe_id", "pass_fail", "fingerprint_context"}
        ctx = r["fingerprint_context"]
        assert set(ctx.keys()) == {
            "axis", "probe_family", "deformation_level",
            "paired_probe_id", "expected_invariant",
        }, f"fingerprint_context keys wrong: {sorted(ctx.keys())}"
        assert "family" not in ctx, f"raw 'family' leaked into fingerprint_context: {ctx}"


def test_apply_estimator_obs_records_excludes_target_probes():
    """obs_records must contain only observed probe ids, never target ids."""
    captured: list[list[dict]] = []

    def capture(obs_fails, n_obs, obs_records=None):
        captured.append(obs_records)
        return "ACCEPT"

    apply_estimator(capture, PASS_RESULTS, OBSERVED_IDS, SAMPLE_PROBE_INDEX)
    pids = {r["probe_id"] for r in captured[0]}
    assert pids == set(OBSERVED_IDS)
    assert "t1" not in pids


def test_apply_estimator_feature_aware_policy_can_discriminate():
    """A new policy can read obs_records to make a different decision than obs_fails alone."""

    def family_rejects_on_order(obs_fails, n_obs, obs_records=None):
        # Reject if any observed probe has axis == 'order' (s2 and s3 see p2 with order).
        if obs_records and any(
            r["fingerprint_context"]["axis"] == "order" for r in obs_records
        ):
            return "REJECT"
        return "ACCEPT"

    preds = apply_estimator(
        family_rejects_on_order, PASS_RESULTS, OBSERVED_IDS, SAMPLE_PROBE_INDEX
    )
    assert all(p == "REJECT" for p in preds.values()), (
        f"feature-aware policy should REJECT all (order probe present): {preds!r}"
    )

    # Same policy called WITHOUT obs_records: should ACCEPT all (no axis info).
    preds_no_ctx = apply_estimator(family_rejects_on_order, PASS_RESULTS, OBSERVED_IDS)
    assert all(p == "ACCEPT" for p in preds_no_ctx.values()), (
        f"feature-aware policy without obs_records should ACCEPT all: {preds_no_ctx!r}"
    )
