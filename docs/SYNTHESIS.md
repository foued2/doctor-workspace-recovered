# docs/SYNTHESIS.md
# Doctor/Bimaristan — Cross-Phase Synthesis
# Date: 2026-06-06
# Status: Final documentation layer. Does not reopen any closed phase.

---

## 1. What this document is

A single-layer synthesis of findings across all closed phases.
No new measurements. No new claims. No causal language.
All statements are observations from the closed phase record.

---

## 2. The phase sequence

| Phase | Tag | Finding |
|---|---|---|
| project-closure-004 | `ccbf927` | Transfer hypothesis. C_structured_fingerprint does not improve decision utility over B1 under symmetric decision_loss on frozen populations. |
| C-1 | `phase-c1-results` | Asymmetric-cost sweep. Gap identically 0 at all 9 λ values on both populations. FAIL with mathematical certainty under the freeze's linear cost model. |
| C-3a | `phase-c3a-results` | Per-solver identity resolution. D=0, A=0 on both populations. C_structured_fingerprint and B1 misclassify identical solver sets. FULL_EQUIVALENCE. |
| C-4 | `phase-c4-results` | C_genuine (probe_family coherence rule) produces D=6, A=50, gap > 0.10 at all 9 λ on LC322 (PASS). Introduces 1 false accept on LC45 where B1 is perfect (FAIL). |
| C-5 | `phase-c5-results` | Distribution shift analysis. C-4 gain survives 6 of 11 pre-declared perturbations. PARTIALLY_SURVIVES. |

---

## 3. Why C-1 and C-3a produced equivalence

C_structured_fingerprint was bound to `_fail_count_policy` — the same policy as B1.
The structured fingerprint context (`obs_records`) was accepted by the interface
but not consulted in the decision function.
Both estimators reduced to the same functional:
count failures → threshold decision.
Same input function produces same decision manifold.
Equivalence under C-1 and C-3a is a property of the implementation,
not a property of the representation class.

---

## 4. What C-4 introduced and what it did not introduce

C_genuine introduced a new dependency: probe_family from obs_records.
Decision rule: ACCEPT if 0 failures OR all failures share one probe_family;
REJECT otherwise.
This is a different decision language from B1, not a refinement of the same language.

C-4 did not establish:
- that C as an estimator class is superior to B1
- that structured fingerprints produce generalizable utility gains
- that the observed gap is an estimator property

C-4 established:
- that a decision rule using probe_family produces measurable divergence from B1
  on LC322 under the C-1 asymmetric-cost protocol
- that the divergence satisfies the pre-declared falsification criterion on LC322
- that the same rule introduces a false accept on LC45

---

## 5. What C-5 established

The C-4 gain survives 6 of 11 pre-declared perturbations and collapses on 5.
The collapse pattern is not random:

- P1 (label inversion): collapses. The rule's accept bias becomes a liability
  when the majority class flips.
- P2 (solver subsample): unstable across the three fixed draws.
- P3 (probe family knockout): collapses on knockouts of families the 5 recovered
  solvers' failures belong to. Survives knockouts of unrelated families.
- P4 (LC45 cross-population): collapses. C_genuine introduces false accept
  where B1 is perfect.

The survival pattern is consistent with the gain being an interaction between
C_genuine's decision rule and the specific structural geometry of the LC322
solver population. It is not consistent with the gain being a stable property
of C_genuine as an estimator across distribution transformations.

---

## 6. The open question this record does not answer

The phase sequence tested one decision rule (probe_family coherence)
on two populations (LC322, LC45) under a fixed cost model.

The following question is not answered by any phase in this record:

> Can any estimator built on the structured fingerprint representation class
> produce distribution-invariant separation from B1?

This is a different question from anything tested here.
It is not answerable by iterating on the current populations or cost model.
It requires either a theoretical argument about the representation class
or empirical testing across a substantially wider distribution family.

---

## 7. What the project record supports

The following claims are supported by the closed phase record:

1. Under the frozen protocol with C_structured_fingerprint bound to
   _fail_count_policy, no utility gain over B1 is observable at any
   tested λ value on either population.

2. The equivalence in (1) is per-solver identity equivalence, not
   aggregation artifact.

3. A decision rule that consults probe_family produces measurable
   divergence from B1 on LC322 under specific population conditions.

4. That divergence does not survive all tested distribution transformations.

5. The survival pattern of the divergence is consistent with a dataset
   geometry interaction, not estimator superiority.

---

## 8. What the project record does not support

The following claims are not supported:

1. That C_structured_fingerprint has no utility advantage over B1 under
   any possible implementation or decision rule.

2. That structured fingerprints cannot produce distribution-invariant
   separation from B1 under any conditions.

3. That the probe_family coherence rule is the best possible structured
   decision rule for this representation class.

4. That the C-4 gain is generalizable beyond the tested populations
   and perturbations.

---

## 9. Epistemological constraints applied throughout

1. Compression drift: no claim stronger than the observation.
2. Negative result inflation: no generalization beyond tested populations,
   λ range, and perturbation set.
3. Hidden causal language: no because / therefore / explains /
   caused by / due to.

All phase results docs passed audit under these constraints before commit.

---

## 10. Closure reference

Substantive closure: project-closure-004 (`ccbf927`).
Transfer hypothesis as operationalized: not supported.
No future formulation claimed to be ruled out.
This document does not reopen that closure.
