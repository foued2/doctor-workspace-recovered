# PHASE_C3A_SPEC.md
# Doctor Phase C-3a: Per-Solver Identity Resolution
# Status: APPROVED — Foued override granted (C-3a)
# Date: 2026-06-06

---

## Explicit Non-Relationship Declaration

Phase C-3a is a **new program** authorized by Foued override. It is **not** a continuation of Phase C-1. It violates C-1's explicit constraint `"runners_load_existing_decisions_only": true` by design — C-3a generates new per-solver decisions by re-running estimators against the frozen solver packs.

C-3a builds on C-1's freeze (`PHASE_C1_FREEZE.json`, commit 3bd286d) for **lineage only**:
- Same estimators (B0_prior, B1_count, B2_calibrated_count, B3_raw_pf_vector, B4_raw_full_tensor, B5_nearest_neighbor_raw_tensor, B6_regularized_raw_tensor, C_structured_fingerprint).
- Same populations (LC322, LC45).
- Same cost model (linear, global `λ_A = 1`, `λ_sweep = [1, 2, 5, 7, 10, 15, 20, 30, 50]`).
- Same frozen probe index.
- Same `apply_estimator` interface.

What changes in C-3a:
- Per-solver accept/reject decisions are **persisted** (not just aggregated to (WA, WR)).
- A new three-case decision rule (D, A) determines the outcome.

The C-1 closure (`phase-c1-results`, commit 77ae794) is **not reopened**. The aggregate (WA, WR) result is data, not an obstacle. C-3a measures what the aggregate erased.

---

## Research Question

**RQ-C3a:** Under the C-1 freeze cost model, do `C_structured_fingerprint` and `B1_count` misclassify the same solvers (full equivalence) or different solvers (structural difference)?

C-1's aggregate result — gap identically 0 across the 9-value λ sweep on both populations — is consistent with two structurally different scenarios:

1. **True equivalence.** C and B1 make **identical mistakes** on the same solvers. The (WA, WR) tie reflects the underlying solver-mistake tie.
2. **Masked divergence.** C and B1 make **different mistakes** that happen to cancel at the (WA, WR) level. The (WA, WR) tie hides the structural difference.

C-3a distinguishes these by exposing per-solver decisions. The aggregate (WA, WR) is a sufficient statistic under the freeze's symmetric-within-type cost; the per-solver joint distribution is not, and is the object of measurement in C-3a.

---

## Three-Case Decision Rule

C-3a has three falsifiable outcomes. All three are reportable.

### Definitions

Let:
- `M_C` = set of solver indices misclassified by `C_structured_fingerprint`.
- `M_B1` = set of solver indices misclassified by `B1_count`.
- `D = |M_C △ M_B1| / |M_C ∪ M_B1|` (Jaccard distance on misclassified sets).
- `cost_X(i, λ)` = per-solver cost of estimator X on solver i at λ, under the C-1 cost function.
- `A = max over λ in λ_sweep, max over solver i of |cost_C(i, λ) − cost_B1(i, λ)|`.

### Outcomes

- **D = 0 → Full equivalence.** `M_C = M_B1`. C and B1 misclassify the same solvers. The aggregate tie is real, not a cancellation artifact.
- **D > 0, A = 0 → Masked divergence.** `M_C ≠ M_B1`, but per-solver cost differences are uniformly zero. C and B1 misclassify different solvers, but the per-solver cost is the same on every solver at every λ. (E.g., C and B1 each make one false accept and one false reject, but on different solvers — totals cancel under the symmetric-within-type cost.)
- **D > 0, A > 0 → Directional superiority.** `M_C ≠ M_B1`, AND per-solver costs differ in a way that does not cancel. This is the case where a per-solver-weighted cost functional (C-2 territory) could in principle exploit the difference. C-3a reports it; it does not run C-2.

### Thresholds

D and A are integer-valued under the freeze (solver identities are discrete; costs are 0, `λ_A`, or `λ_R`, all integers at integer λ). Threshold is **0**: zero means zero, non-zero means non-zero. No fuzz, no floating-point edge cases.

### Why three cases, not two

The C-1 verdict "FAIL with mathematical certainty under the freeze's pre-declared cost model" is the result of the aggregate gap being identically 0. But this is consistent with D = 0 (true equivalence) or D > 0 (structural difference, masked by aggregation). C-3a is the disambiguator.

