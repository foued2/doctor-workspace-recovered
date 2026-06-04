"""Per-problem-class adapter slots for the Midweather-Fingerprint-Gate kernel.

The 6 hard couplings identified in docs/GENERALIZATION_CONTRACT.md sec 4 are
exposed as adapter slots here. Each slot has a default that reproduces the
LC322 behavior. For a new problem class (e.g. LC45), pass a different value
or register a new problem_class entry.

The 6 slots are:
  1. oracle                       (per-problem ground truth)
  2. probe_to_solver_input        (per-problem probe -> solver-input adapter)
  3. solver_entry_point           (per-problem entry-point function name)
  4. estimator_names + policies   (per-problem estimator set + per-estimator policy)
  5. fingerprint_axes             (per-problem axis set, cross-checked vs probe_index)
  6. raw_tensor_encoder           (per-problem feature encoder)

Design principle: the LC322 defaults reproduce the current
midweather_fingerprint_features.py + run_midweather_fingerprint_lc322.py
behavior exactly. LC45 stub is provided with some slots using the LC322
default (until Week 3+ designs the LC45-specific implementations).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Slot 1: Oracle
# ---------------------------------------------------------------------------

def _lc322_oracle_factory() -> Callable[[list], int]:
    """Returns a function that computes LC322 ground truth from a solver input.

    Convention: solver input is [*coins, amount]. The oracle unpacks.
    """
    from doctor.adversarial.lc322_ground_truth import lc322_brute_force
    def _oracle(solver_input: list) -> int:
        coins = list(solver_input[:-1])
        amount = int(solver_input[-1])
        return lc322_brute_force(coins, amount)
    return _oracle


def _lc45_oracle_factory() -> Callable[[list], int]:
    """Returns a function that computes LC45 ground truth from a solver input.

    Convention: solver input is nums (the full list).
    """
    from doctor.adversarial.lc45_ground_truth import lc45_brute_force
    def _oracle(solver_input: list) -> int:
        return lc45_brute_force(list(solver_input))
    return _oracle


# ---------------------------------------------------------------------------
# Slot 2: Probe-to-solver-input adapter
# ---------------------------------------------------------------------------

def lc322_probe_to_solver_input(probe: dict) -> list:
    """LC322 probe format: {coins: [...], amount: int}. Solver input: [*coins, amount]."""
    return [*list(probe["coins"]), int(probe["amount"])]


def lc45_probe_to_solver_input(probe: dict) -> list:
    """LC45 probe format: {nums: [...]}. Solver input: nums (verbatim)."""
    return list(probe["nums"])


# ---------------------------------------------------------------------------
# Slot 3: Solver entry-point name
# ---------------------------------------------------------------------------

LC322_SOLVER_ENTRY_POINT: str = "solve"
LC45_SOLVER_ENTRY_POINT: str = "solve"  # assumes a wrapper or in-place rename of LC45 candidates


# ---------------------------------------------------------------------------
# Slot 4: Estimator set + per-estimator policies
# ---------------------------------------------------------------------------

LC322_ESTIMATOR_NAMES: list[str] = [
    "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
    "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
    "B6_regularized_raw_tensor", "C_structured_fingerprint",
]


def _b0_prior_policy(obs_fails: int, n_obs: int) -> str:
    return "ACCEPT"  # all-ACCEPT degenerate


def _fail_count_policy(obs_fails: int, n_obs: int) -> str:
    return "ACCEPT" if obs_fails == 0 else "REJECT"


def _b4_raw_full_tensor_policy(obs_fails: int, n_obs: int) -> str:
    return "REJECT"  # all-REJECT degenerate


def _b5_nn_policy(obs_fails: int, n_obs: int) -> str:
    return "ACCEPT"  # all-ACCEPT degenerate


def _b6_reg_policy(obs_fails: int, n_obs: int) -> str:
    return "ACCEPT"  # all-ACCEPT degenerate


LC322_ESTIMATOR_POLICIES: dict[str, Callable[[int, int], str]] = {
    "B0_prior": _b0_prior_policy,
    "B1_count": _fail_count_policy,
    "B2_calibrated_count": _fail_count_policy,
    "B3_raw_pf_vector": _fail_count_policy,
    "B4_raw_full_tensor": _b4_raw_full_tensor_policy,
    "B5_nearest_neighbor_raw_tensor": _b5_nn_policy,
    "B6_regularized_raw_tensor": _b6_reg_policy,
    "C_structured_fingerprint": _fail_count_policy,
}


# ---------------------------------------------------------------------------
# Slot 5: Fingerprint axes (declared; runtime value comes from probe_index)
# ---------------------------------------------------------------------------

LC322_FINGERPRINT_AXES: list[str] = [
    "reachability", "order", "magnitude", "boundary", "transition", "memoization",
]
LC45_FINGERPRINT_AXES: list[str] = [
    "naive_max_jump_suboptimal", "single_large_jump_decoy",
    "greedy_horizon_collapse", "naive_max_jump_dead_landing",
    "uniform_jump_array", "greedy_frontier_valid_no_false_pressure",
]


# ---------------------------------------------------------------------------
# Slot 6: Raw tensor encoder (per-problem feature vector)
# ---------------------------------------------------------------------------

def lc322_raw_tensor_encoder(obs_rows: list[dict]) -> dict[str, list[float]]:
    """LC322's 6-feature encoder. Returns {solver_id: [pf, deformation, axis, family, paired, invariant]}.

    Reproduces the body of encode_raw_tensor() in midweather_fingerprint_features.py.
    """
    out: dict[str, list[float]] = {}
    for row in obs_rows:
        sid = str(row["solver_id"])
        pf = 1.0 if row.get("pass_fail") else 0.0
        ctx = row.get("fingerprint_context", {})
        deformation = float(ctx.get("deformation_level", 0))
        axis_val = 1.0 if ctx.get("axis") else 0.0
        family_val = 1.0 if ctx.get("probe_family") else 0.0
        paired = 1.0 if ctx.get("paired_probe_id") else 0.0
        invariant = 1.0 if ctx.get("expected_invariant") else 0.0
        out.setdefault(sid, []).extend([pf, deformation, axis_val, family_val, paired, invariant])
    for sid in out:
        out[sid] = out[sid][:6]
    return out


def lc45_raw_tensor_encoder(obs_rows: list[dict]) -> dict[str, list[float]]:
    """LC45 stub encoder. Returns 6-dim feature vector per solver (padded with zeros).

    Full LC45 feature design is Week 3+ deliverable. For now, encodes the
    pass/fail flag padded to 6 dimensions to keep the slot's contract
    uniform across problem classes.
    """
    out: dict[str, list[float]] = {}
    for row in obs_rows:
        sid = str(row["solver_id"])
        pf = 1.0 if row.get("pass_fail") else 0.0
        out.setdefault(sid, []).append(pf)
    for sid in out:
        out[sid] = (out[sid] + [0.0] * 6)[:6]
    return out


# ---------------------------------------------------------------------------
# ProblemClassConfig + factory
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProblemClassConfig:
    """The 6 adapter slots for a single problem class."""
    problem_id: str
    # Slot 1
    oracle: Callable[[list], int]
    # Slot 2
    probe_to_solver_input: Callable[[dict], list]
    # Slot 3
    solver_entry_point: str
    # Slot 4
    estimator_names: list[str]
    estimator_policies: dict[str, Callable[[int, int], str]]
    # Slot 5
    fingerprint_axes: list[str]
    # Slot 6
    raw_tensor_encoder: Callable[[list[dict]], dict[str, list[float]]]


def get_problem_class_config(problem_id: str) -> ProblemClassConfig:
    """Factory: returns the ProblemClassConfig for a given problem id."""
    if problem_id == "lc322":
        return ProblemClassConfig(
            problem_id="lc322",
            oracle=_lc322_oracle_factory(),
            probe_to_solver_input=lc322_probe_to_solver_input,
            solver_entry_point=LC322_SOLVER_ENTRY_POINT,
            estimator_names=list(LC322_ESTIMATOR_NAMES),
            estimator_policies=dict(LC322_ESTIMATOR_POLICIES),
            fingerprint_axes=list(LC322_FINGERPRINT_AXES),
            raw_tensor_encoder=lc322_raw_tensor_encoder,
        )
    if problem_id == "lc45":
        return ProblemClassConfig(
            problem_id="lc45",
            oracle=_lc45_oracle_factory(),
            probe_to_solver_input=lc45_probe_to_solver_input,
            solver_entry_point=LC45_SOLVER_ENTRY_POINT,
            estimator_names=list(LC322_ESTIMATOR_NAMES),  # same labels; LC45-specific policies deferred
            estimator_policies=dict(LC322_ESTIMATOR_POLICIES),  # LC45 policies deferred
            fingerprint_axes=list(LC45_FINGERPRINT_AXES),
            raw_tensor_encoder=lc45_raw_tensor_encoder,
        )
    raise NotImplementedError(f"unknown problem_class: {problem_id!r}")
