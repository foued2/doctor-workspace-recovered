commit 18d886d159653fa5a0c31a5c9147b4f43ac9a76b
Author: Doctor Agent <doctor-agent@local>
Date:   Tue Jun 9 23:39:30 2026 +0100

    paper-conclusion-rewrite-conditional-empirical-framing

diff --git a/doctor_bimaristan_scientific_paper.md b/doctor_bimaristan_scientific_paper.md
index 100d576..bfe01cf 100644
--- a/doctor_bimaristan_scientific_paper.md
+++ b/doctor_bimaristan_scientific_paper.md
@@ -9,7 +9,14 @@
 
 ## Abstract
 
-This paper evaluates whether a structured behavioral fingerprint estimator (C_genuine) improves accept/reject decision utility over a failure-count baseline (B1) when applied to algorithmic solver populations on LeetCode problems. Across the two evaluated problem classes ÔÇö LC322 (Coin Change) and LC3946 ÔÇö C_genuine shows ╬╗-dependent performance relative to B1 on the tested solver populations: negative utility gap at low reject-cost weights, positive and increasing gap at high reject-cost weights, with sign-flip behavior consistent across both populations. These results are conditional on the specific solver distributions tested; the generator populations produced a small number of distinct behavioral regimes, limiting interpretation to the observed support.
+This paper evaluates whether a structured behavioral fingerprint estimator (C_genuine) improves accept/reject
+decision utility over a failure-count baseline (B1) when applied to algorithmic solver populations on LeetCode
+problems. Across the two evaluated problem classes ÔÇö LC322 (Coin Change) and LC3946 ÔÇö C_genuine shows
+╬╗-dependent performance relative to B1 on the tested solver populations: negative utility gap at low
+reject-cost weights, positive and increasing gap at high reject-cost weights, with sign-flip behavior
+consistent across both populations. These results are conditional on the specific solver distributions tested;
+the generator populations produced a small number of distinct behavioral regimes, limiting interpretation to
+the observed support.
 
 ---
 
@@ -824,17 +831,17 @@ all estimators receive identical O_obs).
 
 **Layer A observation:**
 
-| Estimator                | Decision Loss | Wrong Accepts | Wrong Rejects | Accept Rate | Degenerate |
-|--------------------------|:-------------:|:-------------:|:-------------:|:-----------:|:----------:|
-| B0_prior                 |      15.0     |      15       |       0       |     1.0     | all-ACCEPT |
-| B1_count                 |       1.0     |       0       |       1       |    0.467    |            |
-| B2_calibrated_count      |       1.0     |       0       |       1       |    0.467    |            |
-| B3_raw_pf_vector         |       1.0     |       0       |       1       |    0.467    |            |
-| B4_raw_full_tensor       |      15.0     |       0       |      15       |     0.0     | all-REJECT |
-| B5_nearest_neighbor      |      15.0     |      15       |       0       |     1.0     | all-ACCEPT |
-| B6_regularized_raw_tensor|      15.0     |      15       |       0       |     1.0     | all-ACCEPT |
-| C_structured_fingerprint |       1.0     |       0       |       1       |    0.467    |            |
-| **C_genuine**            |     **0.0**   |     **0**     |     **0**     |   **0.500** |            |
+| Estimator                 | Decision Loss | Wrong Accepts | Wrong Rejects | Accept Rate | Degenerate |
+|---------------------------|:-------------:|:-------------:|:-------------:|:-----------:|:----------:|
+| B0_prior                  |     15.0      |      15       |       0       |     1.0     | all-ACCEPT |
+| B1_count                  |      1.0      |       0       |       1       |    0.467    |            |
+| B2_calibrated_count       |      1.0      |       0       |       1       |    0.467    |            |
+| B3_raw_pf_vector          |      1.0      |       0       |       1       |    0.467    |            |
+| B4_raw_full_tensor        |     15.0      |       0       |      15       |     0.0     | all-REJECT |
+| B5_nearest_neighbor       |     15.0      |      15       |       0       |     1.0     | all-ACCEPT |
+| B6_regularized_raw_tensor |     15.0      |      15       |       0       |     1.0     | all-ACCEPT |
+| C_structured_fingerprint  |      1.0      |       0       |       1       |    0.467    |            |
+| **C_genuine**             |    **0.0**    |     **0**     |     **0**     |  **0.500**  |            |
 
 **Layer B $\delta_{3946}$:**
 
@@ -859,20 +866,20 @@ A C-5 perturbation analysis tests whether the C-4 result survives protocol pertu
 
 **Perturbation types tested:**
 
