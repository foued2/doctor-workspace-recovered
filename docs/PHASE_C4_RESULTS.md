# PHASE_C4_RESULTS.md
# Doctor Phase C-4: Genuine Structured Policy — Results
# Status: CLOSED — RQ-C4 verdict: PASS on LC322 (primary), FAIL on LC45 (stress test)
# Date: 2026-06-06
# Freeze: PHASE_C4_FREEZE.json (commit 88d0243)
# Spec: PHASE_C4_SPEC.md (commit cab8af3)

---

## 1. Verdict

**RQ-C4: PASS on LC322 (primary), FAIL on LC45 (stress test).**

On the primary population (LC322), `C_genuine` produces different per-solver decisions than B1 on 6 solvers (D = 6 > 0), and the utility gap exceeds the pre-declared threshold δ = 0.10 at every lambda in the C-1 sweep. The best gap is 8.30 at λ = 50.

On the stress test (LC45), `C_genuine` differs from B1 on 1 solver (D = 1 > 0) but the utility gap is negative at every lambda (`C_genuine` introduces 1 false accept on a population where B1 is perfect). The gap never exceeds 0.10. LC45 result is reported separately and does not override the LC322 verdict, per the C-4 spec.

Phase C-4 is closed.

---

## 2. Numerical Detail (LC322, primary)

| λ_R | utility(B1) | utility(C_genuine) | gap | eligible (gap > 0.10) |
|----:|-----------:|------------------:|----:|----------------------:|
|   1 |     0.8333 |            0.9667 |  0.1333 | True |
|   2 |     0.6667 |            0.9667 |  0.3000 | True |
|   5 |     0.1667 |            0.9667 |  0.8000 | True |
|   7 |    -0.1667 |            0.9667 |  1.1333 | True |
|  10 |    -0.6667 |            0.9667 |  1.6333 | True |
|  15 |    -1.5000 |            0.9667 |  2.4667 | True |
|  20 |    -2.3333 |            0.9667 |  3.3000 | True |
|  30 |    -4.0000 |            0.9667 |  4.9667 | True |
|  50 |    -7.3333 |            0.9667 |  8.3000 | True |

Source: `data/c4_decisions_lc322.json`.

The falsification PASS condition is satisfied at all 9 lambda values. The best gap is 8.30 at λ = 50.

---

## 3. Per-Solver Evidence (LC322)

C_genuine and B1 differ on 6 solvers:

| solver_id | ground_truth | B1 decision | C_genuine decision | Outcome for C_genuine |
|---|---|---|---|---|
| solver_018 | REJECT | REJECT | ACCEPT | False accept (worse) |
| solver_019 | ACCEPT | REJECT | ACCEPT | True recovery (better) |
| solver_020 | ACCEPT | REJECT | ACCEPT | True recovery (better) |
| solver_021 | ACCEPT | REJECT | ACCEPT | True recovery (better) |
| solver_025 | ACCEPT | REJECT | ACCEPT | True recovery (better) |
| solver_027 | ACCEPT | REJECT | ACCEPT | True recovery (better) |

Net: 5 true recoveries, 1 false accept. C_genuine is more permissive than B1, and on LC322 the benefit (eliminating 5 false rejects) outweighs the cost (introducing 1 false accept) at every tested lambda.

Source: `data/c4_decisions_lc322.json`.

---

## 4. Numerical Detail (LC45, stress test)

| λ_R | utility(B1) | utility(C_genuine) | gap | eligible (gap > 0.10) |
|----:|-----------:|------------------:|----:|----------------------:|
|   1 |     1.0000 |            0.9000 | -0.1000 | False |
|   2 |     1.0000 |            0.9000 | -0.1000 | False |
|   5 |     1.0000 |            0.9000 | -0.1000 | False |
|   7 |     1.0000 |            0.9000 | -0.1000 | False |
|  10 |     1.0000 |            0.9000 | -0.1000 | False |
|  15 |     1.0000 |            0.9000 | -0.1000 | False |
|  20 |     1.0000 |            0.9000 | -0.1000 | False |
|  30 |     1.0000 |            0.9000 | -0.1000 | False |
|  50 |     1.0000 |            0.9000 | -0.1000 | False |

Source: `data/c4_decisions_lc45.json`.

B1 is perfect on LC45 (0 wrong accepts, 0 wrong rejects). C_genuine introduces 1 false accept (a REJECT solver whose failures are concentrated in one probe_family, triggering the C_genuine ACCEPT branch). The gap is -0.10 at every lambda. The falsification PASS condition is not satisfied.

