# docs/SYNTHESIS.md

# Doctor/Bimaristan — Cross-Phase Synthesis

# Date: 2026-06-07

# Status: Final documentation layer. Does not reopen any closed phase.

---

## 1. What this document is

A single-layer synthesis of findings across all closed phases.
No new measurements. No new claims. No causal language.
All statements are observations from the closed phase record.

---

## 2. The phase sequence

| Phase               | Tag                 | Finding                                                                                                                                                          |
|---------------------|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| project-closure-004 | `ccbf927`           | Transfer hypothesis. C_structured_fingerprint does not improve decision utility over B1 under symmetric decision_loss on frozen populations.                     |
| C-1                 | `phase-c1-results`  | Asymmetric-cost sweep. Gap identically 0 at all 9 λ values on both populations. FAIL with mathematical certainty under the freeze's linear cost model.           |
| C-3a                | `phase-c3a-results` | Per-solver identity resolution. D=0, A=0 on both populations. C_structured_fingerprint and B1 misclassify identical solver sets. FULL_EQUIVALENCE.               |
| C-4                 | `phase-c4-results`  | C_genuine (probe_family coherence rule) produces D=6, A=50, gap > 0.10 at all 9 λ on LC322 (PASS). Introduces 1 false accept on LC45 where B1 is perfect (FAIL). |
| C-5                 | `phase-c5-results`  | Distribution shift analysis. C-4 gain survives 6 of 11 pre-declared perturbations. PARTIALLY_SURVIVES.                                                           |

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

A theoretical characterization of the open question: the population the
question refers to would need to satisfy a property the current record
does not satisfy. Two conditions need to be distinguished. First,
failure patterns would need to correlate with correctness — failure
clustering that predicts accept/reject. Second, those patterns would
need to reflect genuine algorithmic differences — interpretable as
properties of solver internals, not as artifacts of probe design. A
population could satisfy the first without the second: predictive
clustering is not the same as interpretable clustering. The LC322 probe
geometry clusters failures by family; that clustering is observable
in the probe design. Whether it reflects genuine algorithmic
differences is not answered by the closed phases.

A further observation: probes designed to test specific algorithmic
families build in probe-family structure by construction. The
clustering observed on LC322 is not an accident of this particular
probe set. It is a property of probes that target specific algorithmic
properties. A population where failure clustering is driven by solver
internals rather than probe internals would require a method for
distinguishing the two sources of clustering. Such a method would
itself be a version of the structured estimator the phases are trying
to test. The requirement may not be satisfiable through probe design
alone.

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

---

## 11. Five lessons from the closed phase record

The phase record can be restated as a diagnostic map with three coordinates:

- Where separation can appear: structured clustering that is observable
  in the probe geometry (probe_family coherence on LC322).
- Where it disappears: under distribution shift (label inversion,
  solver subsampling, probe family knockout, cross-population to LC45).
- What kinds of gains are not durable: gains that depend on dataset
  geometry rather than on properties of the estimator itself.

Five observations follow from this diagnostic map.

1. A gap of zero between two estimators on a frozen protocol (C-1)
   is informative. It distinguishes estimators that are operationally
   the same on the tested populations and cost model from estimators
   that could differ. The observation is stronger than "we did not
   find a better model." It is a property of the two estimators on
   the tested scope.

2. Per-solver identity resolution (C-3a) precedes per-aggregate
   comparison. Aggregation can mask structural differences or
   simulate differences that are not present at the per-solver
   level. Confirming per-solver equivalence or per-solver difference
   is a prerequisite for interpreting aggregate utility gaps.

3. A structured-feature estimator is operationally distinct from
   a feature-blind estimator only when the structured feature is
   actually consulted (C-4). The C-3a finding that C_structured_
   fingerprint and B1_count were bound to the same function was
   the trigger for re-implementing C to consult the structured
   feature. The re-implementation (C_genuine) produced different
   per-solver decisions on LC322.

