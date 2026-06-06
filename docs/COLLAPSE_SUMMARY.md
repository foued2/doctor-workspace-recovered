# Collapse Summary (Single-Layer)

This is a single-layer summary of established claims and closure findings. It is observational, code-anchored, and does not introduce new structural claims. It is not a theory, not a taxonomy, not a framework, not a research paper. It is a re-expression of the existing record under `project-closure-004`.

## Established Invariants (per `DOCTOR_OPERATING_PROTOCOL.md` §10)

Only three claims survive both CI suites as of 2026-06-02:

1. **Monotonicity**: P4 refines P3 refines P2 refines P1 in both LC45 and LC322.
2. **Survivor Separability**: The SURVIVOR remains distinguishable from all BUGGY solvers under P1 and P3 in both problems.
3. **Finite-Sample Projection Stability**: Under fixed seed sampling, each solver has a stable projection signature (no observed stochastic drift at n=1000).

All other claims are interpretive load and are not established.

## Closure Findings (per `docs/PROJECT_CLOSURE.md` addendum at `project-closure-004`)

- **Cross-problem transfer hypothesis**: closed-not-supported. The transfer-hypothesis Phase 1 audit (`docs/PHASE1_AUDIT.md`, `de12b3e`) ran under option B (frozen mapping, calibration gate disabled). 2 of 3 auditable.
- **LC322 verdict (Midweather-Fingerprint clean gate, Evidence Stage 3)**: FAIL. C_structured_fingerprint decision_loss = 1.0 ties B1/B2/B3. C does not strictly beat every same-observation baseline. RMSE (0.024) is secondary.
- **LC45 verdict**: FAIL, 1/9 split. B4 degenerate. C ties B1/B2/B3 on decision_loss (all 0.0).
- **Path A chosen at closure**: stop. The 2-class rank test is recorded as available but not pursued (would be hypothesis downgrade, not continuation).
- **Original freeze commit**: unrecoverable (PhotoRec loss); reconstructed at `c3db242`.

## Audit Status (per `docs/PHASE1_AUDIT.md`)

| Stress axis group | LC322 probes | LC45 probes | Status |
|---|---|---|---|
| boundary | 5 (greedy_dp_threshold) | 10 (single_large_jump_decoy + naive_max_jump_dead_landing) | auditable in both |
| scale | 5 (large_amount_stress) | 0 (no large_amount_stress manifold in LC45) | auditable in LC322, degenerate_no_probes in LC45 |
| monotonicity | 5 (non_canonical_coin_order) | 5 (naive_max_jump_suboptimal) | auditable in both |
| unmapped | 15 (reachability, transition, memoization) | 15 (greedy_horizon_collapse, uniform_jump_array, greedy_frontier_valid_no_false_pressure) | not classified by Phase 0 mapping |

15 probes remain unassigned in each problem. No reclassification was performed during the audit.

## Non-Transferable Findings (Recorded Under §7 Hard Stop)

- Solver sets differ: LC322 has 30 solvers (solver_001..solver_030, external blind pack); LC45 has 10 solvers (1 survivor + 9 buggy, external baseline pack).
- Probe distributions differ: LC45 has no `large_amount_stress` manifold; LC322 has 5 `large_amount_stress` probes.
- Manifold/axis definitions differ: LC322 uses 6 fingerprint axes; LC45 uses 6 manifolds. The cross-problem vocabulary in `LC45_SYMBOL_REGISTRY` (5 CROSS_PROBLEM entries) is a documentation mapping, not an invariance claim.
- Cross-problem factorization is not explicit.

> Pattern exists (FAIL in both, B4 degenerate in both, C-ties-B1/B2/B3 in both) but the cross-K correspondence is not identifiable under current construction.

## What This Summary Is Not

- Not a research paper generator.
- Not a theory of computation.
- Not a general benchmarking framework.
- Not a model of "algorithm difficulty."
- Not a new structural claim.
- Not a transfer claim.
- Not an invariance claim.

It is a re-expression of the existing observational record under `project-closure-004`, formatted as a single-layer summary of established claims and closure findings.
