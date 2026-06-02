# A Clean LC322 Decision Gate Where Structured Solver Fingerprints Did Not Strictly Improve Utility

## A Hardening Sequence from Exploratory Probes to a Clean Budget-Matched Gate

**Author:** Abidi Foued  
**Affiliation:** Independent Researcher  
**Repository:** <https://github.com/foued2/doctor-workspace>  
**Date:** May 2026

## Abstract

This paper reports a scoped negative case study in solver evaluation. We ask whether structured partial behavioral
fingerprints improve solver accept/reject decisions over same-information raw baselines in the LC322 Coin Change
problem. The study is structured as a hardening sequence across three evidence stages.
**Evidence Stage 1 (exploratory/diagnostic):** The earlier DOCTOR/BIMARISTAN project history motivates the failure
mode. Probes and features were designed before clean S_eval separation was enforced. The evidence is not clean final
proof but establishes why the question is worth asking.

**Evidence Stage 2 (retrospective/contaminated):** A Midweather retrospective audit applies the later protocol to
existing LC322 solver data. The audit is contaminated because the solver population and probes were not causally
separated before measurement. The result is negative/inconclusive: old LC322 evidence cannot support a clean utility
claim.

**Evidence Stage 3 (clean gate):** A Midweather-Fingerprint gate is implemented with frozen observation budget
($B=15$), external blind solver pack (30 solvers), same-information baselines (B0--B6), anti-degeneracy checks, and
decision-utility comparison (ACCEPT vs REJECT under decision_loss). The clean-run result is FAIL: the structured
fingerprint policy C ties the strongest raw baselines on decision_loss (1.0) and does not strictly improve. RMSE
improvement (0.024 vs 0.030) is a secondary metric and does not override the primary decision-loss result.

The study does not claim that fingerprint-based solver evaluation generally fails. It presents one floor-limited
LC322 gate where the tested fingerprint representation did not strictly improve the declared ACCEPT/REJECT
decision utility over the best simple raw baselines in this floor-limited LC322 solver pack. All claims are
K-local and scoped to the reported protocol. The result is a strict local utility failure, not a general
impossibility claim about behavioral fingerprints.

This negative result is also an ontological closure point for the Doctor/Bimaristan line of work. The project
produced structured measurements, probe families, labels, contracts, and fingerprint features, but the hardened
utility gate shows that this structure did not improve the evaluator decision it was meant to support. The
contribution is therefore not a repaired evaluator, but a documented failure analysis of an evaluator idea whose
internal structure did not translate into decision utility.

---

# Introduction

Adversarial evaluation systems for algorithmic programs commonly report pass rates, divergence rates, AUC values, or
failure labels. An open question is whether structured behavioral fingerprints — partial execution features
designed to capture solver behavior beyond pass/fail — improve evaluator decisions over simpler baselines.
This paper tests that question in the LC322 Coin Change problem through a hardening sequence: we progressively
tighten the evaluation protocol across three evidence stages, ending in one clean budget-matched gate.

The study uses the DOCTOR/BIMARISTAN project as its case-study subject. The paper does not convert the project
into a generic testing framework. Earlier DOCTOR/BIMARISTAN work explored whether algorithm behavior can be
captured through structured representation; those explorations revealed measurement-drift and
representation-dependence issues that motivated the hardened final gate. The question here is not measurability
itself, but whether the specific fingerprint representation tested here improves decision utility over
same-information baselines under a clean protocol.

## Protocol Notation

Results are scoped to the declared evaluation stack: problem, solver pack, generator, oracle, comparator,
representation, and perturbation set. The full stack definition is written as $K = (P, S, G, O, C, R, F)$
(see Appendix A for the complete registry). All claims are K-local: they hold under this specific stack only.

The budget for observed probe executions is written $B = 15$ (also called the observation budget). Earlier
experiments reference the additional notation $T_{\mathrm{obs}}$ (instrument-relative target)
and $T_{\mathrm{ext}}$ (external projection), defined in Appendix A. The clean Evidence Stage 3 gate does not
use that ontology and relies on standard decision-utility terminology instead.

## Research Question and Hypothesis

**Primary research question:**

> RQ1: Under a frozen LC322 evaluation budget, do structured solver fingerprints improve ACCEPT/REJECT decision
> utility over same-information raw baselines?

**Hypothesis:**

> H1: Structured fingerprint features improve decision_loss over all same-information baselines under the clean
> Midweather-Fingerprint gate.

**Result: H1 is not supported.**

## Core Claims and Evidence Stages

The paper is structured as a hardening sequence across three evidence stages. Each stage tightens the
protocol, and only the final stage supports a clean claim.

### Evidence Stage 1 — Exploratory / Diagnostic (DOCTOR/BIMARISTAN history)

Motivates why the evaluator-utility question is worth asking. Not clean final proof.

1. **E0 is a representation-sensitivity observation: suite-equivalent solvers (all pass the same 88-case expanded
   suite) can induce different observed structure under trajectory representation.** `MEASUREMENT_OBSERVATION_ONLY`:
   all six solvers pass 88/88, but
   trajectory representation separates them. No evidence that trajectory separation predicts future failure,
   robustness, external labels, or correctness improvement.

2. **Within-$K$ conditioning in LC560 reveals confounded proxy structure in $R$.** Not a $\Delta K$ claim. Demonstrates
   representation-internal sensitivity that motivates why $R$ is load-bearing.

3. **E2 produced directional artifact-level observations; no statistically supported boundary claim is made.**
   Moved to Appendix B. The primary E2 result is the prefix-length audit disqualification of `normalized_progress`.

### Evidence Stage 2 — Retrospective / Contaminated (Midweather retrospective audit)

Applies the later protocol to existing LC322 solver data. The audit is contaminated because probes and features
were not causally separated from the solver population before measurement. Result: negative/inconclusive.
Old LC322 evidence cannot support a clean utility claim.

### Evidence Stage 3 — Clean gate (Midweather-Fingerprint)

The main result. A clean LC322 case study with frozen observation budget ($B=15$), external blind solver pack (30
solvers),
same-information baselines (B0--B6), anti-degeneracy checks, and ACCEPT/REJECT decision utility under decision_loss.
The structured fingerprint policy C ties the strongest raw baselines on decision_loss (1.0). Decision: FAIL.
RMSE improvement is secondary and does not override.

The paper's contribution is a clean LC322 case study (Evidence Stage 3) preceded by a documented hardening sequence (
Stages 1--2)
that shows why the final protocol was necessary. Earlier stages are exploratory/diagnostic context, not clean proof.

# Related Work

This case study is adjacent to metamorphic testing, differential testing, property-based testing, benchmark auditing,
and adversarial code evaluation. Metamorphic testing addresses oracle limitations through relations among executions.
Differential testing compares implementations under shared inputs. Property-based testing generates inputs from declared
properties.

In adversarial code evaluation, recent work generates LLM-assisted test cases for competitive programming
(Wang et al., 2025; Shi et al., 2026; Hort and Moonen, 2025). These systems measure whether generated solutions pass
expanded or adversarial test suites—a correctness-vs-oracle paradigm. This case study
differs by treating oracle agreement as a K-relative measurement rather than a correctness verdict, and by targeting
decision utility under same-information baselines rather than maximizing the number of tests a solver fails.

EvalPlus and LiveCodeBench provide context for generated or adversarial code-evaluation tests.

Relative to these lines of work, the contribution here is not a new test-generation method, a stronger oracle, or a
larger benchmark. Metamorphic testing studies relations among executions when direct oracles are limited; differential
testing compares implementations under shared inputs; property-based testing explores declared input properties; and
expanded-suite code benchmarks measure agreement with larger output suites. This paper tests a different question:
whether structured fingerprint features improve decision utility over same-information baselines under a clean
budget-matched protocol in LC322.

This paper does not claim novelty for adversarial testing or oracle sensitivity.

