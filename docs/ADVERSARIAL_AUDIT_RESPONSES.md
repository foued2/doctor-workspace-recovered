# ADVERSARIAL_AUDIT_RESPONSES.md
# Doctor/Bimaristan — Adversarial Audit Responses
# Date: 2026-06-07
# Status: Folded into SYNTHESIS.md as §13 (commit 7371776). Standalone file
# retained for direct reference. Audit 11 numerical claims corrected
# pre-fold: numerator sums 43 (R1) and 58 (R3); denominator 270 =
# 7×30 + 3×20, tied to perturbation-dependent sample sizes.

---

## Audit 1 — Ontology Audit

Question: for every named object, identify its operational definition
and every phase where that definition changed. Find semantic drift.

**"correctness"**
- Operational definition: oracle_output matches solver_output on target probes.
- Defined in `compute_ground_truth` (run_midweather_fingerprint_lc322.py).
- Stable across C-1, C-3a, C-4, C-5, C-6. No drift.

**"failure pattern"**
- Operational definition: a set of (probe_id, pass_fail) pairs for a solver,
  grouped by probe_family of the failures.
- Defined in C-4 (`_c_genuine_policy`). Inherited by C-5, C-6.
- No drift within the C-4 lineage.

**"fingerprint"** (semantic drift detected)
- C-1, C-3a: a 6-dim vector from `encode_raw_tensor`
  (pf, deformation, axis_val, family_val, paired, invariant).
  `family_val` is 1.0/0.0 indicator of whether the field exists.
- C-4: expanded to include the categorical `probe_family` string
  label, accessed via `obs_records[i].fingerprint_context.probe_family`.
- The C-4 "fingerprint" is a different object from the C-1
  "fingerprint." C-4's findings operate on the expanded definition.
- Continuity question: was C-4 a continuation of the fingerprint
  hypothesis or a replacement? The word "fingerprint" carried over
  from C-1/C-3a to C-4, but the operational meaning changed. C-4
  is more accurately a redefinition than a continuation. The
  C_structured_fingerprint estimator (C-1, C-3a) and the
  C_genuine estimator (C-4 onward) share a name stem but operate
  on different inputs.

**"algorithmic structure"**
- Operational definition: not directly measured. Inferred from
  probe_family clustering of failures.
- The 6-dim feature space does not include direct measures of
  solver internals. The phrase "algorithmic structure" appears in
  narrative, not in measurements.

**"decision utility"**
- Operational definition: linear cost = (correct_accepts +
  correct_rejects - lambda_R * wrong_rejects -
  lambda_A * wrong_accepts) / n_solvers.
- Defined in `asymmetric_cost.py:run_sweep_aggregate`.
- Stable across all phases.

**"generalization" / "distribution-invariant"** (semantic narrowing)
- C-1: lambda robustness within a single population.
- C-4: cross-population (LC322, LC45).
- C-5: perturbation robustness (11 perturbations on LC322).
- C-6: class robustness (4 rules, 11 perturbations, 2 populations).
- By C-6, the term carries the constraint of invariance across
  the full 4-rule, 11-perturbation, 2-population, 9-lambda scope.

---

## Audit 2 — Null-Reconstruction Audit (revised)

Question: reconstruct the project under the null (no algorithmic
structure, no fingerprints, no robustness signal, no solver taxonomy).
Can every result still arise?

The findings are **compatible with the null**, but not specifically
**expected under the null**. The distinction matters.

- C-1 (gap=0): compatible with the null. C and B1 share a policy.
  Under null, interchangeability is expected. C-1 is also
  derivable from the null.
- C-3a (D=0, A=0): compatible with the null. The binding is
  expected under the null. C-3a is derivable from the null.
- C-4 (D=6, A=50 on LC322): compatible with the null. The specific
  numbers (5 recoveries, 1 false accept) are not derivable from a
  general null. They depend on the specific LC322 data values
  (which 5 solvers have all-failures-in-one-family, which 1 has
  mixed-family failures, which REJECT solvers are accepted).
- C-5 (PARTIALLY_SURVIVES, 6/11): compatible with the null. The
  specific 6/11 split is not derivable from the null. It depends
  on the LC322 data and the C-5 perturbation design.
- C-6 (RQ-C6 NO, 0/4 surviving rules): compatible with the null.
  The fact that 4 pre-declared rules all fail is consistent with
  the null. The specific per-rule, per-perturbation patterns
  (R1's 6/10, R3's 3/10) are not derivable from the null.

The findings do not refute the null. They are also not confirmed by
the null. Compatibility is a weaker claim than derivability.

