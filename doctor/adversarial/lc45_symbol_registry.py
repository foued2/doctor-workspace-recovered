"""LC45 Jump Game II — Symbol Registry.

The LC45 bimaristan layer. Symbols are predicates that evaluate a
candidate's behavior on probes. Each symbol is a `compute(ctx)`
function. Mirror structure: lc322_symbol_registry.py (which mirrors
the LC11 sibling pattern).

The registry has 5 categories:
  - ALGORITHM_FAMILY: which algorithm pattern the candidate uses
                     (5 entries)
  - TIE_BREAKER: which tie-breaking rule the candidate uses
                 (3 entries)
  - RETURN_SEMANTICS: which return-value semantics the candidate uses
                      (3 entries)
  - ORACLE_DEPENDENT: predicates computed from the BFS oracle on the
                      probe (5 basic + 5 derived + 12 manifold = 22
                      entries, target >= 20)
  - CROSS_PROBLEM: vocabulary that transfers from LC322 to LC45
                   (5 entries)

────────────────────────────────────────────────────────────────────────
Cross-problem transfer decisions (LC322 -> LC45)
────────────────────────────────────────────────────────────────────────
  uses_exhaustive_search                 DIRECT
    BFS is exhaustive; the symbol applies directly to the LC45 BFS
    survivor. LC322's `dp_agrees_with_truth` analogue maps onto this.

  uses_greedy_tie_breaker                DIRECT
    Greedy tie-breaking (max-index vs max-value) applies in jump-game
    as it does in coin-change; the three LC45 greedy candidates
    exercise the same decision pattern.

  panics_on_dead_end                     DIRECT
    The zero_dead_end_panic family in LC45 maps directly onto
    LC322's `panics_on_dead_end` (or `zero_dead_end_panic`). Both
    return -1 when a dead-end position is encountered.

  uses_memoization                       EXCLUDED
    LC45 jump-game is not sub-problem-decomposable: there is no
    sub-problem index to memoize against. The LC322 symbol, which
    presumes a sub-problem axis (e.g., the amount axis), does not
    apply. Return value is False by definition; reason recorded on
    the entry as transfer=EXCLUDED.

  state_space_bounded_by_amount          RE_DERIVE
    LC45's state-space is bounded by array length (positions 0..n-1),
    not by an "amount" axis. The re-derived symbol is named
    `state_space_bounded_by_array_length` and is True for the BFS
    survivor (which has state space = n positions). The original
    LC322 symbol is left out of the LC45 registry.
────────────────────────────────────────────────────────────────────────

All entries use a uniform `compute(ctx)` interface. The context dict
varies by symbol category:
  - ALGORITHM_FAMILY, TIE_BREAKER, CROSS_PROBLEM (candidate-level):
      ctx = {"eval_result": LC45EvaluationResult}
  - RETURN_SEMANTICS, ORACLE_DEPENDENT (probe-level):
      ctx = {"nums": list[int], "candidate_output": int | None}
  - ORACLE_DEPENDENT manifold predicates:
      ctx = {"eval_result": LC45EvaluationResult,
             "manifold_probe_ids": set[str]}

The bimaristan layer is self-contained: symbols are computed from the
BFS oracle and the candidate's outputs. No Doctor pipeline dependency.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# SymbolCategory (local definition; mirrors symbol_registry.py)
# ---------------------------------------------------------------------------


class SymbolCategory(Enum):
    ALGORITHM_FAMILY = "algorithm_family"
    TIE_BREAKER = "tie_breaker"
    RETURN_SEMANTICS = "return_semantics"
    ORACLE_DEPENDENT = "oracle_dependent"
    CROSS_PROBLEM = "cross_problem"


# Cross-problem transfer decision constants
TRANSFER_DIRECT = "DIRECT"
TRANSFER_RE_DERIVE = "RE_DERIVE"
TRANSFER_EXCLUDED = "EXCLUDED"


# ---------------------------------------------------------------------------
# Reference algorithms (used as truth references for algorithm-family
# symbols). Each is a hand-rolled implementation of the algorithm pattern.
# ---------------------------------------------------------------------------


def _ref_naive_max_index(nums: list[int]) -> int:
    """Reference: always take the maximum forward step (max index first)."""
    n = len(nums)
    if n <= 1:
        return 0
    pos = 0
    jumps = 0
    while pos < n - 1:
        if nums[pos] == 0:
            return -1
        farthest = pos + 1
        for step in range(2, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            if nxt > farthest:
                farthest = nxt
        pos = farthest
        jumps += 1
    return jumps


def _ref_max_value_landing(nums: list[int]) -> int:
    """Reference: jump to position with max nums[nxt]; on tie pick closest."""
    n = len(nums)
    if n <= 1:
        return 0
    pos = 0
    jumps = 0
    while pos < n - 1:
        if nums[pos] == 0:
            return -1
        max_val = -1
        best_step = 1
        for step in range(1, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            if nums[nxt] > max_val:
                max_val = nums[nxt]
                best_step = step
        pos += best_step
        jumps += 1
    return jumps


def _ref_uniform_formula(nums: list[int]) -> int:
    """Reference: assume uniform, apply ceil((n-1) / max(nums))."""
    n = len(nums)
    if n <= 1:
        return 0
    step = max(nums)
    if step <= 0:
        return -1
    return max(1, int(math.ceil((n - 1) / step)))


def _ref_bounded_lookahead(nums: list[int], k: int = 3) -> int:
    """Reference: DP with bounded k-step lookahead."""
    n = len(nums)
    if n <= 1:
        return 0
    dp = [float("inf")] * n
    dp[0] = 0
    for i in range(n):
        if dp[i] == float("inf"):
            continue
        window = min(nums[i], k, n - 1 - i)
        for step in range(1, window + 1):
            nxt = i + step
            if nxt >= n - 1:
                return dp[i] + 1
            dp[nxt] = min(dp[nxt], dp[i] + 1)
    return -1 if dp[-1] == float("inf") else int(dp[-1])


def _ref_bfs_truth(nums: list[int]) -> int:
    """BFS oracle (the canonical LC45 ground truth)."""
    n = len(nums)
    if n == 0:
        raise ValueError("empty input")
    if n == 1:
        return 0
    if nums[0] == 0:
        raise ValueError("cannot move from start")
    cutoff = n
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    visited = {0}
    while queue:
        pos, jumps = queue.popleft()
        if jumps >= cutoff:
            continue
        for step in range(nums[pos], 0, -1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, jumps + 1))
    raise ValueError("unreachable last index")


def _ref_bfs_trace(nums: list[int]) -> dict[str, int]:
    """Self-contained BFS trace (mirrors lc45_oracle_evaluator._bfs_trace)."""
    if not nums:
        return {
            "visited": 0, "max_depth": 0, "edges": 0, "max_width": 0,
            "output": -1, "reachable_count": 0,
            "frontier_size_at_target": 0, "bfs_depth_to_target": -1,
        }
    n = len(nums)
    if n == 1:
        return {
            "visited": 1, "max_depth": 0, "edges": 0, "max_width": 1,
            "output": 0, "reachable_count": 1,
            "frontier_size_at_target": 1, "bfs_depth_to_target": 0,
        }
    if nums[0] == 0:
        return {
            "visited": 1, "max_depth": 0, "edges": 0, "max_width": 1,
            "output": -1, "reachable_count": 1,
            "frontier_size_at_target": 1, "bfs_depth_to_target": -1,
        }
    visited: set[int] = {0}
    queue: deque[tuple[int, int]] = deque([(0, 0)])
    widths: dict[int, int] = {0: 1}
    edges = 0
    max_depth = 0
    while queue:
        pos, jumps = queue.popleft()
        max_depth = max(max_depth, jumps)
        for step in range(1, nums[pos] + 1):
            edges += 1
            nxt = pos + step
            if nxt >= n - 1:
                widths[jumps + 1] = widths.get(jumps + 1, 0) + 1
                return {
                    "visited": len(visited) + 1,
                    "max_depth": jumps + 1,
                    "edges": edges,
                    "max_width": max(widths.values()) if widths else 0,
                    "output": jumps + 1,
                    "reachable_count": len(visited) + 1,
                    "frontier_size_at_target": widths[jumps + 1],
                    "bfs_depth_to_target": jumps + 1,
                }
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, jumps + 1))
                widths[jumps + 1] = widths.get(jumps + 1, 0) + 1
    return {
        "visited": len(visited),
        "max_depth": max_depth,
        "edges": edges,
        "max_width": max(widths.values()) if widths else 0,
        "output": -1,
        "reachable_count": len(visited),
        "frontier_size_at_target": 0,
        "bfs_depth_to_target": -1,
    }


# ---------------------------------------------------------------------------
# Entry and Registry classes (mirror lc45 stub shape)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LC45Entry:
    name: str
    category: SymbolCategory
    compute: Callable[[dict], Any]
    input_signature: tuple[str, ...] = ()
    transfer: str = "N/A"
    manifold_id: str | None = None


class _LC45Registry:
    def __init__(self) -> None:
        self.problem_id: str = "lc45_jump_game"
        self.entries: tuple[LC45Entry, ...] = ()
        self.names: set[str] = set()

    def get(self, name: str) -> LC45Entry | None:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None


# ---------------------------------------------------------------------------
# Algorithm-family compute functions (5)
# ---------------------------------------------------------------------------


def _af_eval_check(
    eval_result: Any, ref: Callable[[list[int]], int]
) -> bool:
    """True if every probe's candidate output equals the reference."""
    if not eval_result.probe_results:
        return False
    for r in eval_result.probe_results:
        if r.candidate_output is None:
            return False
        try:
            expected = ref(list(r.nums))
        except (ValueError, IndexError):
            return False
        if r.candidate_output != expected:
            return False
    return True