LC45 is a single-survivor skew (1 ACCEPT, 9 REJECT). The C-4 spec records LC45 separately; its result does not override the LC322 verdict.

---

## 5. Identity Resolution (Three-Case Report)

| Population | M_C_genuine | M_B1 | D = |M_C △ M_B1| | A | Three-case |
|---|---|---|---|---|---|
| LC322 | {solver_018, solver_019, solver_020, solver_021, solver_025, solver_027} | {solver_019, solver_020, solver_021, solver_025, solver_027} | 6 | 50 | DIRECTIONAL_SUPERIORITY |
| LC45  | {the 1 REJECT solver with structured failures} | {} (empty, B1 perfect) | 1 | 1 | DIRECTIONAL_SUPERIORITY |

On LC322, D > 0 and A > 0. The C-4 falsification criterion (D > 0 required, utility gap > 0.10 required) is satisfied.

On LC45, D > 0 and A > 0 (the C_genuine ACCEPT branch is triggered for 1 solver that B1 correctly rejects). The identity test shows C_genuine is not operationally B1, but the utility gap is negative (C_genuine introduces 1 false accept on a population where B1 is perfect). The three-case report shows DIRECTIONAL_SUPERIORITY, but the falsification criterion for PASS is not met.

---

## 6. Why C_genuine Improves on LC322

C_genuine's decision rule:

```
ACCEPT if 0 failures OR all failures share one probe_family
REJECT otherwise
```

On LC322, the 5 solvers misclassified by B1 (solver_019, solver_020, solver_021, solver_025, solver_027) all have ground_truth = ACCEPT and a small number of observed failures, all in one probe_family. C_genuine's rule classifies them as ACCEPT because all failures share one family.

The 1 additional false accept (solver_018) is a REJECT solver whose observed failures are also in one probe_family. C_genuine accepts it under the same rule, but the ground truth is REJECT.

The cost model is linear with global weights. At lambda = 50:
- B1's cost: 5 false rejects × 50 = 250
- C_genuine's cost: 1 false accept × 1 = 1
- Net savings: 249

At lambda = 1:
- B1's cost: 5 × 1 = 5
- C_genuine's cost: 1 × 1 = 1
- Net savings: 4

The net savings is positive at every tested lambda. Normalized utility gap is 8.30 at lambda = 50 and 0.13 at lambda = 1. Both exceed delta = 0.10.

---

## 7. Scope Discipline

This result is conditional on:

- The PHASE_C4 freeze (commit 88d0243), which inherits the C-1 cost model and lambda sweep.
- The C_genuine decision rule as declared in the spec before implementation (ACCEPT if 0 failures or all failures share one probe_family; REJECT otherwise).
- The 8 original C-1 estimators preserved in the codebase. C_genuine is an additional estimator, not a replacement.
- The tested populations: LC322 (primary) and LC45 (stress test).
- The frozen probe index, solver packs, and oracle from C-1.

This result does **not** establish any of the following:

- That C_genuine would beat B1 on populations outside LC322 and LC45. The C-4 spec restricts the claim to these two frozen populations.
- That C_genuine is the best possible structured policy. The decision rule is one specific option among many. Other rules that consume `probe_family` (or other fingerprint features) could produce different results.
- That the C-1 verdict is reopened. C-1 tested `C_structured_fingerprint` (which is bound to `_fail_count_policy`); C-4 tests `C_genuine` (which uses `probe_family`). These are different estimators with different policies. C-1's FAIL on `C_structured_fingerprint` is not contradicted by C-4's PASS on `C_genuine`.
- That the C-3a verdict is reopened. C-3a compared `C_structured_fingerprint` and B1 (both bound to `_fail_count_policy`) and found FULL_EQUIVALENCE. C-4 compares `C_genuine` and B1, which differ by design. The C-3a finding about `C_structured_fingerprint` is not contradicted by the C-4 finding about `C_genuine`.
- That project-closure-004 is reopened.

---

## 8. Connection to Closed Phases

| Phase | Estimator compared | Verdict | Scope |
|---|---|---|---|
| C-1 | `C_structured_fingerprint` (bound to `_fail_count_policy`) vs B1 | FAIL (gap ≡ 0) | Both populations |
| C-3a | `C_structured_fingerprint` vs B1 (identity, not utility) | FULL_EQUIVALENCE (D=0, A=0) | Both populations |
| C-4 | `C_genuine` (uses `probe_family`) vs B1 | PASS (gap > 0.10 at all λ) on LC322, FAIL on LC45 | LC322 primary, LC45 stress |

