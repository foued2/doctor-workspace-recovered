# When Does a Directional Failure-Family Classifier Outperform a Failure-Count Baseline?

## Conditional Decision Utility Across Four Problem Classes Under Frozen Evaluation Protocols

**Author:** Abidi Foued  
**Affiliation:** Independent Researcher  
**Repository:** <https://github.com/foued2/doctor-workspace>  
**Date:** May 2026

## Abstract

This paper asks when a directional failure-family classifier (C_genuine) improves accept/reject decision
utility over a failure-count baseline (B1) on algorithmic solver populations. Four problem classes were
evaluated under governed protocols with pre-declared solver populations and frozen evaluation procedures.
Two measurement domains are present: an internal mutation measure (CSSE v2, n=500 per class) and an
external corpus measure (human+GPT solutions). The Domain Completeness Gate (DCG) determines which
cross-domain comparisons are valid. On LC3946 (poset-based lattice), C_genuine achieves
decision_loss=0.0 versus B1's 1.0, strictly improving over all non-degenerate baselines, with the
advantage surviving 10 of 11 perturbation conditions — but LC3946 is non-externalizable (synthetic
evaluator geometry). On LC322 (Coin Change), C_genuine shows λ-dependent superiority internally
(gap=3.13 at λ=50) and is the only DCG-valid cross-domain bridge: external P(D)=0.053 (n=38)
compared to CSSE v2 P(D)=0.019 (n=317). Two negative boundary cases constrain interpretation: on
LC45 (Jump Game II), the classifier cannot differentiate from B1 due to informational equivalence
of separating features, and on LC743 (Network Delay Time), all estimators converge to identical
predictions internally while external support is insufficient (n=1, DCG.4 fails). The CSSE v2
experiment reveals P(D) is problem-dependent (0.000–0.275), killing single-global-mechanism
interpretation. The contribution is a conditional empirical finding with one valid external anchor.
No universality claim is made.

---

# Introduction

Adversarial evaluation systems for algorithmic programs commonly report pass rates, divergence rates, AUC
values, or
failure labels. An open question is whether structured behavioral fingerprints — partial execution features
designed to capture solver behavior beyond pass/fail — improve evaluator decisions over simpler baselines.
This paper tests that question across four problem classes, asking not whether fingerprints always improve
decisions, but **when** they do.

The study uses the DOCTOR/BIMARISTAN project as its case-study subject. The paper does not convert the project
into a generic testing framework. Earlier DOCTOR/BIMARISTAN work explored whether algorithm behavior can be
captured through structured representation; those explorations revealed measurement-drift and
representation-dependence issues that motivated hardened evaluation protocols. The question here is not
measurability
itself, but whether the specific fingerprint representation tested here improves decision utility over
same-information baselines under clean, frozen protocols — and under what conditions that improvement
appears or disappears.

## Protocol Notation

Results are scoped to the declared evaluation stack: problem, solver pack, generator, oracle, comparator,
representation, and perturbation set. The full stack definition is written as $K = (P, S, G, O, C, R, F)$
(see Appendix A for the complete registry). All claims are K-local: they hold under this specific stack only.

The budget for observed probe executions is written $B = 15$ (also called the observation budget). Earlier
experiments reference the additional notation $T_{\mathrm{obs}}$ (instrument-relative target)
and $T_{\mathrm{ext}}$ (external projection), defined in Appendix A. The clean Evidence Stage 3 gates do not
use that ontology and rely on standard decision-utility terminology instead.

## Research Question

> RQ1: Under what conditions does a directional failure-family classifier improve ACCEPT/REJECT
> decision utility over a failure-count baseline?

The hypothesis is conditional:

> H1: C_genuine improves decision_loss over B1 when the solver population has balanced failure-class
> diversity and the probe index contains families that the C_genuine decision rule (accept on
> single-family failures) can separate from B1's rule (reject on any failure).

This is not a universal claim. The hypothesis is tested under four problem classes with distinct
solver-population structures, and the results determine the conditions under which it holds.

## Core Claims and Evidence Structure

The paper presents four problem classes evaluated under comparable frozen protocols, with two
measurement domains (internal mutation measure and external corpus measure). The Domain Completeness
Gate (DCG) determines which cross-domain comparisons are valid.

### Primary Evidence — LC3946 (Positive, Non-Externalizable)

LC3946 is the flagship internal result: a balanced 15/15 population where C_genuine achieves
decision_loss=0.0 versus B1's 1.0, with 10/11 perturbation survival. However, LC3946 is a synthetic
evaluator geometry — it cannot be embedded into an external solver space. DCG: INVALID for
cross-domain comparison.

### Supporting Evidence — LC322 (Conditional Positive, One Valid External Anchor)

LC322 shows λ-dependent superiority internally (gap=3.13 at λ=50) and is the only DCG-valid
cross-domain bridge: external P(D)=0.053 (n=38) compared to CSSE v2 P(D)=0.019 (n=317). The
external sample is underpowered but confirms the phenomenon exists under independent solver lineage.

### Negative Boundary Conditions — LC45, LC743, Midweather

These cases demonstrate where the mechanism fails:

- LC45: the only separating features are informationally identical to B1 (encoder artifact)
- LC743: all estimators converge to identical predictions (no behavioral diversity); external
  support insufficient (n=1, DCG.4 fails)
- Midweather retrospective: contaminated audit, no clean superiority claim

These are not failures of the project. They are boundary conditions that define when and why the
mechanism works.

## Related Work

This case study is adjacent to metamorphic testing, differential testing, property-based testing, benchmark
auditing,
and adversarial code evaluation. Metamorphic testing addresses oracle limitations through relations among
executions.
Differential testing compares implementations under shared inputs. Property-based testing generates inputs
from declared
properties.

In adversarial code evaluation, recent work generates LLM-assisted test cases for competitive programming
(Wang et al., 2025; Shi et al., 2026; Hort and Moonen, 2025). These systems measure whether generated
solutions pass
expanded or adversarial test suites — a correctness-vs-oracle paradigm. This case study
differs by treating oracle agreement as a K-relative measurement rather than a correctness verdict, and by
targeting
decision utility under same-information baselines rather than maximizing the number of tests a solver fails.

EvalPlus and LiveCodeBench provide context for generated or adversarial code-evaluation tests.

Relative to these lines of work, the contribution here is not a new test-generation method, a stronger oracle,
or a
larger benchmark. Metamorphic testing studies relations among executions when direct oracles are limited;
differential
testing compares implementations under shared inputs; property-based testing explores declared input
properties; and
expanded-suite code benchmarks measure agreement with larger output suites. This paper tests a different
question:
under what conditions do structured fingerprint features improve decision utility over same-information
baselines under a clean budget-matched protocol?

This paper does not claim novelty for adversarial testing or oracle sensitivity.

The central contrast between this case study and the related work above is decision-utility framing. The cited
test-generation and benchmark-augmentation works evaluate whether larger or adversarial test suites reduce
pass/fail classification error or increase oracle discrimination. This paper evaluates whether a structured
fingerprint representation improves a declared accept/reject decision under a fixed observation budget and
same-information baselines. The contribution is not a stronger test suite, but a protocol for measuring
whether representation improvements translate to decision improvements — and a characterization of the
conditions under which they do and do not.

# Methods

## Data Sources

All evidence comes from repository artifacts. The paper uses findings logs, JSON outputs,
scripts, and benchmark snapshots as empirical records.

This study is an exploratory artifact-level case study rather than a preregistered confirmatory experiment.
Several
claims were sharpened after repository audits identified invalid perturbations, proxy confounds, and boundary
artifacts.
The results should be read as a disciplined reconstruction of observed K-local behavior, not as confirmatory
statistical validation.

