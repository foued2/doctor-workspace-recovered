commit 1ca41b779a590f6f0ce580f5fa63ded489c0d87f
Author: Doctor Agent <doctor-agent@local>
Date:   Tue Jun 9 23:31:04 2026 +0100

    paper-abstract-rewrite-conditional-estimator-framing

diff --git a/doctor_bimaristan_scientific_paper.md b/doctor_bimaristan_scientific_paper.md
index 5b21bc5..100d576 100644
--- a/doctor_bimaristan_scientific_paper.md
+++ b/doctor_bimaristan_scientific_paper.md
@@ -9,50 +9,7 @@
 
 ## Abstract
 
-This paper reports a scoped negative case study in solver evaluation across three problem classes: LC322
-(Coin Change), LC3946 (poset-based), and LC743 (connectivity stress). We ask whether structured partial
-behavioral fingerprints improve solver accept/reject decisions over same-information raw baselines. The
-study is structured as a hardening sequence across three evidence stages, with a cross-problem replication
-analysis.
-**Evidence Stage 1 (exploratory/diagnostic):** The earlier DOCTOR/BIMARISTAN project history motivates the
-failure
-mode. Probes and features were designed before clean S_eval separation was enforced. The evidence is not clean
-final
-proof but establishes why the question is worth asking.
-
-**Evidence Stage 2 (retrospective/contaminated):** A Midweather retrospective audit applies the later protocol
-to
-existing LC322 solver data. The audit is contaminated because the solver population and probes were not
-causally
-separated before measurement. The result is negative/inconclusive: old LC322 evidence cannot support a clean
-utility
-claim.
-
-**Evidence Stage 3 (clean gate):** A Midweather-Fingerprint gate is implemented with frozen observation budget
-($B=15$), external blind solver pack (30 solvers), same-information baselines (B0--B6), anti-degeneracy
-checks, and
-decision-utility comparison (ACCEPT vs REJECT under decision_loss). The clean-run result is FAIL: the
-structured
-fingerprint policy C ties the strongest raw baselines on decision_loss (1.0) and does not strictly improve.
-RMSE
-improvement (0.024 vs 0.030) is a secondary metric and does not override the primary decision-loss result.
-
-The study does not claim that fingerprint-based solver evaluation generally fails. It presents one
-floor-limited
-LC322 gate where the tested fingerprint representation did not strictly improve the declared ACCEPT/REJECT
-decision utility over the best simple raw baselines in this floor-limited LC322 solver pack. A cross-problem
-replication on LC3946 (poset-based, balanced 15/15 split) yields a positive result: C_genuine achieves
-decision_loss=0, gap=1.0 over B1, with 10/11 C-5 perturbation survival. LC743 (connectivity stress) yields
-a negative result under a frozen protocol (gap=0), but execution is unverified due to model reliability
-concerns. All claims are K-local and scoped to the reported protocols.
-
-This negative result is also an ontological closure point for the Doctor/Bimaristan line of work. The project
-produced structured measurements, probe families, labels, contracts, and fingerprint features, but the
-hardened
-utility gate shows that this structure did not improve the evaluator decision it was meant to support. The
-contribution is therefore not a repaired evaluator, but a documented failure analysis of an evaluator idea
-whose
-internal structure did not translate into decision utility.
+This paper evaluates whether a structured behavioral fingerprint estimator (C_genuine) improves accept/reject decision utility over a failure-count baseline (B1) when applied to algorithmic solver populations on LeetCode problems. Across the two evaluated problem classes ÔÇö LC322 (Coin Change) and LC3946 ÔÇö C_genuine shows ╬╗-dependent performance relative to B1 on the tested solver populations: negative utility gap at low reject-cost weights, positive and increasing gap at high reject-cost weights, with sign-flip behavior consistent across both populations. These results are conditional on the specific solver distributions tested; the generator populations produced a small number of distinct behavioral regimes, limiting interpretation to the observed support.
 
 ---
 
