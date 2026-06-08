# GEOMETRY_FREEZE.md — Experimental Geometry Freeze
# Status: PARTIAL FREEZE — see §5 (halt condition assessment)
# Date: 2026-06-08

---

## Purpose

This file specifies, without reference to any specific problem, the procedures
for deriving the experimental geometry that must be frozen before any solver is
written or any probe is generated. It covers four components:

1. Failure taxonomy rule
2. Probe family generation rule
3. Solver sampling procedure
4. Perturbation weighting

Each section states the abstract procedure, names the judgment the procedure
requires, and bounds that judgment. Where a judgment cannot be made without
seeing the problem, this is stated explicitly.

---

## 1. Failure Taxonomy Rule

### Procedure

Given a problem statement P:

**Step 1.** Enumerate the set A of algorithmic strategies that a solver could
use to solve P. The set A is derived from the problem's computational
structure (e.g., dynamic programming, greedy, brute force, BFS/DFS, memoized
recursion). Each strategy a ∈ A is a distinct algorithmic approach, not a
specific implementation.

**Step 2.** For each strategy a ∈ A, identify the set D_a of structural
properties of P's input space that cause a to produce incorrect output or to
fail to terminate. Each d ∈ D_a is a property of the input (not of the
solver implementation) that triggers a specific failure mode in strategy a.

**Step 3.** The failure taxonomy is the set F = ∪_{a∈A} D_a, partitioned by
the strategy that each property defeats. Two properties d1, d2 are in the
same failure direction if they defeat the same strategy a. The failure
direction categories are the equivalence classes of F under this relation.

**Step 4.** Enumerate the failure direction categories as f_1, f_2, ..., f_N.
N is determined by the problem's structure; it is not fixed in advance.

### Named Judgments

The procedure requires one judgment that cannot be derived from the problem
statement alone:

**J1 — Strategy relevance:** Which algorithmic strategies are "relevant" to
the problem? The set A must be enumerated before any solver is written. A
strategy is relevant if a competent programmer would consider it when
solving P.

**Bounding J1:** The set A must be justifiable by reference to standard
algorithmic taxonomy (e.g., DP, greedy, BFS, backtracking). Exotic or
highly specialized strategies are excluded unless the problem statement
explicitly motivates them. The set A must be committed before any solver is
generated and must not be expanded after seeing solver behavior.

### Output

A finite set of failure direction categories {f_1, ..., f_N} with N ≥ 2,
each justified by a reference to a specific (strategy, input-property) pair.

### What This Rule Does Not Produce

- It does not produce the probe families (§2 derives those).
- It does not produce the solver population (§3 derives that).
- It does not predict which failure directions will be observed in any
  specific solver population.

---

## 2. Probe Family Generation Rule

### Procedure

Given the failure taxonomy F = {f_1, ..., f_N} from §1 and the problem's
input space I:

**Step 1.** For each failure direction f_i, construct a probe generator G_i
that produces (input, expected_output) pairs satisfying:
  (a) The input is a valid instance of P.
  (b) The input is designed to trigger f_i in at least one strategy a ∈ A.
  (c) The input does not trigger f_j for j ≠ i (orthogonality condition).

**Step 2.** Each G_i produces a family of probes. The family name is derived
from the structural property that defines f_i. The naming convention is:

    family_name = f_i.structural_property

where structural_property is a short descriptive string (e.g.,
"boundary_crossover", "scale_stress", "ordering_violation").

**Step 3.** The number of families is N (the number of failure directions
from §1). Each family contains K probes (the observation budget per family).
K must be ≥ 2 to support within-family paired analysis. K is frozen per
problem.

**Step 4.** For each family i, the K probes are split into O_obs (observed)
and D_target (held-out) subsets. The split ratio is frozen. The canonical
split is 3+2 per family (3 observed, 2 held-out), yielding 3K/5 observed
and 2K/5 held-out probes per family.

### Named Judgments

**J2 — Orthogonality:** Whether probe generator G_i truly produces inputs
that trigger f_i and not f_j for j ≠ i. This requires analyzing the
interaction between failure directions, which depends on the problem's
specific input structure.

