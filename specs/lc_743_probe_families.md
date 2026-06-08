# specs/lc_743_probe_families.md
# LC743 Probe Families — Derived from Input Space Structure
# Status: FROZEN — committed before probe generation
# Date: 2026-06-08
# Procedure: §2 of GEOMETRY_FREEZE.md, applied to LC743 input space

---

## Derivation Note

The §2 procedure in GEOMETRY_FREEZE.md states "the number of families is N
(the number of failure directions from §1)." For LC743, N = 4 failure
directions. However, LC743's input space has 6 independently variable
structural properties (the five axes listed in the task plus the density
axis extracted from topology). Each property defines a distinct probe
generator that produces inputs stressing that property. The 6 families are
derived from these 6 structural properties, not from the 4 failure
directions. Some families stress the same failure direction; this is
expected and does not violate non-overlap (non-overlap applies to probes,
not to failure-direction predictions).

---

## Family 1: CONNECTIVITY_STRESS

### 1.1 Definition

Probes that vary graph connectivity: the presence or absence of directed
paths from source `k` to every node. This family tests whether the solver
correctly identifies unreachable nodes and returns `-1` when any exist.

### 1.2 Probes

| ID | Description |
|----|-------------|
| c1 | Graph with exactly 1 unreachable node (out of N ≥ 3). Correct answer: -1. Tests whether solver detects a single missing reachability. |
| c2 | Graph with 2 unreachable nodes in separate components. Correct answer: -1. Tests whether solver detects multiple disconnected components. |
| c3 | Graph where source `k` has no outgoing edges and N > 1. Correct answer: -1. Tests whether solver handles an isolated source. |
| c4 | Graph that appears connected but has a directed bridge whose removal disconnects a subset. Correct answer: -1. Tests sensitivity to directed connectivity vs undirected connectivity. |
| c5 | Graph with 1 unreachable node that is reachable via a very long path (N-1 hops). Correct answer: a finite value. Tests that the solver does not confuse long paths with unreachable nodes. |

### 1.3 Predicted Failure-Direction Correlation

**Stresses F4 (DISCONNECTED_MISHANDLING).** Probes c1–c4 have disconnected
graphs; a solver that returns a finite value instead of `-1` fails here.
Probe c5 is connected but tests the boundary between "long path" and
"unreachable," which can trigger F1 (UNDER_PROPAGATION) if the solver
incorrectly returns `-1` for a reachable node.

### 1.4 Non-Overlap Declaration

No probe in this family duplicates a probe in any other family. All probes
in this family have at least one unreachable node (c1–c4) or a directed
bridge structure (c5), which no other family produces.

---

## Family 2: WEIGHT_MAGNITUDE_STRESS

### 2.1 Definition

Probes that vary edge weight values while keeping graph structure fixed.
This family tests whether the solver correctly processes weighted edges
and computes shortest-path distances under different weight regimes.

### 2.2 Probes

| ID | Description |
|----|-------------|
| w1 | All edges have weight 1. Correct answer equals the minimum hop count from `k` to the farthest node. Tests basic Dijkstra/BFS behavior on uniform weights. |
| w2 | All edges have weight 100. Correct answer equals 100 × (minimum hop count). Tests that the solver multiplies weights correctly and does not treat all edges as unit weight. |
| w3 | Mixed weights: some edges weight 1, some weight 50. Correct path may use a single weight-50 edge to skip many weight-1 edges. Tests relaxation correctness under mixed magnitudes. |
| w4 | One edge on the critical path has weight equal to the maximum allowed (100). Correct answer is dominated by this single edge. Tests that the solver handles extreme weight values without overflow or incorrect comparison. |
| w5 | Weights are strictly decreasing along the shortest path (e.g., 10, 8, 5, 3). Correct answer is the sum. Tests relaxation when later edges have smaller weights than earlier ones. |

### 2.3 Predicted Failure-Direction Correlation

**Stresses F2 (OVER_COST_BIAS).** Incorrect weight handling (treating
weights as uniform, failing to sum correctly, or using the wrong weight in
relaxation) produces an overcount. Also stresses F3 (PRIORITY_ORDER_FAILURE)
if weight mismanagement causes incorrect heap ordering.

### 2.4 Non-Overlap Declaration

No probe in this family duplicates a probe in any other family. All probes
in this family have connected graphs with varying edge weights. No other
family varies weight values as its primary structural property.

---

## Family 3: SOURCE_CENTRALITY_STRESS

### 3.1 Definition

Probes that vary the position of source node `k` within the graph: from
peripheral (leaf node, few outgoing edges) to central (hub, many outgoing
edges). This family tests whether the solver's behavior depends on the
source's structural role.

### 3.2 Probes

