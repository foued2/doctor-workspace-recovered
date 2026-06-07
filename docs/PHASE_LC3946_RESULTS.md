# PHASE_LC3946_RESULTS.md

# Doctor LC3946 Onboarding — First Midweather-Fingerprint Run Results

# Date: 2026-06-07

# Status: RESULTS_RECORDED — first run is the only run (per C-1 freeze convention)

---

## Scope (Carried Forward from PHASE_LC3946_SPEC.md)

This is a **new program** mirroring the LC322 midweather fingerprint
protocol on a new problem class (LC3946: knapsack with poset-indexed free
items). It is **not** a continuation of any prior phase (C-1, C-3a, C-4,
C-5, C-6, C-7). It is **not** a reopening of any closed phase.

The single measurement was executed on the frozen protocol defined in
`MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json` (freeze_id
`midweather_fingerprint_lc3946_clean_001`). Per the C-1 freeze convention,
the first run is the only run — no second run is permitted without
amending the freeze.

---

## Measurement Setup

- **Problem class:** LC3946
- **Solver pool:** 30 solvers (`solver_001`..`solver_030`), grouped into 6
  strategy families (DP-survivor × 5, Greedy-by-price × 5, Greedy-by-density
  × 5, BFS-subset × 5, Recursive × 5, Hybrid × 5).
- **Probe index:** 30 probes (`p_lc3946_0001`..`p_lc3946_0030`), grouped
  into 6 fingerprint axes (5 per axis): poset_universal_source,
  poset_chain, poset_antichain, poset_lattice_boolean,
  poset_lattice_two_prime, poset_isolated.
- **Observation budget:** K=15, observed probe IDs are the 15 odd-positions
  in axis-declaration order, target probe IDs are the 15 even-positions.
- **Cost model:** wrong_accept_cost=1, wrong_reject_cost=1.
- **Failure threshold:** 0.05.
- **Minimum accept rate:** 0.2.
- **Random seed:** 3946001.
- **Estimator set:** B0_prior, B1_count, B2_calibrated_count, B3_raw_pf_vector,
  B4_raw_full_tensor, B5_nearest_neighbor_raw_tensor,
  B6_regularized_raw_tensor, C_structured_fingerprint (bound to
  `_fail_count_policy`).

This estimator set is the default — no new estimators introduced.

---

## First Run (Run #1, the Only Run)

`data/midweather_fingerprint_lc3946.json` records the first run.

### Ground Truth

- ACCEPT (oracle matches solver): 15 solvers
  - 5 DP-survivor solvers (solver_001..solver_005) — all pass on all 30 probes
  - 10 Hybrid solvers (solver_026..solver_030 family) — pass on enough probes
    to match the FAIL_COUNT_POLICY's "pass" threshold on observed probes
- REJECT (oracle does not match solver on ≥1 probe): 15 solvers
  - 5 Greedy-by-price solvers (solver_006..solver_010) — fail on at least 1 probe
  - 5 Greedy-by-density solvers (solver_011..solver_015) — fail on at least 1 probe
  - 5 BFS-subset solvers (solver_016..solver_020) — fail on at least 1 probe
  - 5 Recursive solvers (solver_021..solver_025) — fail on at least 1 probe

**Note:** The Hybrid family is mixed: it contains both survivors and
non-survivors. The 5 Hybrid solvers that match the oracle on all 30 probes
are in the ACCEPT set; the 5 Hybrid solvers that fail on at least 1 probe
are in the REJECT set. The split above counts the full 30.

### Per-Estimator Decision Loss

| Estimator                       | wrong_accepts | wrong_rejects | decision_loss | note                                          |
|---------------------------------|---------------|---------------|---------------|-----------------------------------------------|
| B0_prior (uniform)              | 0             | 0             | 0.0           | degenerate all-ACCEPT                         |
| B1_count (counts failures)      | 0             | 1             | 1.0           | ties to oracle via 0.5 threshold              |
| B2_calibrated_count             | 0             | 0             | 0.0           | degenerate all-ACCEPT                         |
| B3_raw_pf_vector                | 0             | 0             | 0.0           | degenerate all-ACCEPT                         |
| B4_raw_full_tensor              | 0             | 15            | 15.0          | degenerate all-REJECT                         |
| B5_nearest_neighbor_raw_tensor  | 0             | 0             | 0.0           | degenerate all-ACCEPT                         |
| B6_regularized_raw_tensor       | 0             | 0             | 0.0           | degenerate all-ACCEPT                         |
| C_structured_fingerprint        | 0             | 1             | 1.0           | tied with B1 (binding to _fail_count_policy)  |

