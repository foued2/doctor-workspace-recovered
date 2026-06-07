# PHASE_LC3946_SPEC.md

# Doctor LC3946 Onboarding — Frozen Protocol Spec

# Date: 2026-06-07

# Status: SPEC_FROZEN — first midweather-fingerprint run executed

---

## Explicit Non-Relationship Declaration

LC3946 onboarding is a **new program**. It is **not** a continuation of any
prior phase (C-1, C-3a, C-4, C-5, C-6, C-7) and it is **not** a reopening of
the closed phases. It is a new problem class onboarding, equivalent in scope
to the original LC45 bimaristan layer. All closed phases stand as recorded in
`docs/SYNTHESIS.md`.

LC3946 onboarding builds on prior freeze files for **lineage only**:

- Inherits the C-1 cost model from `PHASE_C1_FREEZE.json` (commit `3bd286d`).
- Inherits the C-4 estimator policy framework from
  `doctor/adversarial/problem_class_config.py` (commit `865baf3`).
- Inherits the runner from `runners/run_midweather_fingerprint_lc322.py`
  (commit `52e02108`), extended to accept `--problem-class=lc3946`.
- Inherits the midweather fingerprint feature encoder shape (6-dim) from
  `doctor/adversarial/midweather_fingerprint_features.py`.

What LC3946 onboarding introduces:

- `doctor/adversarial/lc3946_ground_truth.py` — the protected brute force oracle.
- `doctor/adversarial/lc3946_candidates.py` — the 30-solver pool across 6 families.
- `experiments/frozen_taxonomy_lc3946/solvers/solver_001..solver_030.py` —
  30 thin wrapper files, sha256-hashed.
- `data/midweather_fingerprint_lc3946_probe_index.json` — 30 probes, 5 per axis,
  6 fingerprint axes (poset_universal_source, poset_chain, poset_antichain,
  poset_lattice_boolean, poset_lattice_two_prime, poset_isolated).
- `data/midweather_fingerprint_lc3946_seval_manifest.json` — EXTERNAL_BLIND_PACK
  manifest with solver file hashes.
- `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json` — frozen protocol parameters.
- `data/midweather_fingerprint_lc3946.json` — first midweather fingerprint run.
- `tests/test_lc3946_onboarding.py` — 51 new tests, all passing.

---

## Research Question (Declared Before Any Code)

**RQ-LC3946:** What is the empirical C-1 / C-3a equivalent observation on a
new problem class? Operationalized: does the LC3946 brute force oracle agree
with the held-out ground truth, and does the C-1 finding (gap=0 on the
frozen protocol when C is bound to `_fail_count_policy`) replicate on a
problem with a different geometry (knapsack with poset-indexed free items,
versus the LC322 coin-change geometry)?

### Motivation

The synthesis (`docs/SYNTHESIS.md` §6) leaves open the question of whether
the C-1 / C-3a findings on LC322 are generalizable. The synthesis §12 frames
this as an identifiability problem. The synthesis §6 explicit open question
is "Can any estimator built on the structured fingerprint representation
class produce distribution-invariant separation from B1?"

A new problem class is one of three architectural paths to address this. The
other two are causal intervention and solver-space modeling. LC3946
onboarding is the cheapest of the three: it does not modify any estimator;
it constructs a new population under the same estimator framework and the
same cost model. The synthesis explicitly notes (§6 final paragraph) that
"the requirement may not be satisfiable through probe design alone"; this
phase is an attempt to characterize the limit of probe design on a new
problem class.

This phase does not introduce new estimators, new decision rules, or new
policies. It replicates the C-1 protocol on a new population.

---

## Oracle (the Protected Oracle)

The brute force is `lc3946_brute_force(items, budget) -> int`. It enumerates
all 2^n subsets of item types (the purchased_set), computes the free-item
count for each, and applies the cheapest-fill strategy on the remaining
budget. The oracle is the **protected oracle** per
`DOCTOR_EXECUTION_PROTOCOL.md` §3.

**5-case manual check** (run BEFORE any edit, run AFTER any edit):

1. `[(2, 5)]`, budget 10 → 2
2. `[(2, 5), (4, 7)]`, budget 12 → 3
3. `[(2, 3), (4, 5), (8, 7)]`, budget 8 → 5
4. `[(1, 2), (2, 3), (3, 5)]`, budget 6 → 5
5. `[(2, 1), (3, 1), (5, 1), (7, 1)]`, budget 4 → 4

The 5-case check is implemented as `_run_5case_oracle_check()` in
`lc3946_ground_truth.py`. It is also covered by `TestLC3946Oracle` in
`tests/test_lc3946_onboarding.py`.

