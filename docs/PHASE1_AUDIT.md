# Phase 1 Audit (Cross-Problem Transfer Hypothesis)

**Date:** June 2026
**Trigger document:** `docs/TRANSFER_HYPOTHESIS.md` (revised at commit `7c692e2`)
**Audit kind:** Option B — frozen mapping, calibration gate disabled
**Status:** Phase 1 audit complete; decision pending user review

---

## Scope and interpretation (explicitly tracked caveats)

This audit follows the user-approved option B interpretation of the revised Phase 0 spec (`docs/TRANSFER_HYPOTHESIS.md` at `7c692e2`). Three operational substitutions are in effect:

1. **"Three problems" is a legacy artifact.** Operational system is strictly `LC322 + LC45`. All spec language about "all three problem classes" (lines 65, 146, 185) is treated as non-binding.

2. **Stress-class mapping is heuristic but frozen.** The mapping from probe family to stress class is fixed before the audit runs and is not changed based on results. See "Frozen mapping" section below.

3. **Calibration gate is disabled.** Distribution comparison across problems is undefined when one problem has only 1 ACCEPT-class solver (LC45). The calibration gate as defined in the spec (lines 146-153) is replaced by a weaker feasibility constraint: a stress class is "measurable" in LC45 if and only if (a) ≥1 ACCEPT-class solver and ≥1 REJECT-class solver exist in the LC45 problem AND (b) ≥1 probe in the class. Otherwise the class is "degenerate but not invalidated."

**Non-negotiable:** no probe is reclassified after seeing results. If LC45 is structurally weak in a stress class, that is a result, not a defect.

**Out of scope (per spec line 187-195):** defining new stress classes, introducing new scoring schemes, computing cross-problem transfer statistics, constructing solver packs, building new problem classes, specifying K_min or KS-threshold values, defining the `extremum_type` value vocabulary.

---

## Frozen mapping (binding for this audit)

The mapping from probe family to `(stress_class, extremum_type)` was committed before the audit. It is recorded here for reproducibility. No reclassification was performed.

### LC322 (30 probes, 6 fingerprint axes)

| axis | stress_class | extremum_type | probe count |
|------|--------------|---------------|-------------|
| `magnitude` | `scale` | `large_amount_stress` | 5 |
| `boundary` | `boundary` | `greedy_dp_threshold` | 5 |
| `order` | `monotonicity` | `non_canonical_coin_order` | 5 |
| `reachability` | UNASSIGNED | (excluded) | 5 |
| `transition` | UNASSIGNED | (excluded) | 5 |
| `memoization` | UNASSIGNED | (excluded) | 5 |

### LC45 (30 probes, 6 solver-bug manifolds)

| manifold | stress_class | extremum_type | probe count |
|----------|--------------|---------------|-------------|
| `naive_max_jump_suboptimal` | `monotonicity` | `non_monotonic_max_jump` | 5 |
| `single_large_jump_decoy` | `boundary` | `single_large_decoy` | 5 |
| `naive_max_jump_dead_landing` | `boundary` | `dead_landing` | 5 |
| `greedy_horizon_collapse` | UNASSIGNED | (excluded) | 5 |
| `uniform_jump_array` | UNASSIGNED | (excluded) | 5 |
| `greedy_frontier_valid_no_false_pressure` | UNASSIGNED | (excluded) | 5 |