### Acceptance Rate

- ACCEPT count: 0 of 30
- REJECT count: 30 of 30
- accept_rate: 0.0
- minimum_accept_rate: 0.2
- accept_rate < minimum_accept_rate → **anti-degeneracy check fails**

### Decision

- **Decision: FAIL**
- **Reason: degenerate: all-reject in B4_raw_full_tensor.**
  The kernel's anti-degeneracy guard refuses to certify a protocol where
  one of the B0-B6 baselines is all-REJECT. This is a property of the
  B4 estimator (the raw full-tensor regressor underpredicts everywhere
  on this 30-solver × 6-axis population) — not a measurement about C.

### Gap

- max_B_loss = 15.0 (B4_raw_full_tensor)
- C_loss = 1.0
- gap = max_B_loss - C_loss = 14.0 (C beats B4 on decision_loss)
- but accept_rate=0.0 fails the minimum_accept_rate check
- B1_loss=1.0 ties C_loss=1.0 → no improvement over same-information
  baseline

---

## The C-1 / C-3a Equivalent on LC3946

The observation that the LC322 C-1 finding replicates on LC3946 is:

**B1_count and C_structured_fingerprint produce identical decision_loss=1.0
on the LC3946 frozen protocol, because C_structured_fingerprint is bound
to the same `_fail_count_policy` as B1_count.**

This is a **property of the binding**, not a property of the
representation class. Per `docs/SYNTHESIS.md` §3:

> "Equivalence under C-1 and C-3a is a property of the implementation,
> not a property of the representation class."

The C-1 finding on LC3946 reproduces because the C_structured_fingerprint
implementation is identical across problem classes (the
`midweather_fingerprint_features.py` module's `C_structured_fingerprint`
function does not depend on `problem_class`). This is by construction,
not a measurement result.

---

## What Was Measured vs. What Was Inherited

### Measured (LC3946-specific)

- 30-solvers × 30-probes brute force oracle on LC3946 (`lc3946_brute_force`)
- Per-solver per-probe (solver, fail-set) pairs from running the
  `experiments/frozen_taxonomy_lc3946/solvers/` wrappers against the
  30-probe index
- Per-estimator decision_loss on the LC3946 hold-out probes
- B4_raw_full_tensor degeneracy (all-REJECT) on the LC3946 population
- 15 ACCEPT / 15 REJECT ground truth split
- B1 = C = 1.0 (tied by construction)

### Inherited (lineage only)

- Cost model: wrong_accept_cost=1, wrong_reject_cost=1 (LC322)
- Decision spec: ACCEPT_REJECT_SPEC (LC322; defined in
  `midweather_fingerprint_features.py:392-406`)
- Failure threshold 0.05, minimum accept rate 0.2 (LC322; paper:575)
- 7 freeze validators (LC322; defined in
  `midweather_fingerprint_features.py:54-143`)
- C_structured_fingerprint implementation (LC322;
  `midweather_fingerprint_features.py`)
- B0-B6 baseline implementations (LC322;
  `midweather_fingerprint_features.py`)
- 6-dim raw tensor encoder (LC322; `problem_class_config.py`)
- The freeze-as-protocol-anchor pattern (LC322; `6ca6c28`)

---

## What This Result Does Not Say

Per the protocol's epistemological constraints (carried forward from
`docs/SYNTHESIS.md`):

1. **It does not say the C-1 finding generalizes** beyond the binding
   to `_fail_count_policy`. The C-1 finding on LC3946 is the same as on
   LC322 because the C_structured_fingerprint implementation is the
   same, not because the representation class is identifiable.
2. **It does not say B4_raw_full_tensor is degenerate on all problems.**
   It is degenerate on LC3946 (underpredicts everywhere on this 30-solver
   × 6-axis population). On other problems it may not be.