| ID | Description |
|----|-------------|
| s1 | Source `k` is a leaf node with only incoming edges (no outgoing edges) and N > 1. Correct answer: -1 (no nodes reachable from `k` except `k` itself, but `k` cannot reach others). Tests propagation from a dead-end source. |
| s2 | Source `k` is a hub with outgoing edges to all other N-1 nodes. Correct answer: max weight among direct edges. Tests that the solver explores all direct neighbors. |
| s3 | Source `k` is isolated (no edges at all) and N = 1. Correct answer: 0. Tests the degenerate single-node case. |
| s4 | Source `k` is at the end of a linear chain (k → v1 → v2 → ... → v_{N-1}). Correct answer: sum of all edge weights. Tests sequential propagation through a chain. |
| s5 | Source `k` connects to exactly one intermediate node, which then fans out to all other nodes. Correct answer: max(k→intermediate weight, intermediate→farthest weight). Tests two-hop propagation. |

### 3.3 Predicted Failure-Direction Correlation

**Neutral across directions.** Source centrality does not systematically
stress one failure direction over another. A peripheral source (s1) may
trigger F4 (DISCONNECTED_MISHANDLING) if the solver fails to recognize the
graph is disconnected from `k`. A hub source (s2) may stress F3
(PRIORITY_ORDER_FAILURE) if the solver processes neighbors in the wrong
order. But neither effect is systematic; the family is included for
completeness of the input-space coverage.

### 3.4 Non-Overlap Declaration

No probe in this family duplicates a probe in any other family. All probes
in this family vary the source node's structural position. No other family
varies `k` as its primary structural property.

---

## Family 4: DENSITY_STRESS

### 4.1 Definition

Probes that vary graph density: the ratio of actual edges to the maximum
possible edges (N × (N-1) for a directed graph). This family tests whether
the solver's behavior changes under sparse vs dense edge configurations.

### 4.2 Probes

| ID | Description |
|----|-------------|
| d1 | Extremely sparse: N nodes, N-1 edges forming a single directed path from `k`. Correct answer: sum of all edge weights. Tests traversal of a minimal connected graph. |
| d2 | Sparse with one cycle: N nodes, N edges forming a path plus one back-edge. Correct answer: sum of path weights (cycle does not reduce the max distance). Tests that the solver handles cycles without infinite loops. |
| d3 | Star topology: source `k` at center, edges from `k` to all N-1 other nodes. No edges between non-source nodes. Correct answer: max edge weight from `k`. Tests direct fan-out with no intermediate hops. |
| d4 | Dense: ~N²/4 edges. Graph is strongly connected with many redundant paths. Correct answer: shortest-path max distance. Tests solver performance on heavy edge lists. |
| d5 | Complete directed graph: all N×(N-1) possible edges present. Every node reachable from every other in 1 hop. Correct answer: min over direct edge weights from `k`. Tests that the solver does not get lost in combinatorial edge enumeration. |

### 4.3 Predicted Failure-Direction Correlation

**Stresses F3 (PRIORITY_ORDER_FAILURE).** Dense graphs (d4, d5) increase
the number of relaxation steps and heap operations, amplifying errors in
processing order. Sparse graphs (d1, d2) test whether the solver correctly
traverses minimal structures without skipping edges.

### 4.4 Non-Overlap Declaration

No probe in this family duplicates a probe in any other family. All probes
in this family vary edge count relative to N while keeping weights uniform
(weight = 1 for all edges in this family). No other family varies density
as its primary structural property. The weight-uniform constraint ensures
no overlap with Family 2 (WEIGHT_MAGNITUDE_STRESS).

---

## Family 5: PATH_MULTIPLICITY_STRESS

### 5.1 Definition

Probes that vary the number of distinct shortest paths between pairs of
nodes. This family tests whether the solver correctly identifies the
maximum shortest-path distance when multiple paths of equal length exist.

### 5.2 Probes

| ID | Description |
|----|-------------|
| m1 | Unique shortest path between every pair of nodes (tree structure). Correct answer is determined by the single path. Tests baseline behavior with no path ambiguity. |
| m2 | Exactly 2 shortest paths of equal length between the source and the farthest node. Correct answer equals the common path length. Tests that the solver does not double-count or incorrectly choose. |
| m3 | Many shortest paths (exponential in N) between source and farthest node, all of equal length. Correct answer is the common path length. Tests behavior under combinatorial path explosion. |
| m4 | All shortest paths pass through a single bottleneck edge. Correct answer is dominated by this edge. Tests that the solver identifies the critical edge correctly. |
| m5 | Two paths of equal length to the farthest node, but one passes through a high-weight edge and the other through low-weight edges that sum to the same total. Correct answer is the common total. Tests relaxation under equal-total different-decomposition paths. |

### 5.3 Predicted Failure-Direction Correlation