The central contrast between this case study and the related work above is decision-utility framing. The cited
test-generation and benchmark-augmentation works evaluate whether larger or adversarial test suites reduce
pass/fail classification error or increase oracle discrimination. This paper evaluates whether a structured
fingerprint representation improves a declared accept/reject decision under a fixed observation budget and
same-information baselines. The contribution is not a stronger test suite, but a protocol for measuring
whether representation improvements translate to decision improvements — and a clean negative result under
that protocol for the specific LC322 configuration tested.

# Methods

## Data Sources

All evidence comes from repository artifacts. The paper uses findings logs, JSON outputs,
scripts, and benchmark snapshots as empirical records.

This study is an exploratory artifact-level case study rather than a preregistered confirmatory experiment. Several
claims were sharpened after repository audits identified invalid perturbations, proxy confounds, and boundary artifacts.
The results should be read as a disciplined reconstruction of observed K-local behavior, not as confirmatory
statistical validation.

Within this retrospective reconstruction, Evidence Stage 3 is a clean execution gate because its budget, S_eval
manifest, estimator set, and decision rule were frozen before clean-run metric computation. This is not a preregistered
external study; the gate is clean relative to the reconstruction protocol, not relative to a prospective registry.

The repository is not a clean benchmark release. All claims are artifact-level and K-local, not claims of a clean
benchmark release or a fully passing repository test suite. For the consolidated test-status ledger across all scopes,
see the reproducibility section.

## Oracle Rule

    O defines correctness only within K; O is not a semantic ground truth function.

No result upgrades $O$ to external truth. All correctness language means agreement with $O$ under $C$.

## Perturbation Validity Rule

Every perturbation in this paper is drawn from a declared family $F$ validated against a closed registry (
`doctor/adversarial/perturbation_validity.py`). A perturbation is valid only if it preserves the invariant declared for
its (problem, family) pair under the current $O$ and $C$. The LC45 case—where `multiset_invariant` was initially
declared for a position-sensitive problem—established that validity requires a provable structural argument, not just an
operator name. The closed registry prevents undeclared perturbation families from entering the system, but it does not
by itself prove that every declared invariant is semantically correct. That incident is treated as a limitation of the
project mechanics: perturbation validity is not guaranteed by a family label, and invalid perturbations measure response
to changed semantics rather than stability under preserved problem meaning.

A critical distinction is maintained throughout:

    validity != adversarial strength

A valid perturbation preserves the declared invariant. It does not automatically explore a failure-relevant surface.
The clean Midweather-Fingerprint gate uses perturbations drawn from its predeclared probe registry; historical E2
includes a boundary condition (`normalized_progress`) later disqualified as prefix-length-confounded evidence and is
retained only as exploratory context in Appendix B.

## Experiment Schema

The historical E0/E1/E2 artifacts use the older K/Delta-K/T_obs notation and Layer A/B/C structure, defined in
Appendix A. The clean Midweather-Fingerprint gate is specified independently by its frozen observation budget,
S_eval manifest, decision_spec, estimator set, and primary utility metric. Results use only the notation defined
for each experiment.

## Variables

Variable definitions are fixed:

- `zero_crossing_frequency`: count/frequency of sign-crossing structure used in the LC560 artifact;

- `max_collision_depth`: maximum frequency of a single prefix-sum value in the LC560 artifact;

- (Appendix A defines additional notation used by the historical experiments.)

No variable is redefined after first use.

## Statistical Treatment

The study uses heterogeneous statistics: pass rates in E0, conditional correlations in E1, and AUC values with bootstrap
confidence intervals in E2. No unified inference model is claimed. No structural-causal-model inference is used. No
multiple-comparison correction is applied. E2 includes condition-level bootstrap confidence intervals from 500 resamples
in the artifacts. A post-audit bootstrap delta-CI script (`compute_e2_delta_ci.py`) computes the cross-condition E2
delta intervals; all six cross-condition delta confidence intervals cross zero at 95%. E2 deltas are therefore treated
as directional shifts with uncertain magnitude, not as statistically significant non-invariance findings. E0 and E1 do
not receive matched uncertainty treatment.

## Decision Utility Definition

The primary evaluation metric is decision_loss:

    decision_loss = λ_A · wrong_accepts + λ_R · wrong_rejects

with λ_A = 1 and λ_R = 1 in this study (equal cost). Equal costs are declared without empirical justification;
a production system may assign asymmetric costs. In this specific result both C and the tied baselines (B1/B2/B3)
have 1 wrong accept and 0 wrong rejects, so the tie is robust to any λ_A >= λ_R assignment. Formally:

    true_failure_rate(s) = failures on target evaluation set / target evaluation set size
    true_ACCEPT(s) = true_failure_rate(s) <= failure_threshold (0.05)
    pred_ACCEPT_E(s) = estimated_failure_rate_E(s) <= 0.05
    wrong_accept(E) = |{s: pred_ACCEPT_E(s) = 1 and true_ACCEPT(s) = 0}|
    wrong_reject(E) = |{s: pred_ACCEPT_E(s) = 0 and true_ACCEPT(s) = 1}|
    decision_loss(E) = wrong_accept(E) + wrong_reject(E)

The target evaluation set is the full D_target probe set (15 non-observed probes per solver). Estimators receive
only the 15 observed probes per solver and must predict failure rate on the non-observed probes.

## Estimator Feature Access

All estimators receive identical O_obs (the same 15 observed probe executions per solver). C uses structured derived
features (pair flips, invariants, sensitivity) derived from the observation tensor that includes pass/fail status, axis
metadata (e.g., reachability, order, magnitude), and deformation labels. The key same-information question is whether
at least one raw baseline also receives this same tensor. B4_raw_full_tensor does: it receives pass_fail + axis +
deformation for all 15 probes as its full input tensor. The structured fingerprint features in C are deterministic
functions of this same tensor, not independent observations. The following table documents what each estimator
extracts from O_obs:

| Estimator                      | Input fields used                                                       | Axis metadata | Solver identity | Target leakage | Training rule |
|--------------------------------|-------------------------------------------------------------------------|:-------------:|:---------------:|:--------------:|:-------------:|
| B0_prior                       | population prior only                                                   |      no       |       no        |       no       |     fixed     |
| B1_count                       | pass_fail from O_obs                                                    |      no       |       no        |       no       |     fixed     |
| B2_calibrated_count            | pass_fail from O_obs                                                    |      no       |       no        |       no       |    LOO CV     |
| B3_raw_pf_vector               | pass_fail vector (15 probes)                                            |      no       |       no        |       no       |     fixed     |
| B4_raw_full_tensor             | pass_fail + axis + deformation for all 15 probes                        |      yes      |       no        |       no       |     fixed     |
| B5_nearest_neighbor_raw_tensor | raw tensor (as B4)                                                      |      yes      |       no        |       no       |     fixed     |
| B6_regularized_raw_tensor      | raw tensor (as B4)                                                      |      yes      |       no        |       no       |    LOO CV     |
| C_structured_fingerprint       | deterministic features (pair flips, invariants, sensitivity) from O_obs |      yes      |       no        |       no       |     fixed     |

No estimator may call extra oracle queries, create new observations, or access D_target probe outputs during
training or prediction.

## S_eval Provenance

External blind means generated outside the repository's known solver population and frozen before clean-gate
evaluation. It does not mean externally judged, third-party benchmarked, or independently oracle-validated.

The clean gate uses 30 solver functions generated as an external blind pack:

- **Generator:** Claude (Anthropic), prompted with the LC322 problem statement only.
- **Generation time:** After the protocol freeze (commit 6ca6c28). Solver source was not inspected before the freeze.
- **Number:** 30 distinct solver_id entries (`solver_001`–`solver_030`).
- **Source file:** A single generated solver pack file with all 30 function definitions.
- **No deduplication:** Solvers were not deduplicated by behavior or output. All 30 are included as-is.
- **Hash locking:** Every solver function is pinned by SHA256 in the S_eval manifest.
- **No prior LC322 exposure:** The generator had no access to prior Doctor/Bimaristan LC322 results, probes, or
  failure labels.
