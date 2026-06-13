commit 2bb5dd3611b549c447989e0d811044b92c526c08
Author: Doctor Agent <doctor-agent@local>
Date:   Tue Jun 9 23:24:59 2026 +0100

    paper-limitations-rewrite-l1-l2-l3-generator-estimator-separation

diff --git a/doctor_bimaristan_scientific_paper.md b/doctor_bimaristan_scientific_paper.md
index 7ddf087..5b21bc5 100644
--- a/doctor_bimaristan_scientific_paper.md
+++ b/doctor_bimaristan_scientific_paper.md
@@ -1345,68 +1345,58 @@ non-repository solver population, or external benchmark execution is included. A
 expose
 failure surfaces not covered by the current artifacts.
 
-## Clean Gate Threats
-
-The Evidence Stage 3 clean-gate result is subject to the following scoped limitations beyond those discussed
-above:
-
-- **Floor effect / low reject prevalence.** The clean S_eval pack contains 27 ACCEPT-class solvers and only 3
-  REJECT-class solvers. Decision_loss therefore has very coarse resolution. C can strictly improve over the
-  best
-  simple baseline only by reducing the remaining one wrong accept to zero. This makes the gate conservative
-  and
-  low-powered for detecting marginal fingerprint value. The verdict remains FAIL under the declared protocol,
-  but
-  the interpretation is local: C failed to demonstrate added utility in this skewed LC322 pack.
-- **Single problem (LC322).** The result may not transfer to other Coin Change variants or other problem
-  domains.
-- **Single generated external blind solver pack (30 solvers from one LLM).** A different solver population,
-  different
-  generation procedure, or different LLM provider could produce different decision outcomes.
-- **LLM pretraining / non-naive solver population.** External blind means blind to DOCTOR/BIMARISTAN
-  artifacts, not
-  naive with respect to LC322. Coin Change is a common programming problem, and the Claude-generated solver
-  pack may
-  reflect pretrained familiarity with standard dynamic-programming solution patterns. The high ACCEPT
-  prevalence may
-  therefore reflect the generator's prior exposure to LC322-like solutions rather than a general solver
-  population.
-- **Single budget point ($B=15$).** Results may differ at other observation budgets.
-- **Single decision type (ACCEPT/REJECT).** Other decision types (rank, select top-K, continuous score) were
-  not tested.
-- **Single failure threshold (0.05) and single minimum accept rate (0.2).** Different thresholds change the
-  utility
-  trade-off and could favor different estimators.
-- **Fingerprint axis selection is a design choice.** The six axes (reachability, order, magnitude, boundary,
-  transition,
-  memoization) were derived from the problem specification but remain a choice among possible axis sets.
-- **Axis-design contamination.** The clean gate freezes the budget, solver pack, estimator set, and decision
-  rule
-  before metric computation, but the fingerprint axes were designed after earlier DOCTOR/BIMARISTAN LC322
-  exploration.
-  Therefore, Stage 3 is clean as an execution gate, not as a fully prospective representation-design study.
-  Prior
-  exposure may have influenced which axes were considered worth encoding.
-- **Same-information asymmetry in the effective comparison.** C is a deterministic feature layer over the full
-  observation tensor, and B4/B5/B6 receive the same tensor. However, the baselines that tie C on decision_loss
-  are B1/B2/B3, which use less information. The clean result therefore shows that C's extra structure did not
-  improve the decision over simpler baselines; it does not show that a strong equal-tensor raw policy beat C.
-- **Same-information baselines may not cover all possible policies.** B0--B6 are a reasonable set but do not
-  exhaust
-  the space of functions over the observation tensor.
-- **C's RMSE improvement is secondary under the declared decision spec, but could become primary utility under
-  a
-  different decision spec.** The result is specific to the ACCEPT/REJECT decision_loss formulation.
-- **Coarse decision resolution.** The clean S_eval contains 30 solvers and the best estimators differ by at
-  most
-  one decision error. Decision_loss therefore has coarse resolution: the result supports no strict-improvement
-  claim, but it should not be read as a precise estimate of effect size. Combined with the floor effect above,
-  the evaluation design has limited power to detect a one-decision improvement even if fingerprints genuinely
-  help.
-
-These limitations bound the claim: the negative result holds under the specific LC322 $B=15$
-EXTERNAL_BLIND_PACK
-configuration reported. Changing any of these conditions requires independent re-evaluation.
+## Limitations
+
+### L1. Generator Support Collapse
+
+The solver populations used in all experiments were generated under constrained templates or prompted LLM
+sampling with explicit family distributions. Empirical measurement of ¤ä-vectors across LC743 and LC756
+populations revealed approximately six distinct behavioral regimes within the observed populations. Effective
+rank analysis of the solver feature matrix confirmed near-rank-1 structure.
+
+This means the generator does not explore the full behavioral space of candidate solvers. The observed
+¤ä-space is a small finite regime set determined by the generator's construction method, not by the
+problem's combinatorial structure. Any claim about the geometry of ¤ä-space ÔÇö dimensionality, clustering,
+separation between failure modes ÔÇö is conditionally unidentifiable from this data. The experiments
+characterize the image of the generator, not the space of all possible solvers.
+
+This limitation applies directly to LC743 and LC756. It does not apply to the estimator comparison
+results in LC322 and LC3946, which make no claim about ¤ä-space geometry.
+
+### L2. dm as Projection Under Collapsed Support
+
+The scalar summary dm(s) = ╬ú ¤ä(s) is a deterministic projection from binary trajectory vectors to
+non-negative integers. On a support containing approximately six ¤ä-regimes, dm may appear to behave
+injectively: each dm value corresponds to exactly one observed ¤ä pattern.
+
+This apparent injectivity is an artifact of restricted support. It follows directly from the collapsed
+generator support documented in L1. It is not a structural property of dm on the full solver domain.
+Whether dm loses information about ¤ä on a richer generator ÔÇö one that populates a larger region of binary
+trajectory space ÔÇö is not answerable from the data collected here.
+
+dm is not a studied object in this paper. It is a projection whose behavior is underdetermined given the
+observed support. No inference about its structural properties is warranted.
+
+### L3. Estimator Results Are Conditional on Solver Distribution
+
+The C_genuine vs B1 comparisons in LC322-v2 (gap=3.13) and LC3946 (gap=1.0) are conditional performance
+measurements under specific solver populations. Their validity depends on two factors that were not held
+constant across experiments: solver distribution and ╬╗ regime.
+
+Specifically:
+
+- LC322-v2 used GPT-generated solvers with a declared F1├ù5/F2├ù10/F3├ù11/F4├ù4 prior and a post-freeze
+  termination guard on one solver. LC322-v1 used LLM-generated solvers whose population is unrecoverable.
+- LC3946 used hand-coded solvers across six strategy families.
+- These populations are not drawn from the same distribution. Cross-population comparisons of gap magnitude
+  are not identifiable without controlling for generator method.
+
+C_genuine shows ╬╗-dependent superiority over B1: negative gap at low ╬╗, positive and increasing gap at
+high ╬╗. This sign-flip behavior is a property of the estimator under these distributions. It is not
+claimed to be invariant across generators, problem classes, or ╬╗ regimes outside those tested.
+
+No universality claim is made. No claim of invariance across generators is made. The results establish
+conditional estimator behavior under the tested populations and ╬╗ values, nothing stronger.
 
 # Conclusion
 