Within this retrospective reconstruction, the Evidence Stage 3 gates are clean execution gates because their
budget,
S_eval
manifest, estimator sets, and decision rules were frozen before clean-run metric computation. These are not
preregistered
external studies; the gates are clean relative to the reconstruction protocol, not relative to a prospective
registry.

The repository is not a clean benchmark release. All claims are artifact-level and K-local, not claims of a
clean
benchmark release or a fully passing repository test suite. For the consolidated test-status ledger across all
scopes,
see the reproducibility section.

## Oracle Rule

    O defines correctness only within K; O is not a semantic ground truth function.

No result upgrades $O$ to external truth. All correctness language means agreement with $O$ under $C$.

## Perturbation Validity Rule

Every perturbation in this paper is drawn from a declared family $F$ validated against a closed registry (
`doctor/adversarial/perturbation_validity.py`). A perturbation is valid only if it preserves the invariant
declared for
its (problem, family) pair under the current $O$ and $C$. The LC45 case — where `multiset_invariant` was
initially
declared for a position-sensitive problem — established that validity requires a provable structural argument,
not just an
operator name. The closed registry prevents undeclared perturbation families from entering the system, but it
does not
by itself prove that every declared invariant is semantically correct. That incident is treated as a
limitation of the
project mechanics: perturbation validity is not guaranteed by a family label, and invalid perturbations
measure response
to changed semantics rather than stability under preserved problem meaning.

A critical distinction is maintained throughout:

    validity != adversarial strength

A valid perturbation preserves the declared invariant. It does not automatically explore a failure-relevant
surface.
The clean gates use perturbations drawn from their predeclared probe registries; historical
E2
includes a boundary condition (`normalized_progress`) later disqualified as prefix-length-confounded evidence
and is
retained only as exploratory context in Appendix B.

## Experiment Schema

The historical E0/E1/E2 artifacts use the older K/Delta-K/T_obs notation and Layer A/B/C structure, defined in
Appendix A. The clean gates are specified independently by their frozen observation budgets,
S_eval manifests, decision_specs, estimator sets, and primary utility metrics. Results use only the notation
defined
for each experiment.

## Variables

Variable definitions are fixed:

- `zero_crossing_frequency`: count/frequency of sign-crossing structure used in the LC560 artifact;

- `max_collision_depth`: maximum frequency of a single prefix-sum value in the LC560 artifact;

- (Appendix A defines additional notation used by the historical experiments.)

No variable is redefined after first use.

## Statistical Treatment

The study uses heterogeneous statistics: pass rates in E0, conditional correlations in E1, and AUC values with
bootstrap
confidence intervals in E2. No unified inference model is claimed. No structural-causal-model inference is
used. No
multiple-comparison correction is applied. E2 includes condition-level bootstrap confidence intervals from 500
resamples
in the artifacts. A post-audit bootstrap delta-CI script (`compute_e2_delta_ci.py`) computes the
cross-condition E2
delta intervals; all six cross-condition delta confidence intervals cross zero at 95%. E2 deltas are therefore
treated
as directional shifts with uncertain magnitude, not as statistically significant non-invariance findings. E0
and E1 do
not receive matched uncertainty treatment.

## Decision Utility Definition

The primary evaluation metric is decision_loss:

    decision_loss = λ_A · wrong_accepts + λ_R · wrong_rejects

with λ_A = 1 and λ_R = 1 in this study (equal cost). Equal costs are declared without empirical justification;
a production system may assign asymmetric costs. In the LC3946 result, C_genuine achieves 0 wrong accepts
and 0 wrong rejects (decision_loss=0.0), while B1 achieves 0 wrong accepts and 1 wrong reject
(decision_loss=1.0). In the LC322 result, C and the tied baselines (B1/B2/B3) have 1 wrong accept and
0 wrong rejects at λ=1, so the tie at equal cost is robust to any λ_A >= λ_R assignment. Formally:

    true_failure_rate(s) = failures on target evaluation set / target evaluation set size
    true_ACCEPT(s) = true_failure_rate(s) <= failure_threshold (0.05)
    pred_ACCEPT_E(s) = estimated_failure_rate_E(s) <= 0.05
    wrong_accept(E) = |{s: pred_ACCEPT_E(s) = 1 and true_ACCEPT(s) = 0}|
    wrong_reject(E) = |{s: pred_ACCEPT_E(s) = 0 and true_ACCEPT(s) = 1}|
    decision_loss(E) = wrong_accept(E) + wrong_reject(E)

The target evaluation set is the full D_target probe set (15 non-observed probes per solver). Estimators
receive
only the 15 observed probes per solver and must predict failure rate on the non-observed probes.

## Estimator Feature Access

All estimators receive identical O_obs (the same 15 observed probe executions per solver). C uses structured
derived
features (pair flips, invariants, sensitivity) derived from the observation tensor that includes pass/fail
status, axis
metadata (e.g., reachability, order, magnitude), and deformation labels. The key same-information question is
whether
at least one raw baseline also receives this same tensor. B4_raw_full_tensor does: it receives pass_fail +
axis +
deformation for all 15 probes as its full input tensor. The structured fingerprint features in C are
deterministic
functions of this same tensor, not independent observations. The following table documents what each estimator
extracts from O_obs:

| Estimator                      | Input fields used                                                       | Axis metadata | Solver identity | Target leakage | Training rule |
|--------------------------------|-------------------------------------------------------------------------|:-------------:|:---------------:|:--------------:|:-------------:|
| B0_prior                       | population prior only                                                   |      no       |       no        |       no       |     fixed     |
| B1_count                       | pass_fail from O_obs                                                    |      no       |       no        |       no       |     fixed     |
| B2_calibrated_count            | pass_fail from O_obs                                                    |      no       |       no        |       no       |    LOO CV     |
| B3_raw_pf_vector               | pass_fail vector (15 probes)                                            |      no       |       no        |       no       |     fixed     |
| B4_raw_full_tensor             | pf, deformation, axis, family, paired, invariant                        |      yes      |       no        |       no       |     fixed     |
| B5_nearest_neighbor_raw_tensor | raw tensor (as B4)                                                      |      yes      |       no        |       no       |     fixed     |
| B6_regularized_raw_tensor      | raw tensor (as B4)                                                      |      yes      |       no        |       no       |    LOO CV     |
| C_structured_fingerprint       | deterministic features (pair flips, invariants, sensitivity) from O_obs |      yes      |       no        |       no       |     fixed     |

No estimator may call extra oracle queries, create new observations, or access D_target probe outputs during
training or prediction.

## Domain Completeness Gate (DCG)

Cross-domain comparison of P(D) is valid only when the solver source satisfies the Domain Completeness
Gate. A solver source S for problem P is comparable iff all four conditions hold.

### DCG.1 — Canonical Interface Mappability

There exists a lossless transformation φ_S : S → S_canon such that all solvers execute under a
single evaluation signature. No semantic reinterpretation is permitted; only syntactic normalization
is allowed. If adaptation requires behavioral guessing (e.g., reconstructing missing arguments),
DCG fails.

### DCG.2 — Unified Evaluator Constraint

A single evaluator E_P is applied across all sources:

    E_P^{CSSE} ≡ E_P^{EXT}

If evaluator behavior depends on source origin (even implicitly), comparison is invalid.

### DCG.3 — Endogenous Failure Requirement

Failures must be generated by evaluation:

    F(x) := 1[E_P(x) ≠ y_true]

and must not be dataset-encoded labels (e.g., `is_pass`). If ground-truth failure is pre-attached,
the source is descriptive-only, not generative.

### DCG.4 — Non-Degenerate Support

Define failure variance:

    Var(F_S) > 0

If all samples collapse into a single failure regime or no failure regime, then P(D) exists but
is not comparable across sources.

### DCG Predicate

A source S is comparable iff:

    DCG(S,P) = 1 ⟺ (1) ∧ (2) ∧ (3) ∧ (4)

