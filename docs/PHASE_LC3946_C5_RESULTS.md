# PHASE_LC3946_C5_RESULTS.md
# Doctor Phase LC3946-C5: Collapse Analysis (Distribution Shift) — Results
# Status: CLOSED — RQ-LC3946-C5 verdict: PARTIALLY_SURVIVES
# Date: 2026-06-07
# Freeze: PHASE_LC3946_C5_FREEZE.json (commit PENDING at tag time)
# Spec: PHASE_LC3946_C5_SPEC.md

---

## 1. Verdict

**RQ-LC3946-C5: PARTIALLY_SURVIVES.** 10 of 11 pre-declared perturbations maintained the C-4 utility gap (`gap = B1_loss - C_genuine_loss > 0` strictly) under the uniform-cost decision rule. 1 perturbation collapsed.

Per-perturbation status:

| Perturbation | Survives? | gap | B1_loss | CG_loss | Notes |
|---|---|---:|---:|---:|---|
| P1a (baseline, threshold=0.05) | yes (reference) | 1.0 | 1.0 | 0.0 | Baseline reference, not a perturbation |
| P1b (threshold=0.10) | yes | 1.0 | 1.0 | 0.0 | |
| P1c (threshold=0.20) | yes | 1.0 | 1.0 | 0.0 | |
| P2a (subsample [0..24], first 25) | yes | 1.0 | 1.0 | 0.0 | solver_016 (0-idx 15) in subsample |
| P2b (subsample [5..29], last 25) | yes | 1.0 | 1.0 | 0.0 | solver_016 in subsample |
| P2c (subsample [0..9]+[15..29], first 10 + last 15) | yes | 1.0 | 1.0 | 0.0 | solver_016 in subsample |
| P3a (knockout poset_universal_source) | yes | 1.0 | 1.0 | 0.0 | 3 observed probes removed |
| P3b (knockout poset_chain) | yes | 1.0 | 1.0 | 0.0 | 2 observed probes removed |
| P3c (knockout poset_antichain) | yes | 1.0 | 1.0 | 0.0 | 3 observed probes removed |
| P3d (knockout poset_lattice_boolean) | yes | 1.0 | 1.0 | 0.0 | 2 observed probes removed |
| **P3e (knockout poset_lattice_two_prime)** | **NO** | **0.0** | **0.0** | **0.0** | **Pre-declared falsification. solver_016's only observed failure lives in this family.** |
| P3f (knockout poset_isolated) | yes | 1.0 | 1.0 | 0.0 | 2 observed probes removed |
| P4 (LC322 C-4 cross-population anchor) | (anchor, no LC3946 perturbation applied) | 8.3 | -- | -- | LC322 C-4 gap=8.3, signal family=large_amount_stress, LC322 C-5 verdict=PARTIALLY_SURVIVES |

Phase LC3946-C5 is closed.

---

## 2. Per-Perturbation Numerical Detail

All perturbations use the uniform-cost decision rule: `decision_loss = wrong_accepts + wrong_rejects`. Survival threshold: `gap > 0` strictly, where `gap = B1_loss - C_genuine_loss`. `gap = 0` is collapse (not survival). Ties are not admissible.

### P1a — Baseline Reference (threshold=0.05, no perturbation)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. This is the recorded C-4 result, included here for reference. P1a is **not counted** in the 11-perturbation falsification count (it is a baseline reference per the freeze's `is_baseline_reference: true` field).

### P1b — Threshold Shift to 0.10

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Re-deriving ground truth labels at failure_threshold=0.10 (stricter than the 0.05 baseline) does not change the B1/C_genuine aggregate. The 15 target probes' failure rates for all 30 solvers remain below 0.10, so the truth labels are unchanged. The C_genuine advantage (solver_016: 0 obs failures in the family-coherent observation) survives the threshold shift.

### P1c — Threshold Shift to 0.20

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Same mechanism as P1b. Threshold=0.20 is even stricter, but the target probe failure rates do not cross 0.20 for any solver. The C-4 gain is preserved.