---

## Audit 3 — Reverse-Causality Audit

Question: for every causal narrative, construct the reverse
explanation.

The project's narratives are mostly descriptive, not causal. Reverse
explanations tend to be the same content, reframed.

- "C and B1 are equivalent" (C-3a): the cause is the binding; the
  effect is the equivalence. Reversing gives "the equivalence is the
  binding" — same content, different framing.
- "Distribution shift collapses the C-4 gain" (C-5): the collapse
  happens; the rule does not generalize. Reversing gives "the rule
  does not generalize; the collapse happens" — same content.
- "C_genuine gains are an interaction with LC322 probe geometry":
  the rule interacts with the data; the gain is a property of both.
  Reversing gives "the gain is a property of both; the rule interacts
  with the data" — same content.

The reverse-causality audit finds that the project has minimal causal
structure to reverse. The findings are co-occurrences, not causal
chains.

---

## Audit 4 — Adversarial Renaming Audit

Question: replace evocative names with neutral labels. Do conclusions
become less convincing?

Replacing names:
- C_genuine → Estimator_7
- B1 → Estimator_3
- fingerprint → Feature_Vector_12
- probe_family → Metadata_Field_4

The empirical results stand, with reduced narrative contamination.

- C-4 finding: "Estimator_7 produces measurable divergence from
  Estimator_3 on LC322 under the asymmetric-cost protocol." The
  mechanism is no longer named, but the empirical fact stands.
- C-5 finding: "Estimator_7's gain over Estimator_3 survives 6/11
  perturbations." Standalone, this is informative.
- C-6 finding: "4 candidate rules built on Feature_Vector_12 do not
  produce invariant separation." The framing as "representation
  class" is gone; the empirical claim is unchanged.
- §12 framing: "the failure to separate Estimator_7 from
  Estimator_3's structure from Metadata_Field_4's structure
  persisted." Awkward, but the empirical claim is unchanged.

The renaming reduces evocative power. It does not change the data.
The findings are about estimators and data, not about
"fingerprints" or "structure" as concepts.

---

## Audit 5 — Hidden Symmetry Audit

Question: which results are mathematically forced by design choices?

- C-1 (gap=0): forced by the structural invariance result. 8
  estimators → 3 equivalence classes. C and B1 in same class. The
  gap=0 is mathematical, not data-driven. Discovery: the structural
  invariance pattern (3 classes, not 8).
- C-3a (D=0, A=0): forced by the binding of C_structured_fingerprint
  to `_fail_count_policy`. A careful code reader would notice the
  binding before C-3a ran. Documentation of a known fact, not a
  discovery in the strong sense.
- C-4 (PASS on LC322): forced by the intersection of the rule and
  the data. The rule was designed to fire on probe_family
  clustering. LC322 has that clustering. PASS is the natural
  intersection. Discovery: the rule + data interaction produces
  measurable divergence.
- C-5 (PARTIALLY_SURVIVES): not forced. The 6/11 split is
  data-dependent. Discovery: empirical observation about perturbation
  robustness.
- C-6 (RQ-C6 NO): not forced. The 4 rules were declared before
  the data. The fact that none survives is data-dependent.
  Discovery: empirical observation about class robustness.

C-3a is the closest to a tautology: it documents a binding that was
already in the code. The distinction between *discovering
equivalence* and *empirically verifying an equivalence implied by
implementation* is worth preserving.

---

## Audit 6 — Counterfactual Population Audit

Question: generate synthetic populations where the opposite
conclusion is guaranteed.

All three outcomes are constructable through population design.

- C-dominant: a population where solvers with structured failures
  (all in one family) are ACCEPT, and solvers with unstructured
  failures are REJECT. C_genuine correctly ACCEPTs structured and
  REJECTs unstructured. B1 REJECTs all with failures. C wins.
- B1-dominant: a population where any failure is a strong negative
  signal. C_genuine's relaxation (ACCEPT if cluster) introduces
  false accepts. B1 wins.
- Tie: a population where all solvers have 0 failures or all have
  ≥1 failure. C and B1 produce identical decisions.

Doctor's two populations:
- LC322 (11/19 ACCEPT/REJECT): C-dominant. C wins on unperturbed
  (C-4 PASS).
- LC45 (1/9 ACCEPT/REJECT, single-survivor skew): B1-dominant. B1
  is perfect; C introduces 1 false accept (C-4 FAIL on LC45).

The two populations give opposite conclusions. The C-5 perturbations
mix these conditions within LC322.

