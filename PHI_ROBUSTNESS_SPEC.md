# PHI_ROBUSTNESS_SPEC v1.0

**Author:** Claude (architecture)
**Date:** 2026-06-12
**Status:** DRAFT — pending GPT review, then Mimo execution
**Scope:** φ-stability validation layer for DOCTOR/BIMARISTAN paper

---

## 0. Purpose

This spec addresses the single most dangerous reviewer attack surface identified in the post-audit analysis:

> The paper has not demonstrated that ΔU > 0 is invariant under changes in the representational choice (φ)
> that defines the phenomenon.

Until this is shown, ΔU is potentially an artifact of the specific failure-family partition chosen, not a
property of the phenomenon itself.

This spec defines the exact experiments needed to close that gap.

---

## 1. The Problem, Stated Precisely

The current system fixes φ (the failure-family partition) at design time. The result ΔU is then computed under
that fixed φ. This creates a non-independence risk:

```
design(φ) → evaluation(φ) → result(ΔU(φ))
     ↑_________________________________|
              (potential circularity)
```

The required demonstration is:

> ΔU sign is stable across a defined class of admissible φ-perturbations.

This transforms the claim from:

- "we found a partition that works" (artifact)

to:

- "there exists a robustness region over partitions" (phenomenon)

---

## 2. Definitions

### 2.1 φ (Current, Canonical)

The failure-family partition as currently implemented in `csse/run_csse_v2.py`. This is the baseline. All
perturbations are measured relative to it.

### 2.2 Admissible Perturbation

A perturbation of φ is admissible if and only if:

- It preserves the total probe count
- It preserves the binary pass/fail outcome per probe
- It only changes *how probes are grouped into families*

What this means: we are not changing the underlying evaluation. We are changing the labeling of failures into
families. This isolates φ as the sole variable.

### 2.3 ΔU Stability

ΔU is considered sign-stable under a perturbation φ' if:

- sign(ΔU(φ')) = sign(ΔU(φ_canonical))

ΔU is considered magnitude-stable if:

- |ΔU(φ') - ΔU(φ_canonical)| / |ΔU(φ_canonical)| < 0.5

Sign-stability is the primary criterion. Magnitude-stability is secondary.

---

## 3. The Five Perturbation Conditions

Each condition must be run on LC322 and LC3946 (the two positive-ΔU cases). LC45 and LC743 (negative cases)
are run as control — we expect ΔU ≈ 0 to remain stable under all perturbations.

### Condition P1 — Randomized Coarse Graining

Merge current failure families into fewer, broader groups.

**Implementation:** Randomly merge canonical failure families into ceil(N/2) groups. Perform K=20 independent
merge realizations. Report mean ΔU over realizations.

**What this tests:** Whether fine-grained family structure is necessary for ΔU > 0, or whether coarser
structure preserves the signal.

**Expected result if phenomenon is real:** ΔU sign preserved, magnitude may decrease.

---

### Condition P2 — Balanced Stochastic Fine Graining

Split current failure families into more specific subgroups.

**Implementation:** For each canonical family F, randomly split probes into F_a and F_b with equal size. No
external attributes are used — the split is conditioned only on canonical family membership. Repeat K=20
independent splits. Report mean ΔU over realizations.

**What this tests:** Whether the signal survives at higher resolution.

**Expected result if phenomenon is real:** ΔU sign preserved, magnitude may increase or decrease.

---

### Condition P3 — Semantic Reordering

Reassign probes to families using an alternative semantically coherent grouping.

**Implementation:** Use a grouping criterion orthogonal to the canonical one. If canonical φ groups by failure
type (e.g., TLE, WA, RE), P3 groups by input structure (e.g., edge cases, large inputs, adversarial inputs).
Both are semantically meaningful; they are just different axes.

**What this tests:** Whether ΔU depends on the specific semantic axis chosen, or whether any coherent axis
produces the signal.

**Expected result if phenomenon is real:** ΔU sign preserved. If ΔU collapses here but not under P1/P2, the
axis choice is load-bearing and must be disclosed.

---

### Condition P4 — Constrained Random Partition (Null Model)

Assign probes to families uniformly at random, preserving family count and exact family-size vector.

**Implementation:** Randomly permute probe-to-family assignments N=100 times. Preserve:

- family count
- exact family-size vector of canonical φ (same multiset of family sizes)

Only permute assignments under that constraint. Compute ΔU for each permutation. Report mean(ΔU), std(ΔU), and
fraction of permutations where sign(ΔU) = sign(ΔU_canonical).

**What this tests:** This is the null model. If ΔU > 0 under random partitioning at high frequency, the
canonical φ is not special — any grouping produces the signal, which means the signal is not about failure
structure at all.

**Expected result if phenomenon is real:** Random partitions should NOT reliably reproduce ΔU > 0. The
canonical φ should be in the tail of the random distribution.

**Critical:** This is the most important condition. If canonical ΔU is not in the tail of P4's distribution,
the paper cannot be published in its current form.

---

### Condition P5 — Adversarial Partition (Maximally Destructive)

Construct the partition most likely to destroy ΔU.

**Implementation:** Assign probes to families such that each family contains an equal mixture of pass and fail
outcomes across all solvers. This maximally homogenizes the family signal — each family looks like every other
family. This is the worst-case partition for C_genuine.

**What this tests:** The lower bound of ΔU under adversarial φ. This condition is expected to collapse ΔU
toward 0.

**Expected result:** ΔU ≈ 0 or ΔU < 0. If ΔU remains strongly positive even here, C_genuine is doing something
unexpected and must be investigated before publication.

---

## 4. Required Outputs Per Condition

For each perturbation condition Pi, on each problem (LC322, LC3946, LC45, LC743):

All ΔU values include bootstrap confidence intervals computed over ≥100 solver resamples.

```
{
  problem: "LC322",
  condition: "P1",
  phi_description: "...",
  n_families_canonical: N,
  n_families_perturbed: M,
  delta_U_canonical: X,
  delta_U_canonical_ci: [lo, hi],
  delta_U_perturbed: Y,
  delta_U_perturbed_ci: [lo, hi],
  sign_stable: true/false,
  magnitude_ratio: |Y-X|/|X|,
  notes: "..."
}
```

For P4 (random), additionally report:

```
{
  n_permutations: 100,
  delta_U_mean: ...,
  delta_U_std: ...,
  delta_U_canonical_percentile: ...,  ← critical number
  fraction_same_sign: ...
}
```

---

## 5. Stability Classification

After all conditions complete, classify each problem:

| Classification       | Criterion                                                                                             |
|----------------------|-------------------------------------------------------------------------------------------------------|
| ROBUST               | Sign-stable under P1, P2, P3. Canonical φ in tail of P4 (>80th percentile). P5 collapses as expected. |
| CONDITIONALLY ROBUST | Sign-stable under P1, P2. P3 shows axis-dependence. Must be disclosed.                                |
| FRAGILE              | Sign unstable under P1 or P2. Result is partition-dependent.                                          |
| ARTIFACT             | Canonical φ not in tail of P4. Result is not distinguishable from random grouping.                    |

---

## 6. What Each Classification Means for Publication

**ROBUST:** ΔU > 0 is a phenomenon. Paper publishes existence result with φ-robustness section as evidence of
non-artifactuality. Strong submission.

**CONDITIONALLY ROBUST:** Paper must disclose axis-dependence. Existence result stands but claim is
narrowed: "under semantically aligned partitions." Still publishable, weakened.

**FRAGILE:** Paper cannot claim existence result as currently framed. Must reframe as "under canonical φ
specifically." Significantly weakened. May still be publishable as a methodology paper.

**ARTIFACT:** Paper cannot be submitted in current form. The result is an artifact of the partition choice.
Requires fundamental redesign of φ before resubmission.

---

## 7. Sequencing

This spec must be executed before any of the following:

- Claim language rewrite
- ψ section decisions
- arXiv submission of any kind
- Phase diagram revision

Reason: the output of this spec determines what claims are defensible. Writing claims before knowing
φ-stability is writing in the dark.

---

## 8. Scope Boundaries for Mimo

**In scope:**

- Implementing P1–P5 on LC322 and LC3946
- Running LC45 and LC743 as controls
- Producing the structured output per section 4
- Classifying each problem per section 5

**Out of scope:**

- Modifying the canonical φ
- Changing the evaluation protocol (E)
- Changing the solver population
- Interpreting results — classification only, no interpretation
- Any paper edits

**Stop condition:** Mimo stops and reports if any condition cannot be implemented without modifying E or the
solver population. This requires human decision before proceeding.

---

## 9. Acceptance Criteria for This Spec

This spec is accepted when GPT confirms:

1. The five conditions cover the non-independence attack surface adequately
2. The stability classification thresholds (section 5) are appropriate
3. The scope boundaries for Mimo are correctly drawn

This spec is sent to Mimo only after GPT acceptance.