def _uses_bfs_with_visited_compute(ctx: dict) -> bool:
    return _af_eval_check(ctx["eval_result"], _ref_bfs_truth)


def _uses_naive_max_index_compute(ctx: dict) -> bool:
    return _af_eval_check(ctx["eval_result"], _ref_naive_max_index)


def _uses_max_value_landing_compute(ctx: dict) -> bool:
    return _af_eval_check(ctx["eval_result"], _ref_max_value_landing)


def _uses_uniform_formula_compute(ctx: dict) -> bool:
    return _af_eval_check(ctx["eval_result"], _ref_uniform_formula)


def _uses_bounded_lookahead_compute(ctx: dict) -> bool:
    eval_result = ctx["eval_result"]
    if not eval_result.probe_results:
        return False
    for r in eval_result.probe_results:
        if r.candidate_output is None:
            return False
        ref = _ref_bounded_lookahead(list(r.nums), k=3)
        if r.candidate_output != ref:
            return False
    return True


# ---------------------------------------------------------------------------
# Tie-breaker compute functions (3)
#
# These are the heuristic-decision symbols. A candidate "picks X on tie"
# iff its outputs match the reference algorithm that uses X as the
# tie-breaking rule, on every probe in the set.
# ---------------------------------------------------------------------------


def _picks_max_index_on_tie_compute(ctx: dict) -> bool:
    """True iff the candidate's outputs match naive-max-index on every probe.

    Naive-max-index is the unique reference for "picks max index on tie"
    among the LC45 candidates (max-value-landing picks max-value, not
    max-index, on tie).
    """
    return _af_eval_check(ctx["eval_result"], _ref_naive_max_index)


