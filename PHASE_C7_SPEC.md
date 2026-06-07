# PHASE_C7_SPEC.md

# Doctor Phase C-7: Response-Equivalence Quotient on `large_amount_stress`

# Status: PROPOSED — Awaiting Foued authorization

# Date: 2026-06-07

---

## Explicit Non-Relationship Declaration

Phase C-7 is a **new program** authorized by Foued override. It is **not** a continuation of Phase C-1, C-3a,
C-4, C-5, or C-6, and it is **not** a reopening of the closed phases. It is a new research question with a new
quotient construction, applied to data that already exists in the closed record.

C-7 builds on prior freeze files for **lineage only**:

- Inherits the C-1 cost model and lambda sweep from `PHASE_C1_FREEZE.json` (commit `3bd286d`).
- Inherits the C-4 `C_genuine` decision rule from `doctor/adversarial/problem_class_config.py` (commit
  `865baf3`). C-7 does **not** modify `C_genuine`.
- Inherits the C-5 perturbation battery (P1, P2a-c, P3a-f, P4) from `PHASE_C5_FREEZE.json` (commit `98cc8e4`).
  C-7 restricts the battery to perturbations on the `large_amount_stress` subset (see "Perturbation Battery"
  below).
- Inherits the LC322 population (30 solvers) and the seval_manifest at commit `d157d00`.

What C-7 changes:

- Restricts the probe space to the `large_amount_stress` family (5 probes on LC322).
- Constructs a quotient on this restricted probe set by solver-response equivalence.
- Applies the existing `B1_count` and `C_genuine` decision rules to the quotient population.
- Tests whether `C_genuine`'s gain over `B1_count` survives the quotient collapse.

The closed phases are **not reopened**:

| Tag                   | Commit    | Content                                 | Status  |
|-----------------------|-----------|-----------------------------------------|---------|
| `project-closure-004` | `ccbf927` | Transfer-hypothesis. FAIL.              | Stands. |
| `phase-c1-results`    | `77ae794` | Asymmetric-cost sweep. Gap ≡ 0. FAIL.   | Stands. |
| `phase-c3a-results`   | `1ad4777` | Per-solver identity. FULL_EQUIVALENCE.  | Stands. |
| `phase-c4-results`    | `50d33e5` | C_genuine. PASS on LC322, FAIL on LC45. | Stands. |
| `phase-c5-results`    | `d1435a3` | PARTIALLY_SURVIVES. 6/11 perturbations. | Stands. |
| `phase-c6-results`    | `788fc5b` | RQ-C6 NO. 0/4 surviving rules.          | Stands. |

The MDD exploratory test (committed in §14 of `docs/SYNTHESIS.md` at `8d594a7`) is **not** a phase. It is a
doc-only analysis on existing data with a pre-declared test. C-7 does not extend or reinterpret it. C-7 is a
separate program with its own spec, freeze, and tag.

---

## Research Question (Declared Before Any Code)

**RQ-C7:** Does the `large_amount_stress` family boundary reflect solver-internal structure or probe
construction geometry? Operationalized: does oracle separation on the `large_amount_stress` family survive
quotient collapse by solver-response equivalence?

### Motivation

The MDD test in §14 of `docs/SYNTHESIS.md` detected that failure direction is oracle-correlated on LC322. The
signal is concentrated in `large_amount_stress` (family 3): the 5 C-4 recoveries fail only in this family. The
test did not discriminate between solver-internal organization and probe construction as the source of the
concentration.

C-7 takes a step toward discrimination. The C-5 collapse pattern showed that the C-4 gain is robust to P3
family knockouts of *other* families (P3a, P3b, P3d, P3e, P3f) but collapses on P3c (knockout of
`large_amount_stress`). This sensitivity to the family boundary, combined with the MDD concentration,
motivates the quotient construction: if two `large_amount_stress` probes produce identical response patterns
across all 30 solvers, they are probe-equivalent under any estimator that depends only on pass/fail.
Collapsing them removes probe-internal information while preserving solver-internal information.

C-7 tests the question on the existing data. It does not introduce new probes, new solvers, or new estimators.

---

## Quotient Construction (Declared Verbatim)