-| Perturbation | Type | Description | Gap | Survives? |
-|:-------------|:-----|:------------|:---:|:---------:|
-| P1a | baseline | reference (B=15, threshold=0.05) | 1.0 | yes |
-| P1b | threshold_shift | threshold=0.10 | 1.0 | yes |
-| P1c | threshold_shift | threshold=0.20 | 1.0 | yes |
-| P2a | subsample | drop 5 solvers (indices 0-4) | 1.0 | yes |
-| P2b | subsample | drop 5 solvers (indices 25-29) | 1.0 | yes |
-| P2c | subsample | drop 5 solvers (mixed) | 1.0 | yes |
-| P3a | family_knockout | remove poset_universal_source probes | 1.0 | yes |
-| P3b | family_knockout | remove poset_chain probes | 1.0 | yes |
-| P3c | family_knockout | remove poset_antichain probes | 1.0 | yes |
-| P3d | family_knockout | remove poset_lattice_boolean probes | 1.0 | yes |
-| P3e | family_knockout | remove poset_lattice_two_prime probes | 0.0 | **no** |
-| P3f | family_knockout | remove poset_isolated probes | 1.0 | yes |
+| Perturbation | Type            | Description                           | Gap | Survives? |
+|:-------------|:----------------|:--------------------------------------|:---:|:---------:|
+| P1a          | baseline        | reference (B=15, threshold=0.05)      | 1.0 |    yes    |
+| P1b          | threshold_shift | threshold=0.10                        | 1.0 |    yes    |
+| P1c          | threshold_shift | threshold=0.20                        | 1.0 |    yes    |
+| P2a          | subsample       | drop 5 solvers (indices 0-4)          | 1.0 |    yes    |
+| P2b          | subsample       | drop 5 solvers (indices 25-29)        | 1.0 |    yes    |
+| P2c          | subsample       | drop 5 solvers (mixed)                | 1.0 |    yes    |
+| P3a          | family_knockout | remove poset_universal_source probes  | 1.0 |    yes    |
+| P3b          | family_knockout | remove poset_chain probes             | 1.0 |    yes    |
+| P3c          | family_knockout | remove poset_antichain probes         | 1.0 |    yes    |
+| P3d          | family_knockout | remove poset_lattice_boolean probes   | 1.0 |    yes    |
+| P3e          | family_knockout | remove poset_lattice_two_prime probes | 0.0 |  **no**   |
+| P3f          | family_knockout | remove poset_isolated probes          | 1.0 |    yes    |
 
 **C-5 verdict:** PARTIALLY_SURVIVES (10/11 perturbations survive, 1 collapse).
 
@@ -961,11 +968,11 @@ sequence as methodological narrative, not an accumulating proof.
 The paper tests the C_genuine estimator across three problem classes under comparable frozen protocols.
 The per-problem C-4 results and C-5 perturbation survival are:
 
-| Problem | C-4 result | C-5 survival | Signal family | Population split |
-|---------|-----------|-------------|---------------|------------------|
-| LC322   | POSITIVE  | 6/11        | large_amount_stress | 27 ACCEPT / 3 REJECT |
-| LC3946  | POSITIVE  | `C_genuine = 0.0 vs B1 = 1.0, gap = 1.0, C_genuine strictly beats B1` | 10/11 | 15 ACCEPT / 15 REJECT |
-| LC743   | NEGATIVE (gap=0) | not run | N/A | 1 ACCEPT / 29 REJECT |
+| Problem | C-4 result       | C-5 survival                                                          | Signal family       | Population split      |
+|---------|------------------|-----------------------------------------------------------------------|---------------------|-----------------------|
+| LC322   | POSITIVE         | 6/11                                                                  | large_amount_stress | 27 ACCEPT / 3 REJECT  |
+| LC3946  | POSITIVE         | `C_genuine = 0.0 vs B1 = 1.0, gap = 1.0, C_genuine strictly beats B1` | 10/11               | 15 ACCEPT / 15 REJECT |
+| LC743   | NEGATIVE (gap=0) | not run                                                               | N/A                 | 1 ACCEPT / 29 REJECT  |
 
 **Interpretation:** LC322 and LC3946 both show positive C-4 results with C_genuine strictly
 improving over B1 on decision_loss. Both survive partial C-5 perturbation analysis. The signal
@@ -1231,7 +1238,8 @@ verification dependency that bounds the independence of the result.
 
 LC743 specs (problem definition, probe families, honest classifier, C-4 protocol) are cited as
 methodology portability evidence: the LC322 protocol was adapted to a structurally different problem
