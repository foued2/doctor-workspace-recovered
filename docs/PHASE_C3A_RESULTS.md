# PHASE_C3A_RESULTS.md
# Doctor Phase C-3a: Per-Solver Identity Resolution — Results
# Status: CLOSED — RQ-C3a verdict: FULL_EQUIVALENCE on both populations
# Date: 2026-06-06
# Freeze: PHASE_C3A_FREEZE.json (commit a6c97bc)
# Spec: PHASE_C3A_SPEC.md (commit e3c50d9)

---

## 1. Verdict

**RQ-C3a: FULL_EQUIVALENCE on both populations.**

C and B1 misclassify identical solver sets on both frozen populations. The pre-declared three-case rule evaluates to `D = 0`, `A = 0` on LC322 and LC45. The C-1 aggregate tie (`gap(λ) ≡ 0`) is a real per-solver equivalence, not a cancellation artifact.

Phase C-3a is closed.

---

## 2. Numerical Detail

| Population | n_solvers | M_C | M_B1 | D = \|M_C △ M_B1\| | A | Three-case outcome |
|---|---|---|---|---|---|---|
| LC322 (primary) | 30 | {solver_019, solver_020, solver_021, solver_025, solver_027} | {solver_019, solver_020, solver_021, solver_025, solver_027} | 0 | 0 | FULL_EQUIVALENCE |
| LC45 (stress test) | 10 | {} (empty) | {} (empty) | 0 | 0 | FULL_EQUIVALENCE |

The lambda sweep for A: `{1, 2, 5, 7, 10, 15, 20, 30, 50}`. A = 0 across the entire sweep on both populations.

Source: `data/midweather_fingerprint_lc322_per_solver.json` and `data/midweather_fingerprint_lc45_per_solver.json`.

---

## 3. Per-Solver Evidence (LC322)

All 5 misclassified solvers on LC322 are false rejects (ground_truth = ACCEPT, decision = REJECT) for both C and B1:

| solver_id | ground_truth | C decision | B1 decision | In M_C | In M_B1 |
|---|---|---|---|---|---|
| solver_019 | ACCEPT | REJECT | REJECT | yes | yes |
| solver_020 | ACCEPT | REJECT | REJECT | yes | yes |
| solver_021 | ACCEPT | REJECT | REJECT | yes | yes |
| solver_025 | ACCEPT | REJECT | REJECT | yes | yes |
| solver_027 | ACCEPT | REJECT | REJECT | yes | yes |

M_C = M_B1 on LC322. No solver is misclassified by one and not the other.

---

## 4. Per-Solver Evidence (LC45)

M_C = M_B1 = {} on LC45. Both C and B1 are perfect on this population (0 wrong accepts, 0 wrong rejects). The empty-set identity trivially holds.

Source: C-1 aggregate data shows C and B1 both at `(WA, WR) = (0, 0)` on LC45. C-3a per-solver re-run reproduces this exactly.

---

## 5. Why the Misclassified Sets Are Identical

Under the current implementation (`doctor/adversarial/problem_class_config.py`), both C and B1 are bound to the same policy function:

```
def _fail_count_policy(obs_fails, n_obs, obs_records=None):
    return "ACCEPT" if obs_fails == 0 else "REJECT"
```

This function takes only `(obs_fails, n_obs)` as operative inputs. The `obs_records` parameter (which carries structured fingerprint context) is accepted but not consulted. C and B1 are observationally equivalent under this policy implementation.

The aggregate-consistency check (hard-stop gate) was satisfied for all 8 estimators on both populations, confirming that the re-run reproduces the stored `(WA, WR)` exactly. The re-run is deterministic given the same solver pack, probe index, and seval manifest.

---

## 6. Scope Discipline

This result is conditional on:

- The PHASE_C3A freeze (commit a6c97bc), which inherits the C-1 cost function and lambda sweep.
- The 8 estimators as listed in the freeze file, as currently implemented in `problem_class_config.py`.
- The tested populations: LC322 and LC45, as frozen at the closure of project-closure-004.
- The current C policy implementation, which does not consult the structured fingerprint context that the paper describes.

This result does **not** establish any of the following:

- That C and B1 are fundamentally indistinguishable. The paper describes C as using structured features as additional context. The current C implementation does not implement this. If C were implemented to consume `obs_records` and change decisions for some solvers, the per-solver equivalence could be broken.
- That the C-1 aggregate tie is structural in any deeper sense. C-3a confirms the tie is real, not that it is unbreakable.
- That a per-solver-weighted cost functional (C-2 territory) would still produce a tie. C-3a tests a different question (per-solver identity), not per-solver cost sensitivity.
- That the closed project-closure-004 verdict is reopened or affected.

---

## 7. Connection to Phase C-1

