# PHASE_C4_SPEC.md
# Doctor Phase C-4: Genuine Structured Policy
# Status: APPROVED — Foued override granted (C-4)
# Date: 2026-06-06

---

## Explicit Non-Relationship Declaration

Phase C-4 is a **new program** authorized by Foued override. It is **not** a continuation of Phase C-1, Phase C-3a, or project-closure-004. It is a new research question with a new estimator and a new decision rule.

C-4 builds on the C-1 freeze (`PHASE_C1_FREEZE.json`, commit 3bd286d) for **lineage only**:

- Same populations (LC322, LC45).
- Same cost model (linear, global `λ_A = 1`, `λ_sweep = [1, 2, 5, 7, 10, 15, 20, 30, 50]`).
- Same frozen probe index.
- Same `apply_estimator` interface.
- Same `B1_count` as the comparison baseline.

What changes in C-4:

- A new estimator `C_genuine` replaces `C_structured_fingerprint` in the C-vs-B1 comparison.
- `C_genuine` uses a different decision rule than `_fail_count_policy` (the function bound to B1 and to the prior C).
- The prior C's binding to `_fail_count_policy` (a finding of C-3a) is the motivation: C-4 asks what happens when C actually uses structured features.

The closed phases are **not reopened**:

| Tag | Commit | Content | Status |
|---|---|---|---|
| `project-closure-004` | `ccbf927` | Transfer-hypothesis. FAIL. | Stands. |
| `phase-c1-results` | `77ae794` | Asymmetric-cost sweep. Gap ≡ 0. FAIL. | Stands. |
| `phase-c3a-results` | `1ad4777` | Per-solver identity. FULL_EQUIVALENCE. | Stands. |

C-4 is the next step. C-1's `C_structured_fingerprint` is **not** removed from the codebase; it remains available for the C-3a identity comparison. C-4 only changes the primary C-vs-B1 comparison to use `C_genuine` instead of `C_structured_fingerprint`.

---

## Research Question

**RQ-C4:** Does a C estimator that actively uses the probe-indexed structured features already in `doctor/adversarial/midweather_fingerprint_features.py` improve decision utility over B1 on the frozen LC322 and LC45 populations, under the C-1 asymmetric-cost protocol?

### Motivation

C-3a found that `C_structured_fingerprint` and `B1_count` produce identical per-solver decisions on both frozen populations (D = 0, A = 0). The reason, confirmed in `doctor/adversarial/problem_class_config.py:114-123`, is that both estimators are bound to `_fail_count_policy`, which only consults `obs_fails` and `n_obs` and ignores the `obs_records` parameter (which carries the structured fingerprint context). The prior C is operationally a renamed B1.

C-4 asks the question C-3a left open: if C is re-implemented to actually consult the structured fingerprint context, does the result change?

---

## The C_genuine Decision Rule (Declared Before Implementation)

The decision rule is stated here in full, before any code is written. It is grounded in the features that `midweather_fingerprint_features.py` already computes and that `apply_estimator` already passes to the policy function via `obs_records`.

### Feature Used

`probe_family` — a categorical label (string) indicating which of the 6 probe families the probe belongs to. The families are declared in `MIDWEATHER_FINGERPRINT_GATE{,_LC45}_FREEZE.json` and are part of the frozen probe geometry.

For LC322 the 6 families are: `reachability_counterfactual`, `order_dependent`, `magnitude_boundary`, `boundary_collapse`, `transition_break`, `memoization_collision`.

For LC45 the 6 families are: `naive_max_jump_suboptimal`, `single_large_jump_decoy`, `greedy_horizon_collapse`, `naive_max_jump_dead_landing`, `uniform_jump_array`, `greedy_frontier_valid_no_false_pressure`.

The `probe_family` value for each observed probe is available in `obs_records[i].fingerprint_context.probe_family` (via `_probe_to_fingerprint_context` in `run_midweather_fingerprint_lc322.py:171-184`).

### Decision Rule

```
C_genuine(obs_fails, n_obs, obs_records) =
    ACCEPT  if obs_fails == 0
    ACCEPT  if obs_fails > 0 AND all failures share one probe_family
    REJECT  otherwise
```

Formally:

```
failures = [obs_records[i] for i where obs_records[i].pass_fail == False]
if len(failures) == 0:
    return "ACCEPT"
families_of_failures = {r.fingerprint_context.probe_family for r in failures}
if len(families_of_failures) == 1:
    return "ACCEPT"
return "REJECT"
```

### Intuition

B1's rule is: any failure → REJECT. This is conservative. A solver with 1 failure in 15 probes is rejected by B1 even if it passes the other 14.

C_genuine's rule: a solver with failures is still ACCEPTable if those failures are **concentrated in a single probe family**. The intuition: a solver that fails consistently on a specific probe type is exhibiting a structured failure pattern. Its reliability on the other 5 families is preserved. In contrast, a solver with failures spread across multiple families is exhibiting an unstructured failure pattern, and B1's conservative rejection is warranted.

This rule uses the `probe_family` feature dimension, which B1 does not consult. It can produce ACCEPT when B1 produces REJECT (on solvers with structured failures). It is not a placeholder aggregation; it is a specific decision rule with a specific feature and a specific condition.

### Edge Case: `obs_records` is None

If `obs_records` is None (the policy is called without fingerprint context), C_genuine falls back to B1's behavior: ACCEPT iff `obs_fails == 0`. This is a safe default; C_genuine is only differentiated from B1 when the structured context is available.

### Difference from `_fail_count_policy`

`_fail_count_policy` (bound to B1 and to the prior C):

```
return "ACCEPT" if obs_fails == 0 else "REJECT"
```

C_genuine:

```
if obs_fails == 0: return "ACCEPT"
if all failures in one probe_family: return "ACCEPT"
return "REJECT"
```

The difference: C_genuine adds the `all failures in one probe_family` ACCEPT branch. When `obs_records` is provided and there is at least one failure, C_genuine can differ from B1.

---

## Falsification Criterion

The C-4 verdict is determined by the primary comparison on LC322:

- **PASS:** ∃ λ in `{1, 2, 5, 7, 10, 15, 20, 30, 50}` such that `utility(C_genuine) − utility(B1) > 0.10` on LC322, **and** `C_genuine` produces different per-solver decisions than B1 on at least one solver on LC322 (D > 0).
- **FAIL:** No such λ found, **or** D = 0 (C_genuine collapses back to B1 behavior despite the genuine policy).
- **DEGENERATE:** C_genuine or B1 collapses to all-ACCEPT or all-REJECT at a given λ. Record and exclude at that λ.

### The D > 0 Requirement is Mandatory

A PASS verdict that shows D = 0 is **not** a PASS. If D = 0, C_genuine is operationally equivalent to B1, and the new policy has failed to differentiate. This is a FAIL regardless of the utility gap (which would be 0 anyway under D = 0 and identical aggregate (WA, WR)).

The D > 0 requirement guards against the case where C_genuine silently degrades to `_fail_count_policy` behavior despite the genuine policy. If the new policy does not produce at least one different per-solver decision, it is not a genuine policy; it is a relabeled B1.

### Three-Case Report Structure

Following the C-3a precedent, C-4 reports three cases for the LC322 population:

- D = 0 → `FULL_EQUIVALENCE` (C_genuine is operationally B1; FAIL)
- D > 0, A = 0 → `MASKED_DIVERGENCE` (C_genuine decisions differ from B1 but per-solver cost is uniformly equal; FAIL, since utility gap is 0)
- D > 0, A > 0 → `DIRECTIONAL_SUPERIORITY` (C_genuine decisions differ from B1 AND per-solver costs differ; PASS or FAIL based on the utility gap criterion)

The three-case report is orthogonal to the falsification criterion. The falsification criterion is the primary verdict. The three-case report is a secondary disambiguation, carried forward from C-3a for diagnostic clarity.

### LC45 Role

LC45 is a stress test (single-survivor skew: 1 ACCEPT, 9 REJECT). C-4 reports LC45 separately. The LC45 result does not override the LC322 verdict. If LC45 produces a different outcome, the results doc records both and notes the discrepancy.

---

## Estimators Under Comparison

- **C_genuine** (new): the genuine structured policy described above. Bound to `C_genuine` in `problem_class_config.py`.
- **B1_count** (baseline): `_fail_count_policy`. Unchanged from C-1, C-3a.

The prior `C_structured_fingerprint` is not part of the C-4 primary comparison. It remains in the codebase for the C-3a identity comparison and for reproducibility. C-4 does not delete it.