The D > 0, A = 0 case is interesting in its own right: it shows C and B1 differ structurally, but the per-solver cost is the same. This is a "negative result" finding under the freeze's symmetric-within-type metric — the structural difference does not produce a cost difference.

The D > 0, A > 0 case is the only one that motivates a per-solver-weighted cost functional (C-2). C-3a does not run C-2; it only reports whether the structural difference is cost-relevant under the freeze's model.

---

## Experiment Re-Run Protocol

C-3a re-runs the 8 estimators against the frozen solver packs and frozen probe index. Per-solver accept/reject decisions are persisted.

### Estimators

Same 8 as C-1:
- B0_prior
- B1_count
- B2_calibrated_count
- B3_raw_pf_vector
- B4_raw_full_tensor
- B5_nearest_neighbor_raw_tensor
- B6_regularized_raw_tensor
- C_structured_fingerprint

### Populations

Same 2 as C-1:
- **LC322:** 30 solvers, 11/19 accept/reject split. Role: primary.
- **LC45:** 10 solvers, 1/9 accept/reject split. Role: stress test (single-survivor skew; results reported separately, not used as primary evidence).

### Probes

Same frozen probe index as C-1: `data/midweather_fingerprint_lc{322,45}_probe_index.json`.

### Solver Packs

Frozen from C-1:
- `experiments/frozen_taxonomy_lc322/` (1 runner + 30 solver `.py` files).
- `experiments/frozen_taxonomy_lc45/` (1 runner + 10 solver `.py` files).

Confirmed by inspection: solvers are genuine algorithm implementations (e.g., `solver_001.py` is a canonical bottom-up DP for coin change), not hardcoded pass/fail stubs.

### Re-run procedure

For each population:
1. Load the frozen solver pack from `experiments/frozen_taxonomy_lc{322,45}/`.
2. Load the frozen probe index.
3. For each solver, run the solver against the probe set, get per-probe pass/fail.
4. For each estimator, call `apply_estimator(policy, pass_results, observed_ids, probe_index=None)` to get the per-solver accept/reject decision.
5. Persist per-solver decisions to a new data file (format below).

### Aggregate-Consistency Check (STOP CONDITION)

After re-running, for each (estimator, population), the per-solver decisions **must** be consistent with the saved (WA, WR) aggregates in `data/midweather_fingerprint_lc{322,45}.json`.

Specifically, for estimator X on population n:
- `WA_recomputed = count(solver i where decision_X(i) = "ACCEPT" and ground_truth(i) = "REJECT")`.
- `WR_recomputed = count(solver i where decision_X(i) = "REJECT" and ground_truth(i) = "ACCEPT")`.
- `(WA_recomputed, WR_recomputed) == (WA_X, WR_X)`.

If any (estimator, population) fails this check, **STOP IMMEDIATELY**. Do not record any result. Surface the discrepancy to Foued before proceeding. Inconsistency means either:
- The re-run protocol is wrong (e.g., wrong probe index, wrong policy binding, wrong estimator).
- The aggregate was not produced by this solver pack (e.g., a different pack was used originally).

Both require Foued call before proceeding. C-3a is **not** authorized to resolve such discrepancies silently.

---

## Output Format

Per-solver decision data is persisted to:

`data/midweather_fingerprint_lc{322,45}_per_solver.json`

Structure:

```json
{
  "population": "LC322",
  "n_solvers": 30,
  "spec_commit": "...",
  "freeze_commit": "...",
  "c1_freeze_commit": "3bd286d",
  "per_solver": [
    {
      "solver_id": "solver_001",
      "ground_truth": "ACCEPT",
      "decisions": {
        "B0_prior": "ACCEPT",
        "B1_count": "REJECT",
        "C_structured_fingerprint": "REJECT"
      }
    }
  ]
}
```

The `c1_freeze_commit` field is **required** for lineage — it makes the C-1 freeze reference explicit in the artifact. C-3a builds on C-1's freeze; that reference is in the data.

---

## Pre-declared Parameters (C-3a Freeze)

| Parameter | Value | Type | Source |
|---|---|---|---|
| D threshold | 0 | integer | Foued override, prior turn |
| A threshold | 0 | integer | Foued override, prior turn |
| Estimators | 8 (B0-B6, C) | list | C-1 freeze |
| Populations | LC322, LC45 | list | C-1 freeze |
| λ_sweep | [1, 2, 5, 7, 10, 15, 20, 30, 50] | list | C-1 freeze (commit 3bd286d) |
| λ_A | 1 | int | C-1 freeze |
| Cost function | linear, global λ_A, global λ_R | function | C-1 freeze |
| Probe index | frozen | reference | C-1 freeze |
| Solver pack | frozen | reference | C-1 freeze |
| Aggregate-consistency check | required | gate | Foued override, prior turn |

