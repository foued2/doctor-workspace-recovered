# Cross-Problem Transfer Hypothesis

**Date:** June 2026
**Status:** Phase 0 — hypothesis commitment, no code
**Trigger for proceeding past Phase 0:** this document committed
**Trigger for proceeding past Phase 1:** Phase 1 audit shows candidate dimensions auditable in current corpus, OR a clear plan for adding them is committed

---

## Why this document exists

The Doctor/Bimaristan project has two fully-built problem classes (LC322, LC45) with probe families designed independently for each problem. The H1a falsification (`docs/H1A_FALSIFICATION.md`) tested within-LC322 family-conditional rate separability. The LC45 C feature audit (`docs/LC45_C_POLICY_FINDING.md`) tested within-LC45 feature separability. Both are within-problem tests. Neither tests cross-problem transfer of structural properties.

The current 2-problem corpus cannot retroactively answer the cross-problem transfer question because the probe families were designed per-problem with no shared problem-independent structure. The within-problem finding "aggregate pass/fail volume is the load-bearing separator" is consistent with two readings:

- **(a) Structural**: aggregate pass/fail volume is a load-bearing separator in any problem; the family axis is problem-specific descriptive structure that doesn't add separator power
- **(b) Spurious**: this just happens to be true on LC322 and LC45 for reasons specific to those problems

A genuine test of (a) vs (b) requires problem-independent dimensions defined in advance, with probe families named identically across problems. This document commits to those dimensions and the gap threshold before any code is written. Post-hoc threshold relaxation would invalidate the test.

---

## Discriminative gap threshold (committed before running)

**Definition of `gap(D, P)` for dimension D, problem P:**

```
gap(D, P) = mean(fail_rate on D | REJECT class, problem P) - mean(fail_rate on D | ACCEPT class, problem P)
```

**Transfer on dimension D is supported if and only if all three conditions hold:**

1. **Minimum gap**: `gap(D, P) ≥ 0.20` for all three problem classes P ∈ {LC322, LC45, P3}
2. **Direction consistency**: `gap(D, P) > 0` for all three problems (ACCEPT fail rate < REJECT fail rate; no direction flips)
3. **Cross-problem variance**: `max(gap(D, P)) / min(gap(D, P)) ≤ 2.0` across the three problems

**Transfer fails on dimension D if any of:**

- Gap < 0.20 on any problem
- Direction flip (ACCEPT > REJECT on D in some problem)
- Cross-problem variance exceeds factor of 2.0 (e.g., +0.40, +0.05, +0.02)

These numbers are committed before the test runs. The "+0.40, +0.35, +0.38" example given in the plan is transfer; the "+0.40, +0.05, +0.02" example is LC322-specific. The factor-of-2 boundary is the committed cutoff.

---

## Null result definition

The data would look like this if transfer fails:

- Boundary sensitivity gap is large on the problem where boundary cases happen to be in the probe distribution, small or zero on the others
- Scale sensitivity gap shows direction flips (some problems have REJECT class failing less than ACCEPT class on large-magnitude probes)
- Monotonicity violation gap is undefined or zero on at least one problem (because the problem has no monotone subproblem structure to violate)
- No dimension simultaneously satisfies minimum gap, direction consistency, and cross-problem variance bound across all three problems

**If the data look like this, the conclusion is:** collapse dimensions defined problem-independently do not transfer across structurally distinct problem classes. The framework's structural-property claims are K-local to each problem, not general. This is a stronger and more specific negative result than the current paper's K-local FAIL.

This is recorded as a real finding, not a limitation. The paper's central claim would then be: "structured fingerprint representations do not improve decision utility on LC322, and the structural property that aggregate pass/fail volume dominates does not transfer across problems."

---

## Candidate transfer dimension 1: Boundary sensitivity

**Definition (problem-independent):**

A solver exhibits boundary sensitivity if its failure rate on structurally edge-case inputs is higher than its failure rate on structurally typical inputs. Structural edge cases include, at minimum:

- Empty input (or the minimal valid input for the problem)
- Single-element input
- Maximum constraint value (input at or near the problem's declared size bound)
- Zero value (when zero is a valid input, e.g., zero coins, zero length, empty grid)
- Mixed: edge case combined with one or more typical values

This definition makes no reference to LC322, LC45, or any specific problem. A boundary-sensitivity probe family can be implemented for any problem with a structural notion of edge case.

**Probe family implementation:**

A `boundary_sensitivity` probe family contains inputs drawn from the set of structural edge cases above. Each probe carries metadata indicating which edge-case category it instantiates (e.g., `boundary_type: "empty"`, `boundary_type: "max_constraint"`, `boundary_type: "zero_value"`). The probe family is named identically across all three problem classes.

**Solver failure on this dimension in general terms:**

A solver that handles only "typical" inputs correctly will fail on boundary probes. Common patterns: index out of bounds on empty input, integer overflow on max-constraint input, division by zero on zero value, return-on-empty without explicit empty-case handling, off-by-one when the input size is exactly 1. A solver that handles boundary cases explicitly (early returns, defensive checks, problem-specific guards) will pass boundary probes.

**Gap definition for this dimension:**

`gap(boundary_sensitivity, P)` = mean REJECT fail rate on boundary probes - mean ACCEPT fail rate on boundary probes, computed over the K observed boundary probes per solver on problem P.

**Why this is a transfer candidate:**

Boundary cases are universal. Any problem with non-trivial input structure has boundary cases. A solver that fails on boundary cases in one problem is likely to fail on boundary cases in another, because the failure pattern (no empty-case handling, no max-constraint check, no zero handling) is problem-independent even though the specific bug instance is problem-specific. This is a prediction about solver bugs that should hold across problem classes if it holds at all.

---

## Candidate transfer dimension 2: Scale sensitivity

**Definition (problem-independent):**

A solver exhibits scale sensitivity if its failure rate on large-magnitude inputs is higher than its failure rate on small-magnitude inputs, holding structural complexity constant. The probe family varies input magnitude across a range (small, medium, large, maximum) while keeping other structural features fixed.

This dimension is restricted to numeric problems (where "magnitude" is well-defined). For string, graph, or other non-numeric problems, the dimension does not apply; the third problem class will be selected from numeric problems.

**Probe family implementation:**

A `scale_sensitivity` probe family contains inputs of varying magnitude, binned into 3-4 magnitude classes (small, medium, large, maximum). Each probe carries metadata indicating its magnitude class. The probe family is named identically across all three problem classes.

**Solver failure on this dimension in general terms:**

A solver with hard-coded limits (constant array sizes, fixed recursion depth, O(2^n) inner loops, integer types too small for the expected range) will fail on large inputs but pass on small inputs. A solver with linear or polynomial complexity and no hidden constant limits will pass at all magnitudes.

**Gap definition for this dimension:**

`gap(scale_sensitivity, P)` = mean REJECT fail rate on large-magnitude probes - mean ACCEPT fail rate on large-magnitude probes, computed over the K observed large-magnitude probes per solver on problem P. (The "large-magnitude" bin is the top magnitude class.)

**Why this is a transfer candidate:**

Scale-related bugs are universal in algorithm implementations. A solver that has a hard-coded limit or assumes small input will fail at large magnitude in any problem. The specific limit (array size 100, recursion depth 1000) is problem-specific, but the failure pattern is problem-independent. The ACCEPT class in any problem should be the solvers that handle scale correctly, regardless of what the problem is.

---

## Candidate transfer dimension 3: Monotonicity violation

**Definition (problem-independent):**

A solver exhibits monotonicity violation failure if it fails when the problem's natural ordering assumption is locally violated, in problems that have a monotone subproblem structure. The probe family contains inputs that locally violate the natural ordering of the optimal subproblem (e.g., unsorted subarrays, non-monotone sequences, locally-inverted orderings).

This dimension is restricted to problems with a monotone optimal subproblem structure. For problems without monotone structure, the dimension does not apply; the audit records the dimension as not testable for that problem.

**Probe family implementation:**

A `monotonicity_violation` probe family contains inputs that locally violate the natural ordering. Each probe carries metadata indicating the violation type (e.g., `violation_type: "unsorted_subarray"`, `violation_type: "inverted_pair"`). The probe family is named identically across problem classes that support the dimension.

**Solver failure on this dimension in general terms:**

A solver that assumes sorted input, sorted coin order, or monotone subproblem values will fail when the input violates the assumption. A solver that explicitly handles the violation (sorts internally, iterates over all orderings, uses unordered data structures) will pass.

**Gap definition for this dimension:**

`gap(monotonicity_violation, P)` = mean REJECT fail rate on monotonicity-violation probes - mean ACCEPT fail rate on monotonicity-violation probes, computed over the K observed violation probes per solver on problem P.

**Why this is a weaker transfer candidate than boundary or scale:**

Monotonicity violation applies only to problems with monotone subproblem structure. Some problems (e.g., unordered set problems, graph problems without topological structure) have no natural monotonicity to violate. The third problem class must be selected from problems where this dimension is defined. Within the selected subset, the prediction is the same: solvers that fail on ordering violations in one monotone-structured problem should fail in another.

This dimension is included for completeness. If the audit shows it cannot be implemented on the third problem class, it is dropped without invalidating the test for the other two dimensions.

---

## Phase 1 audit plan

After this document is committed, Phase 1 reads the existing probe indexes and checks whether structurally equivalent probes exist under different names.

**Files to audit:**

- `data/midweather_fingerprint_lc322_probe_index.json` — 30 probes, 6 fingerprint axes
- `data/midweather_fingerprint_lc45_probe_index.json` — 30 probes, 6 failure manifolds

**For each candidate dimension, the audit checks:**

1. **Boundary sensitivity**: do existing probes test empty input, single element, max constraint, or zero value? Identify probes by their input structure, not by their axis name.
2. **Scale sensitivity**: do existing probes span a magnitude range with explicit magnitude metadata? Identify probes by their input magnitude.
3. **Monotonicity violation**: do existing probes test unsorted or non-monotone inputs relative to the problem's natural order?

**Audit output for each dimension:**

- Number of existing probes that structurally implement the dimension
- Whether the existing axis name can be renamed to the candidate dimension name without changing probe content
- For dimensions where probes don't exist: cost estimate for adding them (probe generation, oracle verification, freeze update)

**Decision rule from audit result:**

- If at least 2 of 3 candidate dimensions have ≥3 existing probes in both LC322 and LC45: Phase 3 build cost is moderate; proceed to Phase 2.
- If only 1 dimension has existing data: Phase 3 cost includes adding probes to existing problems; flag this in the audit and ask whether to proceed.
- If 0 dimensions have existing data: Phase 3 cost is high (new probes for all 3 problems); the plan says to revisit the decision to proceed.

---

## What this document does and does not commit to

**Commits to:**

- Three candidate transfer dimensions with problem-independent definitions
- A specific gap threshold (0.20 minimum, max/min ≤ 2.0) committed before running
- A null result definition
- A Phase 1 audit plan

**Does not commit to:**

- That the transfer test will be run. That decision is made after Phase 1.
- That any specific third problem class will be built. Phase 2 is selection; Phase 3 is build.
- That the test will be run even if Phase 1 audit is favorable. The user has stated that reopening requires the biographical motivation the assistant cannot supply; the architectural plan is offered but the decision to execute remains open.
- Any change to the existing paper, code, freezes, or tests. Phase 0 is documentation only.
