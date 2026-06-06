# Design Critique Layer (Observational)

This is an observational critique of why the existing LC322/LC45 evaluation architecture behaves as observed. It is purely observational: it records design choices and their consequences on measured K. It does not introduce new primitives, new stress-class design, new transfer claims, or new theory. It is bounded to the recorded record under `project-closure-004`.

## 1. Why the LC322 Verdict is FAIL Despite a Non-Trivial 11/19 Split

**Observed under K_322 (reconstructed_stub, `MIDWEATHER_FINGERPRINT_GATE_LC322_FREEZE.json`):**
- ACCEPT/REJECT split: 11/19
- B1_count, B2_calibrated_count, B3_raw_pf_vector: decision_loss = 1.0 (1 wrong accept, 0 wrong rejects)
- C_structured_fingerprint: decision_loss = 1.0 (1 wrong accept, 0 wrong rejects)
- C RMSE (secondary) = 0.024 (best); B1, B3 RMSE = 0.030
- B0, B5, B6: all-ACCEPT (degenerate)
- B4: all-REJECT (degenerate; triggers FAIL before C-vs-baselines comparison)
- Verdict: FAIL

**Design observation (no theory, no transfer):**
The declared protocol rule is strict improvement on primary utility. Ties are FAIL. The 11/19 split is a population statistic, not the decision utility. C's additional structured information (axis metadata, deformation labels, pair flips) does not improve the ACCEPT/REJECT decision at the declared threshold (failure_threshold=0.05, minimum_accept_rate=0.2). On the tested population, C ties B1's pass/fail count on decision_loss.

C's lower RMSE shows that the structured representation retained predictive signal. Under a continuous failure-rate estimation objective, an evaluator would prefer C. Under the declared ACCEPT/REJECT decision objective, C ties the simplest baselines.

## 2. Why LC45 Has Scale-Axis Probe Group Degeneracy

**Observed under K_45 (`MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json`):**
- ACCEPT/REJECT split: 1/9
- 1 survivor: `lc45_bfs_depth_cutoff` (passes all 30 probes)
- 9 buggy solvers across 4 families (Greedy 4, Reachability confusion 2, Bounded/incomplete 2, Off-by-one 1)
- B1, B2, B3, C: decision_loss = 0.0 on this population
- B4: all-REJECT (degenerate; triggers FAIL)
- Verdict: FAIL

**Audit observation (option B, frozen mapping):**
- Scale axis probe group: 0 probes in LC45 (no `large_amount_stress` manifold). Degenerate_no_probes.
- LC45 has 6 manifolds: `naive_max_jump_suboptimal`, `single_large_jump_decoy`, `greedy_horizon_collapse`, `naive_max_jump_dead_landing`, `uniform_jump_array`, `greedy_frontier_valid_no_false_pressure`. None is `large_amount_stress`.

**Design observation (no theory):**
LC45 has 0 probes in the scale axis probe group. The scale axis probe group is K-anchored to LC322's problem statement; the Phase 0 mapping table recorded `scale=large_amount_stress` for LC322, and no scale probe group is defined for LC45. The scale axis probe group is not a cross-problem primitive.

## 3. Why B4 (raw_full_tensor) is Degenerate in Both K

**Observed:**
- B4_raw_full_tensor: all-REJECT in LC322 (27 wrong rejects, RMSE 1.334) and all-REJECT in LC45
- B0, B5, B6: all-ACCEPT in LC322 (also degenerate under the anti-degeneracy check)
- The anti-degeneracy guard (`degenerate_all_reject=True`) triggers FAIL before the C-vs-baselines comparison is reached

**Design observation:**
B4 receives the full observation tensor (pass_fail + deformation + axis + family + paired + invariant) for all 15 observed probes. On the tested K, B4 is observed to be all-REJECT in both LC322 and LC45. The protocol's anti-degeneracy check catches this and triggers FAIL before the C-vs-baselines comparison is reached. B0, B5, B6 are all-ACCEPT in LC322 and are also caught by the anti-degeneracy check.

## 4. Why C Ties B1/B2/B3 in Both K

**Observed:**
- C_structured_fingerprint decision_loss = B1_count = B2_calibrated_count = B3_raw_pf_vector in both LC322 (1.0) and LC45 (0.0).
- The C policy in both K is `_fail_count_policy` (ACCEPT iff obs_fails == 0), the same policy as B1.

**Design observation:**
C's structured features are derived from the same observations as B1's pass/fail count. C's policy is `_fail_count_policy`, the same as B1's. On the tested K, the pass/fail count (B1) and the structured features (C) produce equal decision_loss. C's additional structure does not improve decision_loss over B1's pass/fail count on the tested K.

The LC45 feature audit (`docs/LC45_C_POLICY_FINDING.md`) found that the only separating features in `lc45_raw_tensor_encoder` are `pass_fail_rate` and `bfs_agrees_rate`, which are informationally identical — the encoder's `bfs_agrees_count` compares `candidate_output == expected_output`, the same condition as `pass_fail`. A threshold on `pass_fail_rate` cannot beat B1: T=1.0 is equivalent to B1; T<1.0 is weaker; T>1.0 is impossible. No combination of the other 4 features (which either overlap with the survivor or are constant probe properties) can beat B1 either.

## 5. Why the LC45 Bimaristan Layer's Inter-Problem Vocabulary Does Not Constitute Transfer

**Observed in `LC45_SYMBOL_REGISTRY` (463 lines, 38 entries):**
- 5 CROSS_PROBLEM entries, listed in the CROSS_PROBLEM category
- Each CROSS_PROBLEM entry documents a transfer decision: "allowed", "disallowed", or "context-dependent"

**Design observation:**
The CROSS_PROBLEM entries document whether a symbol's transfer decision is "allowed", "disallowed", or "context-dependent" between LC45 and LC322. They do not assert that the symbol's behavior is preserved across K. They do not assert that the symbol's discriminative power transfers. They are a vocabulary mapping, not an invariance claim.

The 5 CROSS_PROBLEM entries were used during LC45 manifold construction to prevent the `multiset_invariant` incident (which established that validity requires a provable structural argument, not just an operator name). They are documentation of transfer decisions, not evidence of cross-problem transfer.

## What This Critique Is Not

- Not a research paper generator.
- Not a theory of computation.
- Not a general benchmarking framework.
- Not a model of "algorithm difficulty."
- Not a new structural claim.
- Not a transfer claim.
- Not an invariance claim.
- Not a "why the architecture cannot" claim — only "under K, the architecture produced this outcome."

It is a re-expression of the existing observational record under `project-closure-004`, formatted as a critique of recorded design choices and their measured consequences.