- **Timeline:** Protocol freeze → S_eval generation → probe execution → guard check → metric computation. The
  freeze artifact, manifest, and result JSON are all committed to the repository.

## External Baseline

The paper includes one internal expanded-suite baseline analogous to an EvalPlus-style stronger output suite:

    E0 baseline = LC322 expanded output suite

This is not a third-party benchmark. It ranks only one internal comparison: output-suite agreement versus
trace-representation separation.

# Results

Experimental findings are presented in hardening sequence order: exploratory/diagnostic experiments (Evidence Stage 1),
retrospective audit (Evidence Stage 2), then the clean gate (Evidence Stage 3). The Stage 3 clean gate is the paper's
main result. No interpretation beyond the stated layer is introduced in this section.

## E0: LC322 Expanded-Suite Baseline Versus Trace Representation

    E0 =
    (K0, Delta K0, M0, T_obs.equivalence_class, O0, C0, R0, F0,
     observation0, control0, delta0, effect_size0)

**K0:**

    P = LC322 Coin Change
    S = {
      lc322_canonical_dp,
      lc322_sorted_coin_outer_dp,
      lc322_reverse_coin_outer_dp,
      lc322_amount_outer_equivalent_dp,
      lc322_bfs_shortest_path,
      lc322_recursive_memo_exact
    }
    G = expanded LC322 suite, 88 cases, 31 large-amount cases
    O = LC322 expected outputs in findings/FINDINGS_141.md
    C = output equality
    R = {output pass rate, trajectory representation at n2..n8}
    F = none for output-suite baseline

**$\Delta K_0$:**

    Delta R = output pass-rate representation -> trajectory representation

**$M_0$:**

    M0a = expanded-suite pass rate
    M0b = {silhouette, same-group nearest neighbor, mean gap}

**Layer A observation (output pass rate):**

| **Solver**                         | **Group**       | **M0a pass rate** |
|:-----------------------------------|:----------------|------------------:|
| `lc322_canonical_dp`               | reference-style |          1.000000 |
| `lc322_sorted_coin_outer_dp`       | reference-style |          1.000000 |
| `lc322_reverse_coin_outer_dp`      | reference-style |          1.000000 |
| `lc322_amount_outer_equivalent_dp` | alternate       |          1.000000 |
| `lc322_bfs_shortest_path`          | alternate       |          1.000000 |
| `lc322_recursive_memo_exact`       | alternate       |          1.000000 |

E0 Layer A: Expanded-suite pass rates across all solvers.

**Layer A observation (trajectory representation):**

| **Step** | **Silhouette** | **Same-group NN** | **Alt-ref mean gap** |
|:---------|---------------:|------------------:|---------------------:|
| n2       |       0.429935 |          0.918561 |             0.537637 |
| n3       |       0.346979 |          0.918561 |             0.362530 |
| n4       |       0.262140 |          0.922348 |             0.320355 |
| n5       |       0.249048 |          0.939394 |             0.366116 |
| n6       |       0.287161 |          0.950758 |             0.453013 |
| n7       |       0.300630 |          0.954545 |             0.398497 |
| n8       |       0.291335 |          0.956439 |             0.383728 |

E0 Layer A: Trajectory representation separation metrics at steps n2–n8.

**Layer B $\delta_0$:**

    Delta pass-rate discrimination = 0.000000
    Delta trajectory separation = positive silhouette at n2..n8

**Layer C statement$_0$:**

    E0 is a representation-sensitivity observation: suite-equivalent solvers (all pass the same 88-case expanded
    suite) can induce different observed structure under trajectory representation. This is a
    MEASUREMENT_OBSERVATION_ONLY: all six solvers pass 88/88 on the expanded suite, but trajectory representation
    separates them.
    There is no evidence that trajectory separation predicts future failure, robustness, external
    labels, or correctness improvement.

**Artifacts:**

- `findings/FINDINGS_141.md`

- `data/lc322_true_case_b_test.json`

- `runners/run_lc322_true_case_b_test.py`

- `solvers/lc322_true_case_b_solvers.py`

Scope note: all six E0 solvers are oracle-equivalent on the 88-case expanded suite. The trajectory representation
separates execution geometry inside that oracle-equivalent class; it does not establish that trajectory improves
correctness judgment over a complete oracle.

## E1: LC560 Within-K Conditioning Structure of R

**K1:**

    P = LC560 Subarray Sum Equals K
    S = {lc560_prefix_map, lc560_sliding_window}
    G = wider 50-array partial-dependence sweep
    O = LC560 repository oracle
    C = divergence calculation in artifact
    R = {
      zero_crossing_frequency,
      collision_density,
      max_collision_depth,
      divergence
    }
    F = LC560 sign/k perturbation axes in artifact

This experiment does not change a $K$ component. $R$, $F$, $O$, and $C$ are fixed. The analysis conditions on variables
within the fixed set $R$ to test whether apparent associations hold under conditioning. The wider partial-dependence
sweep is treated as a correction to an earlier small-sample interpretation: `zero_crossing_frequency` and
`collision_density` co-vary by construction, and the remaining result is conditional and correlational rather than
causal mechanism identification.

Conditional correlations within fixed $R_1$:

    M1a = r(zero_crossing_frequency, divergence | collision_density bin)
    M1b = r(max_collision_depth, divergence | zero_crossing_frequency bin)

**Layer A observation:**

    M1a = 0.00 across all three collision_density bins

| **zero_crossing_frequency bin** | **N** | **M1b** |
|--------------------------------:|------:|--------:|
|                               1 |    18 |   0.890 |
|                               2 |    10 |   0.944 |
|                               3 |     6 |   0.890 |

E1 Layer A: Conditional correlation of `max_collision_depth` with divergence, by `zero_crossing_frequency` bin.

**Layer B $\delta_1$:**

    zero_crossing_frequency conditioned on collision_density: r = 0.00 (N=34, 3 bins)
    max_collision_depth conditioned on zero_crossing_frequency: r = [0.890, 0.944, 0.890] (N=34, 3 bins)

**Layer C statement$_1$:**

    Within fixed K1, conditioning by collision_density bins reveals that
    zero_crossing_frequency has no residual association with divergence (r=0.00),
    while max_collision_depth retains conditional association
    (r = [0.890, 0.944, 0.890] within zero_crossing_frequency bins).
    This is not a Delta K result -- R itself is unchanged -- but it demonstrates
    that R contains confounded variables whose apparent association is eliminated
    by conditioning on other R variables.

**Artifacts:**

- `findings/FINDINGS.md` Entry 016

- `doctor/scratch/lc560_partial_dependence_v2.py`

- `runners/run_lc560.py`

- `doctor/adversarial/lc560_candidates.py`

<!-- E2 moved to Appendix B — Exploratory Observations -->

## Midweather Retrospective Audit (Evidence Stage 2)

The Midweather retrospective audit applies the Midweather protocol to existing LC322 solver data from the repository's
known solver population. The audit is explicitly contaminated: probes and fingerprint features were designed
before causal separation from S_eval was enforced. The purpose is to test whether retrospective LC322 evidence
can support a clean evaluator-utility claim. The result is recorded in the separate Midweather-Atomic artifact.

**K_ma:**

    P = LC322 Coin Change
    S = known solver population (7 target solvers with usable data)
    G = original Bimaristan generators
    O = LC322 DP reference
    C = output equality
    R = divergence rates, fingerprint features (reachability, order, magnitude, boundary, transition, memoization)
    F = six-family LC322 probe basis

**Layer A observation:**

Retrospective decision table (primary utility: wrong_accepts):

