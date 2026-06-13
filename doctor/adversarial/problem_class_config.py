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


def _lc3946_oracle_factory() -> Callable[[list], int]:
    """Returns a function that computes LC3946 ground truth from a solver input.

    Convention: solver input is a flat list [factor_0, price_0, factor_1, price_1, ...].
    The oracle unpacks pairs (factor, price) and calls lc3946_brute_force.
    """
    from doctor.adversarial.lc3946_ground_truth import lc3946_brute_force
    def _oracle(solver_input: list) -> int:
        flat = [int(x) for x in solver_input]
        if len(flat) % 2 != 0:
            raise ValueError(
                f"LC3946 oracle: solver input must have even length "
                f"(factor,price pairs), got {len(flat)}"
            )
        items = [(flat[2 * k], flat[2 * k + 1]) for k in range(len(flat) // 2)]
        # Convention: the last pair is (factor, budget). The oracle consumes it
        # as budget. Strip it from the items list.
        if len(items) < 1:
            raise ValueError("LC3946 oracle: solver input must contain at least one pair")
        factor_budget, budget = items[-1]
        if factor_budget != 0 or budget < 0:
            # The trailing pair is interpreted as budget; factor must be 0 sentinel.
            raise ValueError(
                f"LC3946 oracle: trailing pair is (factor, budget); factor must be 0, "
                f"got factor={factor_budget}, budget={budget}"
            )
        return lc3946_brute_force(items[:-1], int(budget))
    return _oracle


def _lc79_oracle_factory() -> Callable[[dict], bool]:
    """Returns a function that computes LC79 ground truth from a solver input.

    Convention: solver input is {"board": list[list[str]], "word": str}.
    The oracle calls lc79_brute_force(board, word).
    """
    from doctor.adversarial.lc79_ground_truth import lc79_brute_force
    def _oracle(solver_input: dict) -> bool:
        board = [row[:] for row in solver_input["board"]]
        word = solver_input["word"]
        return lc79_brute_force(board, word)
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


def lc3946_probe_to_solver_input(probe: dict) -> list:
    """LC3946 probe format: {items: [[factor, price], ...], budget: int}.

    Solver input: a flat list interleaving (factor, price) pairs followed by
    a sentinel pair (0, budget). The trailing (0, budget) is the budget
    convention; the oracle unpacks it.

    Example probe: items=[[2,3],[4,5]], budget=8 -> [2, 3, 4, 5, 0, 8]
    """
    items = list(probe["items"])
    budget = int(probe["budget"])
    flat: list[int] = []
    for item in items:
        flat.append(int(item[0]))
        flat.append(int(item[1]))
    flat.append(0)
    flat.append(budget)
    return flat


def lc79_probe_to_solver_input(probe: dict) -> dict:
    """LC79 probe format: {board: list[list[str]], word: str}.

    Solver input: {"board": list[list[str]], "word": str} (no transformation).
    """
    return {"board": [row[:] for row in probe["board"]], "word": probe["word"]}


# ---------------------------------------------------------------------------
# Slot 3: Solver entry-point name
# ---------------------------------------------------------------------------

LC322_SOLVER_ENTRY_POINT: str = "solve"
LC45_SOLVER_ENTRY_POINT: str = "solve"  # assumes a wrapper or in-place rename of LC45 candidates
LC3946_SOLVER_ENTRY_POINT: str = "solve"
LC79_SOLVER_ENTRY_POINT: str = "solve"


# ---------------------------------------------------------------------------
# Slot 4: Estimator set + per-estimator policies
# ---------------------------------------------------------------------------

LC322_ESTIMATOR_NAMES: list[str] = [
    "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
    "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
    "B6_regularized_raw_tensor", "C_structured_fingerprint",
]

LC45_ESTIMATOR_NAMES: list[str] = [
    "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
    "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
    "B6_regularized_raw_tensor", "C_structured_fingerprint",
]

LC3946_ESTIMATOR_NAMES: list[str] = [
    "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
    "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
    "B6_regularized_raw_tensor", "C_structured_fingerprint",
    "C_genuine",
]

LC79_ESTIMATOR_NAMES: list[str] = [
    "B0_prior", "B1_count", "B2_calibrated_count", "B3_raw_pf_vector",
    "B4_raw_full_tensor", "B5_nearest_neighbor_raw_tensor",
    "B6_regularized_raw_tensor", "C_structured_fingerprint",
    "C_genuine",
]


def _b0_prior_policy(obs_fails: int, n_obs: int, obs_records: list[dict] | None = None) -> str:
    return "ACCEPT"  # all-ACCEPT degenerate


def _fail_count_policy(obs_fails: int, n_obs: int, obs_records: list[dict] | None = None) -> str:
    return "ACCEPT" if obs_fails == 0 else "REJECT"


def _b4_raw_full_tensor_policy(obs_fails: int, n_obs: int, obs_records: list[dict] | None = None) -> str:
    return "REJECT"  # all-REJECT degenerate


def _b5_nn_policy(obs_fails: int, n_obs: int, obs_records: list[dict] | None = None) -> str:
    return "ACCEPT"  # all-ACCEPT degenerate


def _b6_reg_policy(obs_fails: int, n_obs: int, obs_records: list[dict] | None = None) -> str:
    return "ACCEPT"  # all-ACCEPT degenerate


def _c_genuine_policy(obs_fails: int, n_obs: int, obs_records: list[dict] | None = None) -> str:
    """Phase C-4 decision policy.

    Decision rule (declared in PHASE_C4_SPEC.md before implementation):
        ACCEPT if obs_fails == 0
        ACCEPT if obs_fails > 0 AND all failures share one probe_family
        REJECT otherwise

    Falls back to B1 behavior (ACCEPT iff 0 failures) if obs_records is None.

    Reads probe_family from obs_records[i].fingerprint_context.probe_family.
    """
    if obs_records is None:
        return "ACCEPT" if obs_fails == 0 else "REJECT"

    failures = [r for r in obs_records if not r.get("pass_fail", False)]
    if len(failures) == 0:
        return "ACCEPT"

    families: set = set()
    for r in failures:
        ctx = r.get("fingerprint_context", {}) or {}
        family = ctx.get("probe_family")
        if family is not None:
            families.add(family)

    if len(families) == 1:
        return "ACCEPT"
    return "REJECT"


def _c_feature_threshold_policy(
    obs_fails: int, n_obs: int, obs_records: list[dict] | None = None,
) -> str:
    """C_feature_threshold policy for Phase C-6 Rule 2.

    Decision rule (declared in PHASE_C6_SPEC.md before implementation):
        ACCEPT if obs_fails == 0
        ACCEPT if failure_rate_on_deformed_probes < 0.5
        REJECT otherwise
        (A 'deformed' probe has deformation_level > 0; threshold = 0.5)

    Falls back to B1 behavior if obs_records is None or if no deformed probes exist.
    Feature used: deformation_level (dim 1 of the 6-dim encode_raw_tensor output).
    Differs from _fail_count_policy: accepts solvers whose failure rate on
    deformed probes is below the 0.5 threshold.
    """
    if obs_records is None:
        return "ACCEPT" if obs_fails == 0 else "REJECT"

    deformed = [
        r for r in obs_records
        if (r.get("fingerprint_context", {}) or {}).get("deformation_level", 0) > 0
    ]
    if len(deformed) == 0:
        return "ACCEPT" if obs_fails == 0 else "REJECT"

    if obs_fails == 0:
        return "ACCEPT"

    failures_deformed = [r for r in deformed if not r.get("pass_fail", False)]
    rate = len(failures_deformed) / len(deformed)
    if rate < 0.5:
        return "ACCEPT"
    return "REJECT"


def _c_majority_policy(
    obs_fails: int, n_obs: int, obs_records: list[dict] | None = None,
) -> str:
    """C_majority policy for Phase C-6 Rule 3.

    Decision rule (declared in PHASE_C6_SPEC.md before implementation):
        ACCEPT if obs_fails == 0
        ACCEPT if there is a unique mode in the failure-family distribution
        REJECT otherwise
        (A 'unique mode' = one family has more failures than any other single family.
        Ties yield REJECT.)

    Falls back to B1 behavior if obs_records is None.
    Feature used: probe_family from obs_records.
    Differs from _c_genuine_policy: requires only plurality, not unanimity.
    Differs from _fail_count_policy: accepts solvers with a unique-mode failure family.
    """
    if obs_records is None:
        return "ACCEPT" if obs_fails == 0 else "REJECT"

    failures = [r for r in obs_records if not r.get("pass_fail", False)]
    if len(failures) == 0:
        return "ACCEPT"

    counts: dict = {}
    for r in failures:
        ctx = r.get("fingerprint_context", {}) or {}
        family = ctx.get("probe_family")
        if family is not None:
            counts[family] = counts.get(family, 0) + 1

    if not counts:
        return "REJECT"

    max_count = max(counts.values())
    n_with_max = sum(1 for c in counts.values() if c == max_count)
    if n_with_max == 1:
        return "ACCEPT"
    return "REJECT"


def _c_zero_only_policy(
    obs_fails: int, n_obs: int, obs_records: list[dict] | None = None,
) -> str:
    """C_zero_only policy for Phase C-6 Rule 4 (negative control).

    Decision rule (declared in PHASE_C6_SPEC.md before implementation):
        ACCEPT if obs_fails == 0
        REJECT otherwise

    Operationally identical to _fail_count_policy (B1). Does not consult
    obs_records. Included as a negative control to show whether the C-4 gain
    is associated with the coherence condition (Rule 1) or with being more
    permissive than B1.
    """
    return "ACCEPT" if obs_fails == 0 else "REJECT"


LC322_ESTIMATOR_POLICIES: dict[str, Callable[[int, int, list[dict] | None], str]] = {
    "B0_prior": _b0_prior_policy,
    "B1_count": _fail_count_policy,
    "B2_calibrated_count": _fail_count_policy,
    "B3_raw_pf_vector": _fail_count_policy,
    "B4_raw_full_tensor": _b4_raw_full_tensor_policy,
    "B5_nearest_neighbor_raw_tensor": _b5_nn_policy,
    "B6_regularized_raw_tensor": _b6_reg_policy,
    "C_structured_fingerprint": _fail_count_policy,
    "C_genuine": _c_genuine_policy,
    "C_feature_threshold": _c_feature_threshold_policy,
    "C_majority": _c_majority_policy,
    "C_zero_only": _c_zero_only_policy,
}

LC45_ESTIMATOR_POLICIES: dict[str, Callable[[int, int, list[dict] | None], str]] = {
    "B0_prior": _b0_prior_policy,
    "B1_count": _fail_count_policy,
    "B2_calibrated_count": _fail_count_policy,
    "B3_raw_pf_vector": _fail_count_policy,
    "B4_raw_full_tensor": _b4_raw_full_tensor_policy,
    "B5_nearest_neighbor_raw_tensor": _b5_nn_policy,
    "B6_regularized_raw_tensor": _b6_reg_policy,
    "C_structured_fingerprint": _fail_count_policy,
    "C_genuine": _c_genuine_policy,
    "C_feature_threshold": _c_feature_threshold_policy,
    "C_majority": _c_majority_policy,
    "C_zero_only": _c_zero_only_policy,
}

LC3946_ESTIMATOR_POLICIES: dict[str, Callable[[int, int, list[dict] | None], str]] = {
    "B0_prior": _b0_prior_policy,
    "B1_count": _fail_count_policy,
    "B2_calibrated_count": _fail_count_policy,
    "B3_raw_pf_vector": _fail_count_policy,
    "B4_raw_full_tensor": _b4_raw_full_tensor_policy,
    "B5_nearest_neighbor_raw_tensor": _b5_nn_policy,
    "B6_regularized_raw_tensor": _b6_reg_policy,
    "C_structured_fingerprint": _fail_count_policy,
    "C_genuine": _c_genuine_policy,
    "C_feature_threshold": _c_feature_threshold_policy,
    "C_majority": _c_majority_policy,
    "C_zero_only": _c_zero_only_policy,
}

LC79_ESTIMATOR_POLICIES: dict[str, Callable[[int, int, list[dict] | None], str]] = {
    "B0_prior": _b0_prior_policy,
    "B1_count": _fail_count_policy,
    "B2_calibrated_count": _fail_count_policy,
    "B3_raw_pf_vector": _fail_count_policy,
    "B4_raw_full_tensor": _b4_raw_full_tensor_policy,
    "B5_nearest_neighbor_raw_tensor": _b5_nn_policy,
    "B6_regularized_raw_tensor": _b6_reg_policy,
    "C_structured_fingerprint": _fail_count_policy,
    "C_genuine": _c_genuine_policy,
    "C_feature_threshold": _c_feature_threshold_policy,
    "C_majority": _c_majority_policy,
    "C_zero_only": _c_zero_only_policy,
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
LC3946_FINGERPRINT_AXES: list[str] = [
    "poset_universal_source",     # factor=1 items
    "poset_chain",                 # factors in a divisibility chain
    "poset_antichain",             # pairwise coprime factors
    "poset_lattice_boolean",       # powers of 2 forming a boolean lattice
    "poset_lattice_two_prime",     # 2-prime lattice {2,3,6,12,...}
    "poset_isolated",              # factors with no divisibility relations
]

LC79_FINGERPRINT_AXES: list[str] = [
    "path_finding",               # board path existence
    "visited_tracking",           # cell revisitation prevention
    "boundary",                   # grid boundary handling
    "recursion_depth",            # DFS depth management
    "backtracking",               # state restoration on failure
    "exhaustive_search",          # complete exploration guarantee
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


def _bfs_reachable_count(nums: list[int]) -> int:
    """Count positions reachable from start via BFS. Returns the total
    number of positions BFS can reach (including the target if reached).

    This is the BFS oracle's `reachable_count` — a different quantity from
    the BFS oracle's min-jump output. Used by `bfs_agrees_rate` to
    compare the candidate's output against an independent BFS-derived
    quantity, not against the expected_output label.
    """
    from collections import deque
    n = len(nums)
    if n == 0:
        return 0
    if nums[0] == 0:
        return 1
    visited: set[int] = {0}
    queue: deque[int] = deque([0])
    while queue:
        pos = queue.popleft()
        for step in range(1, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return len(visited) + 1
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return len(visited)


def lc45_raw_tensor_encoder(obs_rows: list[dict]) -> dict[str, list[float]]:
    """LC45 concrete encoder. Uses the LC45 bimaristan symbol registry
    to produce a 6-dim feature vector per solver from the observation rows.

    The 6 features are derived from per-probe symbol values, averaged
    across each solver's probe set. They summarize the solver's behavior
    on the LC45 manifold:
      [0] pass_fail_rate             (per-solver)
      [1] bfs_agrees_rate            (algorithm-family, return semantics)
      [2] off_by_one_rate            (return semantics)
      [3] panics_on_dead_end_rate    (cross-problem, return semantics)
      [4] dead_end_present_rate      (oracle-dependent)
      [5] is_uniform_array_rate      (oracle-dependent)

    The encoder wires the LC45 adapter slot to the new oracle evaluator
    and symbol registry (Week 4 bimaristan layer). It is a concrete
    implementation (not a stub).
    """
    by_solver: dict[str, list[dict]] = {}
    for row in obs_rows:
        sid = str(row["solver_id"])
        by_solver.setdefault(sid, []).append(row)

    out: dict[str, list[float]] = {}
    for sid, rows in by_solver.items():
        n = len(rows)
        if n == 0:
            out[sid] = [0.0] * 6
            continue

        pf_rate = sum(1.0 if r.get("pass_fail") else 0.0 for r in rows) / n

        bfs_agrees_count = 0
        off_by_one_count = 0
        panic_count = 0
        dead_end_count = 0
        uniform_count = 0
        for r in rows:
            nums = r.get("nums")
            if not isinstance(nums, (list, tuple)) or len(nums) == 0:
                continue
            candidate_output = r.get("candidate_output")
            expected_output = r.get("expected_output")
            if candidate_output is not None and expected_output is not None:
                if abs(candidate_output - expected_output) == 1:
                    off_by_one_count += 1
            if candidate_output == -1:
                panic_count += 1
            if len(nums) > 1 and any(nums[i] == 0 for i in range(len(nums) - 1)):
                dead_end_count += 1
            if len(set(nums)) == 1:
                uniform_count += 1
            # bfs_agrees_rate: compare candidate output against the BFS oracle's
            # reachable_count (number of positions BFS can reach from start),
            # NOT against expected_output. This makes it informationally distinct
            # from pass_fail_rate.
            if candidate_output is not None and nums is not None:
                reachable = _bfs_reachable_count(list(nums))
                if candidate_output == reachable:
                    bfs_agrees_count += 1

        out[sid] = [
            pf_rate,
            bfs_agrees_count / n,
            off_by_one_count / n,
            panic_count / n,
            dead_end_count / n,
            uniform_count / n,
        ]

    return out


# ---------------------------------------------------------------------------
# Week 4: bimaristan wiring for LC45
# ---------------------------------------------------------------------------


def get_lc45_bimaristan_components() -> dict:
    """Return the LC45 bimaristan components (evaluator + symbol registry).

    Wires the LC45 adapter slot to the new oracle evaluator and symbol
    registry. Used by the bimaristan layer (test_lc45_bimaristan.py and
    any future LC45 bimaristan tooling). Does not affect the LC322
    fingerprint-gate runner.

    Returns:
        dict with keys:
          - "evaluator": LC45OracleEvaluator
          - "symbol_registry": LC45_SYMBOL_REGISTRY
          - "manifolds": tuple of 6 LC45 manifold ids
    """
    from doctor.adversarial.lc45_oracle_evaluator import LC45OracleEvaluator
    from doctor.adversarial.lc45_symbol_registry import (
        LC45_SYMBOL_REGISTRY, LC45_MANIFOLDS,
    )
    return {
        "evaluator": LC45OracleEvaluator(),
        "symbol_registry": LC45_SYMBOL_REGISTRY,
        "manifolds": LC45_MANIFOLDS,
    }


# ---------------------------------------------------------------------------
# Slot 6 (LC3946): 6-feature raw tensor encoder
# ---------------------------------------------------------------------------


def _lc3946_factor_lattice_features(factors: list[int]) -> list[float]:
    """Compute the 6-dim factor-lattice signature for a list of factors.

    Returns 6 floats characterizing the poset structure of the factors:
      [0] has_universal_source    (1.0 if any factor == 1, else 0.0)
      [1] chain_density           (fraction of pairs in the same chain)
      [2] antichain_density       (1.0 if all pairs are coprime, else 0.0)
      [3] boolean_lattice_score   (1.0 if all factors are powers of 2, else 0.0)
      [4] two_prime_lattice_score (1.0 if all factors are products of {2,3}, else 0.0)
      [5] isolated_score          (1.0 if no pair is comparable, else 0.0)
    """
    n = len(factors)
    if n == 0:
        return [0.0] * 6

    has_universal = 1.0 if any(f == 1 for f in factors) else 0.0

    comparable = 0
    total_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_pairs += 1
            a, b = factors[i], factors[j]
            if a == 0 or b == 0:
                continue
            if a % b == 0 or b % a == 0:
                comparable += 1
    chain_density = comparable / total_pairs if total_pairs > 0 else 0.0
    antichain_density = 1.0 if comparable == 0 else 0.0

    boolean_score = 1.0 if all(f > 0 and (f & (f - 1)) == 0 for f in factors) else 0.0

    two_prime_score = 1.0
    for f in factors:
        if f <= 0:
            two_prime_score = 0.0
            break
        # Strip factors of 2 and 3; if anything remains, not 2-prime.
        x = f
        while x % 2 == 0:
            x //= 2
        while x % 3 == 0:
            x //= 3
        if x != 1:
            two_prime_score = 0.0
            break

    isolated_score = 1.0 if antichain_density == 1.0 else 0.0

    return [
        has_universal,
        chain_density,
        antichain_density,
        boolean_score,
        two_prime_score,
        isolated_score,
    ]


def lc3946_raw_tensor_encoder(obs_rows: list[dict]) -> dict[str, list[float]]:
    """LC3946's 6-feature encoder. Mirrors the LC322 encoder shape exactly.

    Per-probe row has a `probe` dict containing `items` (list of [factor, price])
    and `budget`. The 6 features are derived from the per-solver pass/fail
    pattern and the factor-lattice signature of the probe.

    Output layout (per solver):
      [0] pass_fail rate        (per-solver mean pass rate)
      [1] probe budget          (normalized; max observed)
      [2] axis_val              (1.0 if axis field present, else 0.0)
      [3] family_val            (1.0 if probe_family present, else 0.0)
      [4] paired                (1.0 if paired_probe_id present, else 0.0)
      [5] invariant             (1.0 if expected_invariant present, else 0.0)
    """
    by_solver: dict[str, list[dict]] = {}
    for row in obs_rows:
        sid = str(row["solver_id"])
        by_solver.setdefault(sid, []).append(row)

    out: dict[str, list[float]] = {}
    for sid, rows in by_solver.items():
        n = len(rows)
        if n == 0:
            out[sid] = [0.0] * 6
            continue

        pf_rate = sum(1.0 if r.get("pass_fail") else 0.0 for r in rows) / n
        budget_max = max(
            (int(r.get("probe", {}).get("budget", 0)) for r in rows),
            default=0,
        )
        budget_norm = float(budget_max) / 100.0  # arbitrary normalization
        budget_norm = min(budget_norm, 1.0)

        axis_val = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("axis") for r in rows
        ) else 0.0
        family_val = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("probe_family") for r in rows
        ) else 0.0
        paired = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("paired_probe_id") for r in rows
        ) else 0.0
        invariant = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("expected_invariant") for r in rows
        ) else 0.0

        out[sid] = [
            pf_rate,
            budget_norm,
            axis_val,
            family_val,
            paired,
            invariant,
        ]

    return out


def lc79_raw_tensor_encoder(obs_rows: list[dict]) -> dict[str, list[float]]:
    """LC79's 6-feature encoder. Mirrors the LC322 encoder shape exactly.

    Per-probe row has a `board` and `word` in the probe dict. The 6 features
    are derived from the per-solver pass/fail pattern and the probe metadata.

    Output layout (per solver):
      [0] pass_fail rate        (per-solver mean pass rate)
      [1] grid_size             (normalized; max observed)
      [2] axis_val              (1.0 if axis field present, else 0.0)
      [3] family_val            (1.0 if probe_family present, else 0.0)
      [4] paired                (1.0 if paired_probe_id present, else 0.0)
      [5] invariant             (1.0 if expected_invariant present, else 0.0)
    """
    by_solver: dict[str, list[dict]] = {}
    for row in obs_rows:
        sid = str(row["solver_id"])
        by_solver.setdefault(sid, []).append(row)

    out: dict[str, list[float]] = {}
    for sid, rows in by_solver.items():
        n = len(rows)
        if n == 0:
            out[sid] = [0.0] * 6
            continue

        pf_rate = sum(1.0 if r.get("pass_fail") else 0.0 for r in rows) / n
        grid_max = max(
            (len(r.get("probe", {}).get("board", [])) * len(r.get("probe", {}).get("board", [[]])[0]) if r.get("probe", {}).get("board") else 0 for r in rows),
            default=0,
        )
        grid_norm = float(grid_max) / 100.0  # arbitrary normalization
        grid_norm = min(grid_norm, 1.0)

        axis_val = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("axis") for r in rows
        ) else 0.0
        family_val = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("probe_family") for r in rows
        ) else 0.0
        paired = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("paired_probe_id") for r in rows
        ) else 0.0
        invariant = 1.0 if any(
            (r.get("fingerprint_context", {}) or {}).get("expected_invariant") for r in rows
        ) else 0.0

        out[sid] = [
            pf_rate,
            grid_norm,
            axis_val,
            family_val,
            paired,
            invariant,
        ]

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
            estimator_names=list(LC45_ESTIMATOR_NAMES),
            estimator_policies=dict(LC45_ESTIMATOR_POLICIES),
            fingerprint_axes=list(LC45_FINGERPRINT_AXES),
            raw_tensor_encoder=lc45_raw_tensor_encoder,
        )
    if problem_id == "lc3946":
        return ProblemClassConfig(
            problem_id="lc3946",
            oracle=_lc3946_oracle_factory(),
            probe_to_solver_input=lc3946_probe_to_solver_input,
            solver_entry_point=LC3946_SOLVER_ENTRY_POINT,
            estimator_names=list(LC3946_ESTIMATOR_NAMES),
            estimator_policies=dict(LC3946_ESTIMATOR_POLICIES),
            fingerprint_axes=list(LC3946_FINGERPRINT_AXES),
            raw_tensor_encoder=lc3946_raw_tensor_encoder,
        )
    if problem_id == "lc79":
        return ProblemClassConfig(
            problem_id="lc79",
            oracle=_lc79_oracle_factory(),
            probe_to_solver_input=lc79_probe_to_solver_input,
            solver_entry_point=LC79_SOLVER_ENTRY_POINT,
            estimator_names=list(LC79_ESTIMATOR_NAMES),
            estimator_policies=dict(LC79_ESTIMATOR_POLICIES),
            fingerprint_axes=list(LC79_FINGERPRINT_AXES),
            raw_tensor_encoder=lc79_raw_tensor_encoder,
        )
    raise NotImplementedError(f"unknown problem_class: {problem_id!r}")