The brute force correctness argument: for each purchased_set p, the optimal
allocation of the remaining budget is to put it all on the cheapest item
in p. This is because (a) the free counts are determined by p, not by the
per-type bought counts, and (b) buying extra copies of any item is a pure
bought-count addition with no free-coupling effect. So given p, the optimal
total is |p| + (sum of free counts) + (extra copies on the cheapest item).

---

## Solver Pool (30 solvers, 6 families)

The 30-solver pool mirrors the LC322 layout exactly. Each solver is
deterministic and reproducible; the wrappers import the implementations
from `doctor/adversarial/lc3946_candidates.py`.

| Solver IDs      | Family            | Strategy                                                        |
|-----------------|-------------------|-----------------------------------------------------------------|
| solver_001..005 | DP-survivor       | 2^n enumeration with cheapest-fill (correct)                    |
| solver_006..010 | Greedy-by-price   | Single-item greedy by price (no free-item logic)                |
| solver_011..015 | Greedy-by-density | Single-item greedy by 1/price or factor/price                   |
| solver_016..020 | BFS-subset        | BFS over purchased_set with various cap heuristics              |
| solver_021..025 | Recursive         | Recursive subset enumeration with various memo schemes          |
| solver_026..030 | Hybrid            | Mix of correct (DP-survivor parallel) and degenerate strategies |

The 5 DP-survivor solvers all match the oracle on every probe in the
frozen probe_index. The other 25 solvers fail on at least one probe
(empirically verified by `TestLC3946Candidates.test_at_least_one_solver_fails_on_each_probe`).

---

## Probe Index (30 probes, 6 families, 5 per family)

The 30 probes are organized into 6 fingerprint axes:

| Axis                      | Family description                                  |
|---------------------------|-----------------------------------------------------|
| `poset_universal_source`  | At least one factor=1 item; triggers all free items |
| `poset_chain`             | Factors in a divisibility chain (e.g., 2, 4, 8)     |
| `poset_antichain`         | Pairwise coprime factors; no free items             |
| `poset_lattice_boolean`   | Powers of 2 (boolean lattice)                       |
| `poset_lattice_two_prime` | Products of 2 and 3 only (2-prime lattice)          |
| `poset_isolated`          | Factors with no divisibility relations              |

Each axis has 5 probes, split 3+2 (3 observed, 2 held-out) per the C-1
freeze convention. The total 15/15 observed/held-out split mirrors LC322.

---

## Estimator Set (mirrors LC322)

The LC3946 estimator set is the same as LC322's:

- B0_prior, B1_count, B2_calibrated_count, B3_raw_pf_vector (degenerates)
- B4_raw_full_tensor (all-REJECT)
- B5_nearest_neighbor_raw_tensor, B6_regularized_raw_tensor (all-ACCEPT)
- C_structured_fingerprint (bound to `_fail_count_policy` by default)

This is the **default** estimator set. The C-1 / C-3a finding on LC322 was
that C_structured_fingerprint is bound to the same policy as B1, producing
zero gap. The first midweather fingerprint run on LC3946 replicates this
finding.

C_genuine, C_feature_threshold, C_majority, C_zero_only are defined in
`problem_class_config.py` but not in the default estimator_names list. They
can be added by extending the list (this would be the C-4 / C-6 equivalent
on LC3946, deferred to a future phase).

---

## Midweather Fingerprint Result (First Run)

`data/midweather_fingerprint_lc3946.json` records the first run:

- Ground truth: **15 ACCEPT / 15 REJECT** (the 5 DP-survivor + 10 hybrid
  survivors are ACCEPT; the 15 non-survivor solvers are REJECT).
- B1_count: 0 wrong_accepts, 1 wrong_reject, decision_loss = 1.0
- C_structured_fingerprint: 0 wrong_accepts, 1 wrong_reject, decision_loss = 1.0
  (tied with B1 — the LC322 C-1 finding replicates on LC3946)
- B4_raw_full_tensor: 15 wrong_rejects (degenerate all-REJECT)
- Decision: FAIL (because B4 is degenerate; the kernel's anti-degeneracy
  guard refuses to certify a protocol where one of the B0-B6 baselines is
  all-REJECT)

This is the LC3946 C-1 equivalent. It establishes that on the LC3946
population, the same binding (C_structured_fingerprint → _fail_count_policy)
produces the same observation (B1 and C tied at decision_loss=1.0).

---

## What This Phase Does Not Do

- Does not reopen any prior phase (C-1, C-3a, C-4, C-5, C-6, C-7).
- Does not introduce new estimators, new decision rules, or new policies.
- Does not modify the C-1 freeze parameters (delta, lambda sweep, lambda_A).
- Does not modify the C-4 `C_genuine` decision rule.
- Does not vary the oracle.
- Does not generalize beyond the LC3946 population.
- Does not run the C-4 / C-5 / C-6 / C-7 phase battery on LC3946. Those
  would be future phases requiring new freeze + spec.