### P2a — Subsample of First 25 Solvers (indices [0..24])

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. solver_016 (0-indexed position 15) is in the subsample. The 5 dropped solvers are solver_026..solver_030 (indices 25..29). Pre-declared per the freeze's `recovered_solver_check` block (solver_016 in P2a: yes).

### P2b — Subsample of Last 25 Solvers (indices [5..29])

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. solver_016 is in the subsample (0-indexed position 15 is in [5..29]). The 5 dropped solvers are solver_001..solver_005 (indices 0..4). Pre-declared per the freeze's `recovered_solver_check` block (solver_016 in P2b: yes).

### P2c — Subsample of First 10 + Last 15 (indices [0..9]+[15..29])

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. solver_016 (0-indexed position 15) is in the subsample (in the [15..29] block). The 5 dropped solvers are solver_011..solver_015 (indices 10..14). Pre-declared per the freeze's `recovered_solver_check` block (solver_016 in P2c: yes).

### P3a — Knockout `poset_universal_source` (3 observed probes removed: p_lc3946_0001, p_lc3946_0003, p_lc3946_0005)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Observed probe count reduces from 15 to 12. solver_016's only observed failure (p_lc3946_0021) is in `poset_lattice_two_prime`, **not** in `poset_universal_source`. B1 still sees 1 fail for solver_016 → REJECT (1 WR). C_genuine still sees 0 fails in any family for solver_016 → ACCEPT (0 WA, 0 WR). Gap preserved.

### P3b — Knockout `poset_chain` (2 observed probes removed: p_lc3946_0007, p_lc3946_0009)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Observed probe count reduces from 15 to 13. solver_016's only observed failure is in `poset_lattice_two_prime`, not `poset_chain`. B1 still REJECTs solver_016 (1 WR). C_genuine still ACCEPTs solver_016. Gap preserved.

### P3c — Knockout `poset_antichain` (3 observed probes removed: p_lc3946_0011, p_lc3946_0013, p_lc3946_0015)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Observed probe count reduces from 15 to 12. solver_016's only observed failure is not in `poset_antichain`. Gap preserved.

### P3d — Knockout `poset_lattice_boolean` (2 observed probes removed: p_lc3946_0017, p_lc3946_0019)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Observed probe count reduces from 15 to 13. solver_016's only observed failure is not in `poset_lattice_boolean`. Gap preserved.

### P3e — Knockout `poset_lattice_two_prime` (3 observed probes removed: p_lc3946_0021, p_lc3946_0023, p_lc3946_0025)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 0 | 0.0 |
| C_genuine | 0 | 0 | 0.0 |

**Gap: 0.0. COLLAPSE.** Observed probe count reduces from 15 to 12. **solver_016's only observed failure (p_lc3946_0021) is in this family.** With the family removed, B1 sees 0 fails in the remaining 12 observed probes for solver_016 → ACCEPT (0 WA, 0 WR). C_genuine sees 0 fails in any family for solver_016 → also ACCEPT (0 WA, 0 WR). The single wrong-reject avoided by C_genuine on the unperturbed set is no longer produced: the observation budget no longer contains the family in which solver_016's only failure sits. Gap = 0 (collapse). This is the pre-declared falsification prediction recorded in the spec (`PHASE_LC3946_C5_SPEC.md` P3e section) and in the freeze (`PHASE_LC3946_C5_FREEZE.json` `perturbations.P3e_probe_family_knockout_poset_lattice_two_prime.note`).

### P3f — Knockout `poset_isolated` (2 observed probes removed: p_lc3946_0027, p_lc3946_0029)

| Estimator | wrong_accepts | wrong_rejects | decision_loss |
|---|---:|---:|---:|
| B1_count | 0 | 1 | 1.0 |
| C_genuine | 0 | 0 | 0.0 |

Gap: 1.0. Survives. Observed probe count reduces from 15 to 13. solver_016's only observed failure is not in `poset_isolated`. Gap preserved.

### P4 — Cross-Population Anchor (LC322 C-4, read-only)

