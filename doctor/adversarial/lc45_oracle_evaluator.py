"""LC45 Jump Game II — Oracle Evaluator.

The LC45 bimaristan oracle. Evaluates a black-box candidate function
against a set of probes. The BFS survivor (`lc45_bfs_depth_cutoff`)
defines ground truth. Per-probe and aggregated trace features are
collected for use by the LC45 symbol registry.

Mirror structure: lc322_oracle.py (LC322OracleEvaluator), with the
bimaristan-specific extensions:
  - LC45Probe (per-probe typed input)
  - LC45TraceFeatures (per-probe trace stats)
  - LC45ProbeResult (per-probe evaluation result)
  - LC45TraceSummary (aggregated trace stats)
  - LC45EvaluationResult (full evaluation)
  - LC45OracleEvaluator (the evaluator class)

The bimaristan layer is self-contained: trace features come from
running BFS on the probe (the canonical LC45 oracle) and from
comparing the candidate's output to that oracle. The layer does NOT
depend on the full Doctor pipeline.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Probe and result dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LC45Probe:
    """A single LC45 probe instance.

    probe_id: stable identifier (e.g., 'p_lc45_0001')
    nums: the input list (tuple for hashability)
    expected_output: oracle output (BFS min-jump count)
    manifold_id: which of the 6 LC45 manifolds this probe belongs to
    """
    probe_id: str
    nums: tuple[int, ...]
    expected_output: int
    manifold_id: str


@dataclass(frozen=True)
class LC45TraceFeatures:
    """Per-probe trace features.

    visited/max_depth/edges/max_width come from running BFS on the probe
    (the canonical oracle). landing is the candidate's output (the jump
    count it reports; None if the candidate raised an exception).
    output_equals_reachable_count and output_off_by_one are booleans
    comparing the candidate's output to (a) the BFS reachable count
    and (b) the BFS oracle's output.
    """
    visited: int
    max_depth: int
    edges: int
    max_width: int
    landing: int | None
    output_equals_reachable_count: bool
    output_off_by_one: bool


@dataclass(frozen=True)
class LC45ProbeResult:
    """The result of evaluating a candidate on a single probe."""
    probe_id: str
    nums: tuple[int, ...]
    candidate_output: int | None
    oracle_output: int
    correct: bool
    exception: str | None
    trace_features: LC45TraceFeatures


@dataclass(frozen=True)
class LC45TraceSummary:
    """Aggregated trace features across all probes."""
    visited_mean: float
    max_depth_mean: float
    edges_mean: float
    max_width_mean: float
    landing_distribution: dict[int, int]
    output_equals_reachable_count_count: int
    output_off_by_one_count: int
    total_probes: int
    correct_count: int


@dataclass(frozen=True)
class LC45EvaluationResult:
    """The full evaluation result."""
    candidate_id: str
    probe_results: tuple[LC45ProbeResult, ...]
    summary: LC45TraceSummary


# ---------------------------------------------------------------------------
# BFS trace helper (self-contained: no Doctor pipeline dependency)
# ---------------------------------------------------------------------------


def _bfs_trace(nums: list[int]) -> dict[str, int]:
    """Run BFS on the probe and return trace statistics.

    Returns a dict with: visited, max_depth, edges, max_width, output,
    reachable_count, frontier_size_at_target, bfs_depth_to_target.

    reachable_count counts positions reachable from start INCLUDING the
    target (the last index) when the BFS reaches it. This makes
    `reachable_count == len(nums)` for fully-reachable arrays.
    """
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
# Oracle Evaluator
# ---------------------------------------------------------------------------


class LC45OracleEvaluator:
    """Evaluates a black-box candidate function on a set of LC45 probes.

    The BFS survivor (`lc45_bfs_depth_cutoff`) is the canonical oracle;
    the evaluator defaults to `lc45_brute_force` (the same BFS) when
    no oracle is provided. A different oracle can be passed to the
    constructor for testing or experimental purposes.

    Mirror structure: LC322OracleEvaluator.
    """

    def __init__(self, oracle: Callable[[list[int]], int] | None = None) -> None:
        if oracle is None:
            from doctor.adversarial.lc45_ground_truth import lc45_brute_force
            oracle = lc45_brute_force
        self._oracle = oracle

    @property
    def oracle(self) -> Callable[[list[int]], int]:
        return self._oracle

    def evaluate(
        self,
        candidate: Callable[[list[int]], int],
        probes: list[LC45Probe],
        candidate_id: str = "candidate",
    ) -> LC45EvaluationResult:
        probe_results: list[LC45ProbeResult] = []
        for probe in probes:
            probe_results.append(self._evaluate_single(candidate, probe))
        return LC45EvaluationResult(
            candidate_id=candidate_id,
            probe_results=tuple(probe_results),
            summary=self._summarize(probe_results),
        )

    def _evaluate_single(
        self,
        candidate: Callable[[list[int]], int],
        probe: LC45Probe,
    ) -> LC45ProbeResult:
        nums_list = list(probe.nums)
        oracle_output = probe.expected_output
        try:
            candidate_output = int(candidate(nums_list))
            exception: str | None = None
        except Exception as exc:
            candidate_output = None
            exception = f"{type(exc).__name__}: {exc}"
        correct = (candidate_output == oracle_output)
        bfs = _bfs_trace(nums_list)
        reachable_count = bfs["reachable_count"]
        output_equals_reachable_count = (
            candidate_output is not None and candidate_output == reachable_count
        )
        output_off_by_one = (
            candidate_output is not None
            and oracle_output >= 0
            and abs(candidate_output - oracle_output) == 1
        )
        trace = LC45TraceFeatures(
            visited=bfs["visited"],
            max_depth=bfs["max_depth"],
            edges=bfs["edges"],
            max_width=bfs["max_width"],
            landing=candidate_output,
            output_equals_reachable_count=output_equals_reachable_count,
            output_off_by_one=output_off_by_one,
        )
        return LC45ProbeResult(
            probe_id=probe.probe_id,
            nums=probe.nums,
            candidate_output=candidate_output,
            oracle_output=oracle_output,
            correct=correct,
            exception=exception,
            trace_features=trace,
        )

    def _summarize(self, results: list[LC45ProbeResult]) -> LC45TraceSummary:
        n = len(results)
        if n == 0:
            return LC45TraceSummary(
                visited_mean=0.0, max_depth_mean=0.0, edges_mean=0.0,
                max_width_mean=0.0, landing_distribution=dict(),
                output_equals_reachable_count_count=0,
                output_off_by_one_count=0,
                total_probes=0, correct_count=0,
            )
        visited_mean = sum(r.trace_features.visited for r in results) / n
        max_depth_mean = sum(r.trace_features.max_depth for r in results) / n
        edges_mean = sum(r.trace_features.edges for r in results) / n
        max_width_mean = sum(r.trace_features.max_width for r in results) / n
        landing_dist: dict[int, int] = {}
        for r in results:
            if r.candidate_output is not None:
                landing_dist[r.candidate_output] = (
                    landing_dist.get(r.candidate_output, 0) + 1
                )
        eq_count = sum(
            1 for r in results if r.trace_features.output_equals_reachable_count
        )
        off_count = sum(1 for r in results if r.trace_features.output_off_by_one)
        correct_count = sum(1 for r in results if r.correct)
        return LC45TraceSummary(
            visited_mean=visited_mean,
            max_depth_mean=max_depth_mean,
            edges_mean=edges_mean,
            max_width_mean=max_width_mean,
            landing_distribution=dict(sorted(landing_dist.items())),
            output_equals_reachable_count_count=eq_count,
            output_off_by_one_count=off_count,
            total_probes=n,
            correct_count=correct_count,
        )