4. Distribution-shift perturbations (C-5) separate estimator-level gains from dataset-geometry interactions. The C-4 gain
   on unperturbed LC322 is one observation. The C-5 battery of
   11 perturbations showed the gain survives 6 of 11 and collapses
   on 5. The collapse pattern is consistent with the gain being
   an interaction between the decision rule and the specific
   probe geometry of the unperturbed LC322.

5. The right unit of falsification for a representation class
   is the class, not the individual rule (C-6). Four pre-declared
   candidate rules were tested against the C-5 battery on LC322.
   None survives all 11 perturbations. The class-level verdict
   is a structured negative result, not a claim that no estimator
   on the class can work in any context.

---

## 12. The identifiability framing

The closed phase record supports a narrower claim than "Doctor
established an impossibility result." It supports the isolation of
an identifiability problem.

The phases repeatedly failed to separate solver structure from
probe structure. Each failure is an observation about the attempted
separation. The pattern of failures is consistent with two
hypotheses, neither of which the record establishes:

- H1: the project's measurement apparatus could not resolve the
  ambiguity. A different apparatus, with different probe geometry,
  solver populations, or decision rules, would resolve it.
- H2: the underlying evaluation paradigm (probe-response) cannot
  resolve the ambiguity in principle. No apparatus built on this
  paradigm would resolve it.

The closed phases tested one paradigm under several internal
variants. The internal variants produced consistent collapses. To
establish a boundary condition on the paradigm itself, evidence
across multiple fundamentally different measurement regimes would
be needed. The record contains evidence within a single regime.

The defensible endpoint is the isolation of an unresolved ambiguity:
the failure to separate solver structure from probe structure
persisted across the redesigns attempted within the project's scope.
The question of whether a different scope would resolve the ambiguity
is not answered by this record.

---

## 13. Adversarial audits of the phase record

The following 11 audits were applied to the closed phase record.
Each audit is observational. None reopens a closed phase, introduces
new measurements, or modifies findings. Audits 1-9 are the original
10-audit battery. Audit 10 reframes the load-bearing beam question
from a philosophical claim to an engineering claim (supervised
partitioning). Audit 11 is added post-closure (Information
Utilization). All audits honor the three constraints in §9.

The audit content in this section is also available as a standalone
file at `docs/ADVERSARIAL_AUDIT_RESPONSES.md` for direct reference.
The standalone file contains the same text; Audit 11 was
numerically corrected (numerator sums 43 R1 / 58 R3; denominator
270 = 7×30 + 3×20) before being folded in.

### Audit 1 — Ontology Audit

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

### Audit 2 — Null-Reconstruction Audit (revised)

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

### Audit 3 — Reverse-Causality Audit

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

### Audit 4 — Adversarial Renaming Audit

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

### Audit 5 — Hidden Symmetry Audit

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

### Audit 6 — Counterfactual Population Audit

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

### Audit 7 — Information-Theoretic Audit

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

### Audit 8 — Uniqueness Audit

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

### Audit 9 — Research-Laundering Audit

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

### Audit 10 — Impossible Audit (revised)

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

### Audit 11 — Information Utilization Audit (new)

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

---

## 14. Three-model comparison and MDD null result

The identifiability framing in §12 leaves the H1/H2 question unresolved
by the closed record. Three models at three different levels sharpen
the question.

### The three models

- **Epistemic ceiling (this synthesis, §12)**: the closed record is
  finite-sample evidence within a single measurement regime. The C-5
  battery is a sample of the natural class $\mathcal{T}$, not
  $\mathcal{T}$ itself. Finite-sample evidence cannot establish a
  universal claim (H2). The closure statement is the isolation of an
  unresolved ambiguity.

- **Structural diagnosis (external analysis, not in this document)**:
  the observation channel is closed under probe-family dominance.
  Both $C$ and $B1$ are functions of the same sufficient statistic.
  Three exit paths require architectural changes outside the current
  observation channel: causal intervention, solver-space modeling,
  quotient-space equivalence.