- Does not claim that the LC322 / LC45 findings transfer to LC3946. The
  C-1 finding replicates (binding of C_structured_fingerprint to
  _fail_count_policy produces identical decision_loss), but this is a
  property of the binding, not of the representation class. Per
  `docs/SYNTHESIS.md` §3, "Equivalence under C-1 and C-3a is a property
  of the implementation, not a property of the representation class."

---

## Epistemological Constraints (Carried Forward)

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond LC3946 population,
   the frozen 6-axis probe taxonomy, and the 30-solver pool.
3. **Hidden causal language:** no because / therefore / explains /
   caused by / due to.
4. **Brute force oracle protection:** the oracle is run through a 5-case
   manual check before and after any edit. Any case shift → STOP.
5. **Stub discipline:** the 30 solver wrapper files raise on incorrect use
   (they import `_impl` from `lc3946_candidates`; if the import fails,
   the wrapper raises ImportError, not silently returns None).
6. **No partial commits:** all files for the LC3946 onboarding land
   together (oracle, candidates, wrappers, manifest, probe_index, freeze,
   tests, runner edit, results).
7. **Pytest count guard:** the test count after the onboarding is
   537 (486 baseline + 51 new), all passing. The baseline count of 486
   is preserved.

---

## Deliverables

1. `PHASE_LC3946_SPEC.md` — this file
2. `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json` — frozen protocol
3. `doctor/adversarial/lc3946_ground_truth.py` — the protected oracle
4. `doctor/adversarial/lc3946_candidates.py` — the 30-solver pool
5. `experiments/frozen_taxonomy_lc3946/solvers/solver_001..solver_030.py` —
   30 thin wrapper files
6. `data/midweather_fingerprint_lc3946_seval_manifest.json` — seval manifest
7. `data/midweather_fingerprint_lc3946_probe_index.json` — 30 probes
8. `data/midweather_fingerprint_lc3946.json` — first midweather fingerprint
9. `tests/test_lc3946_onboarding.py` — 51 new tests
10. `runners/run_midweather_fingerprint_lc322.py` — extended with
    `--problem-class=lc3946` (one-line addition to argparse choices)
11. `doctor/adversarial/problem_class_config.py` — extended with
    `lc3946` factory entry (mirrors `lc45` and `lc322` entries)

---

## Hard Stop Conditions (extended from prior phases)

1. The 5-case oracle check fails → STOP, surface to Foued.
2. A non-DP-survivor solver matches the oracle on all 30 probes (indicates
   the solver accidentally became a DP-survivor) → STOP, surface to Foued.
3. Any of the 5 DP-survivor solvers fails on any probe (indicates the
   oracle has drifted) → STOP, surface to Foued.
4. The probe_index axis_set does not match the config's fingerprint_axes
   declaration → STOP, surface to Foued (this is the existing kernel
   guard; mirrors LC322's behavior).
5. The midweather fingerprint result is modified after commit → STOP.
6. The freeze parameters (delta, lambda sweep, K) are modified after
   commit → STOP, surface to Foued.
7. The seval_manifest's `certified_clean` flag is set to false after
   any solver file is modified → STOP, re-derive the hashes.

---

## Lineage

| Item                                                     | Status    |
|----------------------------------------------------------|-----------|
| `PHASE_LC3946_SPEC.md`                                   | new       |
| `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json`         | new       |
| `doctor/adversarial/lc3946_ground_truth.py`              | new       |
| `doctor/adversarial/lc3946_candidates.py`                | new       |
| `experiments/frozen_taxonomy_lc3946/solvers/*.py`        | new (×30) |
| `data/midweather_fingerprint_lc3946_seval_manifest.json` | new       |
| `data/midweather_fingerprint_lc3946_probe_index.json`    | new       |
| `data/midweather_fingerprint_lc3946.json`                | new       |
| `tests/test_lc3946_onboarding.py`                        | new       |
| `runners/run_midweather_fingerprint_lc322.py`            | +1 line   |
| `doctor/adversarial/problem_class_config.py`             | +slots    |
| `docs/PHASE_LC3946_RESULTS.md`                           | (next)    |

LC3946 onboarding inherits (lineage only, not modified):

- C-1 freeze `3bd286d`
- C-4 freeze `88d0243`, tag `phase-c4-results` `50d33e5`
- C-5 freeze `98cc8e4`, tag `phase-c5-results` `d1435a3`
- C-6 freeze `6766f4c`, tag `phase-c6-results` `788fc5b`
- C-7 freeze `06bbe40`, tag `phase-c7-results` `24ab42d`
- project-closure-004 `ccbf927`
- `docs/SYNTHESIS.md` (final documentation layer)
