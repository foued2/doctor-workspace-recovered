# specs/lc_743_problem_spec.md
# LC743 Network Delay Time — Problem Specification
# Status: FROZEN — committed before solver generation
# Date: 2026-06-08

---

## 1. Problem Statement

**LC743 Network Delay Time.**

Given a directed weighted graph with `n` nodes (labeled `1` to `n`), a list of
edges `times` where `times[i] = (u_i, v_i, w_i)` represents a directed edge
from `u_i` to `v_i` with travel time `w_i`, a source node `k`, and a positive
integer `timeout` (implicit in some formulations, but not in the standard LC743
statement — see below).

**Standard LC743 formulation (no timeout parameter):**

Return the minimum time for all `n` nodes to receive the signal sent from node
`k`. If any node is unreachable from `k`, return `-1`.

**Function signature:**

```
networkDelayTime(times: List[List[int]], n: int, k: int) -> int
```

**Input constraints (standard LeetCode):**

- `1 <= n <= 100`
- `0 <= times.length <= 6000`
- `times[i].length == 3`
- `1 <= u_i, v_i <= n`
- `1 <= w_i <= 100`
- All `times[i]` are distinct

**Output:**

- An integer: the maximum shortest distance from `k` to any reachable node
  (i.e., the time when the last node receives the signal).
- `-1` if any node is unreachable from `k`.

**Example:**

```
Input: n=3, times=[[2,1,1],[2,3,1], [3,4,1]], k=2
Output: 2
Explanation: Node 1 receives at t=1, node 3 at t=1, node 4 at t=2.
             The answer is max(1,1,2) = 2.
```

```
Input: n=1, times=[], k=1
Output: 0
Explanation: Only one node, it receives the signal immediately.
```

---

## 2. Oracle Definition

The oracle evaluates a solver's output against the correct answer for each
test case. A solver "passes" a case if its output equals the oracle's answer.
A solver "fails" a case if its output differs.

When a solver fails, the oracle assigns a **primary failure direction** from
the following four categories, pre-declared before any solver is written.

### Failure Directions

| ID | Name | Definition |
|----|------|------------|
| F1 | `UNDER_PROPAGATION` | Solver returns `-1` on a connected graph (all nodes reachable from `k`), or solver returns a value but fails to reach nodes that are reachable. |
| F2 | `OVER_COST_BIAS` | Solver returns a numeric value but it is too high (greater than the correct answer). Caused by incorrect relaxation updates, wrong distance initialization, or failure to propagate shortest distances. |
| F3 | `PRIORITY_ORDER_FAILURE` | Solver returns an incorrect result caused by wrong processing order: using BFS instead of Dijkstra, heap mismanagement (push without decrease-key, wrong comparator), or processing nodes out of shortest-distance order. |
| F4 | `DISCONNECTED_MISHANDLING` | Solver fails specifically on graphs with unreachable nodes: returns a finite value instead of `-1`, or propagates sentinel values incorrectly through unreachable components. |

### Tie-Breaking Rule

If a solver fails multiple modes simultaneously on a single test case, the
oracle assigns the **first** detectable mode in the list order
(F1 → F2 → F3 → F4). Detection is based on the output alone, without
inspecting solver internals.

**Detection rules (applied in order):**

1. **F1 detectable if:** the graph is connected AND the solver returns `-1`,
   OR the graph is connected AND the solver returns a value that does not
   match the oracle (undercount).
2. **F2 detectable if:** the solver returns a positive integer that is
   strictly greater than the correct answer.
3. **F3 detectable if:** the solver returns a value that is not equal to the
   correct answer and is not covered by F1 or F2 (i.e., the answer is wrong
   but not consistently too high, and the graph is connected).
4. **F4 detectable if:** the graph is disconnected AND the solver returns a
   finite value (not `-1`).

**Mutual exclusivity note:** F1 and F4 are mutually exclusive by graph
connectivity. F1 applies only to connected graphs; F4 applies only to
disconnected graphs. No case can trigger both. F2 and F3 may co-occur on
connected graphs; the tie-breaking rule resolves this by assigning F2 first.

---

## 3. Failure Taxonomy Justification

### F1 — UNDER_PROPAGATION

This direction is detectable from the output alone: on a connected graph, the
correct answer is always a positive integer (or 0 for single-node graphs), so
a return value of `-1` is immediately identifiable as wrong. Undercount
(returning a value less than the correct answer) is detectable by direct
comparison. This direction is structurally distinct from the others because it
represents a failure to propagate the signal to all reachable nodes — the
solver "under-reaches." It corresponds to real solver errors such as: early
termination of the shortest-path algorithm (stopping when the target is found
instead of when all nodes are visited), visiting only a subset of neighbors,
or incorrectly marking nodes as visited before propagation completes. On
LC743, this is a natural failure class because the problem explicitly requires
all nodes to receive the signal.

### F2 — OVER_COST_BIAS

This direction is detectable from the output alone: the solver returns a
positive integer strictly greater than the correct answer. Overcount is
structurally distinct from undercount (F1) and wrong-but-not-systematic (F3)
because it represents a consistent bias toward longer paths — the solver
"over-estimates." It corresponds to real solver errors such as: failing to
relax an edge (not updating a neighbor's distance when a shorter path is
found), using the wrong weight in relaxation, initializing distances to
infinity but failing to propagate from the source, or accumulating path
weights instead of taking the maximum. On LC743, over-cost bias is the most
common failure class for implementations that correctly identify the algorithm
structure (Dijkstra/BFS) but make an error in the relaxation step.