- **Cheapest diagnostic (this section)**: fit Dirichlet parameters
  $\alpha_0$ and $\alpha_1$ separately on per-solver failure vectors
  split by oracle label. Test $H_0: \alpha_0 = \alpha_1$ via
  likelihood ratio. The data is in the closed record; no new
  measurement is required.

### The MDD test setup

The per-solver failure vector is $f(s) = (f_1, \ldots, f_6)$ where
$f_i$ = count of failures in family $i$ across all 30 probes on
LC322. Six families in axis-declaration order:
`reachability_counterfactual`, `non_canonical_coin_order`,
`large_amount_stress`, `greedy_dp_threshold`,
`forward_dp_overwrite`, `memo_cache_aliasing`. Solvers with
$M(s) = 0$ (all-zero failure vector) are excluded; they carry no
directional information.

The exclusion removed 6 solvers (solver_001 through solver_005, the
DP-survivors, and solver_026, the Hybrid; all oracle ACCEPT, all 30
probes passed). The remaining 24 solvers split into 5 oracle ACCEPT
(solver_019, 020, 021, 025, 027 — the 5 recoveries from C-4) and 19
oracle REJECT.

The likelihood ratio test uses a Newton MLE for each Dirichlet (with
pseudo-count 0.5 per family for regularization, lower bound 0.05 on
$\alpha_i$). The asymptotic reference is $\chi^2_6$ (six additional
parameters in the alternative). The permutation reference shuffles
oracle labels across the 24 included solvers and recomputes the LR
statistic; 2000 permutations, seed 20260607.

### Per-solver failure vectors (24 included solvers)

| Solver      | Oracle | $f_1$ | $f_2$ | $f_3$ | $f_4$ | $f_5$ | $f_6$ | Total |
|-------------|--------|------|------|------|------|------|------|-------|
| solver_006  | REJECT |    0 |    4 |    0 |    5 |    2 |    1 |    12 |
| solver_007  | REJECT |    3 |    5 |    5 |    5 |    5 |    5 |    28 |
| solver_008  | REJECT |    0 |    4 |    0 |    5 |    2 |    1 |    12 |
| solver_009  | REJECT |    0 |    4 |    0 |    5 |    2 |    1 |    12 |
| solver_010  | REJECT |    0 |    4 |    0 |    5 |    2 |    1 |    12 |
| solver_011  | REJECT |    3 |    3 |    1 |    3 |    2 |    2 |    14 |
| solver_012  | REJECT |    3 |    3 |    1 |    3 |    2 |    2 |    14 |
| solver_013  | REJECT |    3 |    3 |    1 |    3 |    2 |    2 |    14 |
| solver_014  | REJECT |    3 |    3 |    1 |    3 |    2 |    2 |    14 |
| solver_015  | REJECT |    3 |    3 |    1 |    3 |    2 |    2 |    14 |
| solver_016  | REJECT |    5 |    0 |    5 |    1 |    0 |    0 |    11 |
| solver_017  | REJECT |    5 |    0 |    5 |    0 |    0 |    0 |    10 |
| solver_018  | REJECT |    1 |    0 |    4 |    0 |    0 |    0 |     5 |
| solver_019  | ACCEPT |    0 |    0 |    2 |    0 |    0 |    0 |     2 |
| solver_020  | ACCEPT |    0 |    0 |    1 |    0 |    0 |    0 |     1 |
| solver_021  | ACCEPT |    0 |    0 |    2 |    0 |    0 |    0 |     2 |
| solver_022  | REJECT |    5 |    5 |    5 |    5 |    5 |    5 |    30 |
| solver_023  | REJECT |    5 |    0 |    5 |    0 |    0 |    0 |    10 |
| solver_024  | REJECT |    0 |    4 |    1 |    5 |    2 |    1 |    13 |
| solver_025  | ACCEPT |    0 |    0 |    2 |    0 |    0 |    0 |     2 |
| solver_027  | ACCEPT |    0 |    0 |    1 |    0 |    0 |    0 |     1 |
| solver_028  | REJECT |    0 |    4 |    0 |    5 |    2 |    1 |    12 |
| solver_029  | REJECT |    3 |    5 |    5 |    5 |    5 |    4 |    27 |
| solver_030  | REJECT |    5 |    5 |    5 |    5 |    5 |    4 |    29 |

