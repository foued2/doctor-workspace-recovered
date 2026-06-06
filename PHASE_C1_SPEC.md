# PHASE_C1_SPEC.md
# Doctor Phase C-1: Asymmetric-Cost Decision Utility
# Status: APPROVED — Foued override granted, GPT + Minimax inspection passed
# Date: 2026-06-06

---

## Explicit Non-Relationship Declaration

The closed work (project-closure-004, `ccbf927`) tested:

> Do structured behavioral fingerprints transfer across problems in a way
> that improves decision utility under symmetric decision_loss?

Verdict: FAIL. Closure stands. This plan does not reopen it.

The new work tests:

> Under what asymmetric cost ratio λ_R/λ_A does C_structured_fingerprint
> strictly improve over B1_count in cost-weighted decision utility, on the
> frozen LC322 and LC45 solver populations?

Different success criterion. Different objective function class.
The closed negative result is data, not an obstacle.

---

## Research Question

**RQ-C1:** Does there exist a cost ratio λ_R/λ_A in the tested range under
which C_structured_fingerprint produces strictly higher cost-weighted
decision utility than B1_count, on the frozen LC322 and LC45 solver
populations, by at least δ?

---

## Falsification Criterion

**PASS:** ∃ λ_R/λ_A in the tested range such that
utility(C) − utility(B1) > δ on at least one frozen population.

**FAIL:** No such λ found across the full tested range on either population.
(Observable statement: symmetric decision_loss did not expose a gap across
the tested λ range and the tested populations. No causal claim.)

**DEGENERATE:** Estimator collapses to all-ACCEPT or all-REJECT at a given λ.
Record and exclude from comparison at that λ. Not a verdict on the RQ.

All three outcomes are valid results.

---

## Objective Function — Explicit Acknowledgment

This plan changes the objective function class.

The closed work used:
    decision_loss = 1 if verdict != ground_truth else 0

This plan uses:
    cost(decision, ground_truth) =
        λ_R  if decision=REJECT and ground_truth=ACCEPT  (false reject)
        λ_A  if decision=ACCEPT and ground_truth=REJECT  (false accept)
        0    if decision == ground_truth

Reported metrics (both required, neither optional):

    raw_cost(estimator, λ_R, λ_A) =
        mean(cost over population)

    normalized_utility(estimator, λ_R, λ_A) =
        1 − raw_cost / λ_A

Normalization is per-population using that population's λ_A.
Raw cost and normalized utility are both reported.
Per-population normalization is used to prevent cross-population masking.
This choice is declared here and not revisited after results are seen.

Old results used λ_R = λ_A = 1. New results sweep λ_R/λ_A across the
declared range. Old results remain untouched and are not reinterpreted.

---

## δ — Minimum Meaningful Gap

**δ = 0.10 (per-population)**

Rationale (LC45): 10 solvers. δ = 0.05 corresponds to 0.5 solver-outcome
difference — below the smallest meaningful granularity on this population.
δ = 0.10 = 1 wrong decision on LC45. This is the minimum resolvable gap.

Rationale (LC322): 30 solvers. δ = 0.10 is conservative but consistent.
A gap below 0.10 on LC322 would not be commercially actionable.

δ is declared here. It is not adjusted after results are seen.

---

## λ Sweep

Tested range: {1, 2, 5, 7, 10, 15, 20, 30, 50}

Nine values. Denser in the 5–20 production-deployment region.
Both populations. All 8 estimators.

---

## Populations

Frozen. No new solver packs.

- **LC322**: 30 solvers, 11/19 accept/reject split.
  Source: `data/midweather_fingerprint_lc322.json`.
  Role: primary evaluation population.

- **LC45**: 10 solvers, 1/9 accept/reject split.
  Source: `data/midweather_fingerprint_lc45.json`.
  Role: stress test. Results on LC45 are fragile due to single-survivor
  skew. LC45 findings are reported but not used as primary evidence.

If LC322 and LC45 diverge, both results are reported as-is.
No post-hoc reconciliation.

---

## Estimators Under Test

Primary comparison: C_structured_fingerprint vs B1_count

Secondary (anti-degeneracy audit):
B0_prior, B2_calibrated_count, B3_raw_pf_vector,
B4_raw_full_tensor, B5_nearest_neighbor_raw_tensor,
B6_regularized_raw_tensor

No new estimator construction in this phase.

---

## Protocol

**Step 0 — Commit this spec and freeze file before any code is written.**
No runner is written until both files are committed and tests are green.

**Step 1 — Write `PHASE_C1_FREEZE.json`**
Contents: δ, λ sweep values, population identifiers, estimator list,
normalization rule, role of each population (primary / stress test).
Commit before sweep runs.

**Step 2 — Write runners**
`runners/run_asymmetric_cost_lc322.py`
`runners/run_asymmetric_cost_lc45.py`
Runners load frozen solver decisions from existing data files.
They do not re-run probes. They apply the cost function to existing
accept/reject decisions.

**Step 3 — Write tests**
New test file covering:
- cost function correctness
- normalization formula
- anti-degeneracy detection at each λ
282 + N passed required before sweep runs.

**Step 4 — Run sweep**
Record raw_cost and normalized_utility for each
(estimator, λ_R/λ_A, population). No interpretation during sweep.

**Step 5 — Apply falsification criterion**
Does ∃ λ such that utility(C) − utility(B1) > δ on either population?
Yes or No. No partial credit.

**Step 6 — Write `docs/PHASE_C1_RESULTS.md`**
Findings only. No causal language. No compression drift.
No generalization beyond tested λ range and tested populations.

**Step 7 — Commit and tag**
Tag: `phase-c1-results`

---

## Infrastructure Reuse

| Component | Status |
|---|---|
| Gate kernel (LC322 runner) | Extend with cost function |
| ProblemClassConfig adapter slots | Unchanged |
| LC45 bimaristan layer | Unchanged |
| Frozen solver packs (LC322 + LC45) | Unchanged |
| Freeze file mechanism | New freeze file for this phase |
| 8 estimators | Unchanged |
| Test suite | 282 passing; must remain green |

---

## What This Phase Does Not Do

- Does not reopen project-closure-004.
- Does not introduce new probes, stress-class definitions,
  or fingerprint primitives.
- Does not construct a new C estimator.
- Does not reinterpret closed results under new framing.
- Does not expand to new problem classes.
- Does not claim the closed FAIL verdict was wrong.

---

## Epistemological Constraints (Carried Forward)

1. Compression drift: no claim stronger than the observation.
2. Negative result inflation: no generalization beyond tested
   λ range and tested populations.
3. Hidden causal language: no because / therefore / explains /
   caused by / due to.

§7 hard-stop rule: if any move requires violating the above,
stop and surface the conflict. Do not proceed.

---

## Deliverables

1. `PHASE_C1_SPEC.md` — this file
2. `PHASE_C1_FREEZE.json` — pre-declared parameters
3. `runners/run_asymmetric_cost_lc322.py`
4. `runners/run_asymmetric_cost_lc45.py`
5. `data/asymmetric_cost_lc322.json`
6. `data/asymmetric_cost_lc45.json`
7. `docs/PHASE_C1_RESULTS.md`
8. New test file: `tests/test_asymmetric_cost_utility.py`