**Unassigned rationale:**
- **LC322** (`reachability`, `transition`, `memoization`): these axes are LC322-internal solver-bug patterns (BFS reachability cutoff, forward-DP overwrite corruption, memoization MOD-key aliasing) that do not map onto the 3 problem-independent stress classes in the spec. They are not "boundary" cases (the problem has no declared minimum/maximum-amount invariant beyond the 30-probe axis coverage), not "scale" (the magnitude axis is already assigned to scale; the other axes are not magnitude), and not "monotonicity" (LC322's optimal subproblem structure is DP, not monotone DP in the sense the spec requires).
- **LC45** (`greedy_horizon_collapse`, `uniform_jump_array`, `greedy_frontier_valid_no_false_pressure`): these manifolds test greedy-algorithm bug patterns (horizon collapse, uniformity assumptions, frontier validity) that are solver-internal, not problem-input-stress. They are not "boundary" cases (no input-boundary regime is being tested), not "scale" (probe sizes are small, 4-10 elements), and not "monotonicity" violations (the spec's monotonicity stress requires "monotone optimal subproblem structure" with local violation; LC45's optimal subproblem is monotone, but the unassigned manifolds test greedy response to uniform/horizon inputs, not monotone-subproblem violations).

The unassigned categories represent **half of the existing probe set in each problem** (15/30 LC322, 15/30 LC45). The 3 committed stress classes account for the other half. This is a structural finding about the existing probe design relative to the stress-class taxonomy, not a defect of the audit.

---

## Audit procedure

For each of the 3 committed stress classes (`boundary`, `scale`, `monotonicity`), the audit computes three things:

1. **Cross-problem existence**: non-empty in both LC322 and LC45.
2. **Identifiability feasibility**: union of `extremum_type` values across both problems has cardinality ≥ 2. (This is the spec's precondition from line 181.)
3. **LC45 measurability** (replacement for calibration gate): problem has ≥1 ACCEPT and ≥1 REJECT solver AND ≥1 probe in the class in LC45.

A class is **auditable** if all three checks pass. Otherwise the audit labels the class as `degenerate` (measurable fails) or `missing` (no probes in LC45) per the user-approved B interpretation.

**No cross-problem transfer statistics are computed in this audit** (out of scope per spec line 191).

---

## Coverage table

| stress_class | LC322 n | LC45 n | LC322 extremum_types | LC45 extremum_types |
|--------------|---------|--------|----------------------|---------------------|
| `boundary`   | 5       | 10     | `greedy_dp_threshold` | `dead_landing`, `single_large_decoy` |
| `scale`      | 5       | 0      | `large_amount_stress` | (none) |
| `monotonicity` | 5     | 5      | `non_canonical_coin_order` | `non_monotonic_max_jump` |
| UNASSIGNED   | 15      | 15     | (3 families: `forward_dp_overwrite`, `memo_cache_aliasing`, `reachability_counterfactual`) | (3 families: `frontier_greedy_valid`, `horizon_collapse`, `uniform_array`) |

**Total LC322 = 30 probes; total LC45 = 30 probes; 15 unassigned per problem.**

---

## Audit results table

| class | cross-problem exists | identif feasible | LC45 measurability | notes |
|-------|----------------------|-------------------|---------------------|-------|
| `boundary` | YES | YES (cardinality 3) | measurable | 5+10 probes; LC45 ACCEPT-class solver_001; LC45 has 9 REJECT solvers |
| `scale`    | NO  | NO (cardinality 1) | degenerate_no_probes | LC322 has 5 `large_amount_stress` probes; LC45 has 0 scale probes |
| `monotonicity` | YES | YES (cardinality 2) | measurable | 5+5 probes; same solver pool |

---

## Solver pool structural facts

| problem | ACCEPT n | REJECT n | ACCEPT ids |
|---------|----------|----------|------------|
| LC322 | 11 | 19 | solver_001..solver_005, solver_019..solver_021, solver_025..solver_027 |
| LC45 | 1 | 9 | solver_001 only |

LC45 has only 1 ACCEPT-class solver. This is the structural reason the calibration gate is disabled in this audit (distribution comparison undefined for n=1). It is **not** a defect of LC45; it is a fact about the current solver pack.

---

## Summary

| stress_class | LC322 probes | LC45 probes | auditable? | reason if not |
|--------------|--------------|-------------|------------|---------------|
| `boundary`     | 5 | 10 | **YES** | — |
| `scale`        | 5 | 0  | NO | LC45 has no scale probes; LC322 alone |
| `monotonicity` | 5 | 5  | **YES** | — |

**Auditable stress classes: 2 of 3** (`boundary`, `monotonicity`).
**Degenerate: 1 of 3** (`scale` — LC45 has no probes in this class).

---

## Decision-rule application (with substitution)

The spec's decision rule (lines 199-201) is gated on the calibration gate:

> If at least 2 of 3 stress classes pass the calibration gate with at least 3 probes in each of LC322 and LC45: Phase 3 build cost is moderate; proceed to Phase 2.
> If only 1 stress class passes: Phase 3 cost includes adding probes to existing problems; flag this in the audit and ask whether to proceed.
> If 0 stress classes pass: Phase 3 cost is high; the plan says to revisit the decision to proceed.

In this audit, the calibration gate is **disabled** and replaced with the auditable predicate (cross-problem existence + identif feasibility + LC45 measurability). Applying the decision rule with this substitution:

> 2 of 3 auditable (boundary, monotonicity) → "Phase 3 build cost moderate; proceed to Phase 2."

**This is a substitution under option B, not a literal application of the spec rule.** The spec rule as written requires the calibration gate, which is disabled. The substituted result should be read as: "under the constraints of option B, 2 of 3 stress classes are structurally auditable; the spec's proceed-to-Phase-2 trigger would be met if the calibration gate were applied as a structural-auditability check."

---

## Structural findings (not defects)

1. **LC45 has no scale probes.** The 6 LC45 manifolds were designed around solver-bug patterns (greedy horizons, uniform arrays, frontier pressure), not around input-magnitude regimes. There is no scale dimension in the LC45 probe set. This is a structural fact about the existing probe design relative to the 3 stress classes, not an audit failure.

2. **Half of each problem's probe set is unassigned under the 3 stress classes.** LC322 has 3 fingerprint axes (`reachability`, `transition`, `memoization`) that do not map to the committed stress classes. LC45 has 3 manifolds (`greedy_horizon_collapse`, `uniform_jump_array`, `greedy_frontier_valid_no_false_pressure`) that do not map. The committed 3 stress classes cover the "natural" computational stressors (input boundary, input scale, monotonicity) but not all solver-bug patterns. This is a structural mismatch between the existing probe design (problem-internal, solver-bug-focused) and the spec's stress-class taxonomy (problem-independent, computational-stressor-focused).

3. **LC45 has only 1 ACCEPT-class solver.** The solver pack is heavily REJECT-skewed (1/9 split). This is a structural fact about the current pack, not a defect. It does, however, make the calibration gate (distribution comparison) undefined for LC45, which is why option B disables it.

4. **The unassigned 30 probes (15 per problem) are excluded from this audit.** They are not reclassified to "fix" the audit. If the user wants to extend the stress-class taxonomy to cover them, that is a Phase 0 re-revision, not a Phase 1 reclassification.

---

## What is NOT decided by this audit

- The transfer test itself is **not** run in Phase 1. The spec defers Phase 4 transfer computation to a later stage.
- The 2-of-3 result does **not** authorize building a 3rd problem class. The spec's "Phase 2" is third-problem-class selection, which is moot in the operational 2-problem system.
- The 2-of-3 result does **not** authorize running the cross-problem rank test on the 2 auditable stress classes. That would be a Phase 2-3 transition, which requires user direction.

---

## Next steps (require user direction)

Three paths are available; this audit does not choose between them.

**(A) Stop the program.** The 1-of-3 degenerate (scale) result is a structural negative. Transfer as a cross-problem phenomenon is not testable in the current corpus without expanding either the stress-class taxonomy or the problem class set. The framework's structural-property claims remain K-local to each problem, consistent with the closure of `project-closure-003`.

**(B) Run the rank test on the 2 auditable classes (boundary, monotonicity) using the existing LC322 and LC45 probe sets and solver packs.** This is a partial transfer test: 2 problems × 2 stress classes. The rank test would compute `Δ(P, d)` for each problem × stress class combination and check sign consistency. This is a restricted version of the spec's transfer test. The user must decide whether 2 problems is enough for a sign-consistency check (the spec was written for 3 problems; 2 problems gives a single Δ sign comparison, which is not a statistical sign-consistency test but a single observation).

**(C) Expand the probe set.** Add scale probes to LC45 (e.g., `nums` lists with progressively larger jump ranges) to make all 3 stress classes auditable. This requires re-doing the LC45 probe construction, which is out of Phase 1 scope per the spec. It would also require re-freezing the LC45 probe index and re-running the gate.

---

## Audit artifacts

- Audit script: `phase1_audit.py` (reproducibility — applies frozen mapping, computes coverage, identifiability, measurability)
- Summary JSON: `phase1_audit_summary.json` (machine-readable output of the audit)
- Source data: `data/midweather_fingerprint_lc322_probe_index.json`, `data/midweather_fingerprint_lc45_probe_index.json`, `data/midweather_fingerprint_lc322.json`, `data/midweather_fingerprint_lc45.json`

---

## Spec trigger status

Per `docs/TRANSFER_HYPOTHESIS.md` line 6:

> **Trigger for proceeding past Phase 1:** Phase 1 audit shows candidate stress classes auditable in current corpus under the strict definition, OR a clear plan for adding them is committed.

This audit shows **2 of 3 candidate stress classes auditable** under the option B definition (which is a relaxed version of the spec's strict definition, with the calibration gate replaced by an auditable predicate). The strict definition (with calibration gate) is not applicable because LC45 n=1 ACCEPT makes the gate undefined. The trigger is **partially met** — auditable in current corpus, but not under strict definition.