Let $P$ be the set of 5 `large_amount_stress` probes on LC322: $\{p_{11}, p_{12}, p_{13}, p_{14}, p_{15}\}$ (
probes `p_fp_0011` through `p_fp_0015`). Let $S$ be the LC322 solver set ($|S| = 30$).
Let $R(s, p) \in \{\text{pass}, \text{fail}\}$ be the response of solver $s$ on probe $p$.

**Equivalence relation:** $p \sim p'$ iff $\forall s \in S: R(s, p) = R(s, p')$.

**Quotient population:** $\tilde{P} = P / {\sim}$, the set of equivalence classes of `large_amount_stress`
probes under solver-response equivalence. The size $|\tilde{P}|$ is the number of distinct 30-dim response
vectors across the 5 family-3 probes (1 to 5, computed in Step 3).

Each abstract probe $\tilde{p} \in \tilde{P}$ is a class of original probes. The response $R(s, \tilde{p})$ is
the response $R(s, p)$ for any $p \in \tilde{p}$ (well-defined by the equivalence).

---

## Estimators Under Test

- **$M_{B1}$ (B1_count, existing):** ACCEPT iff observed failures = 0. Inherited from `PHASE_C1_FREEZE.json`.
  Unchanged.
- **$M_C$ (C_genuine, existing):** ACCEPT iff observed failures = 0 OR all observed failures share one
  `probe_family`. Inherited from `doctor/adversarial/problem_class_config.py` (commit `865baf3`). Unchanged.

C-7 applies both estimators to the quotient population $\tilde{P}$. The estimator's interface is the same as
in prior phases:

```
rule(obs_fails, n_obs, obs_records) -> "ACCEPT" | "REJECT"
```

For the quotient, `obs_records` is built from the abstract probes in $\tilde{P}$. Each abstract probe has
`probe_family` = `large_amount_stress` (inherited from the original probes in the class).

**C-7 does not introduce new estimators.** Both estimators are applied as-is. No new rule functions, no new
policy bindings, no modification of `problem_class_config.py`.

---

## Success and Failure Criteria

### Setup

Let $\Delta(M_C, M_{B1}; \tilde{P})$ be the per-solver decision divergence: the number of solvers where $M_C$
and $M_{B1}$ produce different decisions, restricted to $\tilde{P}$ (or the appropriate perturbed population).
The aggregate utility gap is computed under the C-1 cost model.

### Success Criterion (declared verbatim)

$\Delta(M_C, M_{B1}; \tilde{P}) > 0$ AND stable under the C-5 perturbation battery restricted to
`large_amount_stress`.

### Degeneracy on Unperturbed Quotient

On the unperturbed family-3 quotient $\tilde{P}$, the condition
$\Delta(M_C, M_{B1}; \tilde{P}) > 0$ is an arithmetic identity, not
a measurement. The condition holds by construction whenever any
solver has a family-3 failure; no application of the estimators is
required to verify it.

The `C_genuine` rule accepts a solver if (a) observed failures = 0,
or (b) all observed failures share one `probe_family`. On the
family-3 quotient, every probe has `probe_family` =
`large_amount_stress` by inheritance from the original probes in the
class. The set of failures sharing one `probe_family` is the set of
all failures. Condition (b) is vacuously satisfied for any solver
with one or more failures. `C_genuine` accepts every solver with 0
failures (matching `B1_count`) AND every solver with one or more
failures (differing from `B1_count`).

The unperturbed $\Delta(M_C, M_{B1}; \tilde{P})$ equals the count of
solvers with one or more family-3 failures. This is a count of
solvers with family-3 failures, not a measurement of estimator
behavior on the quotient. The unperturbed $\Delta > 0$ is guaranteed
by construction whenever any solver has a family-3 failure; the
condition is satisfied by inspection of the data.

The informative condition is the **stability of the divergence
under the four perturbations in the C-7 battery**. A perturbation of
$\tilde{P}$ either preserves the family-3 boundary (the arithmetic
identity continues to hold) or modifies it (the quotient no longer
reduces to a single family, and the vacuous-satisfaction argument
does not apply). The four perturbations in the C-7 battery (P1, P2a,
P2b, P2c) test these conditions. A 'positive' C-7 result requires
the divergence to hold at all 9 lambda values on all 4 perturbations.
A 'positive' verdict on the unperturbed $\Delta$ alone is not a
positive verdict on RQ-C7; the unperturbed condition is necessary
but uninformative.

### Per-Perturbation Stability