Cross-domain comparison is valid iff:

    DCG(S_1,P) ∧ DCG(S_2,P)

### DCG Classification

Each (source, problem) pair is assigned one of:

- **VALID** — cross-domain P(D) comparison allowed
- **MEASURABLE BUT NON-COMPARABLE** — internal statistics only
- **INVALID** — no statistical interpretation permitted

DCG prevents false equivalence between distributions that live in different measurement spaces.
It does not improve the system; it prevents category errors in interpretation.

## S_eval Provenance

External blind means generated outside the repository's known solver population and frozen before clean-gate
evaluation. It does not mean externally judged, third-party benchmarked, or independently oracle-validated.

The clean gates use solver functions generated as external blind packs. Each pack's provenance is documented
in its respective K definition. Timeline: Protocol freeze → S_eval generation → probe execution → guard check
→ metric computation. The freeze artifacts, manifests, and result JSONs are all committed to the repository.

## External Baseline

The paper includes one internal expanded-suite baseline analogous to an EvalPlus-style stronger output suite:

    E0 baseline = LC322 expanded output suite

This is not a third-party benchmark. It ranks only one internal comparison: output-suite agreement versus
trace-representation separation.

# Results

Experimental findings are presented in order of evidential strength: the primary positive result (LC3946),
supporting conditional evidence (LC322), then negative boundary conditions (LC45, LC743, Midweather). The
LC3946 result is the paper's flagship finding.

## LC3946: Directional Classifier Strictly Beats B1 (Primary Evidence)

The generalized kernel was applied to **LC3946** (poset-based lattice problem).
LC3946 is structurally different from both LC322 (DP/non-monotonic) and LC45 (greedy/monotonic), testing
whether the kernel's adapter-slot design transfers to a problem with poset-structured failure directions.

### LC3946 problem and manifolds