| Estimator                      | Wrong Accepts | Wrong Rejects | Decision Cost |  RMSE  |  MAE   | AUROC |
|--------------------------------|:-------------:|:-------------:|:-------------:|:------:|:------:|:-----:|
| B0_prior                       |       0       |       2       |      2.0      | 0.3047 | 0.2755 |  0.5  |
| B1_count                       |       0       |       0       |      0.0      | 0.1254 | 0.1000 |  1.0  |
| B2_calibrated_count            |       0       |       2       |      2.0      | 0.1260 | 0.1015 |  1.0  |
| B3_raw_vector                  |       0       |       0       |      0.0      | 0.1254 | 0.1000 |  1.0  |
| B4_nearest_neighbor_raw_vector |       1       |       0       |      1.0      | 0.2000 | 0.1429 |  0.9  |
| B5_regularized_raw_vector      |       1       |       0       |      1.0      | 0.2715 | 0.2156 |  0.9  |
| C_structured_features          |       0       |       0       |      0.0      | 0.1490 | 0.0955 |  1.0  |

**Layer B $\delta_{ma}$:**

    C achieves 0 wrong accepts (ties B1/B3) with 0 wrong rejects. B1/B3/C also achieve 0.0 decision cost.
    C does not strictly beat every baseline on wrong_accepts (ties B1/B3).
    The audit is contaminated and supports no clean superiority claim.

**Layer C statement$_{ma}$:**

- This is a retrospective contaminated audit, not a clean result.
- Old LC322 evidence cannot support a clean evaluator-utility claim because probes and
  features were not causally separated from S_eval.
- Even on its own terms, C does not strictly beat every baseline on the primary utility.
- Correct finding: negative/inconclusive boundary marker.
- These metrics are not directly comparable to the clean Midweather-Fingerprint gate:
  the Atomic audit uses a different primary utility (wrong_accepts), solver count (7),
  and probe split (retrospective, not causally separated).

**Artifacts:**

- `data/midweather_atomic_lc322.json` — full result JSON
- `findings/FINDINGS_MIDWEATHER_ATOMIC_LC322.md` — findings report

## Midweather-Fingerprint: Clean Gate (Evidence Stage 3)

This is the main result: a clean LC322 case study testing whether structured fingerprint features
improve solver accept/reject decisions over same-information raw baselines under a frozen protocol,
external blind S_eval, and anti-degeneracy guards.

**K_mf:**

    P = LC322 Coin Change
    S = 30 externally generated blind solver functions (solver_001..solver_030)
    G = frozen probe index, 30 probes across 6 fingerprint axes
    O = correct_dp (exhaustive DP reference)
    C = output equality
    R = {
      B0: population prior,
      B1: failure count,
      B2: calibrated count,
      B3: raw pass/fail vector,
      B4: raw full observation tensor (pass_fail + axis + deformation),
      B5: nearest-neighbor over raw tensor,
      B6: regularized regression over raw tensor,
      C: structured fingerprint features (pair flips, invariants, sensitivity)
    }
    F = six predeclared fingerprint axes: reachability, order, magnitude, boundary, transition, memoization

**Protocol guards (all passed — the clean-gate runner emits guard statuses before computing metrics):**

| Guard                                                                    | Status |
|--------------------------------------------------------------------------|--------|
| $B=15$ frozen (observed probes = 15, budget unit = one solver execution) | passed |
| decision_spec present (failure_threshold=0.05, minimum_accept_rate=0.2)  | passed |
| B6 config frozen (leave-one-out ridge, alpha=1.0)                        | passed |
| Axis provenance clean (problem_specification_only)                       | passed |
| S_eval certified EXTERNAL_BLIND_PACK                                     | passed |
| S_eval freeze linkage matches                                            | passed |
| Solver file hashes present                                               | passed |
| No degenerate target collapse                                            | passed |
| No degenerate C policy (not all-ACCEPT, not all-REJECT)                  | passed |
| All estimators receive identical O_obs                                   | passed |

Degenerate baselines (B0 all-ACCEPT, B4 all-REJECT, B5/B6 all-ACCEPT) are reported rather than blocked.
The anti-degeneracy guard applies to C (no degenerate prediction) and to target collapse (all solvers
ACCEPT or all REJECT), not to every baseline policy.

**Layer A observation:**

| Estimator                      | Decision Loss | Wrong Accepts | Wrong Rejects | Accept Rate | RMSE (secondary) | Degenerate |
|--------------------------------|---------------|---------------|---------------|-------------|------------------|------------|
| B0_prior                       | 3.0           | 3             | 0             | 1.0         | 0.070            | all-ACCEPT |
| B1_count                       | 1.0           | 1             | 0             | 0.933       | 0.030            |            |
| B2_calibrated_count            | 1.0           | 1             | 0             | 0.933       | 0.032            |            |
| B3_raw_pf_vector               | 1.0           | 1             | 0             | 0.933       | 0.030            |            |
| B4_raw_full_tensor             | 27.0          | 0             | 27            | 0.0         | 1.334            | all-REJECT |
| B5_nearest_neighbor_raw_tensor | 3.0           | 3             | 0             | 1.0         | 0.072            | all-ACCEPT |
| B6_regularized_raw_tensor      | 3.0           | 3             | 0             | 1.0         | 0.072            | all-ACCEPT |
| C_structured_fingerprint       | 1.0           | 1             | 0             | 0.933       | 0.024            |            |

**Layer B $\delta_{mf}$:**

    C decision_loss = 1.0, best baseline decision_loss = 1.0 (B1, B2, B3).
    C does not strictly beat every same-observation baseline on decision_loss.
    C satisfies minimum_accept_rate (0.933 >= 0.2) and is not degenerate.
    C RMSE (0.024) is best overall but secondary.

**Interpretive note on same-information baselines:** C ties B1/B2/B3 on decision_loss, and those baselines use
less structural information than C. The equal-tensor baselines B4/B5/B6 receive the same axis/deformation tensor
as C, but they are degenerate in this run. Thus, the FAIL verdict is not that C loses to a well-performing
equal-information tensor policy. The verdict is that C's additional structured information does not improve the
final ACCEPT/REJECT decision over simpler lower-information raw baselines under this floor-limited LC322 solver
pack.

**Layer C statement$_{mf}$:**

- Under a frozen $B=15$ budget, external blind 30-solver S_eval, same-observation baselines B0--B6,
  and ACCEPT/REJECT decision utility measured by decision_loss, the structured fingerprint policy C
  does not strictly improve over the strongest raw baselines.
- C ties B1/B2/B3 on decision_loss (1.0). Notably, B1/B2/B3 use *less* information than C (pass/fail
  counts only, no axis metadata or deformation labels). C outperforms all same-tensor baselines
  (B4/B5/B6) that receive the same full observation tensor — those baselines are degenerate. The
  meaningful tie is against simpler baselines that use less observation information, which strengthens
  the negative result: even against information-poorer estimators, C does not improve the primary
  decision metric.
- The protocol requirement is strict improvement on primary utility (decision_loss). Ties are FAIL.
- RMSE improvement alone cannot produce PASS per the declared success rule.
- This is a clean LC322 case study: the tested fingerprint representation did not improve
  decision utility over same-observation baselines in this configuration.

**Artifacts:**

- `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` — frozen protocol artifact
- `MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json` — S_eval certification schema
- `data/midweather_fingerprint_lc322_seval_manifest.json` — S_eval manifest for blind solver pack
- `data/midweather_fingerprint_lc322.json` — full result JSON
- `findings/FINDINGS_MIDWEATHER_FINGERPRINT_LC322.md` — findings report
- `tests/test_midweather_fingerprint.py` — 39 protocol tests (all pass at commit 6ca6c28: `pytest` yields 39/39)

**Clean-run status:** all guards passed. Metrics computed. Decision: FAIL.
No evaluator-utility claim is made. The clean negative result is the contribution.

# Discussion

## Hardening Sequence Summary

The paper presents three evidence stages that progressively harden the protocol:

| Stage | Evidence                               | Protocol Status                         | Result                                  |
|-------|----------------------------------------|-----------------------------------------|-----------------------------------------|
| 1     | DOCTOR/BIMARISTAN history (E0, E1, E2) | Exploratory / diagnostic                | Motivates the question; no clean claim  |
| 2     | Midweather retrospective audit         | Contaminated / retrospective            | Negative/inconclusive boundary marker   |
| 3     | Midweather-Fingerprint clean gate      | Clean (frozen K, external blind S_eval) | FAIL: C ties baselines on decision_loss |

