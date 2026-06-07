# PHASE_LC3946_C5_SPEC.md

# Doctor Phase LC3946-C5: Collapse Analysis (Distribution Shift)

# Status: DRAFT — pending Foued approval (Step 0 of protocol)

# Date: 2026-06-07

---

## Explicit Non-Relationship Declaration

Phase LC3946-C5 is a **new program** that tests the boundary conditions
of the LC3946 C-4 finding. It is **not** a continuation of any prior
phase (C-1, C-3a, C-4, C-5, C-6, C-7, LC3946 C-1) and it is **not** a
reopening of any closed phase. All closed phases stand as recorded in
`docs/SYNTHESIS.md` and the prior tag history.

LC3946-C5 builds on prior freeze files for **lineage only**:

- C-4 freeze `88d0243`, tag `phase-c4-results` `50d33e5`
- LC322 C-5 freeze `bb51f2c` (the LC322 C-5 protocol pattern)
- LC3946 onboarding freeze
  `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json` (the unperturbed
  baseline)

What changes in LC3946-C5:

- Three pre-declared population perturbation families (P1, P2, P3) test
  whether the LC3946 C-4 utility gain (`gap = B1_loss - C_genuine_loss = 1.0`)
  survives distribution shift.
- One cross-population reference (P4: the LC322 C-4 result, recorded
  for parity with the LC322 C-5 spec; no new execution).

The closed phases are **not reopened**:

| Tag                   | Commit    | Content                                      | Status |
|-----------------------|-----------|----------------------------------------------|--------|
| `project-closure-004` | `ccbf927` | Transfer-hypothesis. FAIL.                   | Stands |
| `phase-c1-results`    | `77ae794` | Asymmetric-cost sweep. Gap ≡ 0. FAIL.        | Stands |
| `phase-c3a-results`   | `1ad4777` | Per-solver identity. FULL_EQUIVALENCE.       | Stands |
| `phase-c4-results`    | `50d33e5` | Genuine structured policy. PASS on LC322.    | Stands |
| `phase-c5-results`    | `d1435a3` | LC322 collapse analysis. PARTIALLY_SURVIVES. | Stands |
| `phase-c6-results`    | `788fc5b` | C-6 closing layer.                           | Stands |
| `phase-c7-results`    | `24ab42d` | C-7 closeout.                                | Stands |
| LC3946 C-1 (in-repo)  | (pending) | LC3946 onboarding + C-4 equivalent. gap=1.0. | Stands |

LC3946-C5 tests the boundary conditions of the LC3946 C-4 finding. It
does not claim the LC3946 C-4 gain is or is not "real" in any general
sense. It reports per-perturbation survival status only.

---

## Research Question

**RQ-LC3946-C5:** Does `C_genuine`'s decision utility advantage over
B1 on LC3946 survive distribution shift — specifically, does the
probe_family coherence rule produce gains that are not specific to
the LC3946 solver population structure at the default
`failure_threshold = 0.05`?

### Motivation

The LC3946 C-4 equivalent (the C_genuine addition to the LC3946
default estimator set) produced:

- `C_genuine` decision_loss = 0.0
- `B1_count` decision_loss = 1.0
- `gap = 1.0` (C_genuine recovers 1 solver that B1 false-rejects; no
  false accepts on the LC3946 30-solver population)
- The recovery uses `probe_family` to ACCEPT solvers whose failures
  all fall within a single fingerprint axis

On LC322, the C-4 gain survived P2 (subsample) but collapsed on P3
(probe family knockout of `large_amount_stress`). The LC3946
equivalent of the LC322 C-5 is the question: which perturbation
modes does the LC3946 gap=1.0 survive, and which does it collapse
on?

If `gap > 0` survives all 11 perturbation conditions, the C-4 finding
on LC3946 is robust to the tested perturbation modes. If it collapses
on some, the C-4 finding is fragile in those modes. If it collapses
on all, the LC3946 C-4 finding is a property of the unperturbed
population structure.

---

## Aggregate Consistency Check (Required Pre-Execution)

Before any perturbation is applied, B1 and C_genuine must be re-run on
the unperturbed LC3946 population and reproduce the (WA, WR, loss)
triple recorded in `data/midweather_fingerprint_lc3946.json`:

| Estimator | Expected (WA, WR, loss) | Source                                    |
|-----------|-------------------------|-------------------------------------------|
| B1_count  | (0, 1, 1.0)             | `data/midweather_fingerprint_lc3946.json` |
| C_genuine | (0, 0, 0.0)             | `data/midweather_fingerprint_lc3946.json` |