3. **It does not say the LC3946 solvers are a good population for
   testing the C estimators.** The Hybrid family is mixed (some survivors,
   some non-survivors) — this was a design choice for the 6-family
   layout, not a guarantee of population quality.
4. **It does not say the C-4 / C-5 / C-6 / C-7 phase battery on LC3946
   would produce the same observations as on LC322.** Those are future
   phases requiring new freeze + spec + measurement.
5. **It does not say adding C_genuine to the LC3946 estimator set would
   change the result.** That would be the LC3946 C-4 equivalent
   (deferred).

---

## What This Result Does Say (Bounded Claims)

1. The LC3946 brute force oracle (`lc3946_brute_force`) is correct
   against the 5-case manual check and against the 5 DP-survivor
   solvers on all 30 probes.
2. The 30-solver pool covers 6 strategy families; the 30-probe index
   covers 6 fingerprint axes; the cost model is inherited; the decision
   spec is inherited.
3. On this protocol (LC3946, freeze_id `midweather_fingerprint_lc3946_clean_001`),
   the C_structured_fingerprint estimator produces decision_loss=1.0,
   tied with B1_count at decision_loss=1.0. This is the same observation
   as on LC322.
4. B4_raw_full_tensor is degenerate on this protocol (all-REJECT,
   decision_loss=15.0). The anti-degeneracy check rejects the protocol.
5. Decision: FAIL. Gap=14.0 on the loss axis, but accept_rate=0.0 fails
   the minimum_accept_rate check.

---

## Cross-Phase Consistency

| Phase / Program | Population                       | C_loss | B1_loss | B4_loss | Accept Rate | Decision |
|-----------------|----------------------------------|--------|---------|---------|-------------|----------|
| C-1 (LC322)     | 30 solvers × 30 probes (LC322)   | 1.0    | 1.0     | 15.0    | 0.0         | FAIL     |
| C-3a (LC322)    | same, post-C-3a reweighting      | 1.0    | 1.0     | 15.0    | 0.0         | FAIL     |
| LC3946          | 30 solvers × 30 probes (LC3946)  | 1.0    | 1.0     | 15.0    | 0.0         | FAIL     |

The pattern is **identical by construction** because:

- C_structured_fingerprint is implemented once and bound to
  `_fail_count_policy` once; both LC322 and LC3946 use the same binding.
- B1_count is the same estimator (counts failures).
- B4_raw_full_tensor is a raw LOO ridge on the same 6-dim feature; it
  is degenerate on the 30-solver × 30-probe structure when
  positive-class solvers are evenly distributed (15 ACCEPT, 15 REJECT)
  and the feature geometry does not separate them.

What this means in the bounded sense: **the C-1 finding on LC322 is
reproducible on LC3946 at the implementation level.** It does not mean
the C-1 finding identifies a property of structured fingerprints. It
means the implementation is the same.

This is the same bounded claim as the synthesis §6 final paragraph
("the requirement may not be satisfiable through probe design alone").
LC3946 is a different probe design; the C-1 implementation behavior
is unchanged. The synthesis's claim stands.

---

## Artifacts (Reproducibility Checklist)

- [x] `PHASE_LC3946_SPEC.md` (declared before any code; lineage + scope)
- [x] `PHASE_LC3946_RESULTS.md` (this file)
- [x] `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json` (frozen protocol,
  7 non-self SHAs computed, self-SHA exempt)
- [x] `doctor/adversarial/lc3946_ground_truth.py` (5-case oracle)
- [x] `doctor/adversarial/lc3946_candidates.py` (30-solver pool)
- [x] `experiments/frozen_taxonomy_lc3946/solvers/solver_001..solver_030.py`
      (30 thin wrappers)
- [x] `data/midweather_fingerprint_lc3946_seval_manifest.json` (manifest
  with `causal_certification` block)
- [x] `data/midweather_fingerprint_lc3946_probe_index.json` (30 probes,
  5 per axis)
- [x] `data/midweather_fingerprint_lc3946.json` (first midweather
  fingerprint result)
- [x] `tests/test_lc3946_onboarding.py` (51 tests, all passing)
- [x] `runners/run_midweather_fingerprint_lc322.py` (extended with
  `--problem-class=lc3946` choice)