def _picks_max_value_on_tie_compute(ctx: dict) -> bool:
    """True iff the candidate's outputs match max-value-landing on every probe."""
    return _af_eval_check(ctx["eval_result"], _ref_max_value_landing)


def _picks_closest_on_tie_compute(ctx: dict) -> bool:
    """True iff the candidate's outputs match the BFS oracle on every probe.

    The BFS oracle breaks ties by visiting in order (the step loop runs
    from nums[pos] down to 1), so the first position reached at a given
    depth is the closest one. Hence "picks closest on tie" is uniquely
    satisfied by the BFS algorithm family.
    """
    return _af_eval_check(ctx["eval_result"], _ref_bfs_truth)


# ---------------------------------------------------------------------------
# Return-semantics compute functions (3)
# ---------------------------------------------------------------------------


def _output_equals_reachable_count_compute(ctx: dict) -> bool:
    """True iff the candidate's output equals the BFS reachable count
    on at least one probe in the candidate's evaluation result.

    Probe-level: ctx = {"nums": list[int], "candidate_output": int|None}
    Candidate-level: ctx = {"eval_result": LC45EvaluationResult}
    """
    if "eval_result" in ctx:
        for r in ctx["eval_result"].probe_results:
            if r.candidate_output is None:
                continue
            trace = _ref_bfs_trace(list(r.nums))
            if r.candidate_output == trace["reachable_count"]:
                return True
        return False
    nums = ctx.get("nums")
    candidate_output = ctx.get("candidate_output")
    if nums is None or candidate_output is None:
        return False
    trace = _ref_bfs_trace(list(nums))
    return candidate_output == trace["reachable_count"]