**Stresses F2 (OVER_COST_BIAS).** When multiple paths exist, a solver that
incorrectly selects a longer path (due to relaxation errors) will overcount.
Also stresses F3 (PRIORITY_ORDER_FAILURE) if the solver processes nodes in
an order that causes it to settle on a suboptimal path before finding the
optimal one.

### 5.4 Non-Overlap Declaration

No probe in this family duplicates a probe in any other family. All probes
in this family have connected graphs with varying path multiplicity. No
other family varies the number of shortest paths as its primary structural
property. The weight-uniform constraint (all weights = 1) ensures no overlap
with Family 2 (WEIGHT_MAGNITUDE_STRESS). The connected-graph constraint
ensures no overlap with Family 1 (CONNECTIVITY_STRESS).

---

## Family 6: SCALE_STRESS

### 6.1 Definition

Probes that vary node count N while keeping other structural properties
approximately fixed. This family tests whether the solver's behavior
degrades under increasing problem size.

### 6.2 Probes

| ID | Description |
|----|-------------|
| z1 | N = 2, 1 edge. Minimal non-trivial graph. Correct answer: edge weight. Tests baseline on the smallest possible input. |
| z2 | N = 5, 4 edges forming a path. Correct answer: sum of 4 edge weights. Tests small-graph behavior. |
| z3 | N = 50, ~100 edges (sparse). Correct answer: shortest-path max distance. Tests medium-scale behavior. |
| z4 | N = 100 (maximum allowed), ~200 edges (sparse). Correct answer: shortest-path max distance. Tests maximum-scale behavior under sparsity. |
| z5 | N = 100 (maximum allowed), ~3000 edges (dense). Correct answer: shortest-path max distance. Tests maximum-scale behavior under density. |

### 6.3 Predicted Failure-Direction Correlation

**Neutral across directions.** Scale does not systematically stress one
failure direction. Small graphs (z1, z2) may not expose bugs that only
manifest at scale. Large sparse graphs (z4) may stress F3
(PRIORITY_ORDER_FAILURE) if the solver has O(N²) behavior that degrades.
Large dense graphs (z5) may stress F2 (OVER_COST_BIAS) if relaxation errors
accumulate. But neither effect is systematic; the family tests scalability,
not a specific failure mode.

### 6.4 Non-Overlap Declaration

No probe in this family duplicates a probe in any other family. All probes
in this family vary N as the primary structural property. No other family
varies node count as its primary structural property. The weight-uniform
constraint (all weights = 1) ensures no overlap with Family 2. The
connected-graph constraint ensures no overlap with Family 1.

---

## Cross-Family Non-Overlap Summary

| Family | Primary structural property | Varies | Fixed |
|--------|----------------------------|--------|-------|
| CONNECTIVITY_STRESS | Graph connectivity | Reachability from `k` | Weights, density, N, source position |
| WEIGHT_MAGNITUDE_STRESS | Edge weight values | Weight magnitudes | Connectivity, density, N, source position |
| SOURCE_CENTRALITY_STRESS | Source node position | `k`'s structural role | Weights, connectivity, density, N |
| DENSITY_STRESS | Edge count / N² | Density ratio | Weights (=1), connectivity, N, source position |
| PATH_MULTIPLICITY_STRESS | Number of shortest paths | Path count | Weights (=1), connectivity, N, source position |
| SCALE_STRESS | Node count N | N | Weights (=1), connectivity, density, source position |

Each family varies exactly one structural property while holding the others
fixed (to the extent possible within the problem's constraints). No probe
in any family duplicates a probe in any other family.

---

## Failure-Direction Coverage Summary

| Direction | Families that stress it | Families that are neutral |
|-----------|------------------------|--------------------------|
| F1: UNDER_PROPAGATION | CONNECTIVITY_STRESS (c5 boundary) | WEIGHT_MAGNITUDE, SOURCE_CENTRALITY, DENSITY, PATH_MULTIPLICITY, SCALE |
| F2: OVER_COST_BIAS | WEIGHT_MAGNITUDE_STRESS, PATH_MULTIPLICITY_STRESS | CONNECTIVITY, SOURCE_CENTRALITY, DENSITY, SCALE |
| F3: PRIORITY_ORDER_FAILURE | DENSITY_STRESS, PATH_MULTIPLICITY_STRESS | CONNECTIVITY, WEIGHT_MAGNITUDE, SOURCE_CENTRALITY, SCALE |
| F4: DISCONNECTED_MISHANDLING | CONNECTIVITY_STRESS (c1–c4) | WEIGHT_MAGNITUDE, SOURCE_CENTRALITY, DENSITY, PATH_MULTIPLICITY, SCALE |

Two families (SOURCE_CENTRALITY, SCALE) are predicted neutral across
directions. This is a valid prediction per §2 — neutrality is explicitly
allowed.

---

*End of lc_743_probe_families.md*