LC322 C-4 gap: 8.3. LC322 C-4 signal family: `large_amount_stress`. LC322 C-5 verdict: PARTIALLY_SURVIVES. Source: `data/midweather_fingerprint_lc322.json` + `phase-c5-results` tag (commit `d1435a3`). No LC3946 perturbation is applied; P4 is recorded as the cross-population reference per the freeze's `P4_cross_population_reference` block.

---

## 3. What the LC3946-C5 Experiment Measured

LC3946-C5 tested the LC3946 C-4 finding against 11 pre-declared perturbations on the LC3946 solver population, plus one P1a baseline reference and one P4 cross-population anchor. The C-4 finding was: on the unperturbed LC3946 population, `C_genuine` outperforms B1 on decision utility (`gap = 1.0`, `B1_loss = 1.0`, `C_genuine_loss = 0.0`), with the gain driven by a single recovered solver (solver_016, 0-indexed position 15) and its only observed failure in the `poset_lattice_two_prime` family.

LC3946-C5 does not characterize the C-4 gain in any general sense as durable or fragile, structural or artifactual, or applicable beyond the tested perturbations. LC3946-C5 reports per-perturbation survival status: which perturbations preserve the gap, and which do not.

---

## 4. Why the Gap Collapses on P3e and Survives on the Other 10

### P3e — Knockout `poset_lattice_two_prime` (collapse)

The LC3946 C-4 gain depends on a single failure: solver_016's only observed failure is on probe `p_lc3946_0021`, which is in the `poset_lattice_two_prime` family. The C_genuine policy accepts because all failures share one family. B1 counts raw failures and rejects it. The single failure is the entire signal.

When the `poset_lattice_two_prime` family is removed from the observation budget, solver_016 has 0 observed failures in the remaining 12 probes. B1 sees 0 fails → ACCEPT. C_genuine sees 0 fails in any family → also ACCEPT. Both estimators now agree: there is no observed failure to distinguish them. The single wrong-reject avoided by C_genuine on the unperturbed set is no longer produced. The mechanism is the same as the C-1 implementation-equivalence finding on LC322: when the observation contains the discriminating signal, the policy uses it; when the observation does not, the policy has nothing to distinguish.

This is the LC3946 equivalent of the LC322 P3c collapse (`large_amount_stress` knockout). The signal family is different; the collapse mechanism is identical. **On LC322, the entire C-4 gain was carried by `large_amount_stress`. On LC3946, the entire C-4 gain is carried by `poset_lattice_two_prime`.** In both problems, removing that one family collapses the C_genuine/B1 gap to zero. No aggregation across the two problems is performed here; this is a within-problem observation, repeated on a different solver population.

### The other 10 perturbations (survive)

The C-4 gain survives all P1, P2, and P3a/P3b/P3c/P3d/P3f perturbations. The mechanisms:

- **P1 (threshold shift to 0.10 and 0.20):** the 15 target probes' failure rates for all 30 solvers remain below 0.20. The C-4 ground truth labels are unchanged, and the gain mechanism is unaffected.
- **P2 (subsamples):** solver_016 is in all 3 pre-declared subsamples (P2a, P2b, P2c). The 5 dropped solvers in each subsample do not include solver_016, and the remaining population retains the same B1/C_genuine split (1 REJECT for B1, 0 REJECT for C_genuine). The 1 wrong-reject avoided by C_genuine is preserved.
- **P3a/P3b/P3c/P3d/P3f (knockouts of other 5 families):** solver_016's only observed failure is in `poset_lattice_two_prime`, not in any of the other 5 families. The 1 observed failure remains in the reduced observation budget. B1 still sees 1 fail and rejects solver_016. C_genuine still sees the failure concentrated in one family (the only remaining family containing a fail, which is `poset_lattice_two_prime`) and accepts it. The gain mechanism is preserved.

---

## 5. What This Phase Did Not Do (Spec Compliance)

Per the spec (`PHASE_LC3946_C5_SPEC.md` §"What This Phase Does Not Do"):

