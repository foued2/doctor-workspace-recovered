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

| Item                                                                           | Status                             | Reason                                                                                                                                                                                                                                                                                                                                                        |
|--------------------------------------------------------------------------------|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ComparabilityContext (cross-problem comparison layer)                          | Deferred indefinitely              | No cross-problem patterns found in the 6-feature vector. The bimaristan layer documents cross-problem transfer decisions per-entry in LC45_SYMBOL_REGISTRY, but a full ComparabilityContext would require problem pairs with shared structure — none were identified.                                                                                         |
| Real LLM benchmark (`experiments/frozen_taxonomy_lc322_real_claude_sonnet_4/`) | Reserved namespace, not pursued    | `ANTHROPIC_API_KEY` not set and `anthropic` SDK not installed in the recovery environment. The 30 hand-curated solvers (`pack_source: "hand_curated_real"`) are honest about not being LLM-generated. If the API becomes available, the hand-curated pack can be replaced with a real LLM-generated pack using the same manifest schema and freeze structure. |
| E0/E1/E2 evidence stage artifacts                                              | Irrecoverable                      | Lost in PhotoRec recovery. The project history is documented in the paper's hardening sequence narrative; the original artifacts are gone.                                                                                                                                                                                                                    |
| 27/3 original solver split                                                     | Irrecoverable, formally documented | The original solver pack that produced the 27/3 split is unrecoverable. The paper's Reproducibility Gap section documents the 27/3 vs 11/19 (reconstructed stub) vs 16/14 (hand-curated real) discrepancy as an irrecoverable evidentiary gap, not a protocol error.                                                                                          |

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

---

# Project Closure Addendum — Meta-Analysis at `project-closure-003`

**Addendum date:** June 2026
**Re-tag point:** commit adding this addendum
**Status:** project remains closed; addendum records meta-analytic findings

---

## Context

After `project-closure-001` (commit `707121b`) and `project-closure-002` (commit `c4b6fa9`), a meta-analytic exchange about the paper's framing produced findings that need to be recorded in the closure record. The exchange did not do new empirical work; it analyzed the paper's structure, the corpus's coverage, and the gap between what the within-problem findings show and what a reader might mistakenly infer from them.

This addendum does not reopen the project. It records what the meta-analysis revealed, refines the framing of the within-problem findings, and states the trigger conditions under which reopening would be warranted.

---

## Finding 1: The paper is A-framed with substantial B-content the framing refuses to develop

The paper (`doctor_bimaristan_scientific_paper.md`, 1406 lines) is structurally a decision-utility test (Evidence Stage 3 FAIL on LC322). It contains substantial cross-problem and cross-evidence-stage material:

- E0 (representation-sensitivity, LC322) and E1 (within-K conditioning, LC560) as Evidence Stage 1
- The LC45 generalization (Stage 2-equivalent) and its C feature audit
- The Midweather retrospective audit (Evidence Stage 2) and the clean gate (Evidence Stage 3)

This material is positioned in the paper as exploratory/diagnostic context or as scope-bounded supporting evidence, not as convergent or cumulative proof. The hardening sequence table (paper line 793) explicitly states: "A reader should read the hardening sequence as methodological narrative, not an accumulating proof."

A C-framing — "this is a measurement-infrastructure project whose target is an unknown natural kind; the FAIL is the closure point of the evaluator-utility claim; the cross-problem material is honest reporting of what the infrastructure can and cannot detect" — is more accurate about what the project was, but the paper as written stays A-framed.

This is not an error in the paper. The A-framing is internally consistent with the stated research question. The C-framing would be a deliberate reframing, not a correction.

## Finding 2: The cross-problem transfer question is not answered by the existing corpus

Two within-problem findings are the strongest evidence in the corpus that "aggregate pass/fail volume is the load-bearing separator":

