# Project Closure — Doctor/Bimaristan

**Closure date:** June 2026
**Closure point:** commit `707121b` on branch `master`
**Repository:** `doctor-workspace-recovered`

---

## Hardening sequence

The project progressed through six phases:

1. **Stage 1–2 (evidence stage 1 + 2):** DOCTOR/BIMARISTAN history reconstruction.
   Exploratory probes and retrospective audits established why a clean budget-matched
   gate was needed. The evidence was contaminated (probes and features not causally
   separated from S_eval) and is not treated as convergent or cumulative proof.

2. **Stage 3 (evidence stage 3):** Midweather-Fingerprint clean gate on LC322.
   Frozen K=15 observation budget, external blind 30-solver S_eval, same-information
   baselines B0–B6, anti-degeneracy checks, decision-utility comparison
   (ACCEPT vs REJECT under decision_loss). Result: FAIL. C ties B1/B2/B3 on
   decision_loss (1.0) and does not strictly improve.

3. **LC45 port:** Generalized kernel applied to LC45 Jump Game II. 6 manifolds,
   9 buggy solver families, 1 survivor. Result: FAIL, 1/9 split, B4 degenerate.
   Bimaristan layer (LC45OracleEvaluator + 38-entry LC45_SYMBOL_REGISTRY) built
   as a self-contained module.

4. **C wiring into LC45 (Week 6):** C_structured_fingerprint added to the LC45
   estimator set using the existing bimaristan layer. C ties B1 on decision_loss.
   Verdict remains FAIL via B4 degenerate.

5. **C feature audit (Week 7):** 10×6 feature table produced. Negative result:
   the only separating feature (`pass_fail_rate`) is equivalent to B1. No
   threshold or combination of features can beat B1 on the LC45 population.

6. **Real benchmark + paper sync (Week 5 + 8):** 30 hand-curated LC322 solvers
   (16/14 split, verdict FAIL). Paper corrections: `:605` degeneracy policy
   fixed, phantom commit `6ca6c28` removed (3 occurrences), Reproducibility Gap
   section documenting 27/3 vs 11/19 vs 16/14 discrepancy, LC45/C/real benchmark
   sections added. `bfs_agrees_rate` encoder artifact fixed; negative result
   confirmed and strengthened.

---

## Central finding

**The structured fingerprint representation does not improve solver accept/reject
decisions over the simplest raw baselines on either problem class tested.**

- **LC322:** C ties B1/B2/B3 on decision_loss (1.0). C's lower RMSE (0.024 vs
  0.030–1.334) is secondary and does not override the primary decision-loss result.
  RMSE would justify C only under a different deployment objective.
- **LC45:** After the encoder fix, the 6-feature vector has one informative
  dimension (`pass_fail_rate`) and five uninformative ones. C cannot differentiate
  from B1 for structural reasons, not measurement artifact reasons.

Both verdicts are FAIL. The central claim is reproducible; the exact population
split is not (27/3 original split is irrecoverable — see Deferred list).

---

## Deferred list (with reasons)

| Item | Status | Reason |
|------|--------|--------|
| ComparabilityContext (cross-problem comparison layer) | Deferred indefinitely | No cross-problem patterns found in the 6-feature vector. The bimaristan layer documents cross-problem transfer decisions per-entry in LC45_SYMBOL_REGISTRY, but a full ComparabilityContext would require problem pairs with shared structure — none were identified. |
| Real LLM benchmark (`experiments/frozen_taxonomy_lc322_real_claude_sonnet_4/`) | Reserved namespace, not pursued | `ANTHROPIC_API_KEY` not set and `anthropic` SDK not installed in the recovery environment. The 30 hand-curated solvers (`pack_source: "hand_curated_real"`) are honest about not being LLM-generated. If the API becomes available, the hand-curated pack can be replaced with a real LLM-generated pack using the same manifest schema and freeze structure. |
| E0/E1/E2 evidence stage artifacts | Irrecoverable | Lost in PhotoRec recovery. The project history is documented in the paper's hardening sequence narrative; the original artifacts are gone. |
| 27/3 original solver split | Irrecoverable, formally documented | The original solver pack that produced the 27/3 split is unrecoverable. The paper's Reproducibility Gap section documents the 27/3 vs 11/19 (reconstructed stub) vs 16/14 (hand-curated real) discrepancy as an irrecoverable evidentiary gap, not a protocol error. |

No remaining known debt.

---

## Final state

- **Tests:** 276 passing (272 prior + 4 new in Week 8)
- **Lockfile:** 94 artifacts, all 3 manifest+freeze pairs validated
- **Paper:** `doctor_bimaristan_scientific_paper.md` — clean, no known uncorrected errors
- **Freezes:** 3 (LC322 stub, LC45, LC322 real) — all validated
- **Code:** `bfs_agrees_rate` encoder fixed, `test_executor.py` debt resolved
- **Reproducibility:** `REPRODUCE.md` covers all three problem-class runs

---

## Final artifact

The paper is the final artifact:

> `doctor_bimaristan_scientific_paper.md`

It contains the full hardening sequence, the central finding, the negative
result, and the documentation of all irrecoverable gaps. The code, tests,
lockfile, and freezes are the reproducible substrate for the paper's claims.

---

## No further work is planned.