C-4 does not reopen C-1 or C-3a. The three phases test different questions with different estimators:

- C-1: Does C (as a placeholder bound to the B1 policy) beat B1 on decision utility? Answer: No. C is operationally B1.
- C-3a: Are C and B1 the same estimator? Answer: Yes, both are bound to `_fail_count_policy`.
- C-4: Does a C that actually uses structured features (probe_family) beat B1 on decision utility? Answer: Yes on LC322, No on LC45.

C-4 is the first phase where the C estimator is genuinely different from B1. The C-4 PASS is not a refutation of C-1's FAIL; it is a finding about a different estimator.

---

## 9. What This Phase Did Not Do (Spec Compliance)

Per the spec (PHASE_C4_SPEC.md §"What This Phase Does Not Do"):

- Did not reopen `project-closure-004`, `phase-c1-results`, or `phase-c3a-results`.
- Did not introduce new probes, probe geometry, or solver packs.
- Did not modify the C-1 freeze parameters (delta, lambda sweep, lambda_A, populations).
- Did not introduce new estimator names beyond `C_genuine`.
- Did not adjust the C_genuine decision rule after seeing per-solver results. The rule was declared in the spec (commit cab8af3) before any code was written.
- Did not construct a per-solver-weighted cost functional (C-2 territory).
- Did not silently resolve aggregate-consistency discrepancies. The hard-stop gate passed for B1 on both populations.

Per the spec (PHASE_C4_SPEC.md §"Epistemological Constraints"):

- No compression drift: all claims are tied to the observed per-solver decision data and the freeze's cost function.
- No negative result inflation: scope is restricted to the tested populations and the C_genuine decision rule. The LC45 FAIL is reported, not hidden.
- No hidden causal language: the PASS is described as an observation about the specific C_genuine rule on the specific frozen populations, not a general claim about structured estimators.

---

## 10. Artifacts Produced

- `data/c4_decisions_lc322.json` — 30 solvers, per-solver B1 and C_genuine decisions, aggregates, D=6, A=50, utility gap table, verdict PASS.
- `data/c4_decisions_lc45.json` — 10 solvers, per-solver B1 and C_genuine decisions, aggregates, D=1, A=1, utility gap table, verdict FAIL.
- `PHASE_C4_SPEC.md` (commit cab8af3) — RQ, decision rule, falsification criterion, D > 0 requirement, governance acknowledgment.
- `PHASE_C4_FREEZE.json` (commit 88d0243) — pre-declared parameters: decision rule, feature used (probe_family), estimators (C_genuine, B1), delta=0.10, lambda sweep, D > 0 requirement.
- `doctor/adversarial/problem_class_config.py` (commit 865baf3) — `_c_genuine_policy` function, bound to `C_genuine` in both `LC322_ESTIMATOR_POLICIES` and `LC45_ESTIMATOR_POLICIES`.
- `tests/test_genuine_policy.py` (commit 865baf3) — 21 tests for C_genuine.
- `tests/test_apply_estimator_signature.py` (commit 865baf3) — updated backward-compat tests to exclude C_genuine; new test that C_genuine intentionally breaks backward-compat.
- `runners/run_c4_decisions_lc322.py` (commit f4329f8) — LC322 runner.
- `runners/run_c4_decisions_lc45.py` (commit f4329f8) — LC45 runner.

---

## 11. Closure Statement

Phase C-4 is closed as of this document. The pre-declared RQ-C4 falsification has been evaluated:

- **LC322 (primary):** PASS. Utility gap > 0.10 at all 9 tested lambda values, with D = 6 > 0 and A = 50. Best gap is 8.30 at lambda = 50.
- **LC45 (stress test):** FAIL. C_genuine introduces 1 false accept on a population where B1 is perfect. Gap is -0.10 at all tested lambda values. Result reported separately; does not override LC322 verdict.

The C-4 finding is about `C_genuine` specifically — a structured policy that uses `probe_family` from the fingerprint context. This is a different estimator from the `C_structured_fingerprint` tested in C-1 and C-3a (which was bound to `_fail_count_policy` and did not use structured features).

The C-1, C-3a, and project-closure-004 closures stand. C-4 builds on the same frozen populations and cost model, but tests a new estimator with a new decision rule. The PASS on LC322 is a positive finding for the C_genuine rule on this specific population, not a refutation of any prior phase.