### Result

LR statistic: 21.12. Asymptotic $\chi^2_6$ p-value: 0.0017. Monte
Carlo permutation p-value: 0.0045 (8/2000 permutations with LR
≥ observed). **Null verdict: REJECT at $\alpha = 0.05$** under both
references.

The fitted parameters:
- $\alpha_0$ (oracle ACCEPT, n=5): (1.69, 1.69, 4.95, 1.69, 1.69, 1.69) — peaked at family 3
- $\alpha_1$ (oracle REJECT, n=19): (1.77, 2.23, 1.69, 2.46, 1.81, 1.58) — range 1.58–2.46
- $\alpha_{combined}$ (all, n=24): (1.82, 2.20, 2.20, 2.38, 1.85, 1.66)

The signal is concentrated: the 5 oracle-ACCEPT solvers with failures
all fail in family 3 only. The 19 oracle-REJECT solvers show
failures across multiple families, with 4 solvers (solver_007, 022,
029, 030) close to uniform failure distributions.

### Caveat on the source of the signal

The test detects that failure direction is oracle-correlated. The
test does not discriminate between two sources of the correlation:

- **Solver-internal interpretation**: the 5 recoveries fail in family
  3. Family 3 is `large_amount_stress`. The pattern is consistent
  with solver-internal organization — a property of the algorithms
  rather than the probes.
- **Probe-induced interpretation**: family 3 (`large_amount_stress`)
  is constructed around amounts that stress BFS-family algorithms.
  Failure in family 3 is associated with probe construction.

The detected $\alpha_0 \neq \alpha_1$ is consistent with both
interpretations. The MDD test is informative for the existence of
the signal, not for the source.

### Logical consequence

With $H_0$ rejected, the question is no longer whether
oracle-correlated directional information exists in the closed
record (it does), and no longer whether finite-sample evidence can
establish H2 (it cannot, per §12). The remaining question is the
source of the signal.

This is the structural-diagnosis question: is the detected signal
solver-internal organization or probe construction, and which
architectural intervention would discriminate between them? The MDD
test answers neither. The question passes to the structural-diagnosis
model.

### Methodological notes

- Pseudo-count 0.5 per family: Laplace-style regularization. The
  qualitative pattern (alpha_0 peaked at family 3) holds across
  pseudo-count 0.1 to 1.0; the LR statistic magnitude scales with
  pseudo-count choice.
- Permutation seed: 20260607. Reproducible.
- Test script: `C:\Users\pakla\AppData\Local\Temp\opencode\mdd_test.py`
  (exploratory, not committed; temp script per the test setup).
- Result JSON: `C:\Users\pakla\AppData\Local\Temp\opencode\mdd_result.json`
  (exploratory, not committed).
- Per-solver per-probe pass/fail data: computed in-memory by
  `runners/run_midweather_fingerprint_lc322.py:execute_solvers` from
  the seval_manifest and probe_index. The data is not stored in any
  committed JSON; running the C-4 / C-1 runners regenerates it.

---

## 15. Phase C-7: quotient on `large_amount_stress` — RQ-C7 NEGATIVE