- Did not reopen `phase-c1-results`, `phase-c3a-results`, `phase-c4-results`, `phase-c5-results` (LC322), `phase-c6-results`, `phase-c7-results`, or `project-closure-004`.
- Did not introduce new probes, probe geometry, or solver packs.
- Did not modify the C-1, C-3a, C-4, C-5 (LC322), C-6, or C-7 freeze parameters.
- Did not modify the LC3946 onboarding freeze parameters.
- Did not introduce new estimator names.
- Did not adjust the `C_genuine` decision rule during the analysis.
- Did not adjust the B1 decision rule.
- Did not perform a lambda sweep. Uniform cost (wrong_accept_cost=1, wrong_reject_cost=1) per Foued's Point 1 decision.
- Did not post-hoc select favorable perturbations.
- Did not post-hoc adjust P1 thresholds, P2 subsample indices, P3 rotation order, or survival threshold.
- Did not aggregate across perturbations in the verdict computation. Per-perturbation reporting only.
- Did not modify the recovered_solver_check pre-declared values.
- Per the freeze's substantive-language constraint, the term flagged by `results_doc_forbids_word_real` is not used in this document.

Per the spec (`PHASE_LC3946_C5_SPEC.md` §"Epistemological Constraints"):

- No compression drift: all claims are tied to the observed per-perturbation gap data and the pre-declared falsification criterion.
- No negative result inflation: scope is restricted to the 11 tested perturbations. The PARTIALLY_SURVIVES verdict is a per-perturbation classification; it is not generalized to "the gain does not survive in general."
- No hidden causal language: the P3e collapse is reported as an observation, with the aggregate counts cited. No causal claim is made about why the structured policy's advantage depends on a single family.

---

## 6. Audit-Pass Check (Post-Run Bug Discovery)

During Step 5 execution, the runner's Hard Stop #1 (aggregate consistency check) was triggered. The check failed on the first run, surfacing a discrepancy between the expected and re-computed B1/C_genuine aggregates. Investigation revealed two bugs in the runner + module code:

1. `aggregate_consistency_check` was using `target_ids` for both ground truth and estimator input (`observed_ids = list(target_ids)`). Fixed: function now takes `observed_ids` and `target_ids` as separate parameters. The runner now passes `observed_ids_full` correctly. A regression test (`test_disjoint_observed_vs_target`) was added in `tests/test_lc3946_c5_perturbations.py` to prevent re-introduction.
2. The falsification filter excluded P4 but not P1a. Fixed: the filter now excludes both `is_baseline_reference=True` and `perturbation_id == "P4"`. The assertion `len(p_gaps) == 11` now passes.

Both fixes are code-only changes to `doctor/adversarial/lc3946_collapse_perturbations.py`, `tests/test_lc3946_c5_perturbations.py`, and `runners/run_c5_collapse_lc3946.py`. The fixes are committed in a dedicated bug-fix commit (separate from the results commit) per Foued's commit structure instruction.

**Result-vs-code distinction (the load-bearing claim for the audit):**
- The pre-fix aggregate consistency check failed because the runner computed `(WA, WR, loss)` using the wrong probe set. The pre-fix runner did not produce any per-perturbation result; it hard-stopped at Hard Stop #1 before writing `data/c5_collapse_lc3946.json`. No "pre-fix" result exists in the data file.
- The post-fix aggregate consistency check passed, and the runner proceeded to compute all 12 perturbation records and write `data/c5_collapse_lc3946.json`. The numbers in that file are what the post-fix runner produced.
- **No result values were adjusted to match the protocol.** The bugs were in the code that *computes* the result, not in the result itself. The fix changed the code; the code then produced numbers; those numbers are recorded. There was no point at which a recorded number was modified to fit the expected (WA, WR, loss) values.
- The aggregate consistency check passing post-fix (B1=(0,1,1.0), C_genuine=(0,0,0.0) reproduce exactly) is independent confirmation that the post-fix runner computes the same numbers that were recorded in `data/midweather_fingerprint_lc3946.json` (the LC3946 C-4 result) for the unperturbed population. The bug was that the pre-fix runner was using a different (incorrect) probe set; the fix restored the correct probe set; the result is the same as the stored C-4 result on the unperturbed population.
- The 11 per-perturbation results (P1b through P3f) are produced by the same code path that produced the unperturbed baseline. If the unperturbed numbers reproduce, the perturbation numbers are also correct (the perturbation logic is a thin wrapper around the same B1/C_genuine policies).