Stage 3 is the main result. The clean result stands on Stage 3 alone. Stages 1--2 explain why the Stage 3 protocol
was necessary; they are not treated as convergent or cumulative evidence. A reader should read the hardening
sequence as methodological narrative, not an accumulating proof.

## Evidence Stage 3: Midweather-Fingerprint Clean Gate Interpretation

The protocol verdict is unambiguous: FAIL under the predeclared primary decision utility rule. Under the declared
protocol, structured fingerprint features did not improve decision utility over same-information raw baselines. The
relevant comparison is:

- C_structured_fingerprint: decision_loss = 1.0 (1 wrong accept out of 30 solvers)
- B1_count, B2_calibrated_count, B3_raw_pf_vector: decision_loss = 1.0 (same)
- C does not strictly beat every baseline → FAIL per protocol rule

C has lower secondary RMSE (0.024 vs baselines' 0.030--1.334) and MAE (0.008 vs baselines'
0.009--1.332) in this run, but the declared primary utility is decision_loss, where C ties
B1/B2/B3 and therefore fails per protocol. The dissociation between prediction accuracy and
decision utility is the paper's main finding: an evaluator optimizing RMSE would prefer C,
but an evaluator optimizing accept/reject decisions under the declared utility function would
find no improvement over the simplest baselines.

C's lower RMSE shows that the structured representation retained predictive signal. However,
the paper's declared object is not continuous failure-rate estimation; it is ACCEPT/REJECT
decision utility. RMSE would justify C only under a different deployment objective. Under
the stated objective, it remains secondary and cannot reverse the FAIL verdict.

Strict improvement was chosen to avoid claiming evaluator utility from a tie. Under a weaker criterion, the result
would become "no demonstrated improvement" or "inconclusive," not "pass." The declared protocol therefore treats
equality with the best simple baseline as a failure to demonstrate added utility.

The strongest decision-loss tie is against B1/B2/B3, which use less structural information than
C (pass/fail counts only, no axis metadata or deformation labels). The equal-tensor baselines
B4/B5/B6 receive the same axis/deformation tensor as C, but they are degenerate in this run
(all-ACCEPT or all-REJECT). Thus, the FAIL verdict is not that C loses to a well-performing
equal-information tensor policy; it is that C's additional structured information does not improve
the final ACCEPT/REJECT decision over simpler lower-information raw baselines under this
floor-limited solver pack.

The result is K-local to the declared protocol (LC322, $B=15$, 30 external blind solvers, six
fingerprint axes, rejection threshold at 0.05, minimum accept rate at 0.2). Changing any of
these conditions could produce a different result. The paper claims only that under this
specific frozen protocol, the tested fingerprint representation did not provide decision utility.

## Primary Alternative Interpretation: Floor-Limited Decision Task

The clean solver pack is strongly acceptance-skewed: 27/30 solvers satisfy the ACCEPT criterion and only 3/30
are reject-class solvers. This makes the decision task low-variance. Once a simple raw baseline identifies nearly
all reject-class behavior, the remaining possible improvement is one decision error. Therefore, the clean FAIL
verdict should be read precisely: C did not strictly improve the declared decision utility in this LC322 gate.
The result does not distinguish a universal absence of fingerprint value from a setting in which the solver
population is too easy or too skewed for fingerprint value to become visible at the decision layer.

This does not rescue C. It bounds the interpretation. The tested fingerprint ontology still failed to improve
the decision it was evaluated on.

## E0: Representation-Sensitivity Observation (Evidence Stage 1 Context)

E0 is a `MEASUREMENT_OBSERVATION_ONLY`: all six solvers pass 88/88 on the expanded suite, but trajectory representation
separates them. There is no evidence that trajectory separation predicts future failure, robustness, external labels,
or correctness improvement.

In E0.K0, pass-rate metric $M_{0a}$ is identical across all listed solvers, while $M_{0b}$ separates the listed solver
groups under a different representation $R$. The result is K-local: it does not claim external LC322 solver
classification. E0 is therefore not a claim that one fixed metric remains invariant across all representations. It shows
that a stable output-pass representation can conceal distinctions exposed by a trajectory representation; the target
interpretation depends on $R$.

Practical implication: an evaluator reporting this stack should not treat the uniform expanded-suite pass rate as the
sole proxy; the report should state that output agreement is invariant across the listed solvers while the trajectory
representation separates solver groups under the tested representation.

E0 limitation: the expanded suite, solver population, and grouping are internal to the repository. The result shows
separation inside $K_0$ only. It does not validate the solver groups externally, show that the trajectory representation
improves correctness judgment over a complete oracle, or close the LC322 failure space for new solver populations.
These limitations motivated the hardening to Evidence Stage 3.

## E1: Conditioning Within R Exposes Proxy Confound Structure (Evidence Stage 1 Context)

Supported by E1.K1 as a within-$K$ observation.

Unlike E0 and E2, E1 does not change a $K$ component. It conditions on variables within the fixed set $R_1$. The result
revises the earlier `zero_crossing_frequency` interpretation: across the wider sweep, `zero_crossing_frequency` and
`collision_density` co-vary by construction, and conditioning on `collision_density` removes the marginal association of
`zero_crossing_frequency`. `max_collision_depth` remains associated within `zero_crossing_frequency`
bins ($r=0.890$--$0.944$), but the bin sizes are small ($N=18,10,6$). This is a representation-internal structure
observation, not a $\Delta K$ invariance test, and it is conditional/correlational rather than causal mechanism
identification.

E1 strengthened the motivation for Evidence Stage 3 by demonstrating why $R$ is load-bearing: the variables inside $R$
are not
independent probes of divergence; they interact through confounded construction. A clean gate had to control for
$R$ by freezing it and testing decision utility directly.

<!-- Claim 2 removed — E2 demoted to Appendix B -->

<!-- Two-coordinate invariance section removed — E2 is now appendix only -->

## Ontological Closure: Measurement Without Utility

Doctor/Bimaristan should be read here as a failure analysis of an evaluator ontology. Earlier stages showed that
solver behavior can be represented, separated, labeled, and stress-tested under a fixed evaluation stack. Those
facts are not enough to establish evaluator utility. A representation can be measurable without improving the
decision that the evaluator is supposed to make.

The final Midweather-Fingerprint gate forced the project through the core utility question: does the structured
fingerprint layer improve ACCEPT/REJECT decisions over simple raw baselines under the same observation budget?
Under the reported LC322 protocol, it did not. C_structured_fingerprint tied the strongest raw baselines on the
primary decision utility, while its RMSE advantage remained secondary under the declared decision rule.

This closes the Doctor/Bimaristan evaluator-utility claim in the tested setting. The correct interpretation is not
that the system found no structure. It found structure, but the structure was not shown to be useful as a solver
evaluator. The tested ontology generated vocabulary and measurements; the hardened gate showed that those
measurements did not improve the decision layer.

The result is stronger than a statistical tie alone. C required additional ontology, feature extraction, axis design,
and maintenance burden, while the best raw baselines reached the same primary decision loss using simpler
observations. Without primary decision improvement, the structured layer did not earn its added complexity.

This distinction is the central lesson of the paper: diagnostic structure is not equivalent to decision utility.
A solver-evaluation system must improve a decision over a simple baseline, not merely produce a richer description
of solver behavior.

## Practical Lesson

The methodological takeaway is to ask the utility question before expanding the ontology. A structured evaluator
should not be credited merely because it creates labels, probes, fingerprints, or separable representations. It
should be credited only if those structures improve a concrete decision over a simple baseline.

In this case, the decisive question was ACCEPT/REJECT utility under a fixed observation budget. The structured
fingerprint layer did not strictly improve that decision over the strongest raw baselines. Therefore, the paper
treats Doctor/Bimaristan as a documented utility failure, not as a system awaiting another reframing.