This subsection is the **actual test** of C-7. The unperturbed
$\Delta > 0$ is an arithmetic identity (see Degeneracy above); the
informative condition is whether the divergence survives
perturbations.

A perturbation is "stable" for C-7 if:

- $\Delta(M_C, M_{B1}; \tilde{P}_{P}) > 0$ at all 9 lambda values in
  the C-1 sweep, AND
- The aggregate utility gap on $\tilde{P}_{P}$ exceeds 0.10 at all 9
  lambda values.

If any lambda on any perturbation has $\Delta \leq 0$ or gap
$\leq 0.10$, the perturbation is a "collapse". A C-7 result with
one or more collapses is a 'negative' or 'mixed' result on RQ-C7,
not a 'positive' result, regardless of the unperturbed $\Delta$.

### Failure Criterion (declared verbatim)

$\Delta \leq 0$ OR collapses under perturbation.

---

## Perturbation Battery (Restricted from C-5)

C-5's battery has 11 perturbations. On the family-3 restricted quotient:

- **P1 (label inversion):** included. The 11/19 ACCEPT/REJECT split is inverted to 19/11 ACCEPT/REJECT for the
  affected solvers.
- **P2a, P2b, P2c (solver subsample):** included. The 30-solver LC322 population is subsampled to 20 solvers
  in the three fixed draws from `PHASE_C5_FREEZE.json`.
- **P3a, P3b, P3d, P3e, P3f (knockout of families 1, 2, 4, 5, 6):** **excluded** as no-ops on the family-3
  quotient. Knocking out non-family-3 probes does not change the family-3 probe set or the quotient.
- **P3c (knockout of family 3, i.e., `large_amount_stress`):** **excluded.** Knockout of the family under test
  zero-outs the quotient population. This perturbation is degenerate on $\tilde{P}$. Recording it as a "
  collapse" would be a definitional artifact, not a finding.
- **P4 (LC45 cross-population):** **excluded.** C-7 is on LC322 only. The LC45 cross-population test was C-5's
  P4 and is not extended to C-7.

**C-7 perturbation battery:** {P1, P2a, P2b, P2c} (4 perturbations). The quotient is unperturbed (P0) plus the
4 perturbations, for 5 conditions total.

C-7 does not introduce new perturbations. C-7 does not modify the C-5 perturbation parameters for the included
perturbations.

---

## What This Phase Does Not Do

- Does not reopen `project-closure-004`, `phase-c1-results`, `phase-c3a-results`, `phase-c4-results`,
  `phase-c5-results`, or `phase-c6-results`.
- Does not introduce new probes or probe families.
- Does not introduce new solver packs.
- Does not introduce new estimators, new rule functions, or new policy bindings.
- Does not modify the C-1 freeze parameters (delta, lambda sweep, lambda_A).
- Does not modify the C-5 perturbation parameters.
- Does not modify the C-4 `C_genuine` decision rule.
- Does not vary the oracle.
- Does not generalize beyond LC322.
- Does not claim that the quotient collapse resolves H1/H2 (see "Epistemological Constraint" below).
- Does not adjust any estimator's decision function after seeing quotient results.
- Does not silently resolve aggregate-consistency discrepancies. Foued call required.

---

## Epistemological Constraint (Declared Verbatim)

A positive result establishes that separation survives response-equivalence collapse. It does not establish
that the signal is solver-internal. The H1/H2 ambiguity is not resolved by this phase.

A positive C-7 outcome (Δ > 0 stable under the C-5 battery restricted to `large_amount_stress`) is a
structural observation about the quotient: the C-4 gain is not an artifact of probe-level distinctions within
the family. It is consistent with the signal being solver-internal. It is also consistent with the signal
being probe-induced at the family level (i.e., the family-3 boundary is a property of the probe design, not
the solvers). The quotient collapse rules out the third possibility (probe-level distinctions within the
family) but does not discriminate between the first two.

A negative C-7 outcome (Δ ≤ 0 on the quotient, or collapses under perturbation) is consistent with the C-4
gain being an artifact of within-family probe distinctions. The C-4 result would then be reframed: the gain is
a property of how the 5 family-3 probes distinguish solvers, not of the family-3 boundary itself.

In neither case does C-7 resolve H1/H2. The H1/H2 question is about the discrimination between solver-internal
organization and probe construction at the family level. C-7 tests a different question: does the
within-family probe geometry contribute to the gain? The two questions are related but distinct.

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested population (LC322), tested family (
   large_amount_stress), and tested perturbation set (P1, P2a-c).