Phase C-7 is a new program authorized by Foued override. The
research question, quotient construction, perturbation battery,
and verdict criteria are pre-declared in `PHASE_C7_SPEC.md`
(commit `779f9cb`) and `PHASE_C7_FREEZE.json` (commit
`06bbe40`). The phase record is in `docs/PHASE_C7_RESULTS.md`
(commit `24ab42d`) and `data/c7_quotient_lc322.json` (commit
`5880f9b`). Tag: `phase-c7-results`. This section places C-7 in
the cross-phase sequence; it does not introduce new claims beyond
what the C-7 results doc §6 and §7 state.

### 15.1 Setup

Population: LC322 (30 solvers, 11 ACCEPT / 19 REJECT). The probe
set is restricted to the 5 `large_amount_stress` (family 3)
probes: `p_fp_0011` through `p_fp_0015`. The quotient population
$\tilde{P}$ is the set of equivalence classes of family-3 probes
under solver-response equivalence, restricted to a given solver
set $S$. On the unperturbed population, $|T_P| = 5$ (the 5
family-3 probes are in 5 distinct response classes). The
estimators under test are `B1_count` and `C_genuine` (existing,
unchanged). The cost model is the C-1 asymmetric cost with delta
= 0.10 and 9 lambda values. The C-7 battery has 5 conditions:
P0 (unperturbed) plus P1 (label inversion) and P2a, P2b, P2c
(solver subsamples of 20). P3a-f and P4 from C-5 are excluded
(P3a-f are no-ops on the family-3 quotient; P3c is degenerate;
P4 is the LC45 cross-population, out of scope for C-7).

### 15.2 Per-condition summary

| Condition  | \|S\| | \|T_P\| | D    | B1 (WA, WR)  | C_genuine (WA, WR) | Verdict     |
|------------|-------|---------|------|--------------|--------------------|-------------|
| P0         | 30    | 5       | 19   | (5, 5)       | (19, 0)            | COLLAPSE    |
| P1         | 30    | 5       | 19   | (6, 14)      | (11, 0)            | STABLE      |
| P2a        | 20    | 4       | 11   | (4, 2)       | (13, 0)            | COLLAPSE    |
| P2b        | 20    | 5       | 18   | (1, 5)       | (14, 0)            | COLLAPSE    |
| P2c        | 20    | 4       | 9    | (5, 3)       | (11, 0)            | COLLAPSE    |

RQ-C7 verdict: **NEGATIVE** (P0 COLLAPSE on the unperturbed
family-3 quotient). Aggregate consistency check on B1
(full 30-probe set) matches stored (WA=0, WR=5). **PASS.**

The unperturbed gap on P0 at lambda=1 is -0.30; at lambda=2 is
-0.13. Both are below delta=0.10. The C-1 cost model weights
wrong_rejects at lambda_R times the rate. At larger lambdas, the
gap sign-flips: B1's reject-bias becomes more costly, and C
catches up. The sign-flip with lambda is a property of the cost
model, not of the quotient.

### 15.3 P1 STABLE is an artifact, not a finding

P1 inverts the oracle labels (11/19 → 19/11). The quotient on
$R(s, p)$ is unchanged (equivalence is on solver responses, not on
labels). Estimator decisions are unchanged (B1 and C_genuine
operate on $R(s, p)$, not on the oracle). The label inversion
flips the cost calculation: C's 19 wrong_accepts on the original
labels become 19 correct_accepts on the inverted labels. B1's 5
wrong_rejects on the original become 5 wrong_accepts on the
inverted labels.

P1 surviving while P0, P2a, P2b, P2c all collapse is consistent
with the cost model operating correctly under a label-flip
perturbation, not with the quotient separation surviving any
meaningful perturbation. P1 is a control demonstrating the cost
model is operating correctly, not evidence that the family-3
quotient supports cost-weighted separation.

### 15.4 What C-7 adds to the three-phase sequence