**Bounding J2:** Orthogonality is verified empirically at freeze time by
checking that each probe triggers exactly one failure direction in a reference
solver set. If a probe triggers multiple failure directions, it is assigned
to the direction it most reliably triggers (majority vote over the reference
set). Probes that cannot be assigned uniquely are excluded.

**J3 — Family count N:** The number of families is determined by the failure
taxonomy (§1), not chosen independently. If §1 produces N failure directions,
then §2 produces N families. The number is not a free parameter.

### Output

A set of N probe families {F_1, ..., F_N}, each containing K probes, with a
frozen O_obs/D_target split per family. Total probes = N × K.

---

## 3. Solver Sampling Procedure

### Procedure

Given the failure taxonomy F = {f_1, ..., f_N} from §1:

**Step 1.** Declare a target distribution π over failure directions before
any solver is written. π = (π_1, ..., π_N) where π_i is the fraction of
the solver population expected to exhibit failure direction f_i as their
primary failure mode.

**Step 2.** The target distribution must satisfy:
  (a) π_i > 0 for all i (every failure direction is represented).
  (b) Σ π_i = 1 (the distribution is normalized).
  (c) max(π_i) ≤ 0.5 (no single failure direction dominates the population).
  (d) min(π_i) ≥ 1/(2N) (no failure direction is negligibly represented).

**Step 3.** The solver population S is generated to match π as closely as
possible. For a population of size |S|, the expected count in direction f_i
is n_i = π_i × |S|. Actual counts may differ by at most 1 from n_i
(remainder allocation by largest-remainder method).

**Step 4.** After generation, the actual distribution π̂ is computed from the
solver population and committed. The aggregate consistency check verifies
that π̂ is within the tolerance of π (max |π̂_i - π_i| ≤ 1/|S|).

### Prior Declaration

The target distribution π is a declared prior. It is committed before any
solver is written. The aggregate consistency check verifies against the
pre-declared prior, not against zero or against the observed distribution.

### Default Prior (When No Problem-Specific Information Is Available)

If no problem-specific information is available to set π, the uniform prior
is used:

    π_i = 1/N for all i

This is the maximum-entropy prior and makes no assumptions about which
failure directions will be more common.

### Named Judgments

**J4 — Prior specification:** If the uniform prior is not used, the choice
of π requires problem-specific judgment about which failure directions are
likely to be more common. This judgment must be justified in writing before
any solver is generated.

**Bounding J4:** The prior is either (a) uniform (no judgment required) or
(b) non-uniform with a written justification referencing the problem's
computational structure. The justification must be based on the problem
statement alone, not on any solver's behavior.

### Output

A declared prior π, a solver population S with actual distribution π̂, and
a verification that |π̂_i - π_i| ≤ 1/|S| for all i.

---

## 4. Perturbation Weighting

### Meta-Structure

The perturbation battery has three categories, applied in order:

- **P1 — Decision-threshold perturbations:** Variations of the
  failure_threshold parameter that defines the ACCEPT/REJECT boundary.
  These test sensitivity to the decision threshold.

- **P2 — Solver-population perturbations:** Subsamples of the solver
  population. These test sensitivity to which solvers are included.

- **P3 — Probe-family perturbations:** Knockouts of individual probe
  families from the observation budget. These test dependence on specific
  failure directions being observable.

### Counts

The number of perturbation conditions within each category is determined by
the problem geometry:

- **P1 count:** 2 conditions (threshold at 0.10 and 0.20, in addition to
  the baseline at 0.05). This is fixed across problems because the
  threshold sweep tests the same structural question regardless of problem.

- **P2 count:** 3 conditions (three fixed subsamples of the solver
  population). The subsample sizes and indices are problem-specific and
  must be committed before any runner is written.

- **P3 count:** N conditions, one per failure direction (one family knockout
  per family). This is equal to the number of probe families from §2.

### Total

Total perturbation conditions = 2 + 3 + N, where N is the number of failure
directions from §1.

For the canonical case N = 6: total = 2 + 3 + 6 = 11 perturbation
conditions.

### The "5/3/3 Split" — Clarification