- **`docs/LC45_C_POLICY_FINDING.md` (Week 7, encoder-fixed in Week 8)**: the 6 features in `lc45_raw_tensor_encoder` produce clean separation only on `pass_fail_rate`; the other 5 features are either constant (zero variance) or overlap with the survivor. A threshold or combination policy on the 6 features cannot beat B1 on the LC45 1/9 population.
- **`docs/H1A_FALSIFICATION.md` (after `project-closure-002`)**: the 6 family-conditional pass/fail rates on LC322 all overlap at 1.00 in the ACCEPT class; aggregate `pass_fail_rate` already produces clean separation (ACCEPT min 0.87 > REJECT max 0.80); no family-conditional rate improves on aggregate.

Both findings are mutually reinforcing on a structural property: **aggregate volume of failure is the load-bearing separator; structured fingerprint dimensions describe *how* a solver fails but not *whether* it fails.**

Neither finding answers the cross-problem transfer question. The two problems tested have different structural properties (LC322 is DP/non-monotonic, LC45 is greedy/monotonic), and their fingerprint axes were designed independently for each problem. The consistency of the within-problem finding is directionally suggestive that "aggregate-volume dominance" may be a general property of the fingerprint framework. But it could equally be that both problems happened to share a structural feature that suppresses structured-dimension load-bearingness, and a third problem class would not. The corpus has 2 fully-built problem classes; the third problem class needed to test cross-problem transfer is not in the corpus.

A previous version of the meta-analysis described the H1a and LC45 audit findings as "directionally negative on cross-problem transfer." That framing was incorrect. The two findings are within-problem; their consistency is suggestive but not conclusive on transfer. The corrected framing is recorded here.

## Finding 3: Three utility directions are real but not pursued

Three directions for genuine utility that do not depend on the FAIL verdict on decision-utility were identified in the meta-analysis:

1. **Solver triage at scale**: a perturbation framework on top of binary pass/fail that produces richer signals for platforms with millions of submissions (LeetCode, Codeforces, competitive-programming corpora).
2. **Problem statement quality evaluation**: a problem statement that generates systematically different collapse patterns across solver populations is potentially a badly specified problem; the perturbation framework could automate problem-statement auditing.
3. **Curriculum and difficulty sequencing**: if collapse patterns are even partially stable across problems, sequence problems by failure mode rather than by topic.

Each direction requires cross-problem evidence the corpus does not have. None are concretely pursued in the current closed state. Each is a real candidate for a future research program but is not a present obligation.

---

## Decision triggers (options remain open)

The four options raised in the meta-analysis remain open. The project does not commit to any of them in this addendum.

- **(a) Reopen for new problem classes**: trigger condition is that any of the three utility directions becomes worth pursuing concretely. The entry test in that case is a single third problem class with a structurally different design (e.g., not DP or greedy, perhaps a graph/search problem or a numeric problem). Do not build speculatively. If the trigger condition is not met, option (a) does not activate.
- **(b) Re-tag with this addendum**: this is what the addendum is. Done as part of the meta-analysis. No new empirical work.
- **(c) Paper reframe to C-framing**: this is a paper-editing task that does not require reopening code. The data does not change; the framing does. Not committed to in this addendum; left as a future decision.
- **(d) Leave closed**: the default state if no trigger condition is met. The project remains at `project-closure-003`.

---

## What this addendum does

- Records the meta-analysis findings in the closure document.
- Refines the framing of the H1a and LC45 audit findings: they are mutually reinforcing within-problem findings, not cross-problem evidence.
- Names the genuine open question: does any collapse dimension (e.g., "aggregate-volume dominance", "family-conditional structure of failure") transfer across problems without being forced.
- States the trigger conditions under which reopening would be warranted.

## What this addendum does not do

- Does not claim that the corpus points negative on cross-problem transfer. The within-problem findings are consistent with that direction but do not establish it.
- Does not commit to reopening. The trigger conditions are stated but not activated.
- Does not modify the paper text. The paper is sealed as the final artifact of `project-closure-001` and `project-closure-002`.
- Does not modify any test, freeze, or code artifact. The empirical state of the repo is unchanged.
