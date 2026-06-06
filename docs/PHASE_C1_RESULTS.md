# PHASE_C1_RESULTS.md
# Doctor Phase C-1: Asymmetric-Cost Decision Utility — Results
# Status: CLOSED — RQ-C1 verdict: FAIL on both populations
# Date: 2026-06-06
# Freeze: PHASE_C1_FREEZE.json (commit 3bd286d)
# Spec: PHASE_C1_SPEC.md (commit 3f1a647)

---

## 1. Verdict

**RQ-C1: FAIL on both populations.**

The pre-declared PASS condition is `∃ λ_R/λ_A in {1,2,5,7,10,15,20,30,50} such that utility(C) − utility(B1) > 0.10` on at least one frozen population.

Observed:
- **LC322 (primary, n=30, 11/19 split):** `gap(λ) ≡ 0` for all 9 tested λ values. C and B1 have identical `(WA, WR) = (0, 5)`. PASS condition not satisfied.
- **LC45 (stress test, n=10, 1/9 split):** `gap(λ) ≡ 0` for all 9 tested λ values. C and B1 have identical `(WA, WR) = (0, 0)` (both perfect). PASS condition not satisfied.

Phase C-1 is closed.

---

## 2. Numerical Detail (LC322, primary)

| λ_R | utility(C) | utility(B1) | gap | eligible (gap > 0.10) |
|----:|-----------:|-----------:|----:|----------------------:|
|   1 |     0.8333 |      0.8333 | 0.0 | False |
|   2 |     0.6667 |      0.6667 | 0.0 | False |
|   5 |     0.1667 |      0.1667 | 0.0 | False |
|   7 |    -0.1667 |     -0.1667 | 0.0 | False |
|  10 |    -0.6667 |     -0.6667 | 0.0 | False |
|  15 |    -1.5000 |     -1.5000 | 0.0 | False |
|  20 |    -2.3333 |     -2.3333 | 0.0 | False |
|  30 |    -4.0000 |     -4.0000 | 0.0 | False |
|  50 |    -7.3333 |     -7.3333 | 0.0 | False |

Source: `data/asymmetric_cost_lc322.json`.

---

## 3. Numerical Detail (LC45, stress test)

| λ_R | utility(C) | utility(B1) | gap | eligible (gap > 0.10) |
|----:|-----------:|-----------:|----:|----------------------:|
|   1 |     1.0000 |      1.0000 | 0.0 | False |
|   2 |     1.0000 |      1.0000 | 0.0 | False |
|   5 |     1.0000 |      1.0000 | 0.0 | False |
|   7 |     1.0000 |      1.0000 | 0.0 | False |
|  10 |     1.0000 |      1.0000 | 0.0 | False |
|  15 |     1.0000 |      1.0000 | 0.0 | False |
|  20 |     1.0000 |      1.0000 | 0.0 | False |
|  30 |     1.0000 |      1.0000 | 0.0 | False |
|  50 |     1.0000 |      1.0000 | 0.0 | False |

Source: `data/asymmetric_cost_lc45.json`. LC45 results reported separately; not used as primary evidence per the spec.

---

## 4. Structural Invariance Finding

Under the PHASE_C1 freeze cost model — a linear cost functional with global `λ_A = 1` and global `λ_R` — the total cost of an estimator is fully determined by `(wrong_accepts, wrong_rejects)`. The 8 estimators reduce to equivalence classes on each population:

**LC322 equivalence classes (under freeze's linear cost model):**
| Class | Estimators | (WA, WR) | n |
|---|---|---|---|
| All-ACCEPT (degenerate) | B0_prior, B5_nearest_neighbor_raw_tensor, B6_regularized_raw_tensor | (19, 0) | 30 |
| 5-FR (tied) | B1_count, B2_calibrated_count, B3_raw_pf_vector, C_structured_fingerprint | (0, 5) | 30 |
| All-REJECT (degenerate) | B4_raw_full_tensor | (0, 11) | 30 |

**LC45 equivalence classes:**
| Class | Estimators | (WA, WR) | n |
|---|---|---|---|
| All-ACCEPT (degenerate) | B0_prior, B5_nearest_neighbor_raw_tensor, B6_regularized_raw_tensor | (9, 0) | 10 |
| Perfect (tied) | B1_count, B2_calibrated_count, B3_raw_pf_vector, C_structured_fingerprint | (0, 0) | 10 |
| All-REJECT (degenerate) | B4_raw_full_tensor | (0, 1) | 10 |

The 8 estimators differ in implementation (calibrated vs. uncalibrated count, raw vs. regularized tensor, fingerprint features vs. raw probe count, etc.) but produce **identical aggregate cost outcomes** on both frozen populations under the freeze's cost model. They are observationally equivalent on the freeze's metric.

This is a structural invariance result, not an epistemic failure. The 8 estimators collapse to a small number of equivalence classes under any linear cost functional with global weights. No amount of additional data, λ value, or population in the tested ranges would change this.

---

## 5. Why the Gap is Identically Zero

The freeze's cost function:

```
cost(decision, ground_truth, λ_R, λ_A) =
    λ_A  if decision = ACCEPT and ground_truth = REJECT  (false accept)
    λ_R  if decision = REJECT and ground_truth = ACCEPT  (false reject)
    0    otherwise
```

Total cost for estimator X on a population of size n:

```
total_cost(X, λ) = WA_X · λ_A + WR_X · λ_R
```

The gap between C and B1:

```
gap(λ) = [total_cost(B1, λ) − total_cost(C, λ)] / (n · λ_A)
        = (WA_B1 − WA_C) · λ_A / (n · λ_A) + (WR_B1 − WR_C) · λ_R / (n · λ_A)
        = (WA_B1 − WA_C) / n + (WR_B1 − WR_C) · λ_R / n
```

If `(WA_B1, WR_B1) = (WA_C, WR_C)`, then `gap(λ) = 0` for all λ. This holds algebraically for any λ, any population, any scaling. The sufficient statistics `(WA, WR)` are fully observed; the cost functional is fully specified; the gap is analytically determined to be zero.

---

## 6. Scope Discipline

This result is conditional on:

- The PHASE_C1 freeze cost model (linear, global `λ_A`, global `λ_R`).
- The tested λ range: `{1, 2, 5, 7, 10, 15, 20, 30, 50}`.
- The tested populations: LC322 and LC45, as frozen at the closure of project-closure-004.
- The 8 estimators as listed in the freeze file.

This result does **not** establish any of the following:

- That C has no value under any cost model. A per-solver-weighted cost functional (where `λ_R` or `λ_A` varies with solver identity, e.g., by probe-cluster assignment) would not have `(WA, WR)` as a sufficient statistic, and the 8 estimators could differ under such a model.
- That no further estimator development could break the tie. New estimators that produce different `(WA, WR)` on these populations would shift the gap.
- That the closed symmetric decision_loss result (project-closure-004) is reopened or affected. Phase C-1 is a separate program; the closed negative result is data, not an obstacle.

A per-solver-weighted cost model would be a different research object (Phase C-2 territory). It would require a new spec, new freeze, new tests, and new runners, with explicit non-relationship to this result.

---

## 7. Connection to Closed Work (project-closure-004)

Phase C-1 was authorized by Foued override as Option C (explicit non-relationship to closed work). The two programs test different questions:

| Program | Question | Cost model | Verdict |
|---|---|---|---|
| project-closure-004 | Does the structured fingerprint transfer across problem classes? | symmetric decision_loss | FAIL |
| Phase C-1 | Does C beat B1 under any asymmetric cost ratio? | linear, global λ | FAIL |

The two FAIL verdicts are independent. Phase C-1 does not change the closure of project-closure-004, and project-closure-004 does not pre-determine the outcome of Phase C-1.

---

## 8. What This Phase Did Not Do (Spec Compliance)

Per the spec (PHASE_C1_SPEC.md §"What This Phase Does Not Do"):

- Did not reopen project-closure-004.
- Did not introduce new probes, stress-class definitions, or fingerprint primitives.
- Did not construct a new C estimator.
- Did not reinterpret closed results under new framing.
- Did not expand to new problem classes.
- Did not claim the closed FAIL verdict was wrong.

Per the spec (PHASE_C1_SPEC.md §"Epistemological Constraints"):

- No compression drift: all claims are tied to the observed `(WA, WR)` data and the freeze's cost function.
- No negative result inflation: scope is restricted to the tested λ range and the tested populations.
- No hidden causal language: the result is stated as an algebraic outcome, not a claim about estimator quality in general.

---

## 9. Artifacts Produced

- `data/asymmetric_cost_lc322.json` — LC322 sweep results (8 estimators × 9 λ values + gap table).
- `data/asymmetric_cost_lc45.json` — LC45 sweep results (8 estimators × 9 λ values + gap table, role = stress_test).
- `PHASE_C1_SPEC.md` (commit 3f1a647) — research question, falsification criterion, scope, constraints.
- `PHASE_C1_FREEZE.json` (commit 3bd286d) — pre-declared parameters: `δ=0.10`, `λ_sweep=[1,2,5,7,10,15,20,30,50]`, `λ_A=1`, 8 estimators, 2 populations.
- `doctor/asymmetric_cost.py` (commit 432e71f, extended 6a2fd89) — `compute_cost`, `compute_raw_cost`, `compute_normalized_utility`, `is_degenerate`, `run_sweep`, `run_sweep_aggregate`.
- `tests/test_asymmetric_cost_utility.py` (commit 432e71f, extended 6a2fd89) — 341 passing tests as of close.
- `runners/run_asymmetric_cost_lc322.py` (commit 598c0cc, updated 6a2fd89) — LC322 runner.
- `runners/run_asymmetric_cost_lc45.py` (commit 2d8f04d, updated 6a2fd89) — LC45 runner.

---

## 10. Closure Statement

Phase C-1 is closed as of this document. The pre-declared RQ-C1 falsification has been evaluated: PASS condition is not satisfied on either population. The result is FAIL with mathematical certainty under the freeze's pre-declared cost model.

A natural follow-up object — per-solver-weighted cost models — is **not** a continuation of Phase C-1. It is a different research program (Phase C-2 territory) requiring a new spec, new freeze, new tests, and new runners. It is not authorized, scoped, or started as of this closure.