3. **Hidden causal language:** no because / therefore / explains / caused by / due to.
4. **Aggregate-consistency check:** required before any result is recorded; failure stops the phase and
   surfaces to Foued.
5. **Per-perturbation reporting only:** no aggregation across perturbations.
6. **Per-estimator reporting only:** no aggregation across estimators except the pre-declared Δ criterion.

§7 hard-stop rule: if any move requires violating the above, stop and surface the conflict.

---

## Hard Stop Conditions (Extended from C-4, C-5, C-6)

1. Re-run produces (WA, WR) inconsistent with stored aggregates for B1 → STOP.
2. The C-5 perturbation battery parameters are modified after the freeze is committed → STOP, surface to
   Foued.
3. The C-4 `C_genuine` decision rule is modified after the freeze is committed → STOP, surface to Foued.
4. A new estimator is introduced without Foued override → STOP, surface to Foued.
5. The oracle is varied without Foued override → STOP, surface to Foued.
6. The quotient construction is changed after the freeze is committed → STOP, surface to Foued.

---

## Deliverables

1. `PHASE_C7_SPEC.md` — this file
2. `PHASE_C7_FREEZE.json` — pre-declared parameters (commit before any code)
3. `doctor/adversarial/quotient.py` (new module) — quotient construction on the family-3 probe set
4. `tests/test_quotient.py` — tests for quotient construction
5. `runners/run_c7_quotient_lc322.py` — runner (committed before execution)
6. `data/c7_quotient_lc322.json` — quotient population, per-perturbation decisions, gaps
7. `docs/PHASE_C7_RESULTS.md` — findings, audit-passed
8. Tag: `phase-c7-results`

---

## Protocol (mirrors C-4, C-5, C-6)

**Step 0 — Commit this spec and the freeze file before any code is written.** No runner is written until both
files are committed.

**Step 1 — Write `PHASE_C7_FREEZE.json`.** Contents: 5 family-3 probe IDs, the equivalence relation, the C-1
cost model, the C-5 perturbation battery restricted to {P1, P2a-c}, the success/failure criteria, the delta =
0.10 threshold, the lambda sweep. Commit before any runner is written.

**Step 2 — Write `tests/test_quotient.py` (TDD red phase).** Tests must include:

- Equivalence relation is reflexive, symmetric, transitive (sanity check).
- Two probes with identical 30-dim response vectors are in the same equivalence class.
- Two probes with at least one differing solver response are in different classes.
- The quotient population $\tilde{P}$ has size 1 to 5.
- The quotient construction is deterministic (same input → same output).
- B1 and C_genuine applied to the quotient produce decisions in {ACCEPT, REJECT}.
- Aggregate-consistency check carries forward from C-3a, C-4, C-5, C-6.

**Step 3 — Implement `doctor/adversarial/quotient.py`.** Module exports the quotient construction. Commit
module + tests together. All tests green.

**Step 4 — Write runner `runners/run_c7_quotient_lc322.py`.** For each of {P0, P1, P2a, P2b, P2c}, compute the
quotient (where applicable), apply B1 and C_genuine, record (D, A, gap) per (estimator, perturbation). Commit
before execution.

**Step 5 — Execute.** Check aggregate consistency for B1. STOP if any inconsistency. If passes, apply success
criterion and failure criterion per perturbation. Apply stability criterion across the C-7 battery.

**Step 6 — Write `docs/PHASE_C7_RESULTS.md`.** Per-perturbation Δ and gap table. RQ-C7 verdict (POSITIVE /
NEGATIVE / MIXED). Audit against three failure modes before commit.

**Step 7 — Tag `phase-c7-results`.**

---

## Governance Acknowledgment

C-7 is authorized by Foued override. The MDD exploratory result in §14 of `docs/SYNTHESIS.md` (commit
`8d594a7`) is a doc-only analysis that motivated C-7's research question. C-7 is a new program, not an
extension of §14. C-7 does not modify any prior phase.

C-7 does not introduce new estimators. Both estimators (B1_count and C_genuine) are inherited unchanged. C-7's
only novel artifact is the quotient construction, which is declared verbatim in this spec.

If Foued at any point withdraws the C-7 override, the phase stops. The C-7 spec and freeze remain in the
repository as a record of the authorized program.