C-4 showed the gain on the full 30-probe set on LC322. The MDD
test (SYNTHESIS §14) showed the gain is concentrated in family-3
failures. C-7 shows that when the probe space is restricted to
family-3 and the quotient is applied, C_genuine's accept-bias
becomes a liability: 19 false_accepts (the 19 oracle REJECT
solvers with at least one family-3 failure) versus B1's 5
false_rejects (the 5 C-4 recoveries). The C-4 gain on the
family-3 restricted population is a property of the
full-population cost geometry, not of estimator behavior on the
signal family.

The three-phase sequence (C-4 → MDD → C-7) is a sequence of
narrowing questions on the same closed data. Each step is a
doc-only analysis or a phase with a pre-declared criterion. No
step modifies any prior phase. The C-4 result stands at
`phase-c4-results` (commit `50d33e5`). The C-7 result stands at
`phase-c7-results` (tag).

### 15.5 What the C-7 result does not establish

(Mirrors `docs/PHASE_C7_RESULTS.md` §6. No new claims.)

1. The C-4 gain is not refuted by C-7. C-7 tests the family-3
   restricted quotient only, not the full 30-probe set. The
   full-30 C-4 result stands at `phase-c4-results`.

2. The C-4 gain is not established as probe-internal by C-7. A
   NEGATIVE C-7 result is consistent with the C-4 gain being a
   within-family probe distinction, but does not establish this.
   The H1/H2 ambiguity is not resolved by C-7 (per the spec).

3. `C_genuine` is not refuted as a decision rule. C-7 applies
   the rule on a restricted probe set where the rule's
   accept-bias produces many false_accepts. The full-30 result
   (C-4 PASS on LC322) and the family-3 restricted result (C-7
   NEGATIVE) are observations on different probe spaces; they
   are not in contradiction.

### 15.6 What the C-7 result does establish

(Mirrors `docs/PHASE_C7_RESULTS.md` §7. No new claims.)

On the unperturbed family-3 quotient population (P0, n=30
solvers, $|T_P| = 5$ abstract probes):

- The C-4 gain on the full 30-probe set does not survive
  restriction to the family-3 probe set.
- B1 has 5 wrong_rejects (the 5 C-4 recoveries). C_genuine has 0
  wrong_rejects and 19 wrong_accepts.
- The unperturbed gap at lambda=1 is -0.30; at lambda=2 is
  -0.13. Both are below delta=0.10.
- C_genuine's accept-bias is a liability on the family-3
  restricted population, where most solvers with family-3
  failures are oracle REJECT.

The collapse pattern (P0, P2a, P2b, P2c all collapse; only P1 is
stable, and P1 is the label-inversion control) is consistent
with the C-4 gain on the family-3 restricted population being a
property of the original accept/reject rate of the population,
not a property of the estimators.

### 15.7 Methodological notes

- Quotient construction is deterministic (sorted by
  representative_probe_id). See `tests/test_quotient.py`
  (commit `5963657`).
- Quotient on subsamples (P2a, P2b, P2c) is recomputed on the
  subsample solver set. The equivalence relation is over the
  subsampled solvers; two probes equivalent on the full 30 may
  not be equivalent on a subsample of 20.
- T_P sizes: P0=5, P1=5 (unchanged from P0), P2a=4, P2b=5,
  P2c=4. The P2a and P2c subsamples collapse one equivalence
  class; the discriminating solver is not in the subsample.
- Per-condition gap tables: see
  `data/c7_quotient_lc322.json` (commit `5880f9b`).
- The degeneracy on the unperturbed $\Delta$ is an arithmetic
  identity; the gap on the unperturbed quotient is informative
  and is the actual test. C-7 reports per-condition verdicts; the
  RQ-C7 verdict is the conjunction of all 5 conditions being
  STABLE, with P0 as one of the 5 conditions.

### 15.8 Lineage

