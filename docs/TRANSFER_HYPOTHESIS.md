# Cross-Problem Transfer Hypothesis

**Date:** June 2026
**Status:** Phase 0 — hypothesis commitment, no code
**Trigger for proceeding past Phase 0:** this document committed
**Trigger for proceeding past Phase 1:** Phase 1 audit shows candidate stress classes auditable in current corpus under the strict definition, OR a clear plan for adding them is committed

**Revision note (June 2026):** This revises the prior Phase 0. The prior version used a 4-tuple signature `(input_type, constraint_shape, extremum_type, perturbation_operator)`. Phase 1 audit (against `data/midweather_fingerprint_lc322_probe_index.json` and `data/midweather_fingerprint_lc45_probe_index.json`) showed 0 cross-problem matches under that signature because every tuple element is encoding-bound to its problem class. This revision replaces the 4-tuple with a 2-tuple `(stress_class, perturbation_operator)`, treats `extremum_type` as a per-probe local realization detail, and redefines the cross-problem object of study as stress-class equivalence under different encodings rather than syntactic probe identity.

---

## Why this document exists

The Doctor/Bimaristan project has two fully-built problem classes (LC322, LC45) with probe families designed independently for each problem. The H1a falsification (`docs/H1A_FALSIFICATION.md`) tested within-LC322 family-conditional rate separability. The LC45 C feature audit (`docs/LC45_C_POLICY_FINDING.md`) tested within-LC45 feature separability. Both are within-problem tests. Neither tests cross-problem transfer of structural properties.

The prior Phase 0 attempted to define a cross-problem invariant via a 4-tuple signature. Phase 1 audit falsified that signature as a matching scheme: it required identity of problem encoding primitives, which guarantees disjoint signature spaces whenever problems differ in representation. The result was not a negative result on transfer; it was a non-identifiability result under the chosen equivalence relation.

The transfer question remains open, but only under a different object of study. This document commits to that revised object: stress-class equivalence under different encodings. A stress class is a coarse, problem-independent categorization of the computational stressor a probe instantiates. Three stress classes are committed (`boundary`, `scale`, `monotonicity`). Each problem realizes each stress class in its own encoding; the realization details are captured by `extremum_type` and do not gate cross-problem matching.

Post-hoc relaxation of the stress-class equivalence rule invalidates the test.

---

## Probe signature and structural equivalence

**Probe signature:**

A probe p is defined by a 2-tuple:

```
signature(p) = (stress_class, perturbation_operator)
```

- `stress_class`: a coarse, problem-independent categorization of the computational stressor the probe instantiates. Committed values: `boundary`, `scale`, `monotonicity`. A probe may also be assigned `stress_class = none` if it does not fit any committed stress class; such probes are excluded from cross-problem analysis.
- `perturbation_operator`: the perturbation applied to the input. Currently `identity` for all probes in the existing corpus.

**Local realization detail (retained, not part of equivalence):**

Each probe additionally carries an `extremum_type` value describing the specific extremum regime realized in the problem's encoding. `extremum_type` is problem-internal. It does not gate cross-problem matching. Two probes with the same `stress_class` but different `extremum_type` values are equivalent for cross-problem comparison.

For example:
- An LC322 boundary probe with `extremum_type = "greedy_dp_crossover"` and an LC45 boundary probe with `extremum_type = "zero_value_present"` are equivalent at the cross-problem level: both realize the boundary stress class.
- `extremum_type` is recorded for each probe in the probe index but is not consulted by the cross-problem equivalence check.

**Equivalence rule:**

Two probes p1, p2 are structurally equivalent for cross-problem comparison if and only if `signature(p1) == signature(p2)` exactly on the 2-tuple `(stress_class, perturbation_operator)`. Probes with `stress_class = none` are excluded from cross-problem analysis. If a stress class is missing from any problem (i.e., no probes in that problem have that `stress_class`), that stress class is excluded from cross-problem analysis for that problem.

Exclusion is permanent; probes are not approximated, partial-matched, or re-included under any post-hoc correction.

---

## Rank-based transfer test

**Test statistic:**

For each problem P and stress class d with K observed probes in d, compute the rank of each probe by pass rate:

```
Δ(P, d) = E[rank of probes in stress class d for ACCEPT class] - E[rank of probes in stress class d for REJECT class]
```

**Transfer on stress class d is supported if and only if:**

1. **Sign consistency**: sign(Δ(P, d)) is the same for all three problem classes
2. **Sufficient non-emptiness**: each problem has at least K_min probes in stress class d (K_min is committed in Phase 1)

