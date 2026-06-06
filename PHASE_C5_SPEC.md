# PHASE_C5_SPEC.md
# Doctor Phase C-5: Collapse Analysis (Distribution Shift)
# Status: APPROVED — Foued override granted (C-5)
# Date: 2026-06-06

---

## Explicit Non-Relationship Declaration

Phase C-5 is a **new program** authorized by Foued override. It is **not** a continuation of Phase C-1, C-3a, C-4, or project-closure-004. It is a distribution-shift analysis of the C-4 finding.

C-5 builds on the C-4 freeze (`PHASE_C4_FREEZE.json`, commit 88d0243) for **lineage only**:

- Same `C_genuine` decision rule (ACCEPT if 0 failures or all failures share one probe_family; REJECT otherwise).
- Same `B1_count` baseline.
- Same populations (LC322, LC45).
- Same cost model (linear, global `λ_A = 1`, `λ_sweep = [1, 2, 5, 7, 10, 15, 20, 30, 50]`).
- Same δ = 0.10.

What changes in C-5:

- Four pre-declared population perturbations (P1–P4) test whether the C-4 utility gain survives distribution shift.
- Per-perturbation reporting; no aggregation across perturbations.

The closed phases are **not reopened**:

| Tag | Commit | Content | Status |
|---|---|---|---|
| `project-closure-004` | `ccbf927` | Transfer-hypothesis. FAIL. | Stands. |
| `phase-c1-results` | `77ae794` | Asymmetric-cost sweep. Gap ≡ 0. FAIL. | Stands. |
| `phase-c3a-results` | `1ad4777` | Per-solver identity. FULL_EQUIVALENCE. | Stands. |
| `phase-c4-results` | `50d33e5` | Genuine structured policy. PASS on LC322, FAIL on LC45. | Stands. |

C-5 tests the boundary conditions of the C-4 finding. It does not claim the C-4 gain is or is not "real" in any general sense. It reports per-perturbation survival status only.

---

## Research Question

**RQ-C5:** Does `C_genuine`'s decision utility advantage over B1 on LC322 survive distribution shift — specifically, does the probe_family coherence rule produce gains that are not specific to the LC322 solver population structure?

### Motivation

C-4 produced a PASS on LC322: `C_genuine` recovers 5 solvers that B1 false-rejects, at the cost of 1 false accept. The net utility gap exceeds δ = 0.10 at all 9 tested lambda values. C-4 also produced a FAIL on LC45: `C_genuine` introduces 1 false accept on a population where B1 is perfect.

GPT correctly identified the LC45 result as evidence that the C-4 gain may be specific to the LC322 solver population structure. C-5 formalizes that observation by testing the C-4 gain against a pre-declared set of population perturbations on LC322.

---

## Falsification Criterion (Three Outcomes)

The C-5 verdict is determined by the per-perturbation gap behavior at the lambda values where C-4 showed PASS (all 9 lambda values, since C-4 had gap > 0.10 at all of them):

- **SURVIVES:** `C_genuine` maintains `utility(C_genuine) − utility(B1) > 0.10` on **all** tested perturbations at all 9 lambda values.
- **PARTIALLY SURVIVES:** `C_genuine` maintains the gap on **some** perturbations and collapses (gap ≤ 0.10 or reverses) on **others**. Per-perturbation results reported individually; no aggregation.
- **DOES NOT SURVIVE:** `C_genuine` collapses on **all** tested perturbations.

All three outcomes are valid and reportable. No post-hoc selection of favorable perturbations.

### Per-Lambda Reporting

For each perturbation, the gap is computed at all 9 lambda values. A perturbation "survives" at a given lambda if the gap exceeds 0.10. A perturbation "collapses" at a given lambda if the gap is ≤ 0.10 or reverses (gap < 0). The per-perturbation status is reported across the full lambda sweep.

---

## Pre-Declared Perturbations

These four perturbations are declared in this spec, before any runner is written. Indices are fixed and chosen before seeing any C-5 results.

### P1 — Accept/Reject Ratio Shift

Re-label the LC322 population from 11 ACCEPT / 19 REJECT to 19 ACCEPT / 11 REJECT. The same 30 solvers are used, but the ground truth labels are inverted: the 11 solvers formerly labeled ACCEPT are relabeled REJECT, and the 19 solvers formerly labeled REJECT are relabeled ACCEPT.

This tests whether the `C_genuine` advantage depends on the direction of the accept/reject skew.

### P2 — Solver Subsample (Three Fixed Draws)

Three subsamples of 20 solvers from the 30 LC322 solvers, pre-declared as index lists (0-indexed into the sorted `solver_id` list `["solver_001", ..., "solver_030"]`):

- **P2a:** indices `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]` (first 20)
- **P2b:** indices `[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]` (last 20)
- **P2c:** indices `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]` (first 10 + last 10)

These three draws were chosen to have different coverage of the LC322 solver population. P2a covers the first 20, P2b covers the last 20, P2c excludes the middle 10 (indices 10–19). The choice was made before seeing any C-5 results.

This tests whether the `C_genuine` advantage is driven by specific solvers.

### P3 — Probe Family Knockout (Six Rotating Knocks)

Remove all observed probes from one probe_family at a time, then re-run `C_genuine` and B1 on the reduced probe set. The 6 LC322 families (per `data/midweather_fingerprint_lc322_probe_index.json`):