def _output_off_by_one_in_bfs_compute(ctx: dict) -> bool:
    """True iff the candidate's output differs by exactly 1 from the BFS
    oracle on at least one probe in the candidate's evaluation result.

    Probe-level: ctx = {"nums": list[int], "candidate_output": int|None}
    Candidate-level: ctx = {"eval_result": LC45EvaluationResult}
    """
    if "eval_result" in ctx:
        for r in ctx["eval_result"].probe_results:
            if r.candidate_output is None or r.oracle_output < 0:
                continue
            if abs(r.candidate_output - r.oracle_output) == 1:
                return True
        return False
    nums = ctx.get("nums")
    candidate_output = ctx.get("candidate_output")
    if nums is None or candidate_output is None:
        return False
    try:
        oracle_out = _ref_bfs_truth(list(nums))
    except ValueError:
        return False
    return abs(candidate_output - oracle_out) == 1


def _returns_minus_one_on_zero_compute(ctx: dict) -> bool:
    """True iff the candidate returns -1 on at least one probe that has
    an interior zero.

    Probe-level: ctx = {"nums": list[int], "candidate_output": int|None}
    Candidate-level: ctx = {"eval_result": LC45EvaluationResult}
    """
    if "eval_result" in ctx:
        for r in ctx["eval_result"].probe_results:
            if r.candidate_output is None:
                continue
            nums = list(r.nums)
            if len(nums) <= 1:
                continue
            has_interior_zero = any(nums[i] == 0 for i in range(len(nums) - 1))
            if has_interior_zero and r.candidate_output == -1:
                return True
        return False
    nums = ctx.get("nums")
    candidate_output = ctx.get("candidate_output")
    if nums is None or candidate_output is None:
        return False
    if len(nums) <= 1:
        return False
    has_interior_zero = any(nums[i] == 0 for i in range(len(nums) - 1))
    return has_interior_zero and candidate_output == -1


# ---------------------------------------------------------------------------
# Oracle-dependent compute functions (5 basic + 5 derived = 10)
# ---------------------------------------------------------------------------


def _is_reachable_compute(ctx: dict) -> bool:
    nums = ctx.get("nums")
    if nums is None:
        return False
    try:
        return _ref_bfs_truth(list(nums)) >= 0
    except ValueError:
        return False


def _optimal_jump_count_compute(ctx: dict) -> int:
    nums = ctx.get("nums")
    if nums is None:
        return -1
    try:
        return _ref_bfs_truth(list(nums))
    except ValueError:
        return -1


def _frontier_size_at_target_compute(ctx: dict) -> int:
    nums = ctx.get("nums")
    if nums is None:
        return 0
    return _ref_bfs_trace(list(nums))["frontier_size_at_target"]