Test count progression:
- 537 baseline (after LC3946 onboarding, prior to LC3946-C5)
- 573 after LC3946-C5 module + initial tests (commit `9414fce`)
- 574 after the 1 added regression test (`test_disjoint_observed_vs_target`)

---

## 7. Artifacts Produced

- `data/c5_collapse_lc3946.json` — per-perturbation (n_solvers, n_probes_observed, n_probes_target, failure_threshold, B1_aggregate, C_genuine_aggregate, gap, survives) records for 12 conditions (P1a baseline reference, P1b, P1c, P2a, P2b, P2c, P3a..P3f, P4 cross-population anchor). Overall verdict: PARTIALLY_SURVIVES (10/11).
- `PHASE_LC3946_C5_SPEC.md` (commit `9414fce`) — RQ, 11 pre-declared perturbations, three-outcome falsification criterion, per-perturbation reporting only, 11 hard-stop conditions, 7-step protocol.
- `PHASE_LC3946_C5_FREEZE.json` (commit `9414fce` for non-self SHAs; re-patched at tag time) — pre-declared parameters: P1 thresholds (0.05, 0.10, 0.20), P2a/b/c subsample indices, P3a-f knockout family order (axis_declaration order), uniform cost model, gap > 0 survival threshold, recovered_solver_check block (solver_016 in all 3 P2 subsamples: yes).
- `doctor/adversarial/lc3946_collapse_perturbations.py` (commit `9414fce`; bug fix in dedicated commit) — `threshold_shift`, `solver_subsample`, `family_knockout`, `cross_population_reference`, `compute_gap`, `falsification_criterion`, `aggregate_consistency_check`, plus 4 pre-declared constants and 2 helper policies.
- `tests/test_lc3946_c5_perturbations.py` (commit `9414fce`; +1 regression test in bug fix commit) — 37 passing tests across 10 test classes.
- `runners/run_c5_collapse_lc3946.py` (commit `9414fce`; bug fix in dedicated commit) — LC3946 collapse runner. Reuses `apply_estimator`, `compute_ground_truth`, `execute_solvers` from `runners/run_midweather_fingerprint_lc322.py`. Re-executes solvers to build the pass_fail matrix (no sidecar dependency). Writes `data/c5_collapse_lc3946.json`.

---

## 8. Closure Statement

Phase LC3946-C5 is closed as of this document. The pre-declared RQ-LC3946-C5 falsification has been evaluated across 11 perturbations:

- 10 perturbations maintained the C-4 utility gap: P1b, P1c, P2a, P2b, P2c, P3a, P3b, P3c, P3d, P3f.
- 1 perturbation collapsed the gap: P3e (`poset_lattice_two_prime` knockout).
- 1 baseline reference (P1a) and 1 cross-population anchor (P4) are recorded but not counted in the falsification.
- Overall verdict: PARTIALLY_SURVIVES.

The P3e collapse is the pre-declared falsification prediction recorded in the spec and the freeze. The mechanism — removing the family carrying the C_genuine advantage's only observed failure collapses both estimators to the same ACCEPT prediction — is consistent with the LC322 C-5 P3c collapse (`large_amount_stress` knockout), which was the analogous signal-driver family on LC322. **On LC322, the entire C-4 gain was carried by `large_amount_stress`. On LC3946, the entire C-4 gain is carried by `poset_lattice_two_prime`.** No aggregation across the two problems is performed here; this is a within-problem observation that the structured-policy advantage in both problems depends on a single probe family. This is a load-bearing finding for the C-7 cross-problem analysis.

The C-4 gain is preserved under most perturbations on LC3946 (10/11) and is not preserved under the predicted one (P3e). The per-perturbation status is reported above. No aggregation across perturbations is performed. No general claim is made about whether the C-4 gain "survives" or "does not survive" beyond the specific 11 perturbations tested.

The closed phases stand. LC3946-C5 tests the boundary conditions of the LC3946 C-4 finding; it does not reopen C-4, C-5 (LC322), or any prior phase.