The C-3a freeze file (`PHASE_C3A_FREEZE.json`) will encode these as a pre-declared contract, mirroring the C-1 freeze mechanism.

---

## What This Phase Does Not Do

- Does not reopen `project-closure-004`.
- Does not reopen `phase-c1-results`. C-1 is closed by its own result.
- Does not introduce new estimators.
- Does not introduce new probes or probe geometry.
- Does not introduce new solver packs.
- Does not modify the C-1 freeze parameters.
- Does not construct a per-solver-weighted cost functional (C-2 territory).
- Does not claim the structural difference is exploitable for decision utility.
- Does not generalize beyond the tested populations and estimators.
- Does not silently resolve aggregate-consistency discrepancies. Foued call required.

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested populations and estimators.
3. **Hidden causal language:** no because / therefore / explains / caused by / due to.
4. **Aggregate-consistency check:** required before any result is recorded; failure stops the phase and surfaces to Foued.

§7 hard-stop rule: if any move requires violating the above, stop and surface the conflict. Do not proceed.

---

## Deliverables

1. `PHASE_C3A_SPEC.md` — this file
2. `PHASE_C3A_FREEZE.json` — pre-declared parameters (commit before any code)
3. New per-solver decision data files: `data/midweather_fingerprint_lc{322,45}_per_solver.json`
4. `doctor/identity_resolution.py` — D and A computation
5. `tests/test_identity_resolution.py` — tests for D and A
6. `runners/run_per_solver_decisions_lc{322,45}.py` — runners (committed before execution)
7. `docs/PHASE_C3A_RESULTS.md` — findings, three-case decision rule, no causal language
8. Tag: `phase-c3a-results`

---

## Protocol (mirrors C-1)

**Step 0 — Commit this spec and the freeze file before any code is written.** No runner is written until both files are committed.

**Step 1 — Write `PHASE_C3A_FREEZE.json`.** Contents: D threshold (0), A threshold (0), estimator list, population identifiers, λ sweep values, probe index reference, solver pack reference, aggregate-consistency check requirement. Commit before any runner is written.

**Step 2 — Write `doctor/identity_resolution.py`.** Functions:
- `compute_misclassified_set(decisions, ground_truth) -> set` — returns indices of misclassified solvers.
- `compute_jaccard_distance(set_a, set_b) -> int` — returns `|A △ B| / |A ∪ B|` (integer under integer-valued inputs).
- `compute_per_solver_cost(decision, ground_truth, lambda_R, lambda_A) -> float` — per-solver cost.
- `compute_A(c_sweep, b1_sweep, lambda_sweep) -> int` — maximum per-solver cost differential.
- `apply_decision_rule(D, A) -> str` — returns one of "FULL_EQUIVALENCE", "MASKED_DIVERGENCE", "DIRECTIONAL_SUPERIORITY".

Plus tests covering each function. 341 + N passed required.

**Step 3 — Run tests; 341 + N passed required.** No runner written until tests are green.

**Step 4 — Write runners `runners/run_per_solver_decisions_lc{322,45}.py`.** Re-run estimators, persist per-solver decisions, run aggregate-consistency check. Commit before execution.

**Step 5 — Run aggregate-consistency check; STOP if any inconsistency.** No result is recorded if the re-run does not reproduce the saved (WA, WR) aggregates for every (estimator, population).

**Step 6 — Compute D, A; apply three-case decision rule.** No interpretation during the run. Read the rule from the freeze.

**Step 7 — Write `docs/PHASE_C3A_RESULTS.md`.** Findings only. No causal language. No compression drift. No generalization beyond tested populations and estimators. Commit and tag `phase-c3a-results`.

---

## Governance Acknowledgment

C-3a is authorized by Foued override. It violates C-1's explicit constraint `"runners_load_existing_decisions_only": true` by design. This is recorded as a Foued override, not a minor constraint relaxation. The C-1 closure is not reopened; C-3a is a new program with explicit non-relationship to C-1 (other than the freeze reference for lineage).

If Foued at any point withdraws the C-3a override, the phase stops. No further moves are made. The C-3a spec and freeze remain in the repository as a record of the authorized program; no runner is executed beyond that point.