The findings are population-dependent. The "true" answer is
"it depends on the population."

---

## Audit 7 — Information-Theoretic Audit

Question: what information does C use that B1 does not? Count bits.

C_genuine input: (obs_fails, n_obs, obs_records). Uses the
probe_family of each failure.
B1 input: (obs_fails, n_obs). Ignores obs_records.

For a solver with k failures:
- B1's decision space: 1 of 2 (ACCEPT if k=0, REJECT if k>0).
- C_genuine's decision space: 1 of 2 (ACCEPT if k=0 or
  all-failures-in-one-family, REJECT otherwise).

Both produce 1 binary decision. C uses more input information (the
categorical family of each failure) but the output is still binary.

Decision divergence: C produces a different decision from B1 on 6/30
solvers (D=6) on unperturbed LC322. 6/30 = 20% of decisions are
affected by the additional information.

Information-theoretic verdict: C uses more information than B1. The
additional information is sparse — it changes 20% of decisions, not
all. The "feature-rich" framing overstates the impact.

This number (6/30) suggests a more primitive question that the prior
phases did not ask: what is the marginal value per bit of additional
information? See Audit 11.

---

## Audit 8 — Uniqueness Audit

Question: for every finding, list alternative models explaining it.

- C-1 (gap=0): shared policy; linear cost with global weights;
  small populations; limited probe budget. Most likely: shared
  policy.
- C-3a (D=0, A=0): shared policy; C does not consult features;
  per-solver equivalence forced by binding. Most likely: shared
  policy.
- C-4 (PASS on LC322): genuine feature utility; population
  artifact; probe clustering; threshold effect; sampling effect;
  interaction effect. Most likely: feature utility + probe
  clustering.
- C-5 (PARTIALLY_SURVIVES): estimator limitation; population
  limitation; probe design; perturbation design. Most likely:
  estimator + population.
- C-6 (RQ-C6 NO): rules wrong; feature space insufficient; probe
  design constrains; perturbations too strong; population too
  small. Most likely: feature space insufficient.

For each finding, 3-6 alternative explanations are not excluded by
the data. The findings are underdetermined.

---

## Audit 9 — Research-Laundering Audit

Question: which results were genuinely surprising vs formalized
known facts?

- C-1: partially formalized. The structural invariance (8 → 3
  classes) is a discovery. The "C and B1 share policy" is documented
  by the code itself.
- C-3a: formalized. Documenting the binding was documentation of a
  known fact, not a discovery. A code reader would notice the
  binding before C-3a ran. There is a difference between
  *discovering equivalence* and *empirically verifying an equivalence
  implied by implementation*. The latter still has value, but it
  is a different type of result.
- C-4: genuine. The PASS is the natural consequence of the rule's
  interaction with the data; the specific D=6, A=50 numbers are
  empirical.
- C-5: genuine. The 6/11 split is data-dependent and not
  predictable from the rule alone.
- C-6: genuine. The RQ-C6 NO is data-dependent; the 4 rules were
  declared before the data.

C-3a is the clearest case of research-laundering: it documented a
known fact (the binding of C_structured_fingerprint to
`_fail_count_policy`) as a phase finding.

---

## Audit 10 — Impossible Audit (revised)

Question: if Doctor is completely wrong, what is the single deepest
load-bearing assumption without which the project ceases to make
sense?

The prior framing ("correctness is measurable") is philosophical.
Doctor does not require a theory of correctness. Doctor requires an
**operational oracle** — a function from solver to {ACCEPT, REJECT}
that is taken as ground truth. You could replace "correctness" with
*oracle agreement*, *benchmark conformance*, or *reference
behavior*, and the machinery would still run.

The candidate load-bearing beam is **supervised partitioning**: the
existence of an oracle that labels each solver as ACCEPT or REJECT,
where the oracle's labels define the ground truth.

Test: remove the oracle entirely. Identify the first phase that
becomes undefined.

- C-1: uses the oracle via `compute_ground_truth` (target probe
  outcomes). Without the oracle, no ACCEPT/REJECT labels, no
  asymmetric cost inputs, no gap calculation. **C-1 is the first
  phase that becomes undefined.**
- C-3a, C-4, C-5, C-6: all inherit C-1's dependence on the oracle.
  Removing the oracle undefineds them in the same step.

The load-bearing beam is supervised partitioning (an oracle that
labels solvers), not the philosophy of correctness.

