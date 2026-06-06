# Cross-Problem Transfer Hypothesis

**Date:** June 2026
**Status:** Phase 0 — hypothesis commitment, no code
**Trigger for proceeding past Phase 0:** this document committed
**Trigger for proceeding past Phase 1:** Phase 1 audit shows candidate dimensions auditable in current corpus under the strict definition, OR a clear plan for adding them is committed

---

## Why this document exists

The Doctor/Bimaristan project has two fully-built problem classes (LC322, LC45) with probe families designed independently for each problem. The H1a falsification (`docs/H1A_FALSIFICATION.md`) tested within-LC322 family-conditional rate separability. The LC45 C feature audit (`docs/LC45_C_POLICY_FINDING.md`) tested within-LC45 feature separability. Both are within-problem tests. Neither tests cross-problem transfer of structural properties.

The current 2-problem corpus cannot retroactively answer the cross-problem transfer question because the probe families were designed per-problem with no shared problem-independent structure. A genuine test of cross-problem transfer requires:

- Probe equivalence established by a finite computable signature, not by name or semantic clustering
- A transfer test in rank-space, not scalar rates
- A binary distinction between natural solvers and constructed adversaries
- A calibration gate that prevents measuring under incomparable difficulty regimes

This document commits to all four. Post-hoc relaxation of any of them invalidates the test.

---

## Probe signature and structural equivalence

**Probe signature:**

A probe p is defined by a finite signature tuple:

```
signature(p) = (input_type, constraint_shape, extremum_type, perturbation_operator)
```

- `input_type`: the type of the problem input (e.g., list of integers, list of lists, integer)
- `constraint_shape`: the structural shape of the problem's constraints (e.g., bounded/unbounded, ordered/unordered, contiguous/discontiguous)
- `extremum_type`: which extremum class the probe instantiates, drawn from a fixed enumeration per transfer dimension
- `perturbation_operator`: the perturbation applied to the input (e.g., identity, scale, swap, drop)

**Equivalence rule:**

Two probes p1, p2 are structurally equivalent for cross-problem comparison if and only if `signature(p1) == signature(p2)` exactly on all four tuple elements. Probes that do not exact-match across all three problems are excluded from cross-problem analysis. Exclusion is permanent; probes are not approximated, partial-matched, or re-included under any post-hoc correction.

The candidate value sets for each tuple element, per transfer dimension, are enumerated in Phase 1.

---

## Rank-based transfer test

**Test statistic:**

For each problem P and dimension d with K observed matched probes, compute the rank of each probe by pass rate:

```
Δ(P, d) = E[rank of probes in dimension d for ACCEPT class] - E[rank of probes in dimension d for REJECT class]
```

**Transfer on dimension d is supported if and only if:**

1. **Sign consistency**: sign(Δ(P, d)) is the same for all three problem classes
2. **Sufficient non-emptiness**: each problem has at least K_min matched probes in dimension d (K_min is committed in Phase 1)

**Magnitude is not compared across problems.** Rank-space ordinal consistency is the only cross-problem transfer criterion.

**Transfer fails on dimension d if:**

- Sign inconsistency across problems
- Any problem has fewer than K_min matched probes

---

## Candidate transfer dimension 1: Boundary sensitivity

**Definition (problem-independent):**

A solver exhibits boundary sensitivity if its failure rate on structurally edge-case inputs is higher than its failure rate on structurally typical inputs. Structural edge cases include, at minimum:

- Empty input (or the minimal valid input for the problem)
- Single-element input
- Maximum constraint value (input at or near the problem's declared size bound)
- Zero value (when zero is a valid input, e.g., zero coins, zero length, empty grid)
- Mixed: edge case combined with one or more typical values

This definition makes no reference to LC322, LC45, or any specific problem.

**Rank-based test applies.** Dimension-specific signature values for `extremum_type` (e.g., `empty`, `single_element`, `max_constraint`, `zero_value`) are enumerated in Phase 1.

**Why this is a transfer candidate:**

Boundary cases are universal. Any problem with non-trivial input structure has boundary cases. A solver that fails on boundary cases in one problem is likely to fail in another, because the failure pattern (no empty-case handling, no max-constraint check, no zero handling) is problem-independent even though the specific bug instance is problem-specific.

---

## Candidate transfer dimension 2: Scale sensitivity

**Definition (problem-independent):**

A solver exhibits scale sensitivity if its failure rate on large-magnitude inputs is higher than its failure rate on small-magnitude inputs, holding structural complexity constant. The probe family varies input magnitude across a range (small, medium, large, maximum) while keeping other structural features fixed.

This dimension is restricted to numeric problems. For string, graph, or other non-numeric problems, the dimension does not apply; the third problem class will be selected from numeric problems.

**Rank-based test applies.** Dimension-specific signature values for `extremum_type` (magnitude bins, e.g., `small`, `medium`, `large`, `max`) are enumerated in Phase 1.

**Why this is a transfer candidate:**

Scale-related bugs are universal in algorithm implementations. A solver that has a hard-coded limit or assumes small input will fail at large magnitude in any problem. The specific limit is problem-specific, but the failure pattern is problem-independent.

---

## Candidate transfer dimension 3: Monotonicity violation

**Definition (problem-independent):**

A solver exhibits monotonicity violation failure if it fails when the problem's natural ordering assumption is locally violated, in problems that have a monotone subproblem structure. The probe family contains inputs that locally violate the natural ordering of the optimal subproblem (e.g., unsorted subarrays, non-monotone sequences, locally-inverted orderings).

This dimension is restricted to problems with a monotone optimal subproblem structure. For problems without monotone structure, the dimension does not apply; the audit records the dimension as not testable for that problem.

**Rank-based test applies.** Dimension-specific signature values for `extremum_type` (violation types, e.g., `unsorted_subarray`, `inverted_pair`) are enumerated in Phase 1.

**Why this is a weaker transfer candidate:**

Monotonicity violation applies only to problems with monotone subproblem structure. The third problem class must be selected from problems where this dimension is defined. If the audit shows it cannot be implemented on the third problem class, it is dropped without invalidating the test for the other two dimensions.

---

## Solver taxonomy

Every solver in the population is labeled exactly one of:

- `natural_solver`: emerged from independent generation (e.g., LLM generation with no transfer-dimension prompt) without deliberate construction to fail on a candidate transfer dimension
- `constructed_adversary`: deliberately constructed to fail on at least one candidate transfer dimension

**Transfer analysis uses only `natural_solver` instances.** `constructed_adversary` instances are excluded from all Phase 4 transfer statistics. They may be retained for diagnostic pack validation (verifying that the probe families can detect what they claim to detect) but they do not contribute to the cross-problem transfer test.

No intermediate classes, no gradations, no partial labels. The taxonomy is binary and strict.

---

## Calibration gate (precondition, not metric)

For each transfer dimension d, the ACCEPT-class pass rate distribution across all matched probes in d must overlap across all three problems. The check:

- Compute ACCEPT-class pass rate per matched probe in dimension d, per problem
- Apply across-problem overlap test (KS-distance with threshold t_KS, or simple overlap band)

Specific threshold is committed in Phase 1.

**Consequence of failure:** if the calibration gate fails on a dimension, that dimension is excluded from the transfer test. Excluded dimensions are not rescaled, not adjusted, not re-included under any post-hoc correction. The result is: this dimension is not comparable across these problems.

---

## Null result definition

The data would look like this if transfer fails:

- For at least one dimension: sign inconsistency across problems (sign of Δ flips)
- For at least one dimension: insufficient matched probes (below K_min) on at least one problem
- For at least one dimension: calibration gate fails (ACCEPT-class distributions disjoint across problems)
- No dimension simultaneously satisfies sign consistency, non-emptiness, and calibration gate across all three problems

**If the data look like this, the conclusion is:** collapse dimensions defined problem-independently do not transfer across structurally distinct problem classes. The framework's structural-property claims are K-local to each problem, not general. This is a stronger and more specific negative result than the current paper's K-local FAIL.

This is recorded as a real finding, not a limitation.

---

## Phase 1 audit (strict scope)

Phase 1 does exactly three things. No additional analysis is performed in Phase 1.

1. **Signature matching verification**: For each candidate transfer dimension (boundary, scale, monotonicity), enumerate the signature values for that dimension. Check whether any existing probes in `data/midweather_fingerprint_lc322_probe_index.json` and `data/midweather_fingerprint_lc45_probe_index.json` have signature values that exact-match across both problems. Record: number of matched probe pairs per dimension, number of unmatched probes (which are excluded from cross-problem analysis).

2. **Exclusion verification**: Confirm that probes without exact signature matches are correctly filtered out of cross-problem analysis. Document the filter rule and the count of excluded probes per problem.

3. **Calibration gate check**: For each dimension with at least one matched probe pair, compute ACCEPT-class pass rate distribution per problem. Apply the calibration gate (KS-distance or overlap band, threshold committed in Phase 1). Record: pass/fail of the gate per dimension.

**Phase 1 does NOT do:**

- Define new dimensions
- Introduce new scoring schemes
- Compute cross-problem transfer statistics
- Construct solver packs
- Build new problem classes
- Specify K_min or KS-threshold values (these are committed in Phase 1, not before)

**Decision rule from audit result:**

- If at least 2 of 3 candidate dimensions pass the calibration gate with ≥3 matched probe pairs in both LC322 and LC45: Phase 3 build cost is moderate; proceed to Phase 2.
- If only 1 dimension passes: Phase 3 cost includes adding probes to existing problems; flag this in the audit and ask whether to proceed.
- If 0 dimensions pass: Phase 3 cost is high; the plan says to revisit the decision to proceed.

---

## What this document commits to

**Commits to:**

- Probe signature as a 4-tuple: `(input_type, constraint_shape, extremum_type, perturbation_operator)`; equivalence = exact match
- Rank-based transfer test: ordinal consistency of sign across problems; no magnitude comparison
- Three candidate transfer dimensions with problem-independent definitions
- Binary solver taxonomy: `natural_solver` vs `constructed_adversary`; transfer analysis uses only `natural_solver`
- Calibration gate: ACCEPT-class pass rate distributions must overlap across problems; if not, dimension excluded
- Null result definition
- Phase 1 audit scope: signature matching, exclusion verification, calibration gate; nothing more

**Does not commit to:**

- Specific value sets for the signature tuple elements (enumerated in Phase 1)
- Specific K_min threshold (committed in Phase 1)
- Specific KS-distance threshold or overlap band (committed in Phase 1)
- That the transfer test will be run. That decision is made after Phase 1.
- That any specific third problem class will be built. Phase 2 is selection; Phase 3 is build.
- Any change to the existing paper, code, freezes, or tests. Phase 0 is documentation only.