def _bfs_depth_to_target_compute(ctx: dict) -> int:
    nums = ctx.get("nums")
    if nums is None:
        return -1
    return _ref_bfs_trace(list(nums))["bfs_depth_to_target"]


def _dead_end_present_compute(ctx: dict) -> bool:
    nums = ctx.get("nums")
    if nums is None or len(nums) <= 1:
        return False
    return any(nums[i] == 0 for i in range(len(nums) - 1))


def _is_uniform_array_compute(ctx: dict) -> bool:
    nums = ctx.get("nums")
    if nums is None or len(nums) == 0:
        return False
    return len(set(nums)) == 1


def _has_interior_zero_compute(ctx: dict) -> bool:
    return _dead_end_present_compute(ctx)


def _optimal_jumps_is_one_compute(ctx: dict) -> bool:
    nums = ctx.get("nums")
    if nums is None or len(nums) <= 1:
        return False
    return nums[0] >= len(nums) - 1


def _bfs_visited_count_compute(ctx: dict) -> int:
    nums = ctx.get("nums")
    if nums is None:
        return 0
    return _ref_bfs_trace(list(nums))["visited"]


def _bfs_max_frontier_width_compute(ctx: dict) -> int:
    nums = ctx.get("nums")
    if nums is None:
        return 0
    return _ref_bfs_trace(list(nums))["max_width"]


# ---------------------------------------------------------------------------
# Manifold predicates (12: 2 per manifold)
# ---------------------------------------------------------------------------


LC45_MANIFOLDS: tuple[str, ...] = (
    "naive_max_jump_suboptimal",
    "single_large_jump_decoy",
    "greedy_horizon_collapse",
    "naive_max_jump_dead_landing",
    "uniform_jump_array",
    "greedy_frontier_valid_no_false_pressure",
)


def _manifold_predicate_compute(
    manifold_id: str, predicate_kind: str
) -> Callable[[dict], bool]:
    """Build a manifold predicate compute function.

    predicate_kind:
      - "greedy_horizon_collapses": True iff the candidate's output
        is strictly greater than the BFS oracle on every probe in the
        manifold (i.e., the candidate is sub-optimal throughout).
      - "bfs_agrees_with_truth": True iff the candidate's output
        equals the BFS oracle on every probe in the manifold.
    """
    def _compute(ctx: dict) -> bool:
        eval_result = ctx["eval_result"]
        manifold_probe_ids = ctx.get("manifold_probe_ids", set())
        manifold_probes = [
            r for r in eval_result.probe_results if r.probe_id in manifold_probe_ids
        ]
        if not manifold_probes:
            return False
        for r in manifold_probes:
            if r.candidate_output is None:
                return False
            try:
                oracle_out = _ref_bfs_truth(list(r.nums))
            except ValueError:
                return False
            if predicate_kind == "greedy_horizon_collapses":
                if oracle_out < 0 or r.candidate_output <= oracle_out:
                    return False
            elif predicate_kind == "bfs_agrees_with_truth":
                if r.candidate_output != oracle_out:
                    return False
            else:
                raise ValueError(predicate_kind)
        return True
    return _compute


# ---------------------------------------------------------------------------
# Cross-problem compute functions (5)
# ---------------------------------------------------------------------------


def _cp_uses_exhaustive_search_compute(ctx: dict) -> bool:
    """DIRECT: BFS is exhaustive; the candidate matches iff it matches BFS."""
    return _af_eval_check(ctx["eval_result"], _ref_bfs_truth)


def _cp_uses_greedy_tie_breaker_compute(ctx: dict) -> bool:
    """DIRECT: at least one of the LC45 greedy reference algorithms
    matches the candidate on every probe.
    """
    eval_result = ctx["eval_result"]
    if not eval_result.probe_results:
        return False
    return (
        _af_eval_check(eval_result, _ref_naive_max_index)
        or _af_eval_check(eval_result, _ref_max_value_landing)
    )


