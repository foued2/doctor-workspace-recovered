# PHASE_C6_SPEC.md
# Doctor Phase C-6: Representation Class Falsification
# Status: PROPOSED — Awaiting Foued authorization
# Date: 2026-06-06

---

## Explicit Non-Relationship Declaration

Phase C-6 is a **new program** authorized by Foued override. It is **not** a continuation of Phase C-1, C-3a, C-4, C-5, or project-closure-004. It is a new research question with a new set of candidate decision rules and a new falsification criterion.

C-6 builds on prior freeze files for **lineage only**:

- Inherits the C-5 perturbation battery (P1, P2a-c, P3a-f, P4) from `PHASE_C5_FREEZE.json` (commit 98cc8e4).
- Inherits the C-1 cost model and lambda sweep from `PHASE_C1_FREEZE.json` (commit 3bd286d).
- Inherits the C-4 `C_genuine` decision rule as the baseline candidate (Rule 1 below).

What C-6 changes:

- Adds 3 new candidate decision rules beyond `C_genuine` (Rules 2, 3, 4 below).
- Defines a per-rule falsification criterion (each rule SURVIVES or DOES_NOT_SURVIVE the C-5 perturbation battery on LC322).
- Combines per-rule verdicts into a single class-level answer to RQ-C6.

The closed phases are **not reopened**:

| Tag                   | Commit    | Content                                | Status  |
|-----------------------|-----------|----------------------------------------|---------|
| `project-closure-004` | `ccbf927` | Transfer-hypothesis. FAIL.             | Stands. |
| `phase-c1-results`    | `77ae794` | Asymmetric-cost sweep. Gap ≡ 0. FAIL.   | Stands. |
| `phase-c3a-results`   | `1ad4777` | Per-solver identity. FULL_EQUIVALENCE. | Stands. |
| `phase-c4-results`    | `50d33e5` | C_genuine. PASS on LC322, FAIL on LC45. | Stands. |
| `phase-c5-results`    | `d1435a3` | PARTIALLY_SURVIVES. 6/11 perturbations. | Stands. |

C-6 is the next step. The `C_genuine` policy remains in `problem_class_config.py` from C-4. C-6 adds 3 new policy functions (Rule 2, 3, 4) and registers all 4 rules in `LC{322,45}_ESTIMATOR_POLICIES`. C-6 also runs the C-5 battery against each new rule and against the existing `C_genuine` rule, producing a per-rule, per-perturbation survival table.

---

## Research Question

**RQ-C6:** Can any estimator built on the structured fingerprint representation class produce separation from B1 that is invariant under the distribution transformations tested in C-5?

### Motivation

C-4 and C-5 tested one decision rule (`C_genuine`, the probe_family coherence rule). C-4 found that rule produces measurable divergence from B1 on LC322 under specific population conditions. C-5 found that divergence does not survive all tested distribution transformations (collapses on 5 of 11 perturbations).

C-6 does not retest `C_genuine` for the purpose of reopening C-4 or C-5. C-6 tests a different question: does **any** function of the structured fingerprint features produce stable separation, or is the representation class fundamentally limited to producing population-specific gains?

C-6 does not search over all possible rules. That is unconstrained and produces overfitting by construction. C-6 declares a small set of 4 candidate rules grounded in the feature dimensions already in `midweather_fingerprint_features.py`, tests each under the same C-5 perturbation battery, and records which survive.

---

## Candidate Decision Rules (Declared Verbatim Before Implementation)

All 4 rules are stated here in full, before any code is written. All rules use the same interface as C-4's `C_genuine`:

```
rule(obs_fails, n_obs, obs_records) -> "ACCEPT" | "REJECT"
```

If `obs_records` is None for any rule, the rule falls back to B1 behavior: ACCEPT if `obs_fails == 0`, REJECT otherwise.

### Rule 1: C_genuine (baseline, from C-4)