The phrase "5/3/3 split" does not correspond to a fixed parameter in the
existing protocol. The existing protocol uses:
- LC322 C-5: 2 (P1) + 3 (P2) + 6 (P3) = 11
- LC3946 C-5: 2 (P1) + 3 (P2) + 6 (P3) = 11

If "5/3/3" refers to a different split (e.g., 5 probes per family, 3
observed, 2 held-out), that is the probe split from §2, not the perturbation
split.

**This section declares the perturbation structure as fixed:**
- P1: 2 conditions (threshold variations)
- P2: 3 conditions (solver subsamples)
- P3: N conditions (family knockouts, one per family)

Justification: P1 tests a decision-boundary question that is
problem-independent. P2 tests population sensitivity with 3 subsamples
(sufficient to detect solver-specific effects without exhausting the
population). P3 tests every failure direction exactly once (one knockout per
family). The structure is justified by the questions each category answers,
not by a specific numerical target.

### Named Judgments

**J5 — P2 subsample design:** The choice of which solver subsamples to use
requires problem-specific judgment about population coverage. The 3 subsamples
must be committed before any runner is written and must be chosen to have
different coverage of the solver population (e.g., first-third, middle-third,
last-third, or other systematic partition).

**Bounding J5:** The 3 subsamples are specified as explicit index lists
before any solver is generated. The index lists must be verified to include
at least one solver from each failure direction (coverage check). Subsamples
that fail the coverage check are redrawn before commitment.

### Output

A declared perturbation structure: P1 (2 conditions), P2 (3 conditions with
committed index lists), P3 (N conditions with committed knockout order).
Total = 5 + N conditions. Committed before any runner is written.

---

## 5. Halt Condition Assessment

### Question

Can this file be written without making judgment calls that require seeing the
problem?

### Answer

**Partially.** The meta-structure can be frozen. The specific parameters
cannot.

The following can be frozen without seeing the problem:
- The perturbation category structure (P1/P2/P3)
- The P1 count (2 conditions)
- The P2 count (3 conditions)
- The solver sampling procedure (uniform prior as default)
- The probe split ratio (3+2 per family)
- The orthogonality verification procedure
- The aggregate consistency check procedure

The following CANNOT be frozen without seeing the problem:
- The number of failure direction categories N (§1)
- The number of probe families (§2, depends on N)
- The specific family names (§2, derived from problem structure)
- The target distribution π if non-uniform (§3)
- The P2 subsample indices (§4, depends on solver count)
- The P3 knockout count (§4, equals N)

### Implication

The geometry cannot be fully frozen upstream of problem selection. The paper's
limitations section should state this explicitly:

> The experimental geometry (failure taxonomy, probe family count, solver
> population distribution, and perturbation battery size) is problem-dependent
> and cannot be frozen before the problem is selected. The meta-structure
> (perturbation categories, probe split ratio, sampling procedure) is frozen
> and problem-independent. The specific parameters are frozen per-problem
> after problem selection but before any solver is written or any probe is
> generated.

### What This Means for Reproducibility

The meta-structure is reproducible across problems. The specific parameters
are reproducible within a problem (frozen before execution). Cross-problem
comparison of the geometry is not meaningful unless the problems share the
same N (same number of failure directions), which is not guaranteed.

---

## 6. Commitment Record

This file is committed as a partial freeze. The following are frozen:

| Component | Status | Frozen before |
|-----------|--------|---------------|
| P1 perturbation count (2) | FROZEN | This file |
| P2 perturbation count (3) | FROZEN | This file |
| Probe split ratio (3+2) | FROZEN | This file |
| Solver sampling procedure | FROZEN | This file |
| Uniform prior as default | FROZEN | This file |
| Orthogonality verification | FROZEN | This file |
| Aggregate consistency check | FROZEN | This file |

The following are NOT frozen (require problem selection):

| Component | Status | Frozen when |
|-----------|--------|-------------|
| Failure direction count N | NOT FROZEN | After problem selection |
| Probe family count and names | NOT FROZEN | After §1 is applied |
| Target distribution π (if non-uniform) | NOT FROZEN | After problem selection |
| P2 subsample indices | NOT FROZEN | After solver population is defined |
| P3 knockout count | NOT FROZEN | After §1 is applied |

---

*End of GEOMETRY_FREEZE.md*