-class. Specs are citable. Execution unverified. Execution results are not used for any claim. Two contamination events during LC743 development
+class. Specs are citable. Execution unverified. Execution results are not used for any claim. Two
+contamination events during LC743 development
 prevent trust in the execution output: (1) adaptive parameter tuning during C-4 runner iteration
 (p-hacking on observed set size, identified and corrected by freezing the protocol before rerun), and (2) a
 circular classifier in an earlier run that referenced oracle metadata. The frozen-protocol C-4 rerun
@@ -1357,111 +1365,32 @@ conditional estimator behavior under the tested populations and ╬╗ values, nothi
 
 # Conclusion
 
-This paper presents a hardening sequence across three evidence stages, tested across three problem classes
-(LC322, LC3946, LC743), ending in mixed results: one clean negative case, one positive replication, and
-one unverified negative.
-
-**Evidence Stages 1--2 (exploratory/contaminated background):** The earlier DOCTOR/BIMARISTAN experiments
-(Stages 1--2) motivated why causal separation and same-information baselines are necessary. No clean claim is
-made
-from these stages; they are methodological background only. See Appendix B for full detail.
-
-**Evidence Stage 3 (clean gate, LC322 main result):** The Midweather-Fingerprint gate tested structured
-fingerprint features against same-observation baselines B0--B6 under a frozen observation budget ($B=15$),
-external blind S_eval (30 solvers, EXTERNAL_BLIND_PACK certification), and ACCEPT/REJECT decision utility.
-All protocol guards passed.
-
-Result: FAIL. C_structured_fingerprint ties B1/B2/B3 on decision_loss (1.0). The protocol requires strict
-improvement on the primary utility metric. RMSE improvement (secondary) does not override.
-
-**LC3946 positive replication:** Under the same frozen protocol structure, C_genuine achieves
-decision_loss=0, strictly improving over B1 (decision_loss=1.0) with gap=1.0. C-5 perturbation
-survival: 10/11. The signal family is poset_lattice_two_prime. This demonstrates that the honest
-classifier can improve decision utility when the solver population has balanced failure-class
-diversity and the probe index contains exploitable structural families.
-
-**LC743 (specs-only portability evidence):** The LC322 protocol was adapted to a structurally
-different problem class (connectivity stress, 4 failure directions, 24 test cases). Specs are
-cited as methodology portability evidence. Execution is unverified due to model reliability
-concerns (two contamination events during development). The frozen-protocol C-4 rerun yielded
-gap=0 (FAIL), but the result is not used for any claim.
-
-The paper's contribution is a clean, scoped negative case study for LC322, a positive replication
-on LC3946, and a documented portability attempt on LC743:
-
-> Under the LC322 gate, the tested fingerprint representation did not strictly improve the predeclared
-> ACCEPT/REJECT decision loss over the best raw baselines; under the LC3946 gate, C_genuine did strictly
-> improve; under the LC743 gate, the result is unverified. The cross-problem pattern is that C_genuine
-> improves when the solver population has balanced failure-class diversity and the probe index contains
-> problem-specific structural families that the directional classifier can exploit.
-
-The LC3946 result prevents the paper from claiming that fingerprint-based evaluation generally fails.
-The correct interpretation is problem-dependent: C_genuine's value depends on population balance
-and probe-family discriminability. The LC322 negative result is a floor-limited utility failure;
-the LC3946 positive result is a demonstration of conditional utility.
-
-A deliberately balanced or adversarially selected solver pack could test a different hypothesis about when
-fingerprints become useful. The LC3946 result is exactly that test: a balanced population where C_genuine
-demonstrates decision utility. This does not rescue the LC322 result; it contextualizes it.
-
-No claim extends beyond the observed K-space without independent revalidation under $K'$. The paper does not
-claim that fingerprint-based solver evaluation generally fails, that Doctor/Bimaristan is repaired, or that
-the result transfers to other problems, solver populations, or evaluation schemes. The LC743 execution
-remains pending reliable-model rerun.
-
-## Verification Table: Anchor Level and Evidence Stage
-
-The following table anchors all paper claims. "Anchor Level" measures oracle independence (0ÔÇô4, defined
-below).
-"Evidence Stage" marks the hardening protocol stage (1ÔÇô3) for the Midweather evidence chain. Every claim must
-be
-read through both columns.
-
-| Evidence                 | Anchor Level | Evidence Stage | Claim allowed                                    |
-|--------------------------|:------------:|:--------------:|--------------------------------------------------|
-| LC322                    |      2       |       ÔÇö        | bounded local oracle agreement                   |
-| LC3928                   |      2       |       ÔÇö        | bounded local oracle agreement                   |
-| CF2230F                  |      2       |       ÔÇö        | bounded local oracle agreement                   |
-| LC42                     |  0 (unfix)   |       ÔÇö        | no correctness claim                             |
-| LC3946                   |      2       |       ÔÇö        | positive C-4 replication (gap=1.0)              |
-| LC743                    |      2       |       ÔÇö        | specs cited; execution unverified                |
-| E0                       |  2 / 0 util  |       1        | representation sensitivity                       |
-| E2                       |      0       |       1        | exploratory only                                 |
-| Midweather retrospective |      2       |       2        | contaminated audit, negative/inconclusive        |
-| Midweather-Fingerprint   |      2       |       3        | clean LC322 gate, FAIL ÔÇö no decision improvement |
-| external evaluator       |      0       |       ÔÇö        | drop                                             |
-
-**Anchor Level definitions:**
-
-- **Anchor Level 0**: Internal only / circular. No independent anchor.
-- **Anchor Level 1**: Official-sample anchored.
-- **Anchor Level 2**: Independent local anchor (same-repo oracle duel or brute-force ground truth).
-- **Anchor Level 3**: Strong independent implementation anchor (outside reference solver).
-- **Anchor Level 4**: External judge / benchmark validation.
-
-Note: Midweather-Fingerprint is Evidence Stage 3 (clean protocol) but Anchor Level 2 (local oracle anchoring
-via `correct_dp`). It does not claim Anchor Level 3 because the oracle is an internal DP reference, not an
-outside reference solver.
-
-**Upgrade path:** Level 3/4 requires independent outside reference solvers (Level 3) or external
-judge/benchmark checks
-(Level 4). The best next evidence upgrade is to take LC322, LC3928, CF2230F generated cases and run them
-through known
-accepted/reference solutions or an external judge where possible, storing outputs and provenance. Only then
-claim
-anything beyond Level 2.
-
-**Note on passing tests:** **45/45 broader repository regression tests pass** (LC42 oracle duel: 9, comparator
-regression: 17,
-perturbation validity: 4, LC322 duel: 6, CF2230F duel: 4, LC3928 duel: 5). These are a separate scope from the
-39
-Midweather-Fingerprint protocol tests. They confirm mechanical consistency of the repairs. They do **not**
-upgrade Doctor to Anchor Level 3 or Level 4. Passing tests are necessary for claiming correctness of
-implementation, not
-sufficient
-for claiming external validity. Do not add more internal tests and present them as validation ÔÇö that would
-repeat the
-earlier problem.
+This paper evaluated whether a structured behavioral fingerprint estimator (C_genuine) improves accept/reject
+decision utility over a failure-count baseline (B1) on algorithmic solver populations. Two problem classes
+were tested under governed protocols with pre-declared solver populations and frozen evaluation procedures.
+
+On LC322 (Coin Change), C_genuine shows ╬╗-dependent superiority over B1 on the tested solver population:
+utility gap is negative at low reject-cost weights (╬╗=1: gap=-0.133), crosses zero between ╬╗=2 and ╬╗=5, and
+reaches gap=3.13 at ╬╗=50. B1 performs better at low ╬╗ values. C_genuine becomes superior as ╬╗ increases and
+wrong-reject costs dominate.
+
+On LC3946 (poset-based), C_genuine achieves gap=1.0 over B1 with decision_loss=0, consistent with the LC322
+results at moderate to high ╬╗ values under the tested populations.
+
+These findings are conditional. The solver populations used in both experiments produced a small number of
+distinct behavioral regimes. This restricts interpretation to the observed support and prevents generalization
+to richer or differently constructed solver distributions. Cross-population comparison of gap magnitude is not
+identifiable without controlling for generator method, as the LC322 and LC3946 populations were constructed
+differently.
+
+The generator collapse observed in LC743 and LC756 ÔÇö approximately six ¤ä-regimes under template-based
+generation ÔÇö limits identifiability of structural questions about estimator behavior under the current
+experimental setup. That question is deferred.
+
+No claim is made about dm structure, ¤ä-space geometry, or estimator behavior outside the tested populations
+and ╬╗ regimes. The contribution is a conditional empirical finding: C_genuine adds decision utility over B1
+specifically when wrong-reject costs are high and the solver population has genuine behavioral diversity
+across failure modes.
 
 # References
 