Feature used: `probe_family` (from `obs_records[i].fingerprint_context.probe_family`).

```
C_genuine(obs_fails, n_obs, obs_records):
    if obs_records is None: return ACCEPT if obs_fails == 0 else REJECT
    failures = [r for r in obs_records if not r['pass_fail']]
    if len(failures) == 0: return ACCEPT
    families = {r['fingerprint_context']['probe_family'] for r in failures}
    if len(families) == 1: return ACCEPT
    return REJECT
```

### Rule 2: C_feature_threshold (new)

Feature used: `deformation_level` (dim 1 of the 6-dim `encode_raw_tensor` output; from `obs_records[i].fingerprint_context.deformation_level`).

A probe is "deformed" if `deformation_level > 0`. `failure_rate_deformed` = (count of failures among deformed probes) / (count of deformed probes).

```
C_feature_threshold(obs_fails, n_obs, obs_records):
    if obs_records is None: return ACCEPT if obs_fails == 0 else REJECT
    deformed = [r for r in obs_records if r['fingerprint_context'].get('deformation_level', 0) > 0]
    if len(deformed) == 0: return ACCEPT if obs_fails == 0 else REJECT
    failures_deformed = [r for r in deformed if not r['pass_fail']]
    failure_rate_deformed = len(failures_deformed) / len(deformed)
    if obs_fails == 0: return ACCEPT
    if failure_rate_deformed < 0.5: return ACCEPT
    return REJECT
```

Threshold: 0.5 (50% failure rate on deformed probes). This is the natural "majority" threshold.

### Rule 3: C_majority (new)

Feature used: `probe_family` (same as Rule 1), but with a plurality criterion instead of strict unanimity.

A "unique mode" exists when one failure-family has more failures than any other single failure-family. Ties yield REJECT.

```
C_majority(obs_fails, n_obs, obs_records):
    if obs_records is None: return ACCEPT if obs_fails == 0 else REJECT
    failures = [r for r in obs_records if not r['pass_fail']]
    if len(failures) == 0: return ACCEPT
    family_counts = {}
    for r in failures:
        f = r['fingerprint_context']['probe_family']
        family_counts[f] = family_counts.get(f, 0) + 1
    max_count = max(family_counts.values())
    n_with_max = sum(1 for c in family_counts.values() if c == max_count)
    if n_with_max == 1: return ACCEPT
    return REJECT
```

This rule accepts more solvers than Rule 1 (Rule 1 requires all failures in one family; Rule 3 requires only that one family has plurality). Rule 3 still rejects if failures are evenly distributed across families.

### Rule 4: C_zero_only (new)

```
C_zero_only(obs_fails, n_obs, obs_records):
    return ACCEPT if obs_fails == 0 else REJECT
```

Operationally identical to `_fail_count_policy` (B1). This rule is the negative control: it shows whether the C-4 gain is associated with the coherence condition (Rule 1) or with being more permissive than B1. Since this rule is identical to B1, the gap is 0 on every perturbation and at every lambda. The verdict is DOES_NOT_SURVIVE a priori.

---

## Falsification Criterion

### Per-Rule Falsification

For each rule R in {Rule 1, Rule 2, Rule 3, Rule 4}:

- **SURVIVES:** For all 11 perturbations in the C-5 battery, on LC322, `utility(R) − utility(B1) > 0.10` at all 9 lambda values in the C-1 sweep. Aggregate-consistency check passes.
- **DOES_NOT_SURVIVE:** Any perturbation has `gap ≤ 0.10` or `gap < 0` at any lambda value.
- **DEGENERATE:** A rule or B1 collapses to all-ACCEPT or all-REJECT at a given lambda. Record and exclude at that lambda. If the rule is degenerate on all lambdas, it DOES_NOT_SURVIVE.

### RQ-C6 Class-Level Verdict