## Generalization

All claims are non-transferable outside observed K-space unless independently revalidated under a new stack $K'$.

## Oracle Consistency

$O$ defines correctness only within $K$; $O$ is not a semantic ground truth function. All correctness in this paper
means agreement with internal $O$ under $C$.

# Threats to Validity

## Construct Validity

The observation target is instrument-relative. It is not an independent ontology of program behavior. Correctness means
test-empirical consistency with the internal oracle under the current comparator, not semantic truth. Solver classes,
collapse labels, and failure manifolds are therefore instrument labels defined by the evaluation stack, not externally
validated natural kinds.

## Internal Validity

The same ecosystem defines solvers, generators, oracles, comparators, and metrics. This creates instrument
self-consistency bias. The evidence in E0–E2 is therefore treated as artifact-level behavior of the evaluation system,
not as independent validation of solver classes or external correctness.

## Project-Mechanics Limitations Not Directly Exercised by E0–E2

Repository audits identify broader project-mechanics risks outside the main evidence path, including the historical LC45
perturbation-validity error, the fact that perturbation-stability comparisons depend on output-preserving
transformations, and raw Python `==` oracle-alignment behavior that can mix boolean and numeric domains (for example,
`1 == True`). These findings constrain trust in the broader DOCTOR project, but they are not all direct failure modes of
the three reported experiments: LC45 is not part of E0–E2, bool/numeric comparator mixing is a general comparator risk,
and pre-existing test failures do not by themselves falsify the reported artifact tables. They are reported to bound the
project mechanics rather than to retroactively invalidate the main observations.

## K-Space Coverage

The Stage-1 exploratory experiments (E0, E1, E2) vary at most two K-coordinates: one representation change ($R$) in
E0 and one perturbation-family change ($F$) in E2. The clean Evidence Stage 3 gate fixes all K-coordinates and tests the
fingerprint representation under that fixed stack. Within each reported experiment, $O$ and $C$ are fixed for that
experiment. Across experiments the comparator differs: E0 uses output equality, E1 uses a divergence calculation,
E2 uses an AUC scorer over transfer rankings, and the clean gate uses output equality. The overall paper therefore
does not hold $O$ and $C$ constant across all experiments — only within each experiment.

## External Validity

This study does not claim external validity beyond the defined K-space. The repository evidence reported here does not
include third-party benchmark validation, EvalPlus execution, LiveCodeBench execution, an independent
metamorphic-testing baseline, independent oracle comparison, or non-repository replication.

## Statistical Validity

The experiments use heterogeneous statistics: pass rates, AUCs, CIs, and conditional correlations. No unified inference
framework or multiple-comparison correction is claimed. E2 artifacts provide condition-level bootstrap confidence
intervals from 500 resamples, and the post-audit `compute_e2_delta_ci.py` script computes cross-condition delta
confidence intervals. All six E2 cross-condition delta intervals cross zero at 95%, including the reported
point-estimate deltas of -0.577665, -0.312201, and +0.179688. Therefore, E2 does not support a statistically significant
non-invariance claim; it supports only directional boundary sensitivity with uncertain magnitude. E0 and E1 lack matched
uncertainty treatment, so cross-experiment comparisons should not be read as a single inferential model.

## Reproducibility

The repository has artifacts and scripts but no single end-to-end reproduction command. Per-experiment runners exist,
but regenerating the paper's evidence requires manual orchestration; no Makefile, `pyproject.toml`, `tox.ini`,
`pytest.ini`, or `setup.py` entrypoint is available in the repository root. The examined runner scripts insert the
project root into `sys.path` at runtime, making execution path-dependent. `ARTIFACT_MANIFEST.lock` pins SHA256 checksums
for the paper-cited files at the analyzed commit, but reproduction still depends on access to the matching repository
state and local execution environment.

The following test scopes apply to the repository (do not conflate):

| Scope                            | Command                                               |         Key result          | Meaning                                                                          |
|----------------------------------|-------------------------------------------------------|:---------------------------:|----------------------------------------------------------------------------------|
| Historical repository Track A    | archival state                                        | 6 failures across 26 tests  | broader repo test state (archival, not all scoped to this paper)                 |
| Historical targeted pytest audit | archival state                                        |   14 pass, 2 skip, 0 fail   | subset of Track A tests                                                          |
| Midweather-Fingerprint protocol  | `pytest test_midweather_fingerprint.py`               | 39/39 pass (commit 6ca6c28) | clean-gate guard and correctness tests                                           |
| Repair regression suite          | `pytest test_comparator_regression.py` + oracle duels |         45/45 pass          | mechanical consistency of typed comparators, perturbation registry, oracle duels |

One collection error was recorded for a scratch file (`test_euler_4.py`) that calls `sys.exit(0)` at module level
and is not part of the test suite. The repository session state also records pre-existing failures in
`test_doctor_pipeline.py` and `test_sandbox_executor.py`; those failures are not resolved by the targeted audits.

OpenCode found no direct A* solver definitions in the Python files. The E2 $K$ definition references H2/H3
heuristic-family runs and grid generators; if those live outside the project workspace, then E2 is not fully
reproducible
from this workspace alone. The paper therefore treats E2 as artifact-level evidence tied to the recorded AUC, audit, and
delta-CI artifacts rather than as a self-contained reproduction path.

## Baseline Limitation

The LC322 expanded-suite baseline is internal: 88 cases, including 31 large-amount cases, against the repository's known
solver population. The solver population is treated as an internal repository population; this paper does not establish
external provenance for solver generation, model version, prompt history, human editing, or selection procedure. No
third-party EvalPlus, LiveCodeBench, CodeContests+, metamorphic-testing baseline, independent oracle comparison,
non-repository solver population, or external benchmark execution is included. A new solver population could expose
failure surfaces not covered by the current artifacts.

## Clean Gate Threats

The Evidence Stage 3 clean-gate result is subject to the following scoped limitations beyond those discussed above:

- **Floor effect / low reject prevalence.** The clean S_eval pack contains 27 ACCEPT-class solvers and only 3
  REJECT-class solvers. Decision_loss therefore has very coarse resolution. C can strictly improve over the best
  simple baseline only by reducing the remaining one wrong accept to zero. This makes the gate conservative and
  low-powered for detecting marginal fingerprint value. The verdict remains FAIL under the declared protocol, but
  the interpretation is local: C failed to demonstrate added utility in this skewed LC322 pack.
- **Single problem (LC322).** The result may not transfer to other Coin Change variants or other problem domains.
- **Single generated external blind solver pack (30 solvers from one LLM).** A different solver population, different
  generation procedure, or different LLM provider could produce different decision outcomes.
- **LLM pretraining / non-naive solver population.** External blind means blind to DOCTOR/BIMARISTAN artifacts, not
  naive with respect to LC322. Coin Change is a common programming problem, and the Claude-generated solver pack may
  reflect pretrained familiarity with standard dynamic-programming solution patterns. The high ACCEPT prevalence may
  therefore reflect the generator's prior exposure to LC322-like solutions rather than a general solver population.
- **Single budget point ($B=15$).** Results may differ at other observation budgets.
- **Single decision type (ACCEPT/REJECT).** Other decision types (rank, select top-K, continuous score) were not tested.
- **Single failure threshold (0.05) and single minimum accept rate (0.2).** Different thresholds change the utility
  trade-off and could favor different estimators.
- **Fingerprint axis selection is a design choice.** The six axes (reachability, order, magnitude, boundary, transition,
  memoization) were derived from the problem specification but remain a choice among possible axis sets.
- **Axis-design contamination.** The clean gate freezes the budget, solver pack, estimator set, and decision rule
  before metric computation, but the fingerprint axes were designed after earlier DOCTOR/BIMARISTAN LC322 exploration.
  Therefore, Stage 3 is clean as an execution gate, not as a fully prospective representation-design study. Prior
  exposure may have influenced which axes were considered worth encoding.
