# PHASE_C6_RESULTS.md
# Doctor Phase C-6: Representation Class Falsification — Results
# Status: CLOSED — RQ-C6 verdict: NO
# Date: 2026-06-06
# Freeze: PHASE_C6_FREEZE.json (commit 6766f4c)
# Spec: PHASE_C6_SPEC.md (commit 54e2839)

---

## 1. RQ-C6 Verdict

**RQ-C6: NO.** None of the 4 pre-declared candidate decision rules survives the C-5 perturbation battery on LC322. The class does not produce distribution-invariant separation from B1 under the tested perturbations.

| Rule | Verdict on LC322 | Survived / Total |
|---|---|---|
| R1 C_genuine (probe_family coherence) | PARTIALLY_SURVIVES | 6 / 10 |
| R2 C_feature_threshold (deformation-level failure rate) | DOES_NOT_SURVIVE | 0 / 10 |
| R3 C_majority (plurality failure-family) | PARTIALLY_SURVIVES | 3 / 10 |
| R4 C_zero_only (zero-failure only) | DOES_NOT_SURVIVE | 0 / 10 |

Per-rule LC45 status (stress test): all 4 rules DOES_NOT_SURVIVE. See §6.

Phase C-6 is closed.

---

## 2. Per-Rule, Per-Perturbation Status (LC322)

| Rule | P1 | P2a | P2b | P2c | P3a | P3b | P3c | P3d | P3e | P3f | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 C_genuine | NO | NO | YES | YES | NO | YES | NO | YES | YES | YES | 6/10 |
| R2 C_feature_threshold | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | 0/10 |
| R3 C_majority | NO | NO | YES | YES | NO | NO | NO | NO | NO | YES | 3/10 |
| R4 C_zero_only | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | 0/10 |

For each cell, "YES" means the rule's utility gap versus B1 is > 0.10 at all 9 lambda values; "NO" means the gap is ≤ 0.10 or negative at some lambda.

---

## 3. R1 (C_genuine) — Detailed Status

R1 is the C-4 baseline. Its LC322 status matches the C-5 finding (6/11) when restricted to the 10 LC322-specific perturbations (P4, the LC45 perturbation, is excluded here):

- P1 (ratio shift 11/19 → 19/11): NO. min_gap = -0.1333, max_gap = +1.5000. Negative at lambda=1; positive at lambda≥2. Collapses at low lambda.
- P2a (subsample [0..19]): NO. min_gap = +0.0500, max_gap = +4.9500. Just below threshold at lambda=1.
- P2b (subsample [10..29]): YES. min_gap = +0.2000, max_gap = +12.4500. Includes all 5 gain-generating solvers.
- P2c (subsample [0..9]+[20..29]): YES. min_gap = +0.1500, max_gap = +7.5000. Includes 3 of 5 gain-generating solvers.
- P3a (knockout reachability_counterfactual): NO. min_gap = +0.0333, max_gap = +8.2000. 4 false accepts; just below threshold at lambda=1.
- P3b (knockout non_canonical_coin_order): YES. min_gap = +0.1333, max_gap = +8.3000.
- P3c (knockout large_amount_stress): NO. min_gap = -0.1000. All gaps negative. Severe collapse.
- P3d (knockout greedy_dp_threshold): YES. min_gap = +0.1333, max_gap = +8.3000.
- P3e (knockout forward_dp_overwrite): YES. min_gap = +0.1333, max_gap = +8.3000.
- P3f (knockout memo_cache_aliasing): YES. min_gap = +0.1333, max_gap = +8.3000.

R1 verdict: PARTIALLY_SURVIVES (6/10). R1 is the most resilient rule but still fails on P1, P2a, P3a, P3c.

---

## 4. R2 (C_feature_threshold) — Detailed Status

R2 is operationally equivalent to B1 on every LC322 perturbation. The gap is identically 0 across all 10 perturbations at all 9 lambda values.

The reason: the 30 observed probes in LC322 all have `deformation_level = 0`. The "deformed" set (deformation_level > 0) is empty, so R2 always falls back to B1 behavior. R2's `deformation_level` feature carries no signal on the LC322 observed probe set.

This is informative: the deformation_level dimension of the structured fingerprint feature space is not informative on LC322, regardless of the threshold chosen (since the rule cannot fire when no probe is deformed).

R2 verdict: DOES_NOT_SURVIVE (0/10) a fortiori.

---

## 5. R3 (C_majority) — Detailed Status