- **RQ-C6 YES:** At least one of Rules 1, 2, 3 SURVIVES the C-5 battery on LC322. The class can produce invariant separation. (Rule 4 is B1, so it cannot SURVIVE.)
- **RQ-C6 NO:** None of Rules 1, 2, 3 SURVIVES. The class does not produce invariant separation under the tested perturbations. Rule 4 confirms that the gain is not from being more permissive than B1.
- **MIXED (provisional):** Some rules survive and some do not, but no rule is a refinement of another. Report per-rule status; the class-level answer is "class contains both surviving and non-surviving rules" (a structured finding, not a yes/no).

### LC45 Role

LC45 is a stress test. C-6 reports LC45 per-rule survival separately. The LC45 result does not override the LC322 verdict on RQ-C6. If LC45 produces a different outcome, the results doc records both and notes the discrepancy.

---

## Estimators Under Comparison

For C-6, the 4 candidate rules are added to the comparison:

- **C_genuine** (Rule 1, existing): probe_family coherence. Bound to `C_genuine` in `problem_class_config.py` from C-4.
- **C_feature_threshold** (Rule 2, new): deformation-level-based failure rate threshold.
- **C_majority** (Rule 3, new): plurality failure-family rule.
- **C_zero_only** (Rule 4, new): zero-failure only (B1-equivalent negative control).
- **B1_count** (baseline): `_fail_count_policy`. Unchanged from C-1, C-3a, C-4, C-5.

The prior `C_structured_fingerprint` is not part of the C-6 primary comparison. It remains in the codebase for the C-3a identity comparison and for reproducibility. C-6 does not delete it.

The C-1 baseline (B1_count) is preserved unchanged.

---

## Perturbation Battery (Inherited from C-5)

C-6 uses the same 11 perturbations as C-5, on LC322. The battery is declared in `PHASE_C5_FREEZE.json` (commit 98cc8e4):

- P1: label inversion (11/19 → 19/11).
- P2a: subsample first 20 solvers (indices [0..19]).
- P2b: subsample last 20 solvers (indices [10..29]).
- P2c: subsample first 10 + last 10 (indices [0..9] + [20..29]).
- P3a-f: probe family knockout, rotating over the 6 LC322 families.
- P4: LC45 cross-population (already measured in C-4, reused).

C-6 does not introduce new perturbations. C-6 does not modify the C-5 perturbation parameters.

---

## What This Phase Does Not Do

- Does not reopen `project-closure-004`, `phase-c1-results`, `phase-c3a-results`, `phase-c4-results`, or `phase-c5-results`.
- Does not introduce new probes or probe geometry.
- Does not introduce new solver packs.
- Does not modify the C-1 freeze parameters (delta, lambda sweep, lambda_A).
- Does not modify the C-5 perturbation battery.
- Does not modify the C-4 `C_genuine` decision rule.
- Does not adjust any candidate rule's decision function after seeing per-perturbation results.
- Does not construct a per-solver-weighted cost functional (C-2 territory).
- Does not silently resolve aggregate-consistency discrepancies. Foued call required.
- Does not claim that the 4 candidate rules exhaust the representation class.
- Does not claim universal generalization beyond the tested populations and perturbations.

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested populations, lambda range, and perturbation set.
3. **Hidden causal language:** no because / therefore / explains / caused by / due to.
4. **Aggregate-consistency check:** required before any result is recorded; failure stops the phase and surfaces to Foued.
5. **Per-perturbation reporting only:** no aggregation across perturbations.
6. **Per-rule reporting only:** no aggregation across rules except the pre-declared RQ-C6 verdict criterion.

§7 hard-stop rule: if any move requires violating the above, stop and surface the conflict.

---

## Hard Stop Conditions (Extended from C-4 and C-5)