1. `reachability_counterfactual`
2. `non_canonical_coin_order`
3. `large_amount_stress`
4. `greedy_dp_threshold`
5. `forward_dp_overwrite`
6. `memo_cache_aliasing`

The knockout rotation order is the enumeration order above (1, 2, 3, 4, 5, 6). This produces 6 perturbations (P3a–P3f).

This tests whether the `C_genuine` advantage depends on a specific family being present in the observed probe set.

### P4 — LC45 Cross-Population (Already Measured)

The LC45 result is already measured in C-4: `C_genuine` FAIL on LC45. C-5 records this as the cross-population perturbation result. No new execution needed for P4.

---

## Estimators Under Comparison

- **C_genuine**: the genuine structured policy from C-4. Unchanged.
- **B1_count**: `_fail_count_policy`. Unchanged from C-1, C-3a, C-4.

No new estimators, no new probes, no new solver packs.

---

## What This Phase Does Not Do

- Does not reopen `project-closure-004`, `phase-c1-results`, `phase-c3a-results`, or `phase-c4-results`.
- Does not introduce new probes, probe geometry, or solver packs.
- Does not modify the C-1, C-3a, or C-4 freeze parameters.
- Does not introduce new estimator names.
- Does not adjust the `C_genuine` decision rule during the analysis.
- Does not adjust the B1 decision rule.
- Does not post-hoc select favorable perturbations.
- Does not construct a per-solver-weighted cost functional (C-2 territory).
- Does not claim the C-4 gain is or is not "real" in any general sense. Reports per-perturbation survival status only.

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested perturbations.
3. **Hidden causal language:** no because / therefore / explains / caused by / due to.
4. **Per-perturbation reporting:** results are reported per perturbation, not aggregated.
5. **The word "real" is forbidden in the results doc** to describe the C-4 gain. The C-4 gain is an observation on the specific LC322 population under the specific `C_genuine` rule. It is not characterized as real or unreal.

§7 hard-stop rule: if any move requires violating the above, stop and surface the conflict.

---

## Hard Stop Conditions (Extended from C-4)

1. Re-run produces (WA, WR) inconsistent with stored aggregates for B1 on the unperturbed LC322 → STOP.
2. Any perturbation produces a re-run error → STOP, surface to Foued.
3. Perturbation indices are adjusted after seeing C-5 results → STOP, surface to Foued.
4. Any move targets a file that does not exist in the repo → STOP, surface to Foued.

---

## Deliverables

1. `PHASE_C5_SPEC.md` — this file
2. `PHASE_C5_FREEZE.json` — pre-declared parameters (commit before any code)
3. `tests/test_collapse_perturbations.py` — tests for perturbation module (commit with module)
4. `doctor/collapse_perturbations.py` — perturbation construction functions (commit with tests)
5. `runners/run_c5_collapse_lc322.py` — runner (committed before execution)
6. `data/c5_collapse_lc322.json` — output data
7. `docs/PHASE_C5_RESULTS.md` — findings, audit-passed, per-perturbation reporting
8. Tag: `phase-c5-results`

---

## Protocol (mirrors C-1, C-3a, C-4)

**Step 0 — Commit this spec and the freeze file before any code is written.** No runner is written until both files are committed.

**Step 1 — Write `PHASE_C5_FREEZE.json`.** Contents: four perturbations with full parameters (P1 re-labeling rule, P2 subsample indices, P3 knockout family order), delta=0.10, lambda sweep, population reference. Commit before any runner is written.

**Step 2 — Write `tests/test_collapse_perturbations.py`.** TDD red phase first. Tests must cover:
- P1 re-labeling produces 19 ACCEPT / 11 REJECT.
- P2 subsamples produce 20 solvers each, matching the pre-declared index lists.
- P3 knockout removes the correct probes.
- Falsification criterion correctly classifies SURVIVES / PARTIALLY_SURVIVES / DOES_NOT_SURVIVE.

**Step 3 — Implement perturbation module `doctor/collapse_perturbations.py`.** Functions for each perturbation. All tests green. Commit module + tests together.

**Step 4 — Write runner `runners/run_c5_collapse_lc322.py`.** Re-run B1 and C_genuine on the unperturbed LC322 (aggregate-consistency check), then apply each perturbation and compute per-perturbation gaps. Commit before execution.

**Step 5 — Execute.** Check aggregate consistency for B1 on unperturbed LC322. STOP if any inconsistency. If passes, apply each perturbation, compute per-perturbation gap table, apply falsification criterion.

**Step 6 — Write `docs/PHASE_C5_RESULTS.md`.** Audit against three failure modes before commit. Per-perturbation reporting. No "real" language for the C-4 gain. No aggregation.

**Step 7 — Tag `phase-c5-results`.**

---

## Governance Acknowledgment

C-5 is authorized by Foued override. It is a new program that tests the boundary conditions of the C-4 finding via population perturbation. C-4's constraint `"no_post_hoc_adjustment_of_decision_rule": true` is extended to C-5: the `C_genuine` decision rule is not adjusted during the C-5 analysis. The perturbation set is pre-declared in this spec.

If Foued at any point withdraws the C-5 override, the phase stops. The C-5 spec and freeze remain in the repository as a record of the authorized program.