- **Same-information asymmetry in the effective comparison.** C is a deterministic feature layer over the full
  observation tensor, and B4/B5/B6 receive the same tensor. However, the baselines that tie C on decision_loss
  are B1/B2/B3, which use less information. The clean result therefore shows that C's extra structure did not
  improve the decision over simpler baselines; it does not show that a strong equal-tensor raw policy beat C.
- **Same-information baselines may not cover all possible policies.** B0--B6 are a reasonable set but do not exhaust
  the space of functions over the observation tensor.
- **C's RMSE improvement is secondary under the declared decision spec, but could become primary utility under a
  different decision spec.** The result is specific to the ACCEPT/REJECT decision_loss formulation.
- **Coarse decision resolution.** The clean S_eval contains 30 solvers and the best estimators differ by at most
  one decision error. Decision_loss therefore has coarse resolution: the result supports no strict-improvement
  claim, but it should not be read as a precise estimate of effect size. Combined with the floor effect above,
  the evaluation design has limited power to detect a one-decision improvement even if fingerprints genuinely help.

These limitations bound the claim: the negative result holds under the specific LC322 $B=15$ EXTERNAL_BLIND_PACK
configuration reported. Changing any of these conditions requires independent re-evaluation.

# Conclusion

This paper presents a hardening sequence across three evidence stages, ending in one clean negative case study.

**Evidence Stages 1--2 (exploratory/contaminated background):** The earlier DOCTOR/BIMARISTAN experiments
(Stages 1--2) motivated why causal separation and same-information baselines are necessary. No clean claim is made
from these stages; they are methodological background only. See Appendix B for full detail.