If the re-run produces (WA, WR) inconsistent with this table, STOP
immediately. Do not record any perturbation result. Surface the
discrepancy for review.

This check ensures the perturbation runner sees the same population
and decision rules that produced the recorded C-4 result.

---

## Falsification Criterion (Three Outcomes)

The LC3946-C5 verdict is determined by per-perturbation gap behavior
under the uniform-cost loss (wrong_accept_cost=1, wrong_reject_cost=1):

- **SURVIVES:** `gap > 0` on **all** tested perturbations
  (P1b, P1c, P2a, P2b, P2c, P3a, P3b, P3c, P3d, P3e, P3f).
  P1a is the baseline (gap=1.0), not a perturbation, and is recorded
  for reference only.
- **PARTIALLY_SURVIVES:** `gap > 0` on **some** perturbations and
  `gap <= 0` (collapse) on **others**. Per-perturbation results
  reported individually; no aggregation.
- **DOES NOT SURVIVE:** `gap <= 0` on **all** tested perturbations.

All three outcomes are valid and reportable. No post-hoc selection of
favorable perturbations. No post-hoc adjustment of the survival
threshold (`gap > 0` is fixed).

`gap = 0` is collapse (not survival). Ties are not admissible.

### Per-Perturbation Reporting

For each perturbation, the (B1_loss, C_genuine_loss, gap) triple is
recorded. A perturbation "survives" if `gap > 0` strictly. A
perturbation "collapses" if `gap <= 0`. The per-perturbation status
is reported across all 11 perturbation conditions, plus the P1a
baseline reference.

---

## Pre-Declared Perturbations

The perturbations are declared in this spec, before any runner is
written. Indices and parameters are fixed and chosen before seeing
any LC3946-C5 results.

### P1 — Threshold Shift (Three Conditions)

Replace the `failure_threshold` parameter used to derive ground truth
labels and re-derive the accept/reject partition. The threshold
modifies only the ground truth derivation; the oracle's brute force
is unchanged.

- **P1a: failure_threshold = 0.05** (baseline; recorded for reference
  only, not a perturbation)
- **P1b: failure_threshold = 0.10**
- **P1c: failure_threshold = 0.20**