1. Re-run produces (WA, WR) inconsistent with stored aggregates for B1 → STOP.
2. Any candidate rule's decision function is adjusted after seeing per-perturbation results → STOP, surface to Foued.
3. The C-5 perturbation battery is modified after the freeze is committed → STOP, surface to Foued.
4. Any move targets a file that does not exist in the repo → STOP, surface to Foued.
5. More than 4 candidate rules are added without Foued override → STOP, surface to Foued.

---

## Deliverables

1. `PHASE_C6_SPEC.md` — this file
2. `PHASE_C6_FREEZE.json` — pre-declared parameters (commit before any code)
3. `tests/test_structured_candidate_policies.py` — tests for all 4 candidate policies (commit with module)
4. `doctor/adversarial/problem_class_config.py` — 3 new policy functions (C_feature_threshold, C_majority, C_zero_only), updated `LC{322,45}_ESTIMATOR_POLICIES` (commit with tests)
5. `runners/run_c6_collapse_lc{322,45}.py` — runners (committed before execution)
6. `data/c6_collapse_lc{322,45}.json` — output data
7. `docs/PHASE_C6_RESULTS.md` — per-rule, per-perturbation findings, audit-passed
8. Tag: `phase-c6-results`

---

## Protocol (mirrors C-4 and C-5)

**Step 0 — Commit this spec and the freeze file before any code is written.** No runner is written until both files are committed.

**Step 1 — Write `PHASE_C6_FREEZE.json`.** Contents: 4 candidate rules declared verbatim, perturbation battery inherited from C-5, per-rule falsification criterion, RQ-C6 class-level verdict rule, delta=0.10, lambda sweep, aggregate-consistency check. Commit before any runner is written.

**Step 2 — Write `tests/test_structured_candidate_policies.py`.** TDD red phase first. Tests must include:

- Each candidate rule produces decisions that can differ from B1 on at least one constructed input.
- Each candidate rule falls back to B1 behavior when `obs_records` is None.
- Aggregate-consistency check carries forward from C-3a, C-4, C-5.
- Falsification criterion correctly applied per rule.
- Rule 4 (C_zero_only) is operationally identical to `_fail_count_policy`.

**Step 3 — Implement the 3 new policy functions in `doctor/adversarial/problem_class_config.py`.** Add `C_feature_threshold`, `C_majority`, `C_zero_only` alongside the existing 6. Update `LC322_ESTIMATOR_POLICIES` and `LC45_ESTIMATOR_POLICIES` to add the 3 new bindings. All tests green. Commit module + tests together.

**Step 4 — Write runners `runners/run_c6_collapse_lc{322,45}.py`.** For each of the 4 candidate rules, re-run on unperturbed LC322 (and LC45 for stress test) for aggregate-consistency check, then apply each of the 10 C-5 perturbations (P1, P2a-c, P3a-f), then apply the C-5 P4 perturbation (LC45). Commit before execution.

**Step 5 — Execute.** Check aggregate consistency for B1. STOP if any inconsistency. If passes, compute per-rule, per-perturbation D, A, utility gap. Apply per-rule falsification criterion. Apply RQ-C6 class-level verdict rule.

**Step 6 — Write `docs/PHASE_C6_RESULTS.md`.** Per-rule, per-perturbation survival table. Per-rule LC45 result. RQ-C6 class-level verdict. Audit against three failure modes before commit.

**Step 7 — Tag `phase-c6-results`.**

---

## Governance Acknowledgment

C-6 is authorized by Foued override. It adds 3 new estimators (`C_feature_threshold`, `C_majority`, `C_zero_only`) to `problem_class_config.py`, which is a new program. C-1's constraint `"no_new_estimators": true` is acknowledged to be violated by C-6 (as it was by C-4), and the violation is recorded as a Foued override, not a minor constraint relaxation.

C-6 also adds 1 new rule with a 0.5 threshold (Rule 2), which is a pre-declared constant. C-6 does not add a new tunable hyperparameter.

If Foued at any point withdraws the C-6 override, the phase stops. The C-6 spec and freeze remain in the repository as a record of the authorized program.