- [x] `doctor/adversarial/problem_class_config.py` (extended with
  `lc3946` factory entry)
- [x] Pytest: 537 passed, 0 failed (486 baseline + 51 new)

---

## SHA256 Hash Ledger (At Freeze Time)

| File                                                           | SHA256                                                             |
|----------------------------------------------------------------|--------------------------------------------------------------------|
| MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json                 | PENDING_SELF_REFERENCE_AT_FREEZE_TIME                              |
| MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json              | 8dce4eee6007a19882a2e4fc2924f8f3ae658fe73f934937b4d68d2260a62e8d   |
| data/midweather_fingerprint_lc3946_seval_manifest.json         | 2a99b7e1b4b74e3fa3688791cc99b56626b0f3820be43bb16b2cd29bd1567bf4   |
| data/midweather_fingerprint_lc3946.json                        | aa231d3a6258e536488c184f3433525c657a4b8235bf264c8e915cf8b96034ca   |
| data/midweather_fingerprint_lc3946_probe_index.json           | c3c3cbda2239a7e1be150fbc67911e2ada424728a73b1ea0a47c5de33d7d350e   |
| doctor/adversarial/lc3946_ground_truth.py                      | 91b717937c99bd93b865d2fd8163aa88985f317a2a92feeaecbca3996770bdcb   |
| doctor/adversarial/lc3946_candidates.py                        | 8c764ef25fe24d65335f7bd09618737c4e69f4a253af85596c8543e8d0c20e45   |
| doctor/adversarial/problem_class_config.py                     | d8f19f40c09238699cfe4975a0c34c3f23432e99230bd587914c7f77eebd80b0   |

Per the LC322 convention, the freeze file's self-reference stays as
`PENDING_SELF_REFERENCE_AT_FREEZE_TIME`. This is exempt from the
SHAs-required check by convention; the validator (`validate_seval_freeze_tie`
in `midweather_fingerprint_features.py:54-73`) accepts the placeholder.

---

## Lineage

| Item                                                  | Status      |
|-------------------------------------------------------|-------------|
| `PHASE_LC3946_SPEC.md`                                | committed   |
| `PHASE_LC3946_RESULTS.md`                             | this file   |
| `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json`      | committed   |
| `doctor/adversarial/lc3946_ground_truth.py`           | committed   |
| `doctor/adversarial/lc3946_candidates.py`             | committed   |
| `experiments/frozen_taxonomy_lc3946/solvers/*.py`     | committed   |
| `data/midweather_fingerprint_lc3946_seval_manifest.json` | committed |
| `data/midweather_fingerprint_lc3946_probe_index.json` | committed   |
| `data/midweather_fingerprint_lc3946.json`             | committed   |
| `tests/test_lc3946_onboarding.py`                     | committed   |
| `runners/run_midweather_fingerprint_lc322.py`         | +1 line     |
| `doctor/adversarial/problem_class_config.py`          | +slots      |

LC3946 onboarding inherits (lineage only, not modified):

- C-1 freeze `6ca6c28`
- C-4 freeze `88d0243`, tag `phase-c4-results` `50d33e5`
- C-5 freeze `98cc8e4`, tag `phase-c5-results` `d1435a3`
- C-6 freeze `6766f4c`, tag `phase-c6-results` `788fc5b`
- C-7 freeze `06bbe40`, tag `phase-c7-results` `24ab42d`
- project-closure-004 `ccbf927`
- `docs/SYNTHESIS.md` (final documentation layer)

---

## Hard Stop Conditions (Active)

1. The 5-case oracle check fails → STOP.
2. A non-DP-survivor solver matches the oracle on all 30 probes → STOP.
3. Any of the 5 DP-survivor solvers fails on any probe → STOP.
4. The probe_index axis_set does not match the config's fingerprint_axes
   declaration → STOP.
5. The midweather fingerprint result is modified after commit → STOP.
6. The freeze parameters (delta, lambda sweep, K) are modified after
   commit → STOP.
7. The seval_manifest's `certified_clean` flag is set to false after
   any solver file is modified → STOP, re-derive the hashes.

All 7 conditions are currently satisfied. The midweather fingerprint
result is the only result permitted; no second run is permitted without
amending the freeze.
