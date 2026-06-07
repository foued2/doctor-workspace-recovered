# doctor/adversarial/quotient.py
# Phase C-7: Response-Equivalence Quotient on `large_amount_stress`
#
# Implements the quotient construction operator on a restricted probe set
# under solver-response equivalence. The quotient collapses probes that
# produce identical response vectors across a given solver set.
#
# Pairs with PHASE_C7_SPEC.md (commit 779f9cb) and
# PHASE_C7_FREEZE.json (commit 06bbe40).
#
# No new estimators. No new probes. Infrastructure only.

from __future__ import annotations

from typing import Callable


def compute_quotient(
    probe_ids: list[str],
    pass_results: dict[str, dict[str, bool]],
    solver_ids: list[str] | None = None,
    probe_family: str = "large_amount_stress",
) -> list[dict]:
    """Compute equivalence classes of probes under solver-response equivalence.

    Two probes p, p' are equivalent iff for all s in solver_ids,
    R(s, p) = R(s, p'). The quotient is the set of equivalence classes.

    Args:
        probe_ids: list of probe IDs in the restricted set (e.g., family-3 probes).
        pass_results: dict {solver_id: {probe_id: pass_bool}}.
        solver_ids: optional list of solver IDs to restrict the equivalence
            relation (default: all solvers in pass_results, sorted).
        probe_family: probe_family to assign to each abstract probe
            (inherited from the original probes; default: 'large_amount_stress').

    Returns:
        list of equivalence classes, each a dict with:
            - 'member_probes': sorted list of probe IDs in the class
            - 'representative_probe_id': first member probe ID (sorted)
            - 'probe_family': inherited probe_family
            - 'response_vector': tuple of bools, one per solver in solver_ids order
        The list is sorted by representative_probe_id for determinism.
    """
    if solver_ids is None:
        solver_ids = sorted(pass_results.keys())

    classes_dict: dict[tuple, list[str]] = {}
    for pid in probe_ids:
        response = tuple(bool(pass_results[sid].get(pid, False)) for sid in solver_ids)
        classes_dict.setdefault(response, []).append(pid)

    quotient: list[dict] = []
    for response_vector, members in classes_dict.items():
        sorted_members = sorted(members)
        quotient.append({
            "member_probes": sorted_members,
            "representative_probe_id": sorted_members[0],
            "probe_family": probe_family,
            "response_vector": response_vector,
        })

    quotient.sort(key=lambda c: c["representative_probe_id"])
    return quotient


def quotient_size(quotient: list[dict]) -> int:
    """Return |T_P|, the number of equivalence classes in the quotient."""
    return len(quotient)


def apply_rule_to_quotient(
    rule: Callable,
    quotient: list[dict],
    pass_results: dict[str, dict[str, bool]],
    solver_ids: list[str] | None = None,
) -> dict[str, str]:
    """Apply a decision rule to each solver on the quotient population.

    The rule interface is the same as in prior phases:
        rule(obs_fails, n_obs, obs_records) -> "ACCEPT" | "REJECT"

    For the quotient:
        - n_obs = |T_P| (number of abstract probes)
        - obs_fails = number of abstract probes the solver fails
          (one abstract probe contributes 1 to obs_fails if any member
          probe in its class fails for this solver)
        - obs_records = list of records, one per abstract probe, with
          probe_id = representative_probe_id, pass_fail = the solver's
          response on that representative, and fingerprint_context
          containing probe_family

    Args:
        rule: callable (obs_fails, n_obs, obs_records) -> "ACCEPT" | "REJECT"
        quotient: list of equivalence classes (from compute_quotient)
        pass_results: dict {solver_id: {probe_id: pass_bool}}
        solver_ids: optional list of solver IDs (default: sorted keys of pass_results)

    Returns:
        dict {solver_id: "ACCEPT" | "REJECT"}
    """
    if solver_ids is None:
        solver_ids = sorted(pass_results.keys())

    n_obs = len(quotient)
    preds: dict[str, str] = {}
    for sid in solver_ids:
        solver_results = pass_results[sid]
        obs_fails = 0
        obs_records: list[dict] = []
        for c in quotient:
            rep_pid = c["representative_probe_id"]
            passed = bool(solver_results.get(rep_pid, False))
            if not passed:
                obs_fails += 1
            obs_records.append({
                "probe_id": rep_pid,
                "pass_fail": passed,
                "fingerprint_context": {"probe_family": c["probe_family"]},
            })
        preds[sid] = rule(obs_fails, n_obs, obs_records)

    return preds