| Item                                     | Commit    |
|------------------------------------------|-----------|
| `PHASE_C7_SPEC.md`                       | `779f9cb` |
| `PHASE_C7_FREEZE.json`                   | `06bbe40` |
| `doctor/adversarial/quotient.py`         | `5963657` |
| `tests/test_quotient.py`                 | `5963657` |
| `runners/run_c7_quotient_lc322.py`       | `d58fc00` |
| `data/c7_quotient_lc322.json`            | `5880f9b` |
| `docs/PHASE_C7_RESULTS.md`               | `24ab42d` |
| `docs/SYNTHESIS.md` (this section §15)   | (pending) |
| Tag: `phase-c7-results`                  | `24ab42d` |

C-7 inherits (lineage only, not modified):
- C-1 freeze `3bd286d`
- C-3a freeze `a6c97bc`, tag `phase-c3a-results` `1ad4777`
- C-4 freeze `88d0243`, tag `phase-c4-results` `50d33e5`
- C-5 freeze `98cc8e4`, tag `phase-c5-results` `d1435a3`
- C-6 freeze `6766f4c`, tag `phase-c6-results` `788fc5b`
- seval_manifest `d157d00`
- project-closure-004 `ccbf927`
- SYNTHESIS.md §14 (MDD test, commit `8d594a7`)

### 15.9 Mathematical reduction of the three-phase sequence

The material in this subsection is a **mathematical reduction**, not
a new measurement result. It is a definitional equivalence inside
the formalization consistent with the data, applied to the
trajectory C-4 → MDD → C-7. It does not reopen any prior phase. It
does not introduce new estimators, new probes, or new data. The
audit constraints from §Epistemological Constraints (no claim
stronger than the observation; no hidden causal language) apply to
this subsection.

The framing: C-7 did not add a new layer of structure to the
project. It stress-tested whether the previously observed
C–B1 separation survives quotient restriction and perturbation. It
does not, except in the trivial control regime. The question
collapses from "what happens if we refine the estimator" to
"what object is being measured when C appears to outperform B1".

The mathematical reduction is the following.

Let $S$ be the LC322 solver set ($|S| = 30$). Let $P$ be a probe
set on LC322. Let $O: S \to \{0, 1\}$ be the oracle partition.
Let $R(s, p) \in \{0, 1\}$ be the response of solver $s$ on probe
$p$ (0 = pass, 1 = fail; recorded at
`runners/run_midweather_fingerprint_lc322.py:execute_solvers`).

Define the induced partitions:

- B1 induces a scalar projection:
  [
  \phi_{B1}(s) = \sum_{p \in P} \mathbf{1}[R(s,p) = 1]
  ]
  This is a function of marginal failure mass only. B1 is invariant
  under probe relabeling.

- Any C-class estimator (such as `C_genuine`) induces a structured
  functional:
  [
  \phi_C(s) = F(\{R(s, p)\}_{p \in P})
  ]
  This depends on the joint structure of $R$, not only the marginal
  sum. C is not invariant under probe relabeling.

Define the only object that carries the C–B1 comparison across
phases:
[
\Delta_C(P) = \mathbb{E}_{s \sim S}[ \mathbf{1}[\phi_C(s) = O(s)] - \mathbf{1}[\phi_{B1}(s) = O(s)] ]
]

C–B1 "beats" reduces, under the current model, to:
[
\Delta_C(P) > 0
]

C-4, MDD, and C-7 are three test points on the function
$\Delta_C(\cdot)$:

- C-4 (commit `50d33e5`): $\Delta_C(P_{30}) > 0$ on the full
  30-probe LC322 population, where $P_{30}$ is the full probe set.
- MDD (SYNTHESIS §14, commit `8d594a7`): the C-4 gain is
  concentrated in family-3 failures on LC322.
- C-7 (commit `24ab42d`): $\Delta_C(P_{3}) \leq 0$ on the
  family-3 restricted quotient, where $P_{3}$ is the family-3 probe
  set. The collapse pattern is {P0 COLLAPSE, P1 STABLE, P2a
  COLLAPSE, P2b COLLAPSE, P2c COLLAPSE} (§15.2 above).