def _cp_panics_on_dead_end_compute(ctx: dict) -> bool:
    """DIRECT: the candidate returns -1 on at least one probe that has
    an interior zero (i.e., it panics on a dead-end position).
    """
    eval_result = ctx["eval_result"]
    if not eval_result.probe_results:
        return False
    for r in eval_result.probe_results:
        if r.candidate_output is None:
            continue
        nums = list(r.nums)
        if len(nums) <= 1:
            continue
        has_interior_zero = any(nums[i] == 0 for i in range(len(nums) - 1))
        if has_interior_zero and r.candidate_output == -1:
            return True
    return False


def _cp_uses_memoization_compute(ctx: dict) -> bool:
    """EXCLUDED: LC45 jump-game is not sub-problem-decomposable;
    memoization does not apply. Always returns False; transfer=EXCLUDED
    on the entry.
    """
    return False


def _cp_state_space_bounded_by_array_length_compute(ctx: dict) -> bool:
    """RE_DERIVE: the candidate is a BFS (state space = n positions).
    This is the LC45 re-derivation of LC322's
    `state_space_bounded_by_amount`.
    """
    return _af_eval_check(ctx["eval_result"], _ref_bfs_truth)


# ---------------------------------------------------------------------------
# Build registry entries in dependency order
# ---------------------------------------------------------------------------


def _entry(
    name: str,
    category: SymbolCategory,
    compute: Callable,
    signature: tuple[str, ...] = (),
    transfer: str = "N/A",
    manifold_id: str | None = None,
) -> LC45Entry:
    return LC45Entry(
        name=name,
        category=category,
        compute=compute,
        input_signature=signature,
        transfer=transfer,
        manifold_id=manifold_id,
    )