If Doctor is wrong, the candidate locus is the oracle's
partitioning — not whether correctness is measurable, but whether
the specific oracle's ACCEPT/REJECT labels align with the property
the phases are trying to test. The oracle's notion of "correct" is
a designed function, not a natural truth. The phases assume the
oracle is the ground truth. Whether the oracle's labels correspond
to anything stable is not established by the closed record.

---

## Audit 11 — Information Utilization Audit (new)

Question: how much of the additional feature space ever influences
decisions?

The prior phases asked whether C wins, whether C survives
perturbation, whether C generalizes. They did not ask the more
primitive question: how often does the additional information
actually change a decision?

For each rule R and each perturbation P, the data in
`data/c6_collapse_lc322.json` records D(R vs B1, P) — the number of
solvers where R's decision differs from B1's. The denominator for
each (R, P) pair is n_solvers(P), the perturbation-dependent sample
size. The total information utilization for R is the sum of D
across all 10 perturbations, normalized by the sum of n_solvers(P).

Perturbation-specific sample sizes: P1, P3a, P3b, P3c, P3d, P3e,
P3f each have n=30 solvers (7 perturbations × 30 = 210). P2a, P2b,
P2c each have n=20 solvers (3 perturbations × 20 = 60, each
a 20-solver subsample of LC322). Total perturbation × solver pairs
= 210 + 60 = 270.
The 7×30 / 3×20 asymmetry is structural to the C-5 perturbation
design and matters for ratio interpretation: aggregating across
heterogeneous sample sizes without explicit accounting would
produce artefacts of aggregation rather than signal.

Reading the per-rule, per-perturbation D ranges from the c6 data
(D values are not uniquely determined by the (WA, WR) aggregates
alone; the table gives the lower and upper bounds implied by the
aggregate counts):

- R1 (C_genuine):
  - P1:  D in [5, 6],  n=30
  - P2a: D in [2, 3],  n=20
  - P2b: D in [5, 6],  n=20
  - P2c: D in [3, 3],  n=20
  - P3a: D in [5, 9],  n=30
  - P3b: D in [5, 6],  n=30
  - P3c: D in [3, 3],  n=30
  - P3d: D in [5, 6],  n=30
  - P3e: D in [5, 6],  n=30
  - P3f: D in [5, 6],  n=30
  - Sum of D lower bounds: 43. Sum of D upper bounds: 54.
    Sparsity: 43/270 = 15.9% (lower), 54/270 = 20.0% (upper).
    Effective range: ~16–20% of perturbation × solver pairs.
- R2 (C_feature_threshold): D=0 on every perturbation. The
  additional feature (deformation_level) is never informative on
  LC322. The 30 observed probes all have deformation_level=0; the
  rule vacuously falls back to B1 behavior. Information utilization:
  0/270 = 0%.
- R3 (C_majority):
  - P1:  D in [5, 6],   n=30
  - P2a: D in [2, 3],   n=20
  - P2b: D in [5, 6],   n=20
  - P2c: D in [3, 3],   n=20
  - P3a: D in [9, 14],  n=30
  - P3b: D in [7, 12],  n=30
  - P3c: D in [5, 5],   n=30
  - P3d: D in [12, 17], n=30
  - P3e: D in [5, 8],   n=30
  - P3f: D in [5, 6],   n=30
  - Sum of D lower bounds: 58. Sum of D upper bounds: 80.
    Sparsity: 58/270 = 21.5% (lower), 80/270 = 29.6% (upper).
    Effective range: ~21–24% of perturbation × solver pairs
    (lower-bound central tendency; upper bound 29.6% reflects
    high-end per-perturbation overlap, dominated by P3d).
- R4 (C_zero_only): D=0 by construction (operationally identical
  to B1). Information utilization: 0/270 = 0%.

For reference: on unperturbed LC322 (C-4 result, not in the c6
perturbation battery), D=6 for R1 (5 recoveries + 1 false accept).
The unperturbed observation is a single (R, P) pair with n=30, so
it contributes 1/10 of the perturbation × solver total.

A possible reframing: the project debated representational
richness — whether structured fingerprints could beat B1, whether
the gain would generalize, whether the representation class
produces invariant separation. The Information Utilization Audit
shows that the additional feature space was operationally active
on a small fraction of decisions:

- R1: ~16–20% of perturbation × solver pairs.
- R2: 0%.
- R3: ~21–24% (but most of those changes are false accepts, not
  recoveries).
- R4: 0% by construction.

The "feature-rich" framing implies that the additional information
matters globally. The data shows that the additional information
matters locally and sparsely.

The more primitive question the prior phases did not ask is
quantitative: how many decision changes per bit of additional
information? The data exists to answer it.