C-7 is the decisive constraint: $\Delta_C(P)$ changes sign under
restriction to a single family and is not stable under quotient
restriction. This kills the strong form:
[
\forall P' \subseteq P:\ \Delta_C(P') \geq 0
]

The surviving mathematical statement is strictly weaker:
[
\exists P' \subseteq P:\ \Delta_C(P') > 0
]
and
[
\exists P'' \subseteq P:\ \Delta_C(P'') \leq 0
]

This is the only form compatible with all observed phases
(C-4, MDD, C-7).

The key structural conclusion of the reduction: **C is not an
estimator that dominates B1 on an invariant ordering. It is a
functional that reshapes the partition induced by the probe
distribution.**

B1 is invariant under probe relabeling (it depends on marginal
failure mass). C is not; it depends on joint structure
$R(s, p)$.

This is a definitional equivalence inside the formalization, not a
new measurement result. The "tie-breaker" models considered
elsewhere in the project (Dirichlet-multinomial decomposition in
SYNTHESIS §14, mutual information between $\phi_C$ and $O$ at the
proposal level, quotient algebra in C-7) are all projections of
the same fact: the system being measured is non-commuting in the
sense
[
\phi_C \not\perp P
]
— the partition induced by $\phi_C$ over $S$ varies with the probe
distribution $P$.

From this: any apparent gain is a property of the interaction
between the estimator and the probe geometry, not a property of a
dominance relation between solvers as elements of $S$.

The final reduction is the equivalence (definitional inside the
formalization, not a new measurement): C beats B1 is equivalent
to the condition that the probe distribution $P$ induces a
feature-aligned subspace where $F(R)$ correlates with $O$. C-7
shows that this alignment is **not closed under restriction**,
the closure-under-restriction notion of fragility observed across
the C-4 → MDD → C-7 trajectory.

The "break the tie" answer under this reduction: there is no
global ordering $C > B1$. There is only a signed functional over
probe measures:
[
\Delta_C : \mathcal{P}(P) \to \mathbb{R}
]

The project is the empirical characterization of the regions of
$\mathcal{P}(P)$ where $\Delta_C$ is positive, zero, or negative.

That is the complete mathematical content of the C–B1
comparison under the existing data: the C-4 gain is a property of
the full-population cost geometry on $P_{30}$, and is not a
property of the estimators as elements of a dominance order on
$S$. The C-7 collapse on the family-3 restricted quotient
$\tilde{P}$ (§15.2) is the only formal refutation of the strong
form available in the closed record.

#### 15.9.1 What the reduction does not establish

- The reduction does not resolve the H1/H2 ambiguity (see C-7
  spec §Epistemological Constraint, lines 232-249).
- The reduction does not introduce a new estimator.
- The reduction does not generalize beyond LC322, beyond
  $\phi_{B1}$ and $\phi_{C_{\text{genuine}}}$, or beyond the C-1
  asymmetric cost model.
- The reduction does not modify the C-4 result
  (commit `50d33e5`) or the C-7 result (commit `24ab42d`).
- The reduction is consistent with the data; it is not derived
  from a new measurement.

#### 15.9.2 Audit posture

- "The mathematical reduction is...", "Under the current model,
  the tie reduces to...", "This is a definitional equivalence
  inside the formalization, not a new measurement result" — all
  framing statements. The substantive claims are restricted to
  the three test points (C-4 PASS, MDD concentration, C-7
  NEGATIVE) already recorded in §15.2, §14, and the C-4 / C-7
  results docs.
- Hidden causal language check: passed. The forbidden words
  (because, therefore, explains, caused by, due to, results in,
  leads to, comes from, as a result, hence, failed because) do
  not appear in this subsection.
- Word "real" check: passed. The C-4 gain is described as
  "previously observed" or "$\Delta_C(P_{30}) > 0$", not as
  "real".