R3 is more permissive than R1: it accepts any solver with a unique mode in the failure-family distribution, not just solvers with unanimous failures. On LC322, R3 produces 1 false accept on unperturbed data (same as R1), but on probe family knockouts, R3 produces many more false accepts:

- P1: NO. Same as R1 (min_gap = -0.1333).
- P2a: NO. min_gap = +0.0500.
- P2b: YES. min_gap = +0.2000.
- P2c: YES. min_gap = +0.1500.
- P3a (knockout reachability): NO. min_gap = -0.1333. 9 false accepts (vs R1's 4). Plurality rule accepts more REJECT solvers.
- P3b (knockout non_canonical_coin_order): NO. min_gap = -0.0667. 7 false accepts (vs R1's 1).
- P3c (knockout large_amount_stress): NO. min_gap = -0.1667. 6 false accepts.
- P3d (knockout greedy_dp_threshold): NO. min_gap = -0.2333. 12 false accepts (most severe).
- P3e (knockout forward_dp_overwrite): NO. min_gap = +0.0667. 3 false accepts.
- P3f (knockout memo_cache_aliasing): YES. min_gap = +0.1333. 1 false accept.

R3 verdict: PARTIALLY_SURVIVES (3/10). R3 is more permissive than R1 and produces more false accepts on knockouts. Its survival set is a strict subset of R1's: P2b, P2c, P3f.

---

## 6. R4 (C_zero_only) — Detailed Status

R4 is operationally identical to B1 (`_fail_count_policy`). On every perturbation, R4 produces the same (WA, WR) as B1, and the gap is identically 0.

This is the negative control: R4 is included to show whether the C-4 gain is associated with the coherence condition (R1) or with being more permissive than B1. Since R4 is identical to B1, its gap is 0 everywhere, and it DOES_NOT_SURVIVE a priori.

The fact that R1 and R3 both produce non-zero gaps on the unperturbed LC322 (R1: gap=8.30 at lambda=50, R3: gap=8.30) while R4 produces 0 confirms the gain is associated with the coherence condition, not with being more permissive than B1.

R4 verdict: DOES_NOT_SURVIVE (0/10) a fortiori.

---

## 7. LC45 Stress Test (Per-Rule, Unperturbed)

B1 is perfect on LC45 (0 WA, 0 WR). All 4 rules:

| Rule | Aggregate (WA, WR) | min_gap | max_gap | Verdict |
|---|---|---|---|---|
| R1 C_genuine | (1, 0) | -0.1000 | -0.1000 | DOES_NOT_SURVIVE |
| R2 C_feature_threshold | (0, 0) | +0.0000 | +0.0000 | DOES_NOT_SURVIVE |
| R3 C_majority | (4, 0) | -0.4000 | -0.4000 | DOES_NOT_SURVIVE |
| R4 C_zero_only | (0, 0) | +0.0000 | +0.0000 | DOES_NOT_SURVIVE |

- R1 introduces 1 false accept. Cross-checked against C-4 LC45 aggregate; matches.
- R2 does not introduce false accepts (vacuously equivalent to B1 on LC45 too — no deformed probes). But its gap is 0.
- R3 introduces 4 false accepts — the most permissive rule produces the most damage on LC45.
- R4 is identical to B1. Gap is 0.

LC45 result: all 4 rules DOES_NOT_SURVIVE. The C-4 finding on LC45 (R1 fails) generalizes to R2 and R3 as well. R4 fails by construction.

---

## 8. RQ-C6 Class-Level Verdict

Per the C-6 freeze (`PHASE_C6_FREEZE.json`):

- **YES** if at least one of R1, R2, R3 SURVIVES.
- **NO** if none of R1, R2, R3 SURVIVES.
- **MIXED** if some survive and some do not, no rule a refinement of another.

**Verdict: NO.** None of R1, R2, R3 SURVIVES the C-5 battery on LC322. R1 PARTIALLY_SURVIVES (6/10); R2 DOES_NOT_SURVIVE (0/10); R3 PARTIALLY_SURVIVES (3/10); R4 DOES_NOT_SURVIVE (0/10) by construction.

The representation class does not produce distribution-invariant separation from B1 under the tested perturbations, on either LC322 or LC45.

---

## 9. What This Phase Did Not Do (Spec Compliance)

Per the spec (PHASE_C6_SPEC.md §"What This Phase Does Not Do"):

- Did not reopen `project-closure-004`, `phase-c1-results`, `phase-c3a-results`, `phase-c4-results`, or `phase-c5-results`.
- Did not introduce new probes, probe geometry, or solver packs.
- Did not modify the C-1, C-3a, C-4, or C-5 freeze parameters.
- Did not introduce new estimator names beyond the 3 declared in the spec.
- Did not adjust any candidate rule's decision function after seeing per-perturbation results.
- Did not construct a per-solver-weighted cost functional (C-2 territory).
- Did not claim that the 4 candidate rules exhaust the representation class.
- Did not claim universal generalization beyond the tested populations and perturbations.

Per the spec (PHASE_C6_SPEC.md §"Epistemological Constraints"):

- No compression drift: all claims are tied to the observed per-rule, per-perturbation gap data and the pre-declared falsification criterion.
- No negative result inflation: scope is restricted to the 4 tested rules and 11 tested perturbations. The RQ-C6 NO verdict is reported for the specific class of 4 candidate rules, not generalized to "no estimator on this representation class can work."
- No hidden causal language: per-perturbation gap collapse is reported as observation; the per-rule verdict is the pre-declared criterion, not a post-hoc interpretation.

---

## 10. Boundary of the Finding

The RQ-C6 NO verdict is scoped to:

- The 4 pre-declared candidate decision rules (R1, R2, R3, R4).
- The 6-dim `encode_raw_tensor` feature space (pf, deformation_level, axis, probe_family, paired, expected_invariant).
- The 11 pre-declared perturbations (P1, P2a-c, P3a-f, P4).
- The two populations (LC322, LC45).
- The C-1 cost model and lambda sweep.

The NO verdict does not claim:

- That no estimator on this representation class can produce distribution-invariant separation.
- That the representation class has no value under different cost models or perturbation sets.
- That other feature dimensions not in `encode_raw_tensor` (e.g., the 16-dim or other extended encodings) cannot work.

The verdict is a structured negative result on the 4-rule, 11-perturbation, 2-population, 6-dim-feature-space scope.

---

## 11. Artifacts Produced

- `data/c6_collapse_lc322.json` — per-rule, per-perturbation gap tables for 10 perturbations on LC322. RQ-C6 verdict: NO.
- `data/c6_collapse_lc45.json` — per-rule gap tables for unperturbed LC45. All 4 rules DOES_NOT_SURVIVE.
- `PHASE_C6_SPEC.md` (commit 54e2839) — RQ, 4 candidate rules declared verbatim, per-rule and class-level falsification criteria, perturbation battery inherited from C-5, "What This Phase Does Not Do" §, epistemological constraints.
- `PHASE_C6_FREEZE.json` (commit 6766f4c) — 4 candidate rules with verbatim decision functions, per-rule falsification, RQ-C6 class-level verdict rule.
- `doctor/adversarial/problem_class_config.py` (commit d157d00) — 3 new policy functions: `_c_feature_threshold_policy`, `_c_majority_policy`, `_c_zero_only_policy`. All 4 candidate rules (R1-R4) registered in `LC{322,45}_ESTIMATOR_POLICIES`.
- `tests/test_structured_candidate_policies.py` (commit d157d00) — 36 tests covering all 4 candidate rules, falsification criterion, aggregate-consistency carryforward.
- `tests/test_apply_estimator_signature.py` (commit d157d00) — backward-compat tests updated; new `test_c6_candidates_intentionally_break_backward_compat`.
- `runners/run_c6_collapse_lc{322,45}.py` (commit 55b1186) — LC322 and LC45 runners.

---

## 12. Closure Statement

Phase C-6 is closed as of this document. RQ-C6 verdict: NO. None of the 4 pre-declared candidate decision rules built on the structured fingerprint representation class produces separation from B1 that is invariant under the 11 pre-declared perturbations on LC322.

Per-rule verdicts (LC322):
- R1 C_genuine: PARTIALLY_SURVIVES (6/10)
- R2 C_feature_threshold: DOES_NOT_SURVIVE (0/10) — vacuously B1-equivalent
- R3 C_majority: PARTIALLY_SURVIVES (3/10)
- R4 C_zero_only: DOES_NOT_SURVIVE (0/10) — B1-equivalent by construction

All 4 rules DOES_NOT_SURVIVE on LC45 (stress test).

The closed phases stand. C-6 tests the representation class across 4 candidate rules; it does not reopen C-1, C-3a, C-4, or C-5, and it does not claim that no estimator on this class can work. The NO verdict is scoped to the 4 rules, 11 perturbations, 2 populations, and 6-dim feature space tested.

This phase's data, code, tests, spec, and freeze remain in the repository as a record of the falsification attempt.