### F3 — PRIORITY_ORDER_FAILURE

This direction is detectable from the output alone: the solver returns a
value that is incorrect but is not consistently too high (not F2) and the
graph is connected (not F1 or F4). The output is wrong in a way that
suggests the processing order was incorrect. This direction is structurally
distinct from F2 because the error is not systematic overestimation — it may
overestimate on some cases and underestimate on others, depending on the
graph structure. It corresponds to real solver errors such as: using BFS
(unweighted) instead of Dijkstra (weighted) on a weighted graph, using a
min-heap with the wrong comparator (max-heap instead of min-heap), pushing
to the heap without performing decrease-key (processing stale entries), or
processing nodes in arbitrary order. On LC743, this is a critical failure
class because the problem requires correct shortest-path computation on a
weighted graph, and the processing order directly determines correctness.

### F4 — DISCONNECTED_MISHANDLING

This direction is detectable from the output alone: on a disconnected graph
(at least one node unreachable from `k`), the correct answer is `-1`, so a
return value of any finite integer is immediately identifiable as wrong. This
direction is structurally distinct from F1 because it applies only to
disconnected graphs, while F1 applies only to connected graphs. It is
distinct from F2 and F3 because those directions apply to connected graphs
where the answer is a finite integer. It corresponds to real solver errors
such as: always returning the maximum distance among reachable nodes without
checking whether all nodes were reached, propagating `-1` as a sentinel but
overwriting it with a finite value during relaxation, or not maintaining a
count of visited/reached nodes. On LC743, this is a natural failure class
because disconnected graphs are a valid input, and the `-1` return requires
an explicit reachability check that many implementations omit.

---

## 4. Expected Failure Distribution Prior

The target distribution over failure directions for the 30-solver population,
declared before any solver is written.

| Direction | Target fraction | Expected count (of 30) |
|-----------|----------------|------------------------|
| F1: UNDER_PROPAGATION | 0.15 | 4–5 |
| F2: OVER_COST_BIAS | 0.35 | 10–11 |
| F3: PRIORITY_ORDER_FAILURE | 0.35 | 10–11 |
| F4: DISCONNECTED_MISHANDLING | 0.15 | 4–5 |
| **Total** | **1.00** | **30** |

**Justification:**

- F2 and F3 together account for 70% of the population. These are the two
  most common failure classes for shortest-path problems: over-cost bias
  (incorrect relaxation) and priority-order failure (wrong processing order).
  Both are well-documented failure modes in Dijkstra implementations.

- F1 accounts for 15%. Under-propagation is less common than over-cost or
  priority failures because the standard algorithm structure (visit all nodes)
  naturally avoids it. It occurs when implementations terminate early or
  have bugs in neighbor traversal.

- F4 accounts for 15%. Disconnected-mishandling is less common because the
  `-1` return is a simple check. It occurs when implementations omit the
  reachability check or propagate sentinels incorrectly.

**Aggregate consistency check:** After solver generation, the actual
distribution π̂ is computed. The check passes if max_i |π̂_i - π_i| ≤ 1/30
(≤ 0.033). If the check fails, the solver pack is regenerated with adjusted
target counts.

---

## 5. Reachability Constraint

**At least 20% of test cases must have disconnected graphs.**

A "disconnected graph" is defined as a graph where at least one node in
`{1, ..., n}` is not reachable from the source node `k` via directed edges.

**Formal declaration:**

Let T be the set of test cases. Let D ⊆ T be the subset where the graph is
disconnected. The constraint is:

    |D| / |T| ≥ 0.20

This is a hard parameter, not a suggestion. The constraint ensures that:

1. F4 (DISCONNECTED_MISHANDLING) has sufficient test coverage.
2. The oracle's F1/F4 mutual exclusivity boundary is exercised.
3. Solvers that always return a finite value (ignoring the `-1` case) are
   detected.

**Minimum guaranteed count:** For a probe set of 30 cases (5 per axis, 6
axes), at least 6 cases (ceil(30 × 0.20) = 6) must be disconnected. For a
probe set of 15 observed cases, at least 3 must be disconnected.

**Implementation note:** The generator must produce disconnected graphs
explicitly. Disconnected graphs are not a natural byproduct of random graph
generation at sufficient density; they must be constructed with at least one
isolated node or unreachable component.

---

## 6. Commitment Record

This file is committed as the LC743 problem specification. The following
are frozen:

| Component | Status | Frozen when |
|-----------|--------|-------------|
| Problem statement (LC743 standard) | FROZEN | This file |
| Oracle definition (4 directions) | FROZEN | This file |
| Tie-breaking rule (F1→F2→F3→F4) | FROZEN | This file |
| Failure taxonomy justification | FROZEN | This file |
| Prior distribution (0.15/0.35/0.35/0.15) | FROZEN | This file |
| Reachability constraint (≥ 20%) | FROZEN | This file |

The following are NOT frozen (defined elsewhere):

| Component | Defined in |
|-----------|------------|
| Probe families (6 axes) | specs/GEOMETRY_FREEZE.md §2 (after N is determined) |
| Solver population (30 solvers) | Solver generation step (after this file) |
| Observation budget (B=15) | Midweather-Fingerprint-Gate freeze |

---

*End of lc_743_problem_spec.md*
