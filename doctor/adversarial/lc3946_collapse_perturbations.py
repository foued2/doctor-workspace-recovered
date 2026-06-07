"""LC3946-C5 perturbation module.

Implements the pre-declared P1, P2, P3, P4 perturbations from
PHASE_LC3946_C5_FREEZE.json, plus the falsification criterion, the
aggregate consistency check, and the gap function.

All exported functions and constants are tested in
tests/test_lc3946_c5_perturbations.py.

Per the LC3946-C5 spec (Step 3, protocol):
- No new estimators, no new decision rules, no new probes, no new
  solver packs
- The pre-declared P2 subsample index lists and P3 rotation order
  are frozen
- The C_genuine and B1 decision rules are reused from
  doctor/adversarial/problem_class_config.py (no duplication)
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Pre-declared constants (from PHASE_LC3946_C5_FREEZE.json)
# ---------------------------------------------------------------------------

P1A_THRESHOLD: float = 0.05
P1B_THRESHOLD: float = 0.10
P1C_THRESHOLD: float = 0.20

P2A_INDICES: list[int] = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
    20, 21, 22, 23, 24,
]

P2B_INDICES: list[int] = [
    5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
    25, 26, 27, 28, 29,
]

P2C_INDICES: list[int] = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
    25, 26, 27, 28, 29,
]

P3_ROTATION_ORDER: list[str] = [
    "poset_universal_source",
    "poset_chain",
    "poset_antichain",
    "poset_lattice_boolean",
    "poset_lattice_two_prime",
    "poset_isolated",
]

LC322_C4_RESULT_GAP: float = 8.30

RECOVERED_SOLVER_ID: str = "solver_016"


# ---------------------------------------------------------------------------
# P1 — Threshold shift
# ---------------------------------------------------------------------------

def threshold_shift(
    pass_results: dict[str, dict[str, bool]],
    target_ids: list[str],
    failure_threshold: float,
) -> dict[str, dict[str, Any]]:
    """Re-derive ground truth labels with the given failure_threshold.

    For each solver, heldout_fail_rate = (count of not pass_results[sid][pid]
    for pid in target_ids) / len(target_ids). truth_label = "REJECT" if
    rate >= failure_threshold else "ACCEPT".

    Args:
        pass_results: dict mapping solver_id to {probe_id: pass_bool}.
        target_ids: list of probe_ids used to derive ground truth.
        failure_threshold: the failure rate threshold (e.g. 0.05, 0.10, 0.20).

    Returns:
        dict mapping solver_id to {truth_label, heldout_fails, heldout_n,
        heldout_fail_rate}.
    """
    ground: dict[str, dict[str, Any]] = {}
    n = len(target_ids)
    for sid, probe_results in pass_results.items():
        heldout_fails = sum(1 for pid in target_ids if not probe_results.get(pid, False))
        heldout_fail_rate = heldout_fails / n if n else 0.0
        truth_label = "REJECT" if heldout_fail_rate > failure_threshold else "ACCEPT"
        ground[sid] = {
            "truth_label": truth_label,
            "heldout_fails": heldout_fails,
            "heldout_n": n,
            "heldout_fail_rate": heldout_fail_rate,
        }
    return ground


# ---------------------------------------------------------------------------
# P2 — Solver subsample
# ---------------------------------------------------------------------------

def solver_subsample(
    pass_results: dict[str, dict[str, bool]],
    indices_zero_indexed: list[int],
) -> dict[str, dict[str, bool]]:
    """Filter pass_results to keep only solvers at the given 0-indexed
    positions in the sorted solver_id order.

    Args:
        pass_results: dict mapping solver_id to per-probe results.
        indices_zero_indexed: list of 0-indexed positions in sorted solver_id
            order. E.g. P2A_INDICES = [0..24] keeps solver_001..solver_025.

    Returns:
        filtered pass_results dict.
    """
    sorted_ids = sorted(pass_results.keys())
    keep = {sorted_ids[i] for i in indices_zero_indexed if 0 <= i < len(sorted_ids)}
    return {sid: pass_results[sid] for sid in keep}


# ---------------------------------------------------------------------------
# P3 — Probe family knockout
# ---------------------------------------------------------------------------

def family_knockout(
    observed_ids: list[str],
    target_ids: list[str],
    family_to_knock_out: str,
    probe_index: dict,
) -> tuple[list[str], list[str]]:
    """Remove all probes in the given family from both observed and target sets.

    The family assignment is read from the probe_index (each probe's
    ``family`` key).

    Args:
        observed_ids: list of observed probe_ids.
        target_ids: list of target (held-out) probe_ids.
        family_to_knock_out: the family name to remove.
        probe_index: dict with ``probes`` key, each entry has ``probe_id``
            and ``family`` keys.

    Returns:
        (observed_ids_reduced, target_ids_reduced) with family probes removed.

    Raises:
        ValueError: if the family is not present in the probe_index.
    """
    family_probes: set[str] = set()
    for probe in probe_index.get("probes", []):
        if probe.get("family") == family_to_knock_out:
            family_probes.add(probe.get("probe_id"))

    if not family_probes:
        raise ValueError(
            f"Unknown family {family_to_knock_out!r} in probe_index "
            f"(no probes with this family found)"
        )

    obs_reduced = [pid for pid in observed_ids if pid not in family_probes]
    target_reduced = [pid for pid in target_ids if pid not in family_probes]
    return obs_reduced, target_reduced


# ---------------------------------------------------------------------------
# P4 — Cross-population reference (read-only anchor)
# ---------------------------------------------------------------------------

def cross_population_reference() -> dict[str, Any]:
    """Return the LC322 C-4 result as the cross-population anchor.

    P4 is a read-only anchor for the LC3946-C5 spec. It does not apply
    any perturbation to the LC3946 population.

    Returns:
        dict with lc322_c4_gap, lc322_c4_signal_family, and
        lc3946_perturbation_applied (= False).
    """
    return {
        "lc322_c4_gap": LC322_C4_RESULT_GAP,
        "lc322_c4_signal_family": "large_amount_stress",
        "lc322_c5_verdict": "PARTIALLY_SURVIVES",
        "lc3946_perturbation_applied": False,
    }


# ---------------------------------------------------------------------------
# Gap and falsification
# ---------------------------------------------------------------------------

def compute_gap(b1_loss: float, c_genuine_loss: float) -> float:
    """Compute the gap = B1_loss - C_genuine_loss.

    gap > 0 means C_genuine beats B1; gap = 0 means tie; gap < 0 means
    C_genuine is worse.
    """
    return b1_loss - c_genuine_loss


def falsification_criterion(per_perturbation_gaps: dict[str, float]) -> str:
    """Classify per-perturbation gap behavior.

    Args:
        per_perturbation_gaps: dict mapping perturbation_name to gap value.
            Must have exactly 11 entries (P1b, P1c, P2a, P2b, P2c, P3a..P3f).

    Returns:
        "SURVIVES" if all gaps > 0
        "PARTIALLY_SURVIVES" if some > 0 and some <= 0
        "DOES_NOT_SURVIVE" if all <= 0

    Raises:
        ValueError: if the dict does not have exactly 11 entries.
    """
    if len(per_perturbation_gaps) != 11:
        raise ValueError(
            f"falsification_criterion requires exactly 11 perturbation conditions, "
            f"got {len(per_perturbation_gaps)}"
        )
    gaps = list(per_perturbation_gaps.values())
    if all(g > 0 for g in gaps):
        return "SURVIVES"
    if all(g <= 0 for g in gaps):
        return "DOES_NOT_SURVIVE"
    return "PARTIALLY_SURVIVES"


# ---------------------------------------------------------------------------
# Aggregate consistency check
# ---------------------------------------------------------------------------

def _apply_policy(
    policy,
    pass_results: dict[str, dict[str, bool]],
    observed_ids: list[str],
    probe_index: dict | None,
) -> dict[str, str]:
    """Apply a policy to pass_results and return {solver_id: ACCEPT|REJECT}.

    Mirrors the runner's apply_estimator function (line 187-225 of
    runners/run_midweather_fingerprint_lc322.py).
    """
    preds: dict[str, str] = {}
    n_obs = len(observed_ids)
    probe_by_id: dict[str, dict] = (
        {p["probe_id"]: p for p in probe_index.get("probes", [])}
        if probe_index else {}
    )
    for sid, probe_results in pass_results.items():
        obs_fails = sum(1 for pid in observed_ids if not probe_results.get(pid, False))
        obs_records: list[dict] | None = None
        if probe_by_id:
            obs_records = [
                {
                    "probe_id": pid,
                    "pass_fail": probe_results.get(pid, False),
                    "fingerprint_context": _probe_to_fingerprint_context(probe_by_id[pid]),
                }
                for pid in observed_ids
            ]
        preds[sid] = policy(obs_fails, n_obs, obs_records)
    return preds


def _probe_to_fingerprint_context(probe: dict) -> dict:
    """Translate a raw probe_index entry to fingerprint_context schema.

    Inlined from run_midweather_fingerprint_lc322.py (line 171-184).
    """
    return {
        "axis": probe.get("axis"),
        "probe_family": probe.get("family"),
        "deformation_level": probe.get("deformation_level"),
        "paired_probe_id": probe.get("paired_probe_id"),
        "expected_invariant": probe.get("expected_invariant"),
    }


def aggregate_consistency_check(
    pass_results: dict[str, dict[str, bool]],
    observed_ids: list[str],
    target_ids: list[str],
    failure_threshold: float,
    expected_b1_wa_wr_loss: tuple[int, int, float],
    expected_c_genuine_wa_wr_loss: tuple[int, int, float],
    probe_index: dict | None = None,
) -> bool:
    """Re-run B1 and C_genuine on the unperturbed population and verify
    that (WA, WR, loss) match the expected values.

    Args:
        pass_results: dict mapping solver_id to {probe_id: pass_bool}.
        observed_ids: list of probe_ids used as the K-observation budget
            input to the estimators.
        target_ids: list of probe_ids used to derive ground truth labels
            (must be disjoint from observed_ids in production use).
        failure_threshold: threshold for deriving truth labels.
        expected_b1_wa_wr_loss: expected (wrong_accepts, wrong_rejects,
            decision_loss) for B1.
        expected_c_genuine_wa_wr_loss: expected (wrong_accepts, wrong_rejects,
            decision_loss) for C_genuine.
        probe_index: optional probe_index dict for fingerprint_context. If
            None, C_genuine falls back to B1 behavior.

    Returns:
        True if both B1 and C_genuine match their expected (WA, WR, loss).
        False otherwise.
    """
    from doctor.adversarial.problem_class_config import (
        _fail_count_policy,
        _c_genuine_policy,
    )

    b1_preds = _apply_policy(_fail_count_policy, pass_results, observed_ids, probe_index)
    cg_preds = _apply_policy(_c_genuine_policy, pass_results, observed_ids, probe_index)

    ground = threshold_shift(pass_results, target_ids, failure_threshold)

    def _compute_wa_wr_loss(preds: dict[str, str]) -> tuple[int, int, float]:
        wa = 0
        wr = 0
        for sid, pred in preds.items():
            truth = ground[sid]["truth_label"]
            if pred == "ACCEPT" and truth == "REJECT":
                wa += 1
            elif pred == "REJECT" and truth == "ACCEPT":
                wr += 1
        return wa, wr, float(wa + wr)

    actual_b1 = _compute_wa_wr_loss(b1_preds)
    actual_cg = _compute_wa_wr_loss(cg_preds)

    return actual_b1 == expected_b1_wa_wr_loss and actual_cg == expected_c_genuine_wa_wr_loss