Phase C-1 (closed) established that C and B1 produce identical `(WA, WR)` aggregates on both populations, yielding `gap(λ) ≡ 0` algebraically. The C-1 result was agnostic about the mechanism: the aggregate tie could reflect (a) C and B1 misclassifying the same solvers, or (b) C and B1 misclassifying different solvers with the same total cost.

Phase C-3a disambiguates. The per-solver re-run confirms case (a): M_C = M_B1 on both populations. The C-1 aggregate tie is not a cancellation artifact; it is an instance of per-solver equivalence.

| Phase | Question | Method | Verdict |
|---|---|---|---|
| C-1 | Do C and B1 have identical `(WA, WR)` aggregates? | Aggregate sweep over λ | FAIL (gap ≡ 0) |
| C-3a | Do C and B1 misclassify the same solvers? | Per-solver decision persistence + Jaccard | FULL_EQUIVALENCE (D=0, A=0) |

The two phases test different questions and produce complementary findings. C-3a does not reopen C-1, and C-1 does not pre-determine C-3a.

---

## 8. What This Phase Did Not Do (Spec Compliance)

Per the spec (PHASE_C3A_SPEC.md §"Governance Acknowledgment"):

- Did not introduce new estimators, new probes, or new solver packs.
- Did not modify C-1 freeze parameters (delta, lambda sweep, lambda_A, 8 estimators, populations).
- Did not construct or evaluate a per-solver-weighted cost functional (C-2 territory).
- Did not adjust D or A thresholds post-hoc.
- Did not silently resolve aggregate inconsistencies (none occurred; the hard-stop gate passed for all 8 estimators on both populations).
- Did not reopen the C-1 closure or project-closure-004.

Per the spec (PHASE_C3A_SPEC.md §"Epistemological Constraints"):

- No compression drift: all claims are tied to the observed per-solver decision data and the freeze's cost function.
- No negative result inflation: scope is restricted to the current C implementation and the tested populations. The finding is about equivalence under the current code, not about C's value in principle.
- No hidden causal language: the per-solver equivalence is reported as an observation, with the policy implementation cited as the location of the shared decision rule. No claim is made about why the current implementation was written this way or what it would take to differentiate C from B1.

---

## 9. Foued Override Acknowledgment

Phase C-3a was authorized by Foued override, which violates the C-1 constraint `"runners_load_existing_decisions_only": true`. The override is recorded in PHASE_C3A_FREEZE.json (`"violates_c1_constraint": "runners_load_existing_decisions_only"`, `"violation_acknowledged": true`). The violation is necessary to obtain per-solver decisions, which were not persisted in the C-1 data file.

The override does not extend to other C-1 constraints. The C-1 closure is not reopened.

---

## 10. Artifacts Produced

- `data/midweather_fingerprint_lc322_per_solver.json` — 30 solvers × 8 estimators per-solver decisions. M_C = M_B1 = {solver_019, solver_020, solver_021, solver_025, solver_027}.
- `data/midweather_fingerprint_lc45_per_solver.json` — 10 solvers × 8 estimators per-solver decisions. M_C = M_B1 = {}.
- `PHASE_C3A_SPEC.md` (commit e3c50d9) — research question, three-case decision rule, aggregate-consistency stop condition, governance acknowledgment.
- `PHASE_C3A_FREEZE.json` (commit a6c97bc) — pre-declared parameters: D threshold=0, A threshold=0, 8 estimators, 2 populations, lambda sweep inherited from C-1, aggregate-consistency check required.
- `doctor/identity_resolution.py` (commit 52ad9f8) — `misclassified_set`, `compute_D`, `compute_A`, `apply_three_case_rule`, `check_aggregate_consistency`.
- `tests/test_identity_resolution.py` (commit 52ad9f8) — 37 passing tests covering all 5 API functions and edge cases.
- `runners/run_per_solver_decisions_lc322.py` (commit c30ab97) — LC322 runner.
- `runners/run_per_solver_decisions_lc45.py` (commit c30ab97) — LC45 runner.

---

## 11. Closure Statement

Phase C-3a is closed as of this document. The pre-declared RQ-C3a three-case rule has been evaluated: D = 0 and A = 0 on both frozen populations. The outcome is FULL_EQUIVALENCE.

The C-1 aggregate tie is confirmed to be a real per-solver equivalence, not a cancellation artifact. C and B1 misclassify the identical solver sets on both populations under the current implementation.

The three-case rule's other two outcomes (MASKED_DIVERGENCE, DIRECTIONAL_SUPERIORITY) were not realized. These outcomes would require either (a) a different C implementation that consults structured fingerprint context, or (b) a different population where C and B1's shared policy produces different per-solver errors. Neither is in scope for C-3a.