This tests whether the C_genuine recovery is a property of the
threshold definition (i.e., does a stricter threshold eliminate the
recovery because the marginal solver's true fail rate crosses 0.10?)
or of the probe_family signal itself (i.e., the recovery persists
regardless of threshold).

### P2 — Solver Subsample (Three Fixed Draws of 25)

Three subsamples of 25 solvers from the 30 LC3946 solvers,
pre-declared as 0-indexed index lists into the sorted `solver_id`
list `["solver_001", "solver_002", ..., "solver_030"]`:

- **P2a:** indices
  `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]`
  (first 25; drops `solver_026`, `solver_027`, `solver_028`,
  `solver_029`, `solver_030`)
- **P2b:** indices
  `[5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`
  (last 25; drops `solver_001`, `solver_002`, `solver_003`,
  `solver_004`, `solver_005`)
- **P2c:** indices
  `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`
  (first 10 + last 15; drops `solver_011`, `solver_012`,
  `solver_013`, `solver_014`, `solver_015` — the middle 5)

These three draws were chosen to have different coverage of the
LC3946 solver population:

- P2a covers the first 25
- P2b covers the last 25
- P2c excludes the middle 5 (indices 10–14)

The choice was made before seeing any LC3946-C5 results.

This tests whether the C_genuine advantage is driven by a small
number of specific solvers. With 25 of 30 solvers retained, the
P(retaining the recovered solver) is 25/30 ≈ 0.83 — high enough to
give a meaningful survival test while still applying pressure.

### P3 — Probe Family Knockout (Six Rotating Knocks)

Remove all observed probes from one probe_family at a time, then
re-run B1 and C_genuine on the reduced probe set. The 6 LC3946
families (per `LC3946_FINGERPRINT_AXES` axis_declaration order):

1. `poset_universal_source` (probes `p_lc3946_0001`..`p_lc3946_0005`,
   observed `p_lc3946_0001`, `p_lc3946_0003`, `p_lc3946_0005`)
2. `poset_chain` (probes `p_lc3946_0006`..`p_lc3946_0010`,
   observed `p_lc3946_0007`, `p_lc3946_0009`)
3. `poset_antichain` (probes `p_lc3946_0011`..`p_lc3946_0015`,
   observed `p_lc3946_0011`, `p_lc3946_0013`, `p_lc3946_0015`)
4. `poset_lattice_boolean` (probes `p_lc3946_0016`..`p_lc3946_0020`,
   observed `p_lc3946_0017`, `p_lc3946_0019`)
5. `poset_lattice_two_prime` (probes `p_lc3946_0021`..`p_lc3946_0025`,
   observed `p_lc3946_0021`, `p_lc3946_0023`, `p_lc3946_0025`)
6. `poset_isolated` (probes `p_lc3946_0026`..`p_lc3946_0030`,
   observed `p_lc3946_0027`, `p_lc3946_0029`)

The knockout rotation order is the enumeration order above (1, 2, 3,
4, 5, 6). This produces 6 perturbations (P3a–P3f). Each knockout
drops the 2 or 3 observed probes in that family, reducing K from 15
to 12 or 13 (the 6 axes have 3, 2, 3, 2, 3, 2 observed probes
respectively).

P3 knockout rotation order (pre-declared):

| Perturbation | Knocked-out family        | Probes removed from observed set |
|--------------|---------------------------|----------------------------------|
| P3a          | `poset_universal_source`  | 0001, 0003, 0005                 |
| P3b          | `poset_chain`             | 0007, 0009                       |
| P3c          | `poset_antichain`         | 0011, 0013, 0015                 |
| P3d          | `poset_lattice_boolean`   | 0017, 0019                       |
| P3e          | `poset_lattice_two_prime` | 0021, 0023, 0025                 |
| P3f          | `poset_isolated`          | 0027, 0029                       |

This tests whether the C_genuine advantage depends on a specific
probe_family being present in the observed probe set. With the
LC3946 6-axis × 5-probes-per-axis design, a family knockout is a
well-defined structural perturbation.

### P4 — Cross-Population Reference (Already Recorded)

The LC322 C-4 result is already recorded in
`data/c4_decisions_lc322.json` (or the equivalent
`data/midweather_fingerprint_lc322.json` post-C_genuine run, which is
the C-1 file extended with C_genuine). The cross-population reference
is the LC322 result itself; no new execution is needed for P4.

The LC322 C-4 result: `gap = 8.30` at the `large_amount_stress`
family knockout (LC322's signal family). The LC322 C-5 result
(`phase-c5-results`) is `PARTIALLY_SURVIVES` per the LC322 C-5 spec.

P4 is recorded in the LC3946-C5 results doc for parity with the
LC322 C-5 spec's P4 entry. It is **not** counted as a perturbation
on the LC3946 population — it is a cross-population anchor.

---

## Estimators Under Comparison

- **C_genuine**: the genuine structured policy from C-4. Unchanged.
  Decision rule: ACCEPT if 0 failures, ACCEPT if all failures share
  one probe_family, REJECT otherwise. Implementation in
  `doctor/adversarial/problem_class_config.py:_c_genuine_policy`.
- **B1_count**: `_fail_count_policy`. Unchanged from C-1, C-3a, C-4,
  LC3946 C-1.
  Decision rule: ACCEPT iff `obs_fails == 0`. Implementation in
  `doctor/adversarial/problem_class_config.py:_fail_count_policy`.

No new estimators. No new decision rules. No new decision thresholds.

The cost model is the midweather-fingerprint runner's uniform cost
(`wrong_accept_cost = wrong_reject_cost = 1`). The primary utility
metric is `decision_loss` (raw integer, not normalized). The
survival threshold is `gap > 0` strictly.

---

## What This Phase Does Not Do

- Does not reopen `project-closure-004`, `phase-c1-results`,
  `phase-c3a-results`, `phase-c4-results`, `phase-c5-results`,
  `phase-c6-results`, or `phase-c7-results`.
- Does not introduce new probes, probe geometry, or solver packs.
- Does not modify the C-1, C-3a, C-4, C-5, C-6, or C-7 freeze
  parameters.
- Does not modify the LC3946 onboarding freeze parameters (K=15,
  observed/target split, decision spec, weakest baseline config).
- Does not introduce new estimator names.
- Does not adjust the `C_genuine` decision rule during the analysis.
- Does not adjust the B1 decision rule.
- Does not adjust the survival threshold (`gap > 0` is fixed).
- Does not adjust the `failure_threshold` values in P1a/P1b/P1c.
- Does not adjust the pre-declared P2 subsample index lists.
- Does not adjust the pre-declared P3 knockout rotation order.
- Does not perform a lambda sweep (per Foued's Point 1 decision).
- Does not perform per-solver-weighted cost functional analysis
  (C-2 territory).
- Does not post-hoc select favorable perturbations.
- Does not aggregate across perturbations.
- Does not claim the LC3946 C-4 gain is or is not "real" in any
  general sense. Reports per-perturbation survival status only.

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested
   perturbations.
3. **Hidden causal language:** no because / therefore / explains /
   caused by / due to.
4. **Per-perturbation reporting:** results are reported per
   perturbation, not aggregated.
5. **The word "real" is forbidden in the results doc** to describe
   the LC3946 C-4 gain. The LC3946 C-4 gain is an observation on the
   specific LC3946 population under the specific `C_genuine` rule.
   It is not characterized as real or unreal.

§7 hard-stop rule: if any move requires violating the above, stop
and surface the conflict.

---

## Hard Stop Conditions (Extended from LC322 C-5)

1. The aggregate consistency check fails (re-run B1 or C_genuine
   does not reproduce the (WA, WR) from the unperturbed LC3946
   baseline) → STOP, surface the discrepancy.
2. The 5-case oracle check on `lc3946_brute_force` fails → STOP.
3. The 5-case oracle check is run before and after any edit to
   `doctor/adversarial/lc3946_ground_truth.py` per
   `DOCTOR_EXECUTION_PROTOCOL.md` §3.
4. Any perturbation produces a runner error → STOP, surface to Foued.
5. The pre-declared P2 subsample index lists are adjusted after
   seeing C-5 results → STOP, surface to Foued.
6. The pre-declared P3 family knockout rotation order is adjusted
   after seeing C-5 results → STOP, surface to Foued.
7. The pre-declared P1 threshold values (0.05, 0.10, 0.20) are
   adjusted after seeing C-5 results → STOP, surface to Foued.
8. The survival threshold `gap > 0` is adjusted after seeing C-5
   results → STOP, surface to Foued.
9. Any move targets a file that does not exist in the repo → STOP,
   surface to Foued.
10. The `pytest` count drops below 537 (the LC3946 onboarding
    baseline) → STOP, surface the failure.
11. The aggregate consistency check's expected (WA, WR, loss) triple
    for B1 or C_genuine is updated mid-execution → STOP, surface
    to Foued.

---

## Deliverables

1. `PHASE_LC3946_C5_SPEC.md` — this file (commit before any code)
2. `PHASE_LC3946_C5_FREEZE.json` — pre-declared parameters
   (commit before any code)
3. `tests/test_lc3946_c5_perturbations.py` — tests for perturbation
   module (commit with module)
4. `doctor/adversarial/lc3946_collapse_perturbations.py` —
   perturbation construction functions (commit with tests)
5. `runners/run_c5_collapse_lc3946.py` — runner (committed before
   execution)
6. `data/c5_collapse_lc3946.json` — output data
7. `docs/PHASE_LC3946_C5_RESULTS.md` — findings, per-perturbation
   reporting, no aggregation
8. Tag: `phase-lc3946-c5-results`

---

## Protocol (mirrors LC322 C-5)

**Step 0 — Commit this spec and the freeze file before any code is
written.** No runner is written until both files are committed.

**Step 1 — Write `PHASE_LC3946_C5_FREEZE.json`.** Contents: 11
perturbation conditions (P1b, P1c, P2a, P2b, P2c, P3a, P3b, P3c,
P3d, P3e, P3f) with full parameters, the P1a baseline reference,
P4 cross-population anchor, aggregate consistency check expected
values, survival threshold, lineage. Commit before any runner is
written.

**Step 2 — Write `tests/test_lc3946_c5_perturbations.py`.** TDD red
phase first. Tests must cover:

- P1a/P1b/P1c threshold shift changes the ground truth labels as
  expected.
- P2 subsamples produce 25 solvers each, matching the pre-declared
  index lists exactly.
- P3 knockout removes the correct probes from both observed and
  target sets, leaving the others.
- P4 cross-population reference is a read-only anchor, no
  perturbation applied.
- The aggregate consistency check correctly detects a discrepancy
  if one is introduced.
- The falsification criterion correctly classifies SURVIVES /
  PARTIALLY_SURVIVES / DOES_NOT_SURVIVE.
- The 5-case oracle check still passes on the unperturbed
  `lc3946_brute_force`.

**Step 3 — Implement perturbation module
`doctor/adversarial/lc3946_collapse_perturbations.py`.** Functions
for each perturbation. All tests green. Commit module + tests
together.

**Step 4 — Write runner `runners/run_c5_collapse_lc3946.py`.** Re-run
B1 and C_genuine on the unperturbed LC3946 (aggregate-consistency
check), then apply each perturbation and compute per-perturbation
gaps. The runner should:

- Reuse `apply_estimator` and `compute_decision_loss` from
  `runners/run_midweather_fingerprint_lc322.py` (import, do not
  duplicate)
- Reuse `_fail_count_policy` and `_c_genuine_policy` from
  `doctor/adversarial/problem_class_config.py` (import, do not
  duplicate)
- Read the (solver_id, probe_id) → pass_fail matrix from a sidecar
  file written by the main midweather-fingerprint run, OR re-execute
  the solvers directly using the existing seval_manifest. The
  sidecar approach is preferred (avoids 900 solver re-executions per
  perturbation).
- Apply each perturbation by filtering the pass_fail matrix
- Compute per-perturbation (B1_loss, C_genuine_loss, gap)
- Apply the falsification criterion
- Write `data/c5_collapse_lc3946.json` and a stdout summary
- Commit before execution.

**Step 5 — Execute.** Check aggregate consistency for B1 and
C_genuine on unperturbed LC3946. STOP if any inconsistency. If
passes, apply each perturbation, compute per-perturbation gap
table, apply falsification criterion.

**Step 6 — Write `docs/PHASE_LC3946_C5_RESULTS.md`.** Audit against
three failure modes before commit:

- (i) All (B1, C_genuine) per-perturbation triples are recorded
- (ii) No aggregation across perturbations in the verdict
- (iii) No "real" language for the C-4 gain

Per-perturbation reporting. No "real" language. No aggregation.
The verdict is one of: SURVIVES, PARTIALLY_SURVIVES, DOES NOT
SURVIVE.

**Step 7 — Tag `phase-lc3946-c5-results`.**

---

## Governance Acknowledgment

LC3946-C5 is a new program that tests the boundary conditions of the
LC3946 C-4 finding via population perturbation. The
`C_genuine` decision rule is not adjusted during the LC3946-C5
analysis. The perturbation set is pre-declared in this spec.

Per Foued's Point 1 decision: the cost model is the
midweather-fingerprint runner's uniform cost; no lambda sweep; no
new cost-model runner.

Per Foued's Point 2 decision: P1 is replaced with a threshold-shift
perturbation (failure_threshold = 0.05, 0.10, 0.20).

Per Foued's Point 3 decision: P2 subsamples are of size 25 (not
20), with three pre-declared fixed draws (P2a, P2b, P2c).

Per Foued's Point 4 decision: P3 family knockout uses the
axis_declaration order from `LC3946_FINGERPRINT_AXES` as the
rotation order, with the full rotation sequence pre-declared.

LC3946-C5 stops here. If at any point Foued withdraws the LC3946-C5
authorization, the phase stops. The LC3946-C5 spec and freeze remain
in the repository as a record of the authorized program.

---

## Lineage

| Item                                                  | Status            |
|-------------------------------------------------------|-------------------|
| `PHASE_LC3946_C5_SPEC.md`                             | DRAFT (this file) |
| `PHASE_LC3946_C5_FREEZE.json`                         | PENDING           |
| `tests/test_lc3946_c5_perturbations.py`               | PENDING           |
| `doctor/adversarial/lc3946_collapse_perturbations.py` | PENDING           |
| `runners/run_c5_collapse_lc3946.py`                   | PENDING           |
| `data/c5_collapse_lc3946.json`                        | PENDING           |
| `docs/PHASE_LC3946_C5_RESULTS.md`                     | PENDING           |
| `phase-lc3946-c5-results` tag                         | PENDING           |

LC3946-C5 inherits (lineage only, not modified):

- C-1 freeze `3bd286d`
- C-3a freeze `a6c97bc`
- C-4 freeze `88d0243`, tag `phase-c4-results` `50d33e5`
- C-5 freeze `bb51f2c`, tag `phase-c5-results` `d1435a3`
- C-6 freeze `6766f4c`, tag `phase-c6-results` `788fc5b`
- C-7 freeze `06bbe40`, tag `phase-c7-results` `24ab42d`
- project-closure-004 `ccbf927`
- LC3946 onboarding freeze
  (`MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json`)
- `docs/SYNTHESIS.md` (final documentation layer)