def _build_entries() -> tuple[LC45Entry, ...]:
    entries: list[LC45Entry] = []
    # ── Algorithm-family (5) ──
    entries.append(_entry(
        "uses_bfs_with_visited", SymbolCategory.ALGORITHM_FAMILY,
        _uses_bfs_with_visited_compute, ("eval_result",)))
    entries.append(_entry(
        "uses_naive_max_index", SymbolCategory.ALGORITHM_FAMILY,
        _uses_naive_max_index_compute, ("eval_result",)))
    entries.append(_entry(
        "uses_max_value_landing", SymbolCategory.ALGORITHM_FAMILY,
        _uses_max_value_landing_compute, ("eval_result",)))
    entries.append(_entry(
        "uses_uniform_formula", SymbolCategory.ALGORITHM_FAMILY,
        _uses_uniform_formula_compute, ("eval_result",)))
    entries.append(_entry(
        "uses_bounded_lookahead", SymbolCategory.ALGORITHM_FAMILY,
        _uses_bounded_lookahead_compute, ("eval_result",)))
    # ── Tie-breaker (3) ──
    entries.append(_entry(
        "picks_max_index_on_tie", SymbolCategory.TIE_BREAKER,
        _picks_max_index_on_tie_compute, ("eval_result",)))
    entries.append(_entry(
        "picks_max_value_on_tie", SymbolCategory.TIE_BREAKER,
        _picks_max_value_on_tie_compute, ("eval_result",)))
    entries.append(_entry(
        "picks_closest_on_tie", SymbolCategory.TIE_BREAKER,
        _picks_closest_on_tie_compute, ("eval_result",)))
    # ── Return-semantics (3) ──
    entries.append(_entry(
        "output_equals_reachable_count", SymbolCategory.RETURN_SEMANTICS,
        _output_equals_reachable_count_compute,
        ("nums", "candidate_output")))
    entries.append(_entry(
        "output_off_by_one_in_bfs", SymbolCategory.RETURN_SEMANTICS,
        _output_off_by_one_in_bfs_compute,
        ("nums", "candidate_output")))
    entries.append(_entry(
        "returns_minus_one_on_zero", SymbolCategory.RETURN_SEMANTICS,
        _returns_minus_one_on_zero_compute,
        ("nums", "candidate_output")))
    # ── Oracle-dependent basic (5) ──
    entries.append(_entry(
        "is_reachable", SymbolCategory.ORACLE_DEPENDENT,
        _is_reachable_compute, ("nums",)))
    entries.append(_entry(
        "optimal_jump_count", SymbolCategory.ORACLE_DEPENDENT,
        _optimal_jump_count_compute, ("nums",)))
    entries.append(_entry(
        "frontier_size_at_target", SymbolCategory.ORACLE_DEPENDENT,
        _frontier_size_at_target_compute, ("nums",)))
    entries.append(_entry(
        "bfs_depth_to_target", SymbolCategory.ORACLE_DEPENDENT,
        _bfs_depth_to_target_compute, ("nums",)))
    entries.append(_entry(
        "dead_end_present", SymbolCategory.ORACLE_DEPENDENT,
        _dead_end_present_compute, ("nums",)))
    # ── Oracle-dependent derived (5) ──
    entries.append(_entry(
        "is_uniform_array", SymbolCategory.ORACLE_DEPENDENT,
        _is_uniform_array_compute, ("nums",)))
    entries.append(_entry(
        "has_interior_zero", SymbolCategory.ORACLE_DEPENDENT,
        _has_interior_zero_compute, ("nums",)))
    entries.append(_entry(
        "optimal_jumps_is_one", SymbolCategory.ORACLE_DEPENDENT,
        _optimal_jumps_is_one_compute, ("nums",)))
    entries.append(_entry(
        "bfs_visited_count", SymbolCategory.ORACLE_DEPENDENT,
        _bfs_visited_count_compute, ("nums",)))
    entries.append(_entry(
        "bfs_max_frontier_width", SymbolCategory.ORACLE_DEPENDENT,
        _bfs_max_frontier_width_compute, ("nums",)))
    # ── Manifold predicates (12: 2 per manifold) ──
    for manifold_id in LC45_MANIFOLDS:
        entries.append(_entry(
            f"greedy_horizon_collapses_on_{manifold_id}",
            SymbolCategory.ORACLE_DEPENDENT,
            _manifold_predicate_compute(manifold_id, "greedy_horizon_collapses"),
            ("eval_result", "manifold_probe_ids"),
            manifold_id=manifold_id,
        ))
        entries.append(_entry(
            f"bfs_agrees_with_truth_on_{manifold_id}",
            SymbolCategory.ORACLE_DEPENDENT,
            _manifold_predicate_compute(manifold_id, "bfs_agrees_with_truth"),
            ("eval_result", "manifold_probe_ids"),
            manifold_id=manifold_id,
        ))
    # ── Cross-problem (5) ──
    entries.append(_entry(
        "uses_exhaustive_search", SymbolCategory.CROSS_PROBLEM,
        _cp_uses_exhaustive_search_compute, ("eval_result",),
        transfer=TRANSFER_DIRECT))
    entries.append(_entry(
        "uses_greedy_tie_breaker", SymbolCategory.CROSS_PROBLEM,
        _cp_uses_greedy_tie_breaker_compute, ("eval_result",),
        transfer=TRANSFER_DIRECT))
    entries.append(_entry(
        "panics_on_dead_end", SymbolCategory.CROSS_PROBLEM,
        _cp_panics_on_dead_end_compute, ("eval_result",),
        transfer=TRANSFER_DIRECT))
    entries.append(_entry(
        "uses_memoization", SymbolCategory.CROSS_PROBLEM,
        _cp_uses_memoization_compute, ("eval_result",),
        transfer=TRANSFER_EXCLUDED))
    entries.append(_entry(
        "state_space_bounded_by_array_length", SymbolCategory.CROSS_PROBLEM,
        _cp_state_space_bounded_by_array_length_compute, ("eval_result",),
        transfer=TRANSFER_RE_DERIVE))
    return tuple(entries)


_LC45_REGISTRY_INSTANCE = _LC45Registry()
_LC45_REGISTRY_INSTANCE.entries = _build_entries()
_LC45_REGISTRY_INSTANCE.names = {e.name for e in _LC45_REGISTRY_INSTANCE.entries}


LC45_SYMBOL_REGISTRY: _LC45Registry = _LC45_REGISTRY_INSTANCE