**Evidence Stage 3 (clean gate, the paper's main result):** The Midweather-Fingerprint gate tested structured
fingerprint features against same-observation baselines B0--B6 under a frozen observation budget ($B=15$),
external blind S_eval (30 solvers, EXTERNAL_BLIND_PACK certification), and ACCEPT/REJECT decision utility.
All protocol guards passed.

Result: FAIL. C_structured_fingerprint ties B1/B2/B3 on decision_loss (1.0). The protocol requires strict
improvement on the primary utility metric. RMSE improvement (secondary) does not override.

The paper's contribution is a clean, scoped negative case study:

> Under this LC322 gate, the tested fingerprint representation did not strictly improve the predeclared
> ACCEPT/REJECT decision loss over the best raw baselines; because the solver pack had only three reject-class
> solvers, the result should be read as a strict-gate failure under a floor-limited decision setting, not as
> evidence that fingerprint representations are generally useless.

This is the closure point for the Doctor/Bimaristan evaluator claim. The project demonstrated that structured
solver behavior can be measured, labeled, and organized, but the hardened gate did not show that this structure
improves the evaluator's decision. The result is therefore a utility failure, not a measurement failure: the
system produced an ontology, but the ontology did not earn its cost at the decision layer.

A deliberately balanced or adversarially selected solver pack could test a different hypothesis about when
fingerprints become useful, but it would not change the conclusion of this paper. This paper closes the tested
Doctor/Bimaristan evaluator-utility claim under the reported LC322 gate.

No claim extends beyond the observed K-space without independent revalidation under $K'$. The paper does not
claim that fingerprint-based solver evaluation generally fails, that Doctor/Bimaristan is repaired, or that
the result transfers to other problems, solver populations, or evaluation schemes.

## Verification Table: Anchor Level and Evidence Stage

The following table anchors all paper claims. "Anchor Level" measures oracle independence (0–4, defined below).
"Evidence Stage" marks the hardening protocol stage (1–3) for the Midweather evidence chain. Every claim must be
read through both columns.

| Evidence                 | Anchor Level | Evidence Stage | Claim allowed                                    |
|--------------------------|:------------:|:--------------:|--------------------------------------------------|
| LC322                    |      2       |       —        | bounded local oracle agreement                   |
| LC3928                   |      2       |       —        | bounded local oracle agreement                   |
| CF2230F                  |      2       |       —        | bounded local oracle agreement                   |
| LC42                     |  0 (unfix)   |       —        | no correctness claim                             |
| E0                       |  2 / 0 util  |       1        | representation sensitivity                       |
| E2                       |      0       |       1        | exploratory only                                 |
| Midweather retrospective |      2       |       2        | contaminated audit, negative/inconclusive        |
| Midweather-Fingerprint   |      2       |       3        | clean LC322 gate, FAIL — no decision improvement |
| external evaluator       |      0       |       —        | drop                                             |

**Anchor Level definitions:**

- **Anchor Level 0**: Internal only / circular. No independent anchor.
- **Anchor Level 1**: Official-sample anchored.
- **Anchor Level 2**: Independent local anchor (same-repo oracle duel or brute-force ground truth).
- **Anchor Level 3**: Strong independent implementation anchor (outside reference solver).
- **Anchor Level 4**: External judge / benchmark validation.

Note: Midweather-Fingerprint is Evidence Stage 3 (clean protocol) but Anchor Level 2 (local oracle anchoring
via `correct_dp`). It does not claim Anchor Level 3 because the oracle is an internal DP reference, not an
outside reference solver.

**Upgrade path:** Level 3/4 requires independent outside reference solvers (Level 3) or external judge/benchmark checks
(Level 4). The best next evidence upgrade is to take LC322, LC3928, CF2230F generated cases and run them through known
accepted/reference solutions or an external judge where possible, storing outputs and provenance. Only then claim
anything beyond Level 2.

**Note on passing tests:** **45/45 broader repository regression tests pass** (LC42 oracle duel: 9, comparator
regression: 17,
perturbation validity: 4, LC322 duel: 6, CF2230F duel: 4, LC3928 duel: 5). These are a separate scope from the 39
Midweather-Fingerprint protocol tests. They confirm mechanical consistency of the repairs. They do **not**
upgrade Doctor to Anchor Level 3 or Level 4. Passing tests are necessary for claiming correctness of implementation, not
sufficient
for claiming external validity. Do not add more internal tests and present them as validation — that would repeat the
earlier problem.

# References

Wang, Z., Liu, S., Sun, Y., Li, H., and Shen, K. (2025). CodeContests+: High-Quality Test Case Generation for
Competitive Programming. *arXiv preprint arXiv:2506.05817*. <https://arxiv.org/abs/2506.05817>

Shi, J., Yin, X., Huang, J., Zhao, J., and Tao, S. (2026). CodeHacker: Automated Test Case Generation for Detecting
Vulnerabilities in Competitive Programming Solutions. *arXiv preprint arXiv:
2602.20213*. <https://arxiv.org/abs/2602.20213>

Hort, M. and Moonen, L. (2025). Codehacks: A Dataset of Adversarial Tests for Competitive Programming Problems Obtained
from Codeforces. *arXiv preprint arXiv:2503.23466*. <https://arxiv.org/abs/2503.23466>

Liu, J., Xia, C. S., Wang, Y., and Zhang, L. (2023). Is Your Code Generated by ChatGPT Really Correct? Rigorous
Evaluation of Large Language Models for Code Generation. *NeurIPS 2023 / arXiv:2305.01210*.
<https://arxiv.org/abs/2305.01210>

Jain, N., Han, K., Gu, A., Li, W.-D., Yan, F., Zhang, T., Wang, S., Solar-Lezama, A., Sen, K., and Stoica, I. (2024).
LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code. *arXiv preprint
arXiv:2403.07974*. <https://arxiv.org/abs/2403.07974>

# Appendix A. Full K Definitions and Experiment Registry

## E0

    K0 = (
      P = LC322 Coin Change,
      S = {
        lc322_canonical_dp,
        lc322_sorted_coin_outer_dp,
        lc322_reverse_coin_outer_dp,
        lc322_amount_outer_equivalent_dp,
        lc322_bfs_shortest_path,
        lc322_recursive_memo_exact
      },
      G = expanded LC322 suite, 88 cases, 31 large-amount cases,
      O = LC322 expected outputs in findings/FINDINGS_141.md,
      C = output equality,
      R = {output pass rate, trajectory representation at n2..n8},
      F = none for output-suite baseline
    )
    M0 = {pass rate, silhouette, same-group NN, mean gap}
    T_obs0 = T_obs.equivalence_class

**Artifacts:**

- `findings/FINDINGS_141.md`

- `data/lc322_true_case_b_test.json`

- `runners/run_lc322_true_case_b_test.py`

- `solvers/lc322_true_case_b_solvers.py`

## E1

    K1 = (
      P = LC560 Subarray Sum Equals K,
      S = {lc560_prefix_map, lc560_sliding_window},
      G = wider 50-array partial-dependence sweep,
      O = LC560 repository oracle,
      C = divergence calculation in artifact,
      R = {
        zero_crossing_frequency,
        collision_density,
        max_collision_depth,
        divergence
      },
      F = LC560 sign/k perturbation axes in artifact
    )
    M1 = conditional Pearson correlation
    T_obs1 = T_obs.failure_manifold

**Artifacts:**

- `findings/FINDINGS.md` Entry 016

- `doctor/scratch/lc560_partial_dependence_v2.py`

- `runners/run_lc560.py`

- `doctor/adversarial/lc560_candidates.py`

## E2 (Exploratory — Appendix B)

    E2 =
    (K2, Delta K2, M2, T_obs.equivalence_class, O2, C2, R2, F2,
     observation2, control2, delta2, effect_size2)

**K2:**

    P = grid-based A* search corpus
    S = H2/H3 heuristic-family runs
    G = 20x20 and 40x40 grid generators
    O = degenerate/non-degenerate label in artifact
    C = AUC scorer over transfer ranking
    R = {g_at_current_std, fspread_mean}
    F = {
      native proportional boundary,
      depth_matched boundary,
      normalized_progress boundary
    }

**$\Delta K_2$:**

    Delta F_boundary =
       40x40 native proportional ->
       40x40 depth_matched ->
       40x40 normalized_progress

**$M_2$ = balanced transfer AUC.**

**Layer A observation$_2$:**

    normalized_progress prefix_length / total_trajectory_length = 1.000 in 98/100 runs

Audit note: the 40$\times$40 `normalized_progress` condition is reported as a boundary audit result, not as valid prefix
evidence. Because 98/100 runs consumed the full trajectory, the AUC of 1.000 is a full-information artifact rather than
an onset-detection result.

**Layer B $\delta_2$:**

    Delta native-depth_matched H2->H3 = -0.577665
    Delta native-depth_matched H3->H2 = -0.312201
    Delta native-normalized_progress H2->H3 = +0.179688
    Bootstrap delta-CI audit: all six cross-condition E2 delta CIs cross zero at 95%

**Layer C statement$_2$:**

    E2 produced directional artifact-level observations; no statistically supported
    boundary claim is made. normalized_progress is disqualified as valid prefix evidence.

**Artifacts:**

- `data/phase4_experiment2_auc_results.json`

- `findings/FINDINGS_143.md`

- `findings/FINDINGS_144.md`

- `findings/FINDINGS_145.md`

- `run_phase4_experiment2_auc_controls.py`

- `compute_e2_delta_ci.py`

## Project Status (Frozen)

Doctor is not an externally validated evaluator. No evaluator-utility claim is supported.
The clean Midweather-Fingerprint gate produced a negative result: fingerprint features did not improve
decision utility over same-information baselines in the tested LC322 configuration.
Selected oracle artifacts have internal anchoring, but they do not affect the paper's main negative decision-utility
result. All repairs are mechanically verified — **45/45 regression tests pass** (broader repository scope, distinct
from the 39 Midweather protocol tests). These confirm consistency only; they do not affect the paper's main result.

## Supporting LC322 Known-Population Probe Basis

This appendix item supports the case-study context but is not one of the three main claims.

    P = LC322 Coin Change
    S = known 10-solver LLM population from BENCHMARK_SNAPSHOT.md
    G = LC322 Bimaristan generators
    O = LC322 DP reference
    C = output equality
    R = divergence rates by named manifold
    F = six-family LC322 probe basis
    T_obs = T_obs.failure_manifold
    M = per-manifold divergence rate

**Observation:**

    Total candidates = 53
    Greedy divergence rate = 54.72%
    DP divergence rate = 0.00%
    bfs_coin_count_cutoff target failures = 12/12
    named non-target failures under search/resource truncation = 0/12 and 0/12

**Artifacts:**

- `BENCHMARK_SNAPSHOT.md`

- `runners/run_lc322.py`

- `data/lc322_opt_c_survivor_local_dominance.json`

- `data/lc322_search_resource_truncation_probe.json`

## Supporting Prefix-Estimator Audit

This appendix item supports context but is not one of the three main claims.

    P = grid A* search
    S = H2/H3 runs
    G = 20x20 and 40x40 grid corpora
    O = degenerate/non-degenerate labels
    C = AUC scorer
    R = g_at_current_std, fspread_mean, prefix-estimator boundaries
    F = H-B, H-C, scale-transfer prefix-estimator conditions
    T_obs = T_obs.equivalence_class
    M = AUC

**Observation:**

    H-B baseline best AUC = 0.976500
    H-C audit best AUC = 0.962000, failed FM-3 audit
    scale transfer best AUC = 0.973000
    distributional overlap: AUC_hb = 0.976500, AUC_retro = 0.976500, delta = 0.000000

**Artifacts:**

- `experiments/phase5_*_prefix/FINDINGS_phase5.md`

- `experiments/phase5_resolution/FINDINGS_resolution.md`

- `findings/FINDINGS_146.md`

## Appendix C. v0.3 Sealed-Envelope Validation (Not Part of Main Evidence Chain)

A separate sealed-envelope validation, v0.3, tests whether the measurement discipline transfers to internally sealed
unseen cases. The one-time hidden validation passes on 63/63 cases across five declared families (dp\_recurrence,
graph\_shortest\_path, greedy\_trap, state\_space\_search, combinatorics\_counting) with 63/63 oracle-duel agreements,
63/63 exact solver passes, 0 exact solver failures, 63/63 provenance completeness, and no hard stops triggered. The seal
hash is confirmed, hidden\_opened is true, hidden\_validation\_run is true, and rerun\_allowed is false.

This result is not part of the Midweather evidence chain and does not affect the paper's main negative
decision-utility finding. It is included for repository completeness.

# Primary Repository Artifacts

## Clean-Gate Artifacts (Midweather-Fingerprint)

- `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` — frozen protocol artifact
- `MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json` — S_eval certification schema
- `data/midweather_fingerprint_lc322_seval_manifest.json` — S_eval manifest for blind solver pack
- `data/midweather_fingerprint_lc322.json` — full result JSON
- `data/midweather_fingerprint_lc322_probe_index.json` — frozen probe index
- `tests/test_midweather_fingerprint.py` — 39 protocol tests
- `runners/run_midweather_fingerprint_lc322.py` — clean-gate runner

## Historical Artifacts

- `DOCTOR_EPISTEMIC_CONSTRAINTS.md`
- `DOCTOR_CANONICAL.md`
- `BENCHMARK_SNAPSHOT.md`
- `SESSION_STATE.md`
- `doctor/adversarial/ingestion_gate.py`
- `doctor/adversarial/perturbation_validity.py`
- `doctor/adversarial/DRIVER_CONTRACT.md`
- `doctor/adversarial/experiment_contract.py`
- `doctor/adversarial/experiment_runner.py`
- `findings/FINDINGS.md`
- `findings/FINDINGS_058.md` through `FINDINGS_064.md`
- `findings/FINDINGS_139.md` through `FINDINGS_146.md`
- `REPRODUCE.md`
- `SOLVER_MANIFEST.json`
- `ARTIFACT_MANIFEST.lock`
- `compute_e2_delta_ci.py`
- `experiments/phase5_causal_prefix/FINDINGS_phase5.md`
- `experiments/phase5_resolution/FINDINGS_resolution.md`