---

## What This Phase Does Not Do

- Does not reopen `project-closure-004`, `phase-c1-results`, or `phase-c3a-results`.
- Does not introduce new probes or probe geometry.
- Does not introduce new solver packs.
- Does not modify the C-1 freeze parameters (δ, λ sweep, λ_A).
- Does not introduce new estimator names beyond `C_genuine`.
- Does not adjust the decision rule for C_genuine after seeing per-solver results.
- Does not construct a per-solver-weighted cost functional (C-2 territory).
- Does not silently resolve aggregate-consistency discrepancies. Foued call required.

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested populations and λ range.
3. **Hidden causal language:** no because / therefore / explains / caused by / due to.
4. **Aggregate-consistency check:** required before any result is recorded; failure stops the phase and surfaces to Foued.
5. **D > 0 requirement:** a PASS verdict requires D > 0; D = 0 is a FAIL regardless of the utility gap.

§7 hard-stop rule: if any move requires violating the above, stop and surface the conflict.

---

## Hard Stop Conditions (Extended from C-3a)

1. Re-run produces (WA, WR) inconsistent with stored aggregates for B1 → STOP.
2. C_genuine produces D = 0 after implementation → FAIL verdict, do not relabel as PASS.
3. Decision rule for C_genuine is adjusted after seeing per-solver results → STOP, surface to Foued.
4. Any move targets a file that does not exist in the repo → STOP, surface to Foued.

---

## Deliverables

1. `PHASE_C4_SPEC.md` — this file
2. `PHASE_C4_FREEZE.json` — pre-declared parameters (commit before any code)
3. `tests/test_genuine_policy.py` — tests for C_genuine (commit with module)
4. `doctor/adversarial/problem_class_config.py` — new `C_genuine` policy function (commit with tests)
5. `runners/run_c4_decisions_lc{322,45}.py` — runners (committed before execution)
6. `data/c4_decisions_lc{322,45}.json` — output data
7. `docs/PHASE_C4_RESULTS.md` — findings, audit-passed
8. Tag: `phase-c4-results`

---

## Protocol (mirrors C-1 and C-3a)

**Step 0 — Commit this spec and the freeze file before any code is written.** No runner is written until both files are committed.

**Step 1 — Write `PHASE_C4_FREEZE.json`.** Contents: C_genuine decision rule (verbatim from §"The C_genuine Decision Rule"), feature used (`probe_family`), estimator list (C_genuine, B1_count), populations, δ=0.10, λ sweep, D > 0 requirement. Commit before any runner is written.

**Step 2 — Write `tests/test_genuine_policy.py`.** TDD red phase first. Tests must include:
- C_genuine produces different decisions than B1 on at least one constructed input where the structured feature is non-zero.
- C_genuine does not collapse to `_fail_count_policy` (verified by inspecting the policy function source).
- Aggregate-consistency check carries forward from C-3a.
- Falsification criterion correctly applied (D=0 → FAIL regardless of utility gap).

**Step 3 — Implement `C_genuine` in `doctor/adversarial/problem_class_config.py`.** Add the new policy function alongside the existing 5. Update `LC322_ESTIMATOR_POLICIES` and `LC45_ESTIMATOR_POLICIES` to add the `C_genuine` binding. All tests green. Commit module + tests together.

**Step 4 — Write runners `runners/run_c4_decisions_lc{322,45}.py`.** Re-run C_genuine and B1, persist per-solver decisions, run aggregate-consistency check for B1 (hard stop). Commit before execution.

**Step 5 — Execute.** Check aggregate consistency for B1. STOP if any inconsistency. If passes, compute D, A, utility gap. Apply falsification criterion.

**Step 6 — Write `docs/PHASE_C4_RESULTS.md`.** Audit against three failure modes before commit.

**Step 7 — Tag `phase-c4-results`.**

---

## Governance Acknowledgment

C-4 is authorized by Foued override. It adds a new estimator (`C_genuine`) to `problem_class_config.py`, which is a new program. C-1's constraint `"no_new_estimators": true` is acknowledged to be violated by C-4, and the violation is recorded as a Foued override, not a minor constraint relaxation.

If Foued at any point withdraws the C-4 override, the phase stops. The C-4 spec and freeze remain in the repository as a record of the authorized program.