**Magnitude is not compared across problems.** Rank-space ordinal consistency is the only cross-problem transfer criterion.

**Transfer fails on stress class d if:**

- Sign inconsistency across problems
- Any problem has fewer than K_min probes in stress class d

---

## Stress class 1: Boundary

**Definition (problem-independent):**

A probe instantiates the boundary stress class if it stresses solver behavior at the boundary of an allowed input range. Boundary regimes include, at minimum:

- Empty input (or the minimal valid input for the problem)
- Single-element input
- Maximum constraint value (input at or near the problem's declared size bound)
- Zero value (when zero is a valid input, e.g., zero coins, zero length, empty grid)
- Mixed: edge case combined with one or more typical values

This definition makes no reference to LC322, LC45, or any specific problem.

**Local realization:** Each problem realizes the boundary stress class in its own encoding. The realization details are recorded as `extremum_type` values but are not consulted by the cross-problem equivalence check.

**Why this is a transfer candidate:**

Boundary cases are universal. Any problem with non-trivial input structure has boundary cases. A solver that fails on boundary cases in one problem is likely to fail in another, because the failure pattern (no empty-case handling, no max-constraint check, no zero handling) is problem-independent even though the specific bug instance is problem-specific.

---

## Stress class 2: Scale

**Definition (problem-independent):**

A probe instantiates the scale stress class if it stresses solver behavior at varying input magnitudes. The probe family varies input magnitude across a range (small, medium, large, maximum) while keeping other structural features fixed.

This stress class is restricted to numeric problems (where "magnitude" is well-defined). For string, graph, or other non-numeric problems, the stress class does not apply; the third problem class will be selected from numeric problems.

**Local realization:** Each problem realizes the scale stress class in its own encoding. The realization details are recorded as `extremum_type` values but are not consulted by the cross-problem equivalence check.

**Why this is a transfer candidate:**

Scale-related bugs are universal in algorithm implementations. A solver that has a hard-coded limit or assumes small input will fail at large magnitude in any problem. The specific limit is problem-specific, but the failure pattern is problem-independent.

---

## Stress class 3: Monotonicity violation

**Definition (problem-independent):**

A probe instantiates the monotonicity violation stress class if it stresses solver behavior when the problem's natural ordering assumption is locally violated, in problems that have a monotone subproblem structure.

This stress class is restricted to problems with a monotone optimal subproblem structure. For problems without monotone structure, the stress class does not apply; the audit records the stress class as not testable for that problem.

**Local realization:** Each problem realizes the monotonicity stress class in its own encoding. The realization details are recorded as `extremum_type` values but are not consulted by the cross-problem equivalence check.

**Why this is a weaker transfer candidate:**

Monotonicity violation applies only to problems with monotone subproblem structure. The third problem class must be selected from problems where this stress class is defined. If the audit shows it cannot be implemented on the third problem class, it is dropped without invalidating the test for the other two stress classes.

---

## Solver taxonomy

Every solver in the population is labeled exactly one of:

- `natural_solver`: emerged from independent generation (e.g., LLM generation with no transfer-dimension prompt) without deliberate construction to fail on a candidate stress class
- `constructed_adversary`: deliberately constructed to fail on at least one candidate stress class

**Transfer analysis uses only `natural_solver` instances.** `constructed_adversary` instances are excluded from all Phase 4 transfer statistics. They may be retained for diagnostic pack validation (verifying that the probe families can detect what they claim to detect) but they do not contribute to the cross-problem transfer test.

No intermediate classes, no gradations, no partial labels. The taxonomy is binary and strict.

---

## Calibration gate (precondition, not metric)

For each stress class d, the ACCEPT-class pass rate distribution across all probes in d must overlap across all three problems. The check:

- Compute ACCEPT-class pass rate per probe in stress class d, per problem
- Apply across-problem overlap test (KS-distance with threshold t_KS, or simple overlap band)

Specific threshold is committed in Phase 1.

**Consequence of failure:** if the calibration gate fails on a stress class, that stress class is excluded from the transfer test. Excluded stress classes are not rescaled, not adjusted, not re-included under any post-hoc correction. The result is: this stress class is not comparable across these problems.

---

## Null result definition

The data would look like this if transfer fails:

- For at least one stress class: sign inconsistency across problems (sign of Δ flips)
- For at least one stress class: insufficient probes (below K_min) on at least one problem
- For at least one stress class: calibration gate fails (ACCEPT-class distributions disjoint across problems)
- No stress class simultaneously satisfies sign consistency, non-emptiness, and calibration gate across all three problems

**If the data look like this, the conclusion is:** stress classes defined problem-independently do not transfer across structurally distinct problem classes. The framework's structural-property claims are K-local to each problem, not general. This is a stronger and more specific negative result than the current paper's K-local FAIL.

This is recorded as a real finding, not a limitation.

---

## Phase 1 audit (strict scope)

Phase 1 does exactly three things. No additional analysis is performed in Phase 1.

1. **Stress-class assignment verification**: For each probe in `data/midweather_fingerprint_lc322_probe_index.json` and `data/midweather_fingerprint_lc45_probe_index.json`, assign a `stress_class ∈ {boundary, scale, monotonicity, none}` and record the `extremum_type` for each probe. Document the assignment rule per probe. Record: number of probes per stress class per problem, and the set of `extremum_type` values present in each stress class per problem.

2. **Exclusion + feasibility verification**: Three filters are applied in order:
   - (a) Probes with `stress_class = none` are excluded from cross-problem analysis.
   - (b) Stress classes missing from any problem are excluded from cross-problem analysis for that problem.
   - (c) **Feasibility check (identifiability precondition)**: For each stress class retained after (a) and (b), the union of `extremum_type` values across all three problems' probes in that stress class must have cardinality ≥ 2. If a stress class has fewer than 2 distinct `extremum_type` values across all problems, it is excluded as unidentifiable. Excluded stress classes are not re-included.
   
   Document each filter rule and the count of excluded probes per problem per stress class.

3. **Calibration gate check**: For each stress class with at least one probe in all three problems (and passing the feasibility check), compute ACCEPT-class pass rate distribution per problem. Apply the calibration gate (KS-distance or overlap band, threshold committed in Phase 1). Record: pass/fail of the gate per stress class.

**Phase 1 does NOT do:**

- Define new stress classes
- Introduce new scoring schemes
- Compute cross-problem transfer statistics
- Construct solver packs
- Build new problem classes
- Specify K_min or KS-threshold values (these are committed in Phase 1, not before)
- Define the `extremum_type` value vocabulary (this is a per-probe annotation, not a scoring axis)

**Decision rule from audit result:**

- If at least 2 of 3 stress classes pass the calibration gate with at least 3 probes in each of LC322 and LC45: Phase 3 build cost is moderate; proceed to Phase 2.
- If only 1 stress class passes: Phase 3 cost includes adding probes to existing problems; flag this in the audit and ask whether to proceed.
- If 0 stress classes pass: Phase 3 cost is high; the plan says to revisit the decision to proceed.

---

## What this document commits to

**Commits to:**

- Three stress classes: `boundary`, `scale`, `monotonicity` (problem-independent)
- Probe signature as a 2-tuple: `(stress_class, perturbation_operator)`; equivalence = exact match
- `extremum_type` as a per-probe local realization detail, not part of cross-problem equivalence
- Rank-based transfer test: ordinal consistency of sign across problems; no magnitude comparison
- Binary solver taxonomy: `natural_solver` vs `constructed_adversary`; transfer analysis uses only `natural_solver`
- Calibration gate: ACCEPT-class pass rate distributions must overlap across problems; if not, stress class excluded
- Identifiability feasibility check: each retained stress class must have at least 2 distinct `extremum_type` values across all problems; otherwise excluded
- Null result definition
- Phase 1 audit scope: stress-class assignment, exclusion + feasibility verification, calibration gate; nothing more

**Does not commit to:**

- Specific `extremum_type` value sets per problem (enumerated in Phase 1)
- Specific K_min threshold (committed in Phase 1)
- Specific KS-distance threshold or overlap band (committed in Phase 1)
- That the transfer test will be run. That decision is made after Phase 1.
- That any specific third problem class will be built. Phase 2 is selection; Phase 3 is build.
- Any change to the existing paper, code, freezes, or tests. Phase 0 is documentation only.

---

## Disposition (recorded at `project-closure-004`)

The Phase 1 audit (`docs/PHASE1_AUDIT.md`) was run under option B (frozen mapping, calibration gate disabled). Result: 2 of 3 stress classes auditable (`boundary`, `monotonicity`); 1 structurally degenerate (`scale` — no LC45 probes).

The original 3-class transfer claim is **not supported** in the current 2-problem corpus. The framework's structural-property claims remain K-local to each problem. The honest endpoint is the stop decision recorded at `project-closure-004`. The cross-problem transfer hypothesis is closed.

The rank test on the 2 auditable classes is a different question, not a continuation of this hypothesis. It is not pursued under the current label. Pursuing it would require explicitly re-committing as a 2-class exploratory study.

Full closure record: `docs/PROJECT_CLOSURE.md` addendum at `project-closure-004`.