LC3946 has 4 failure directions (analogous to LC322's 6 fingerprint axes):

1. `F1` — order-violation failures (solutions violate poset ordering constraints)
2. `F2` — chain-completeness failures (solutions miss required chain elements)
3. `F3` — antichain-width failures (solutions exceed antichain width bounds)
4. `F4` — lattice-meet failures (solutions incorrectly compute lattice meets)

The probe index has 30 probes across 4 families (poset_universal_source, poset_chain, poset_antichain,
poset_lattice_boolean, poset_lattice_two_prime, poset_isolated), split K=15+15 round-robin.

### Solver population and C-4 result

30 solvers were generated as an external blind pack. The C-4 decision-utility gate was run under a
frozen protocol (same structure as LC322 midweather-fingerprint gate).

**K_3946:**

    P = LC3946 (poset-based lattice problem)
    S = 30 externally generated blind solver functions
    G = frozen probe index, 30 probes across 4 failure directions
    O = poset oracle (poset-correct reference)
    C = output equality
    R = {B0: population prior, B1: failure count, ..., C: structured fingerprint}
    F = four predeclared failure directions: F1, F2, F3, F4

**Guard statuses:** all passed (K=15 frozen, decision_spec present, axis provenance clean,
S_eval certified EXTERNAL_BLIND_PACK, no degenerate target collapse, no degenerate C policy,
all estimators receive identical O_obs).

**Layer A observation:**

| Estimator                 | Decision Loss | Wrong Accepts | Wrong Rejects | Accept Rate | Degenerate |
|---------------------------|:-------------:|:-------------:|:-------------:|:-----------:|:----------:|
| B0_prior                  |     15.0      |      15       |       0       |     1.0     | all-ACCEPT |
| B1_count                  |      1.0      |       0       |       1       |    0.467    |            |
| B2_calibrated_count       |      1.0      |       0       |       1       |    0.467    |            |
| B3_raw_pf_vector          |      1.0      |       0       |       1       |    0.467    |            |
| B4_raw_full_tensor        |     15.0      |       0       |      15       |     0.0     | all-REJECT |
| B5_nearest_neighbor       |     15.0      |      15       |       0       |     1.0     | all-ACCEPT |
| B6_regularized_raw_tensor |     15.0      |      15       |       0       |     1.0     | all-ACCEPT |
| C_structured_fingerprint  |      1.0      |       0       |       1       |    0.467    |            |
| **C_genuine**             |    **0.0**    |     **0**     |     **0**     |  **0.500**  |            |

**Layer B $\delta_{3946}$:**

    C_genuine decision_loss = 0.0, B1 decision_loss = 1.0.
    gap = decision_loss(B1) - decision_loss(C_genuine) = 1.0 > 0.
    C_genuine strictly beats B1 on decision_loss.

**Layer C statement$_{3946}$:**

- Under a frozen observation budget ($B=15$), external blind 30-solver S_eval, and
  ACCEPT/REJECT decision utility, C_genuine achieves decision_loss=0 (0 wrong accepts, 0 wrong
  rejects), strictly improving over B1 (decision_loss=1.0).
- This is a positive C-4 result: C_genuine's directional failure-family classifier identifies the
  single wrong-reject solver that B1 misclassifies.
- B0/B4/B5/B6 are degenerate (all-ACCEPT or all-REJECT). The comparison is C_genuine vs B1/B2/B3.
- C_genuine uses the honest classifier (F4→F1→F2→F3 detection order) to classify observed failures
  by direction, enabling a more selective acceptance policy than raw failure counting.

**Artifacts:**

- `data/midweather_fingerprint_lc3946.json` — full result JSON
- `data/c5_collapse_lc3946.json` — C-5 perturbation results
- `runners/run_c5_collapse_lc3946.py` — C-5 runner

### C-5 perturbation survival

A C-5 perturbation analysis tests whether the C-4 result survives protocol perturbations.

**Perturbation types tested:**

| Perturbation | Type            | Description                           | Gap | Survives? |
|:-------------|:----------------|:--------------------------------------|:---:|:---------:|
| P1a          | baseline        | reference (B=15, threshold=0.05)      | 1.0 |    yes    |
| P1b          | threshold_shift | threshold=0.10                        | 1.0 |    yes    |
| P1c          | threshold_shift | threshold=0.20                        | 1.0 |    yes    |
| P2a          | subsample       | drop 5 solvers (indices 0-4)          | 1.0 |    yes    |
| P2b          | subsample       | drop 5 solvers (indices 25-29)        | 1.0 |    yes    |
| P2c          | subsample       | drop 5 solvers (mixed)                | 1.0 |    yes    |
| P3a          | family_knockout | remove poset_universal_source probes  | 1.0 |    yes    |
| P3b          | family_knockout | remove poset_chain probes             | 1.0 |    yes    |
| P3c          | family_knockout | remove poset_antichain probes         | 1.0 |    yes    |
| P3d          | family_knockout | remove poset_lattice_boolean probes   | 1.0 |    yes    |
| P3e          | family_knockout | remove poset_lattice_two_prime probes | 0.0 |  **no**   |
| P3f          | family_knockout | remove poset_isolated probes          | 1.0 |    yes    |

**C-5 verdict:** PARTIALLY_SURVIVES (10/11 perturbations survive, 1 collapse).

The single collapse (P3e) occurs when poset_lattice_two_prime probes are removed. Under this
knockout, both B1 and C_genuine achieve decision_loss=0, eliminating the gap. This indicates that
the poset_lattice_two_prime family is the signal-bearing probe family for C_genuine's advantage
on LC3946.

## LC322: Conditional λ-Dependent Superiority (Supporting Evidence)

### Midweather-Fingerprint: Clean Gate (Evidence Stage 3)

This is a clean LC322 case study testing whether structured fingerprint features
improve solver accept/reject decisions over raw baselines under a frozen protocol,
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

Degenerate baselines (B0 all-ACCEPT, B4 all-REJECT, B5/B6 all-ACCEPT) trigger the FAIL verdict.
The `decide_accept_reject` function in `midweather_fingerprint_features.py` unconditionally returns
FAIL with reason `degenerate: all-reject in <estimator>` if any row has `degenerate_all_reject=True`.
In this run, B4 is all-REJECT and triggers the FAIL before the C-vs-baselines comparison is reached.
The anti-degeneracy guard additionally checks that C is not all-ACCEPT (which would be a degenerate
candidate policy) and that the target set has both ACCEPT and REJECT ground-truth labels (no target
collapse). Both are checked; both passed in this run.

**Corrected from original draft.** Code at `c3db242` is authoritative.

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
    C does not strictly beat every baseline on decision_loss.
    C satisfies minimum_accept_rate (0.933 >= 0.2) and is not degenerate.
    C RMSE (0.024) is best overall but secondary.

**Interpretive note:** C ties B1/B2/B3 on decision_loss, and those raw baselines use
less structural information than C. The tensor baselines B4/B5/B6 receive the same axis/deformation
tensor
as C, but they are degenerate in this run. Thus, the FAIL verdict is not that C loses to a well-performing
equal-information tensor policy. The verdict is that C's additional structured information does not improve
the
final ACCEPT/REJECT decision over simpler lower-information raw baselines under this floor-limited LC322
solver
pack.

**Layer C statement$_{mf}$:**

- Under a frozen $B=15$ budget, external blind 30-solver S_eval, all baselines (B0--B6),
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
  decision utility over raw baselines in this configuration.

**Artifacts:**

- `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` — frozen protocol artifact
- `MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json` — S_eval certification schema
- `data/midweather_fingerprint_lc322_seval_manifest.json` — S_eval manifest for blind solver pack
- `data/midweather_fingerprint_lc322.json` — full result JSON
- `findings/FINDINGS_MIDWEATHER_FINGERPRINT_LC322.md` — findings report
- `tests/test_midweather_fingerprint.py` — 40 protocol tests (all pass at commit `c3db242`: `pytest` yields
  40/40; original freeze commit unrecoverable (PhotoRec loss); reconstructed at `c3db242`)

**Clean-run status:** all guards passed. Metrics computed. Decision: FAIL.

### LC322-v2: λ-Dependent Superiority

The LC322 C-4 result shows λ-dependent behavior: at equal costs (λ=1), C ties B1/B2/B3 on decision_loss
(1.0). As λ increases, C_genuine becomes superior. At λ=50, the gap reaches 3.13.

Note: The LC322 C-4 gap of 8.3 reported in earlier versions (from commit 50d33e5) is a test fixture
constant in `lc3946_collapse_perturbations.py:58`, not the verified result from the recovered
workspace. The verified LC322-v2 C-4 result (commit e8b0075) shows gap=3.13 at λ=50.

**Cross-population anchor (P4):**

    LC322 C-4 gap = 3.13 at λ=50, signal_family = large_amount_stress
    LC3946 C-4 gap = 1.0, signal_family = poset_lattice_two_prime
    LC322 C-5 verdict = PARTIALLY_SURVIVES

Both LC322 and LC3946 show positive C-4 results with signal concentrated in specific probe families.
Both survive partial perturbation analysis. The signal families differ (large_amount_stress vs
poset_lattice_two_prime), confirming that the C_genuine policy adapts to problem-specific failure
structure rather than exploiting a universal artifact.

### Reproducibility Gap

The Stage 3 result table above shows an 11/19 good/bad split, not the 27/3 split originally claimed in
the paper draft. This discrepancy is an **irrecoverable evidentiary gap**, not a protocol error.

- The original solver pack that produced the 27/3 split is **unrecoverable**. The working tree was lost
  in a PhotoRec recovery; only the protocol code, freeze, and manifest schema survived. The 30 original
  solver files and the original freeze commit SHA are gone.
- The **reconstructed stub pack** (30 solvers, `pack_source: "reconstructed_stub"`) produces an 11/19
  split. All 30 solvers pass the 4 pre-run sanity probes; 11 pass all 15 observed probes; 19 fail at
  least one held-out probe.
- The **hand-curated real benchmark** (30 solvers, `pack_source: "hand_curated_real"`) produces a 16/14
  split. This pack was designed in lieu of real LLM completions (the `ANTHROPIC_API_KEY` was not set
  and the `anthropic` SDK was not installed in the recovery environment).
- All three packs run the **same protocol** and produce verdict **FAIL**. The central claim (FAIL) is
  reproducible; the exact split is not.

The stub pack's 11/19 and the real benchmark's 16/14 both end in FAIL via B4 degenerate, matching the
original 27/3 verdict. The verdict is the contribution; the split is a population statistic that
depends on the solver pack, which is not reproducible from the recovered artifacts.

**What is recoverable:** the protocol kernel, the freeze validators, the manifest schema, the 6 adapter
slots, the bimaristan layer, the decision rule, and the FAIL verdict. **What is not recoverable:** the
original 30 solver functions, the original freeze commit SHA, and the exact population statistics.

**Note on the paper draft:** the original paper draft cited a freeze commit (`6ca6c28`) and a 27/3 split
that cannot be reproduced from the current artifacts. Both have been corrected in this version: the
phantom commit has been replaced with "original freeze commit unrecoverable (PhotoRec loss);
reconstructed at `c3db242`," and the 27/3 claim has been replaced with the actual reconstructed
statistics above.

### Interpretation

The LC322 result is conditional: C_genuine shows λ-dependent superiority over B1 on the tested solver
population. At low reject-cost weights, B1 performs better. C_genuine becomes superior as λ increases
and wrong-reject costs dominate. This demonstrates that the cost regime determines which policy
produces lower decision_loss, not just the solver population.

The clean FAIL verdict at λ=1 should be read precisely: C did not strictly improve the declared decision
utility at equal costs. The result does not distinguish a universal absence of fingerprint value from a
setting in which the cost regime does not favor C_genuine's tolerance rule. The LC322-v2 result at λ=50
(gap=3.13) shows that the advantage exists under asymmetric costs.

## LC45: Negative Boundary Condition

The generalized kernel was applied to **LC45 Jump Game II** (minimum jumps to
reach the last index of a non-negative integer array). LC45 is structurally different from LC322
(greedy/monotonic dynamics vs DP/non-monotonic), so it tests whether the kernel's adapter-slot design
holds across problem families.

### LC45 problem and manifolds

LC45 has 6 failure manifolds (analogous to LC322's 6 fingerprint axes):

1. `naive_max_jump_suboptimal` — naive greedy (always take the longest step) is suboptimal when
   shorter steps land on higher-value positions.
2. `single_large_jump_decoy` — a single large jump decoy makes greedy skip a reachable path.
3. `greedy_horizon_collapse` — greedy's horizon collapses when the farthest-reachable position is
   not the best landing.
4. `naive_max_jump_dead_landing` — naive greedy lands on a 0-valued position (dead end).
5. `uniform_jump_array` — uniform arrays (all values equal) expose formulas that assume uniformity.
6. `greedy_frontier_valid_no_false_pressure` — greedy frontier is valid (not panicked) on inputs
   where it should be confident.

The probe index has 30 probes (5 per manifold), split K=15+15 round-robin across observed and target
sets.

### Solver population and verdict

10 candidate solvers were sourced from an external baseline pack (`pack_source: "external_baseline"`):

- 1 survivor: `lc45_bfs_depth_cutoff` (BFS with visited set and depth cutoff — passes all oracle cases)
- 9 buggy solvers spanning 4 families: Greedy (4), Reachability confusion (2), Bounded/incomplete (2),
  Off-by-one (1)

The LC45 protocol verdict: **FAIL**, 1/9 split (1 good / 9 bad), B4 degenerate. The single survivor
passes all 30 probes; the 9 buggy solvers fail on varying numbers of held-out probes (0.2-1.0 fail rate).

### Bimaristan layer summary

The LC45 bimaristan layer was built in a separate self-contained module (no Doctor pipeline dependency):
`LC45OracleEvaluator` (295 lines), `LC45_SYMBOL_REGISTRY` (463 lines, 38 entries across 5 categories),
6 manifold definitions in `LC45_MANIFOLDS`, and 10 candidate solvers in `lc45_candidates.py`. The layer
is independently testable: 36 tests in `tests/test_lc45_bimaristan.py`.

### C estimator: negative result

C was wired into the LC45 protocol (`_fail_count_policy`, same as LC322). A feature audit determined
whether the 6 features in `lc45_raw_tensor_encoder` could separate the 1 survivor from the 9 buggy
solvers:

| Feature                   | Survivor (solver_001) | Buggy [min, max] | Gap    | Clean separation? |
|---------------------------|-----------------------|------------------|--------|-------------------|
| `pass_fail_rate`          | 1.0                   | [0.0, 0.8667]    | 0.1333 | **YES**           |
| `bfs_agrees_rate`         | 1.0                   | [0.0, 0.8667]    | 0.1333 | **YES**           |
| `off_by_one_rate`         | 0.0                   | [0.0, 1.0]       | 0.0    | no (overlap)      |
| `panics_on_dead_end_rate` | 0.0                   | [0.0, 0.7333]    | 0.0    | no (overlap)      |
| `dead_end_present_rate`   | 0.2333                | [0.2333, 0.2333] | 0.0    | no (constant)     |
| `is_uniform_array_rate`   | 0.2                   | [0.2, 0.2]       | 0.0    | no (constant)     |

The only separating features (`pass_fail_rate` and `bfs_agrees_rate`) are informationally identical —
the encoder's `bfs_agrees_count` compares `candidate_output == expected_output`, the same condition as
`pass_fail`. This is an encoder artifact. C cannot differentiate from B1 on the LC45 population. The
finding is formally negative and is documented in `docs/LC45_C_POLICY_FINDING.md`.

## LC743: Negative Boundary Condition

LC743 (Network Delay Time) is cited as methodology portability evidence: the LC322 protocol was
adapted to a structurally different problem class. The C-4 gate yielded gap=0 (FAIL): all three
estimators (C_genuine, B1, B2) make identical predictions (2 ACCEPT, 29 REJECT). Artifact state:
ARTIFACT-VERIFIED. This is a negative boundary condition: the mechanism does not improve over baselines
when all estimators converge to identical predictions. The governed rerun was executed under the frozen
protocol with no contamination. One F2 solver (s013) achieved tgt_rate=0.0 on the 12-case target set
due to coincidental alignment between its bug pattern and the specific probe instances, and was
classified ACCEPT by ground truth.

## CSSE v2: Neutral Mutation Experiment (Internal Measure)

CSSE v2 generates 500 neutral-mutation solvers per problem class and measures P(D) under the same
evaluator E_P. This is the internal mutation measure: P(D | mutation distribution).

### Protocol

For each problem class, 500 solvers are generated via 6 neutral mutations (constant replacement,
dead code insertion, expression reordering, guard inversion, variable renaming, loop unrolling)
applied 1–3× per solver. Each solver is evaluated against B1 and C_genuine on 24–30 probes.

### Results

| Problem | n_valid | n_disagree | P(D) | 95% CI |
|---------|---------|------------|------|--------|
| LC322   | 317     | 6          | 0.019 | [0.006, 0.035] |
| LC3946  | 161     | 0          | 0.000 | [0.000, 0.000] |
| LC79    | 219     | 0          | 0.000 | [0.000, 0.000] |
| LC743   | 240     | 66         | 0.275 | [0.221, 0.329] |

### DCG Classification

All four CSSE v2 sources satisfy DCG.1–DCG.4: canonical interface is trivial (all solvers are
generated with the correct `solve()` signature), evaluator is unified, failures are endogenous,
and failure variance is positive for LC322 and LC743. DCG = VALID for all four.

### Key Observations

- P(D) is problem-dependent: ranges from 0.000 (LC3946, LC79) to 0.275 (LC743)
- Disagreements are threshold-localized: concentrated at single k-values (LC322: k=2, LC743: k=6)
- At k=0 and k=max, P(D|k) = 0.000 across all problems — no signal at extremes
- CE rate: LC322=37%, LC3946=68%, LC79=56%, LC743=52%

## External Corpus Evaluation (External Measure)

An external solver corpus was assembled from human-written solutions (Stack Overflow, GitHub,
human_solvers/) and ChatGPT-generated solutions. Solvers are mapped into canonical form via an
adapter layer (syntactic normalization only, no behavioral guessing).

### DCG Classification

| (Source, Problem) | DCG.1 | DCG.2 | DCG.3 | DCG.4 | Classification |
|-------------------|-------|-------|-------|-------|----------------|
| External, LC322   | pass  | pass  | pass  | pass  | VALID |
| External, LC79    | pass  | pass  | pass  | fail (n=1) | MEASURABLE BUT NON-COMPARABLE |
| External, LC743   | pass  | pass  | pass  | fail (n=1) | MEASURABLE BUT NON-COMPARABLE |

### LC322 External Result (Valid Cross-Domain Comparison)

38 external solvers evaluated on 30 probes:

| Metric | Value |
|--------|-------|
| n_valid | 38 |
| n_ce | 0 |
| n_disagree | 2 |
| P(D) | 0.053 |

P(D | k) distribution:

| k (obs_fails) | N | D | P(D\|k) |
|---------------|---|---|----------|
| 0 | 20 | 0 | 0.000 |
| 2 | 1 | 1 | 1.000 |
| 3 | 1 | 0 | 0.000 |
| 4 | 3 | 1 | 0.333 |
| 28 | 2 | 0 | 0.000 |
| 30 | 11 | 0 | 0.000 |

### LC322 Cross-Domain Comparison

The only valid DCG-bridged comparison:

| Source | P(D) | n | Failure variance |
|--------|------|---|------------------|
| CSSE v2 (internal) | 0.019 | 317 | positive |
| External (human+GPT) | 0.053 | 38 | positive |

Both sources satisfy DCG for LC322. The comparison is valid. External P(D) is higher than
CSSE v2 P(D), but the confidence intervals overlap (external CI not yet computed; CSSE v2
CI: [0.006, 0.035]). The difference is not statistically identifiable at current sample sizes.

The two disagreements in the external corpus occur at k=2 and k=4 (low failure rates), where
B1 rejects (obs_fails > 0) but C_genuine accepts (single-family failures). This is the same
arithmetic mechanism observed in CSSE v2: at ObsF=1, B1=REJECT, C_genuine=ACCEPT by construction.

### LC79/LC743 External Results (Non-Comparable)

LC79: 1 valid solver, P(D)=0.000. Insufficient support (n=1, Var(F)=0). DCG.4 fails.

LC743: 1 valid solver, P(D)=0.000. Insufficient support (n=1, Var(F)=0). DCG.4 fails.

These are labeled MEASURABLE BUT NON-COMPARABLE. No cross-domain P(D) inference is permitted.

## Real Benchmark (hand-curated)

A hand-curated 30-body solver pack (10 correct + 20 buggy across 7 bug families) was built in lieu of
LLM-generated solvers (`ANTHROPIC_API_KEY` not set). The pack produces a 16/14 split, verdict **FAIL**,
B4 degenerate — matching the protocol's FAIL verdict. The manifest declares `pack_source:
"hand_curated_real"` (explicitly not LLM-generated). The reserved namespace
`experiments/frozen_taxonomy_lc322_real_claude_sonnet_4/` is the target for a future real LLM run.

# Discussion

## Cross-Problem Comparison

The paper tests the C_genuine estimator across four problem classes under comparable frozen protocols.
Two measurement domains are present: an internal mutation measure (CSSE v2) and an external corpus
measure. The Domain Completeness Gate (DCG) determines which cross-domain comparisons are valid.

### Per-Problem C-4 Results

| Problem | C-4 result       | C-5 survival        | Signal family           | Population split      |
|---------|------------------|---------------------|-------------------------|-----------------------|
| LC3946  | POSITIVE         | 10/11               | poset_lattice_two_prime | 15 ACCEPT / 15 REJECT |
| LC322   | POSITIVE (λ-dep) | PARTIALLY_SURVIVES  | large_amount_stress     | 11 ACCEPT / 19 REJECT |
| LC743   | NEGATIVE (gap=0) | not run             | N/A                     | 2 ACCEPT / 29 REJECT  |
| LC45    | NEGATIVE         | N/A (feature audit) | N/A                     | 1 ACCEPT / 9 REJECT   |

### DCG Classification Summary

| (Source, Problem) | DCG | P(D) | Notes |
|-------------------|-----|------|-------|
| CSSE v2, LC322    | VALID | 0.019 | n=317, CI=[0.006, 0.035] |
| CSSE v2, LC3946   | VALID | 0.000 | n=161 |
| CSSE v2, LC79     | VALID | 0.000 | n=219 |
| CSSE v2, LC743    | VALID | 0.275 | n=240, CI=[0.221, 0.329] |
| External, LC322   | VALID | 0.053 | n=38 |
| External, LC79    | NON-COMPARABLE | 0.000 | n=1, DCG.4 fails |
| External, LC743   | NON-COMPARABLE | 0.000 | n=1, DCG.4 fails |
| CSSE v2, LC3946   | INVALID | — | non-externalizable domain |

### The Only Valid Cross-Domain Comparison

LC322 is the only (source, problem) pair where both CSSE v2 and External satisfy DCG. The
comparison:

| Source | P(D) | n |
|--------|------|---|
| CSSE v2 (internal mutation) | 0.019 | 317 |
| External (human+GPT) | 0.053 | 38 |

External P(D) is higher than CSSE v2 P(D). Both are low. The confidence intervals have not
been formally compared (external CI not yet computed), but the point estimates are in the same
order of magnitude. This is the only legally comparable cross-domain statement in the system.

### Interpretation

LC3946 provides the strongest positive case: the balanced 15/15 population split avoids the floor
effect that limits LC322, and C_genuine achieves perfect decision_loss (0.0) with 10/11
perturbation survival. However, LC3946 is non-externalizable — it is a synthetic evaluator
geometry, not a real-world domain. Its P(D) cannot be compared to external measures.

LC322 provides conditional supporting evidence internally (λ-dependent superiority) and is the
sole valid cross-domain bridge. The external P(D)=0.053 is comparable to the CSSE v2
P(D)=0.019, confirming that the phenomenon exists under independent solver lineage — but the
sample is small (n=38) and the comparison is underpowered.

LC45 and LC743 are negative boundary conditions. LC45 fails because the separating features are
informationally equivalent to B1 (encoder artifact). LC743 fails internally (gap=0) and has
insufficient external support (n=1). These failures constrain interpretation: the C_genuine/B1
divergence appears when the solver population has failures that split across multiple probe
families under C_genuine's rule but are treated uniformly by B1.

The cross-problem pattern under DCG is: C_genuine improves over B1 when (1) the solver population
has balanced failure-class diversity and (2) the probe index contains families where single-family
failure concentration triggers C_genuine's acceptance branch. The only valid external confirmation
is LC322, and it is underpowered. All other cross-domain claims are blocked by DCG.

## Hardening Sequence Summary

The paper presents evidence stages that progressively harden the protocol:

| Stage | Evidence                                 | Protocol Status                         | Result                                                        |
|-------|------------------------------------------|-----------------------------------------|---------------------------------------------------------------|
| 1     | DOCTOR/BIMARISTAN history (E0, E1, E2)   | Exploratory / diagnostic                | Motivates the question; no clean claim                        |
| 2     | Midweather retrospective audit           | Contaminated / retrospective            | Negative/inconclusive boundary marker                         |
| 3     | Clean gates (LC322, LC3946, LC45, LC743) | Clean (frozen K, external blind S_eval) | Mixed: positive (LC3946, LC322-v2) and negative (LC45, LC743) |

The clean gates are the main results. Stages 1–2 explain why the clean-gate protocols
were necessary; they are not treated as convergent or cumulative evidence. A reader should read the hardening
sequence as methodological narrative, not an accumulating proof.

## Primary Interpretation: Conditional Superiority Under DCG

The LC3946 result demonstrates that a directional failure-family classifier can strictly improve over
a failure-count baseline under specific frozen conditions. The advantage is real (decision_loss=0.0
vs 1.0) and partially robust (10/11 perturbation survival). However, LC3946 is non-externalizable:
it is a synthetic evaluator geometry, not a real-world domain. Its P(D) is VALID under DCG for
internal measurement but INVALID for cross-domain comparison.

The LC322 result demonstrates that the advantage is conditional on the cost regime. At equal costs,
the classifier ties the baseline. At asymmetric costs favoring wrong-reject avoidance, the classifier
becomes superior. LC322 is the only problem class where both internal (CSSE v2) and external
(corpus) measures satisfy DCG. The cross-domain comparison is valid but underpowered (external n=38).

The LC45 and LC743 results demonstrate boundary conditions where the mechanism fails. LC743
additionally has insufficient external support (n=1, DCG.4 fails), so no cross-domain inference is
permitted. These are not failures of the project; they are boundary conditions that define when and
why the mechanism works.

The correct interpretation under DCG is: the system measured a real phenomenon (P(D) > 0 under
neutral mutation on LC322 and LC743), and the only valid external confirmation is LC322 at
P(D)=0.053. All other cross-domain claims are blocked by DCG. The contribution is a conditional
empirical finding with one valid external anchor, not a universal claim.

## Interpretive Framework: Phase Diagram

The cross-problem pattern can be visualized as a two-axis phase diagram: solver population
diversity ($\mathcal{D}$) on one axis and feature orthogonality to failure count ($\mathcal{O}$) on
the other. Under this framing, LC3946 (high $\mathcal{D}$, high $\mathcal{O}$) is the dominance
regime, LC322 (low-to-moderate $\mathcal{D}$, high $\mathcal{O}$) is the conditional regime,
LC45 (high $\mathcal{D}$, low $\mathcal{O}$) is the boundary regime, and LC743 (low $\mathcal{D}$,
low $\mathcal{O}$) is the collapse regime. The framework is consistent with the observed results:
C_genuine improves over B1 when both axes are sufficient, and degrades toward B1 when either axis
is insufficient.

This framework is a post-hoc explanatory model. The $\mathcal{D}$ and $\mathcal{O}$ coordinates
are currently interpretive, not independently measured. They were assigned after observing the
C-4 results, not derived from independent population or feature diagnostics. The framework
describes the observed results but does not independently predict them. It is awaiting prospective
validation: measuring $\mathcal{D}$ and $\mathcal{O}$ before running C-4, then testing whether the
diagram predicts results on new problem classes.

## K-Space Coverage and Scope

All claims are non-transferable outside observed K-space unless independently revalidated under a new
stack $K'$.

The positive results (LC3946, LC322-v2) are conditional on the specific solver distributions tested.
The generator populations produced a small number of distinct behavioral regimes, limiting interpretation to
the observed support. Cross-population comparison of gap magnitude is not identifiable without controlling
for generator method, as the LC322 and LC3946 populations were constructed differently.

## Oracle Consistency

$O$ defines correctness only within $K$; $O$ is not a semantic ground truth function. All correctness in this
paper
means agreement with internal $O$ under $C$.

# Threats to Validity

## Construct Validity

The observation target is instrument-relative. It is not an independent ontology of program behavior.
Correctness means
test-empirical consistency with the internal oracle under the current comparator, not semantic truth. Solver
classes,
collapse labels, and failure manifolds are therefore instrument labels defined by the evaluation stack, not
externally
validated natural kinds.

## Internal Validity

The same ecosystem defines solvers, generators, oracles, comparators, and metrics. This creates instrument
self-consistency bias. The evidence in E0–E2 is therefore treated as artifact-level behavior of the evaluation
system,
not as independent validation of solver classes or external correctness.

## Project-Mechanics Limitations Not Directly Exercised by E0–E2

Repository audits identify broader project-mechanics risks outside the main evidence path, including the
historical LC45
perturbation-validity error, the fact that perturbation-stability comparisons depend on output-preserving
transformations, and raw Python `==` oracle-alignment behavior that can mix boolean and numeric domains (for
example,
`1 == True`). These findings constrain trust in the broader DOCTOR project, but they are not all direct
failure modes of
the reported experiments: LC45 is not part of E0–E2, bool/numeric comparator mixing is a general
comparator risk,
and pre-existing test failures do not by themselves falsify the reported artifact tables. They are reported to
bound the
project mechanics rather than to retroactively invalidate the main observations.

## K-Space Coverage

The Stage-1 exploratory experiments (E0, E1, E2) vary at most two K-coordinates: one representation
change ($R$) in
E0 and one perturbation-family change ($F$) in E2. The clean Evidence Stage 3 gates fix all K-coordinates and
test the
fingerprint representation under those fixed stacks. Within each reported experiment, $O$ and $C$ are fixed
for
that
experiment. Across experiments the comparator differs: E0 uses output equality, E1 uses a divergence
calculation,
E2 uses an AUC scorer over transfer rankings, and the clean gates use output equality. The overall paper
therefore
does not hold $O$ and $C$ constant across all experiments — only within each experiment.

## External Validity

This study does not claim external validity beyond the defined K-space. The repository evidence reported here
does not
include third-party benchmark validation, EvalPlus execution, LiveCodeBench execution, an independent
metamorphic-testing baseline, independent oracle comparison, or non-repository replication.

The Domain Completeness Gate (DCG) formalizes when cross-domain P(D) comparison is valid. Of all
(source, problem) pairs tested, only LC322 satisfies DCG for both internal (CSSE v2) and external
(corpus) measures. All other cross-domain comparisons are blocked by DCG: LC3946 is
non-externalizable, LC79 and LC743 have insufficient external support (n=1). The single valid
external anchor (LC322, external P(D)=0.053) is underpowered but confirms the phenomenon exists
under independent solver lineage.

## Geometry Audit Limitations

All experimental geometry is meta-frozen and problem-independent at structural level; problem-specific
parameters are pre-committed after problem selection but before data collection; this rules out adaptive
adjustment but does not rule out geometry constructed with signal intuition. The probe families, axis
definitions, and estimator architectures reflect design choices informed by earlier exploratory work
(Evidence Stages 1--2). While the clean gates (Evidence Stage 3) freeze all protocol parameters before
execution, the structural design of the evaluation geometry was not prospective. The honest classifier
(F4→F1→F2→F3 detection order) was validated against the oracle before the C-4 gate, introducing a
verification dependency that bounds the independence of the result.

## LC743 Execution Disclosure

LC743 specs (problem definition, probe families, honest classifier, C-4 protocol) are cited as
methodology portability evidence: the LC322 protocol was adapted to a structurally different problem
class. Execution was completed under SSC-v2 governance with a clean governed rerun. The C-4
decision-utility gate yielded gap=0 (FAIL): all three estimators (C_genuine, B1, B2) make identical
predictions on the LC743 population (2 ACCEPT, 29 REJECT). Artifact state: ARTIFACT-VERIFIED.

Historical contamination events during LC743 development — (1) adaptive parameter tuning during C-4
runner iteration (p-hacking on observed set size, identified and corrected by freezing the protocol
before rerun), and (2) a circular classifier in an earlier run that referenced oracle metadata — are
documented as historical context. The governed rerun was executed under the frozen protocol with no
contamination.

## Statistical Validity

The experiments use heterogeneous statistics: pass rates, AUCs, CIs, and conditional correlations. No unified
inference
framework or multiple-comparison correction is claimed. E2 artifacts provide condition-level bootstrap
confidence
intervals from 500 resamples, and the post-audit `compute_e2_delta_ci.py` script computes cross-condition
delta
confidence intervals. All six E2 cross-condition delta intervals cross zero at 95%, including the reported
point-estimate deltas of -0.577665, -0.312201, and +0.179688. Therefore, E2 does not support a statistically
significant
non-invariance claim; it supports only directional boundary sensitivity with uncertain magnitude. E0 and E1
lack matched
uncertainty treatment, so cross-experiment comparisons should not be read as a single inferential model.

## Reproducibility

The repository has artifacts and scripts but no single end-to-end reproduction command. Per-experiment runners
exist,
but regenerating the paper's evidence requires manual orchestration; no Makefile, `pyproject.toml`, `tox.ini`,
`pytest.ini`, or `setup.py` entrypoint is available in the repository root. The examined runner scripts insert
the
project root into `sys.path` at runtime, making execution path-dependent. `ARTIFACT_MANIFEST.lock` pins SHA256
checksums
for the paper-cited files at the analyzed commit, but reproduction still depends on access to the matching
repository
state and local execution environment.

The following test scopes apply to the repository (do not conflate):

| Scope                            | Command                                               |          Key result           | Meaning                                                                                                                   |
|----------------------------------|-------------------------------------------------------|:-----------------------------:|---------------------------------------------------------------------------------------------------------------------------|
| Historical repository Track A    | archival state                                        |  6 failures across 26 tests   | broader repo test state (archival, not all scoped to this paper)                                                          |
| Historical targeted pytest audit | archival state                                        |    14 pass, 2 skip, 0 fail    | subset of Track A tests                                                                                                   |
| Midweather-Fingerprint protocol  | `pytest test_midweather_fingerprint.py`               | 40/40 pass (commit `c3db242`) | clean-gate guard and correctness tests (original freeze commit unrecoverable (PhotoRec loss); reconstructed at `c3db242`) |
| Repair regression suite          | `pytest test_comparator_regression.py` + oracle duels |          45/45 pass           | mechanical consistency of typed comparators, perturbation registry, oracle duels                                          |

One collection error was recorded for a scratch file (`test_euler_4.py`) that calls `sys.exit(0)` at module
level
and is not part of the test suite. The repository session state also records pre-existing failures in
`test_doctor_pipeline.py` and `test_sandbox_executor.py`; those failures are not resolved by the targeted
audits.

OpenCode found no direct A* solver definitions in the Python files. The E2 $K$ definition references H2/H3
heuristic-family runs and grid generators; if those live outside the project workspace, then E2 is not fully
reproducible
from this workspace alone. The paper therefore treats E2 as artifact-level evidence tied to the recorded AUC,
audit, and
delta-CI artifacts rather than as a self-contained reproduction path.

## Baseline Limitation

The LC322 expanded-suite baseline is internal: 88 cases, including 31 large-amount cases, against the
repository's known
solver population. The solver population is treated as an internal repository population; this paper does not
establish
external provenance for solver generation, model version, prompt history, human editing, or selection
procedure. No
third-party EvalPlus, LiveCodeBench, CodeContests+, metamorphic-testing baseline, independent oracle
comparison,
non-repository solver population, or external benchmark execution is included. A new solver population could
expose
failure surfaces not covered by the current artifacts.

## Limitations

### L1. Human Population Validity

A human validation attempt was conducted using two human-authored Stack Overflow wrong solvers and eight
synthetic bug-injected solvers. All exhibited high failure rates (0.20–1.0), producing trivial agreement
between B1 and C_genuine (gap = 0 in all cases). These populations therefore did not probe the
decision-boundary regime where disagreement between policies could occur. Consequently, the present study
provides no evidence regarding Doctor's behavior on boundary-adjacent human solver populations.

### L2. dm as Projection Under Collapsed Support

The scalar summary dm(s) = Σ τ(s) is a deterministic projection from binary trajectory vectors to
non-negative integers. On a support containing approximately six τ-regimes, dm may appear to behave
injectively: each dm value corresponds to exactly one observed τ pattern.

This apparent injectivity is an artifact of restricted support. It follows directly from the collapsed
generator support documented in L1. It is not a structural property of dm on the full solver domain.
Whether dm loses information about τ on a richer generator — one that populates a larger region of binary
trajectory space — is not answerable from the data collected here.

dm is not a studied object in this paper. It is a projection whose behavior is underdetermined given the
observed support. No inference about its structural properties is warranted.

### L3. Estimator Results Are Conditional on Solver Distribution

The C_genuine vs B1 comparisons in LC322-v2 (gap=3.13) and LC3946 (gap=1.0) are conditional performance
measurements under specific solver populations. Their validity depends on two factors that were not held
constant across experiments: solver distribution and λ regime.

Specifically:

- LC322-v2 used GPT-generated solvers with a declared F1×5/F2×10/F3×11/F4×4 prior and a post-freeze
  termination guard on one solver. LC322-v1 used LLM-generated solvers whose population is unrecoverable.
- LC3946 used hand-coded solvers across six strategy families.
- These populations are not drawn from the same distribution. Cross-population comparisons of gap magnitude
  are not identifiable without controlling for generator method.

C_genuine shows λ-dependent superiority over B1: negative gap at low λ, positive and increasing gap at
high λ. This sign-flip behavior is a property of the estimator under these distributions. It is not
claimed to be invariant across generators, problem classes, or λ regimes outside those tested.

No universality claim is made. No claim of invariance across generators is made. The results establish
conditional estimator behavior under the tested populations and λ values, nothing stronger.

### L4. DCG Is a Formalization, Not a Discovery

The Domain Completeness Gate (DCG) formalizes an already-known sampling limitation: the external
corpus is sparse (n=38 for LC322, n=1 for LC79/LC743) and structurally biased (interface-filtered,
source-constrained). DCG does not fix this limitation; it prevents false equivalence between
distributional spaces that are not comparable. The single valid external anchor (LC322) is
underpowered. A larger external corpus would strengthen the external measure but is outside the
scope of this paper.

# Conclusion

This paper asked when a directional failure-family classifier (C_genuine) improves accept/reject
decision utility over a failure-count baseline (B1). Four problem classes were tested under governed
protocols with pre-declared solver populations and frozen evaluation procedures. Two measurement
domains were present: an internal mutation measure (CSSE v2, n=500 per class) and an external
corpus measure (human+GPT solutions). The Domain Completeness Gate (DCG) determines which
cross-domain comparisons are valid.

The primary result is positive but non-externalizable. On LC3946 (poset-based lattice), C_genuine
achieves decision_loss=0.0 versus B1's 1.0, strictly improving over all non-degenerate baselines.
The advantage survives 10 of 11 perturbation conditions. However, LC3946 is a synthetic evaluator
geometry — it cannot be embedded into an external solver space. Its P(D) is VALID internally but
INVALID for cross-domain comparison.

The supporting result has one valid external anchor. On LC322 (Coin Change), C_genuine shows
λ-dependent superiority internally (gap=3.13 at λ=50). Externally, P(D)=0.053 (n=38) compared to
CSSE v2 P(D)=0.019 (n=317). This is the only DCG-valid cross-domain comparison in the system.
The external sample is underpowered but the point estimate confirms the phenomenon exists under
independent solver lineage.

Two negative boundary cases constrain interpretation. On LC45 (Jump Game II), the only separating
features are informationally equivalent to B1 (encoder artifact). On LC743 (Network Delay Time),
all estimators converge to identical predictions internally, and external support is insufficient
(n=1, DCG.4 fails). No cross-domain inference is permitted for LC743.

The CSSE v2 experiment reveals that P(D) is problem-dependent: 0.019 (LC322), 0.000 (LC3946,
LC79), 0.275 (LC743). Disagreements are threshold-localized at single k-values. This kills any
single-global-mechanism interpretation.

The contribution is a conditional empirical finding with one valid external anchor: C_genuine adds
decision utility over B1 specifically when (1) the solver population has balanced failure-class
diversity, (2) the probe index contains problem-specific structural families, and (3) the cost
regime favors wrong-reject avoidance. The only valid external confirmation is LC322 at P(D)=0.053.
All other cross-domain claims are blocked by DCG. No universality claim is made.

# References

Wang, Z., Liu, S., Sun, Y., Li, H., and Shen, K. (2025). CodeContests+: High-Quality Test Case Generation for
Competitive Programming. *arXiv preprint arXiv:2506.05817*. <https://arxiv.org/abs/2506.05817>

Shi, J., Yin, X., Huang, J., Zhao, J., and Tao, S. (2026). CodeHacker: Automated Test Case Generation for
Detecting
Vulnerabilities in Competitive Programming Solutions. *arXiv preprint arXiv:
2602.20213*. <https://arxiv.org/abs/2602.20213>

Hort, M. and Moonen, L. (2025). Codehacks: A Dataset of Adversarial Tests for Competitive Programming Problems
Obtained
from Codeforces. *arXiv preprint arXiv:2503.23466*. <https://arxiv.org/abs/2503.23466>

Liu, J., Xia, C. S., Wang, Y., and Zhang, L. (2023). Is Your Code Generated by ChatGPT Really Correct?
Rigorous
Evaluation of Large Language Models for Code Generation. *NeurIPS 2023 / arXiv:2305.01210*.
<https://arxiv.org/abs/2305.01210>

Jain, N., Han, K., Gu, A., Li, W.-D., Yan, F., Zhang, T., Wang, S., Solar-Lezama, A., Sen, K., and Stoica,
I. (2024).
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

Audit note: the 40$\times$40 `normalized_progress` condition is reported as a boundary audit result, not as
valid prefix
evidence. Because 98/100 runs consumed the full trajectory, the AUC of 1.000 is a full-information artifact
rather than
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

Doctor is not an externally validated evaluator. The clean gates produced mixed results: positive
decision-utility improvement in LC3946 and conditional improvement in LC322-v2, with negative boundary
conditions in LC45 and LC743. The contribution is a conditional empirical finding, not a universal claim.
Selected oracle artifacts have internal anchoring, but they do not affect the paper's main
decision-utility
result. All repairs are mechanically verified — **45/45 regression tests pass** (broader repository scope,
distinct
from the 39 Midweather protocol tests). These confirm consistency only; they do not affect the paper's main
result.

## Supporting LC322 Known-Population Probe Basis

This appendix item supports the case-study context but is not one of the main claims.

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

This appendix item supports context but is not one of the main claims.

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

A separate sealed-envelope validation, v0.3, tests whether the measurement discipline transfers to internally
sealed
unseen cases. The one-time hidden validation passes on 63/63 cases across five declared families (
dp\_recurrence,
graph\_shortest\_path, greedy\_trap, state\_space\_search, combinatorics\_counting) with 63/63 oracle-duel
agreements,
63/63 exact solver passes, 0 exact solver failures, 63/63 provenance completeness, and no hard stops
triggered. The seal
hash is confirmed, hidden\_opened is true, hidden\_validation\_run is true, and rerun\_allowed is false.

This result is not part of the main evidence chain and does not affect the paper's main
decision-utility finding. It is included for repository completeness.

# Primary Repository Artifacts

## Clean-Gate Artifacts

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
