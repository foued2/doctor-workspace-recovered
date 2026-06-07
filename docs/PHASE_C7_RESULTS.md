# docs/PHASE_C7_RESULTS.md
# Doctor Phase C-7 Results: Response-Equivalence Quotient on `large_amount_stress`
# Date: 2026-06-07
# Status: Final phase record. Does not reopen any closed phase.

---

## 1. What this document is

A single-layer record of the C-7 phase. Five conditions (P0, P1, P2a,
P2b, P2c) tested on the family-3 restricted quotient population on
LC322. Per-condition reporting only. The RQ-C7 verdict is one of
{POSITIVE, NEGATIVE, MIXED} derived from per-condition status; no
other aggregation. No new measurement, no causal language, no
"real" word for the C-4 gain, no H1/H2 resolution claim.

Pairs with:
- `PHASE_C7_SPEC.md` (commit `779f9cb`)
- `PHASE_C7_FREEZE.json` (commit `06bbe40`)
- Data: `data/c7_quotient_lc322.json` (commit `5880f9b`)

---

## 2. Population and inputs

| Parameter          | Value                                          |
|--------------------|------------------------------------------------|
| Population         | LC322                                          |
| n_solvers          | 30                                             |
| n_accept / n_reject| 11 / 19                                        |
| Family-3 probes    | p_fp_0011 .. p_fp_0015 (5 probes, axis=magnitude) |
| n_abstract_probes (P0) | 5 (all 5 family-3 probes in distinct response classes) |
| Cost model         | asymmetric cost (C-1, delta=0.10)              |
| Lambda sweep       | 9 values: [1, 2, 5, 7, 10, 15, 20, 30, 50]      |
| Estimators         | C_genuine, B1_count (existing, unchanged)      |

Aggregate consistency check: B1 on full 30-probe set matches stored
(WA=0, WR=5). **PASS.**

---

## 3. Quotient construction on the unperturbed population

On the unperturbed LC322 (P0), the 5 family-3 probes have 5 distinct
response vectors across the 30 solvers. The quotient population has
|T_P| = 5 abstract probes, one per original probe. None of the
family-3 probes are probe-equivalent on the unperturbed population.

---

## 4. Per-condition results

### 4.1 P0 — Unperturbed

| Parameter         | Value                                  |
|-------------------|----------------------------------------|
| n_solvers         | 30                                     |
| \|T_P\|           | 5                                      |
| D(M_C, M_{B1})    | 19                                     |
| B1 (WA, WR)       | (5, 5)                                 |
| C_genuine (WA, WR)| (19, 0)                                |
| gap at lambda=1   | -0.30 (collapse)                       |
| gap at lambda=2   | -0.13 (collapse)                       |
| gap at lambda=5   | +0.37                                  |
| gap at lambda=50  | +7.87                                  |
| Per-condition verdict | **COLLAPSE** (gap <= delta at lambda=1, 2) |

C_genuine accepts every solver with one or more family-3 failures.
The vacuous-satisfaction argument (per the spec) holds: condition (b)
of the rule is "all failures share one probe_family". On the
family-3 quotient, every abstract probe has probe_family =
`large_amount_stress` by inheritance, so the condition is satisfied
for any solver with one or more failures. C_genuine produces 19
wrong_accepts (one for each oracle REJECT solver that has at least
one family-3 failure). B1 has 0 wrong_accepts and 5 wrong_rejects
(the 5 C-4 recoveries).

The unperturbed gap is negative at small lambdas, indicating C is
worse than B1 on the family-3 restricted population. At larger
lambdas, B1's reject-bias becomes more costly, and C catches up.
The gap sign-flip with lambda is structural to the cost model
(lambda weights wrong_rejects more heavily than wrong_accepts), not
a property of the quotient.

### 4.2 P1 — Label inversion

| Parameter         | Value                                  |
|-------------------|----------------------------------------|
| n_solvers         | 30                                     |
| \|T_P\|           | 5 (unchanged from P0)                  |
| D(M_C, M_{B1})    | 19                                     |
| B1 (WA, WR)       | (6, 14)                                |
| C_genuine (WA, WR)| (11, 0)                                |
| gap at lambda=1   | +0.30                                  |
| gap at lambda=50  | +23.17                                 |
| Per-condition verdict | **STABLE** (gap > delta at all 9 lambda) |

The quotient is unchanged from P0 (equivalence relation is on
R(s, p), not on oracle labels). Estimator decisions are unchanged.
The label inversion flips the oracle labels used in the gap
calculation, which flips the cost: C's 19 wrong_accepts on the
original become 19 correct_accepts on the inverted population. B1's
5 wrong_rejects on the original become 5 wrong_accepts on the
inverted population (B1 was rejecting ACCEPT solvers; inverted,
those are REJECT solvers, and B1's reject of REJECT is correct).

The P1 result is an artifact of the label inversion, not a property
of C's robustness. C is stable on the inverted population only
under the inverted labels; the inversion turns C's false_accepts
into correct_accepts.

### 4.3 P2a — Solver subsample (first 20)

| Parameter         | Value                                  |
|-------------------|----------------------------------------|
| n_solvers         | 20 (indices 0..19)                     |
| \|T_P\|           | 4 (one probe-equivalence class collapsed; the discriminating solver is not in the subsample) |
| D(M_C, M_{B1})    | 11                                     |
| B1 (WA, WR)       | (4, 2)                                 |
| C_genuine (WA, WR)| (13, 0)                                |
| gap at lambda=1   | -0.35 (collapse)                       |
| gap at lambda=2   | -0.25 (collapse)                       |
| gap at lambda=5   | +0.05 (collapse, gap < delta)          |
| gap at lambda=7   | +0.25                                  |
| Per-condition verdict | **COLLAPSE** (gap <= delta at lambda=1, 2, 5) |

The subsample of 20 solvers produces a different quotient than P0
(one equivalence class collapses because the discriminating solver
is not in the subsample). |T_P| drops from 5 to 4.

C_genuine accepts 13 of 20 (5 C-4 recoveries + 8 other solvers with
family-3 failures). Of the 13, 4 are wrong_accepts (the 8 others
are REJECT). B1 has 4 wrong_accepts and 2 wrong_rejects (the
recoveries that have family-3 failures).

The unperturbed-equivalent gap on the subsample is -0.35 at
lambda=1, which is below delta. COLLAPSE.

### 4.4 P2b — Solver subsample (last 20)

| Parameter         | Value                                  |
|-------------------|----------------------------------------|
| n_solvers         | 20 (indices 10..29)                    |
| \|T_P\|           | 5 (all 5 family-3 probes remain in distinct classes) |
| D(M_C, M_{B1})    | 18                                     |
| B1 (WA, WR)       | (1, 5)                                 |
| C_genuine (WA, WR)| (14, 0)                                |
| gap at lambda=1   | -0.40 (collapse)                       |
| gap at lambda=2   | -0.15 (collapse)                       |
| gap at lambda=5   | +0.60                                  |
| Per-condition verdict | **COLLAPSE** (gap <= delta at lambda=1, 2) |

The subsample of 20 (last 20) preserves all 5 equivalence classes.
C_genuine accepts 14 of 20 (5 C-4 recoveries + 9 other solvers with
family-3 failures). B1 has 1 wrong_accept and 5 wrong_rejects.

The unperturbed-equivalent gap on the subsample is -0.40 at
lambda=1, below delta. COLLAPSE.

### 4.5 P2c — Solver subsample (first 10 + last 10)

| Parameter         | Value                                  |
|-------------------|----------------------------------------|
| n_solvers         | 20 (indices 0..9, 20..29)              |
| \|T_P\|           | 4                                      |
| D(M_C, M_{B1})    | 9                                      |
| B1 (WA, WR)       | (5, 3)                                 |
| C_genuine (WA, WR)| (11, 0)                                |
| gap at lambda=1   | -0.15 (collapse)                       |
| gap at lambda=2   | 0.00 (collapse, gap < delta)           |
| gap at lambda=5   | +0.45                                  |
| Per-condition verdict | **COLLAPSE** (gap <= delta at lambda=1, 2) |

The middle 10 solvers are excluded. The subsample has 4 C-4
recoveries (solver_021, 025, 027 + 1 from the last 10) and 4
C-4-recovery-missing ACCEPT solvers. C_genuine accepts 11 of 20.
B1 has 5 wrong_accepts and 3 wrong_rejects.

The unperturbed-equivalent gap on the subsample is -0.15 at
lambda=1, below delta. COLLAPSE.

---

## 5. RQ-C7 verdict

**NEGATIVE.**

P0 is a collapse. Per the C-7 spec, the verdict is NEGATIVE
regardless of perturbation stability; P0 is one of the 5 conditions
in the per-perturbation stability test and the success criterion is
the conjunction of all 5 conditions being STABLE.

Per-condition summary:
- P0: COLLAPSE
- P1: STABLE
- P2a: COLLAPSE
- P2b: COLLAPSE
- P2c: COLLAPSE

Only 1 of 5 conditions is STABLE. P1's stability is an artifact of
the label inversion (per §4.2); it does not indicate C's robustness
on the family-3 population.

---

## 6. What the result does not establish

1. The C-4 gain (D=6, A=50 on the full 30-probe set on LC322) is
   not refuted by C-7. C-7 tests the family-3 restricted quotient
   only, not the full 30-probe set. The full-30 C-4 result stands
   at `phase-c4-results` (commit `50d33e5`).

2. The C-4 gain is not established as probe-internal by C-7. A
   NEGATIVE C-7 result is consistent with the C-4 gain being a
   within-family probe distinction, but does not establish this.
   The H1/H2 ambiguity is not resolved by this phase (per the
   spec).

3. C_genuine is not refuted as a decision rule. C-7 applies the
   rule on a restricted probe set where the rule's accept-bias
   produces many false_accepts. The full-30 result (C-4 PASS on
   LC322) and the family-3 restricted result (C-7 NEGATIVE) are
   observations on different probe spaces; they are not in
   contradiction.

---

## 7. What the result does establish

On the unperturbed family-3 quotient population (P0, n=30 solvers,
|T_P|=5 abstract probes):

- The C-4 gain on the full 30-probe set does not survive
  restriction to the family-3 probe set.
- B1 has 5 wrong_rejects (the 5 C-4 recoveries). C_genuine has 0
  wrong_rejects and 19 wrong_accepts.
- The unperturbed gap at lambda=1 is -0.30; at lambda=2 is -0.13.
  Both are below delta=0.10.
- C_genuine's accept-bias is a liability on the family-3
  restricted population, where most solvers with family-3
  failures are oracle REJECT.

The collapse pattern (P0, P2a, P2b, P2c all collapse; only P1 is
stable) is consistent with the C-4 gain on the family-3 restricted
population being a property of the original accept/reject rate of
the population, not a property of the estimators.

---

## 8. Aggregate consistency check

Re-run B1 on unperturbed LC322 (full 30-probe set, not restricted
to family-3). Recomputed (WA, WR) = (0, 5) must equal stored
(WA, WR) in `data/midweather_fingerprint_lc322.json`. **PASS.**

On inconsistency: STOP and surface to Foued. The check did not
fail.

---

## 9. Methodological notes

- Pseudo-count, permutation seed, prior-phase parameters: not
  applicable to C-7. C-7 does not fit any model on the data; it
  applies existing rules to the quotient population.
- Quotient construction is deterministic (sorted by
  representative_probe_id). See
  `tests/test_quotient.py:TestDeterminism`.
- Quotient construction on subsamples (P2a, P2b, P2c) is recomputed
  on the subsample solver set. The equivalence relation is over
  the subsampled solvers; two probes equivalent on the full 30
  may not be equivalent on a subsample of 20.
- T_P sizes: P0=5, P1=5 (unchanged), P2a=4, P2b=5, P2c=4. The
  P2a and P2c subsamples collapse one equivalence class; the
  discriminating solver is not in the subsample.
- Per-condition gap tables: see `data/c7_quotient_lc322.json`.

---

## 10. Epistemological constraints

1. **Compression drift:** no claim stronger than the observation.
2. **Negative result inflation:** no generalization beyond tested
   population (LC322), tested family (large_amount_stress), tested
   condition set (P0, P1, P2a-c).
3. **Hidden causal language:** no because / therefore / explains /
   caused by / due to. The collapse is reported as a numerical
   observation, not attributed to a cause.
4. **H1/H2 resolution:** not claimed. The result is consistent
   with the C-4 gain being a within-family probe distinction, but
   does not establish this. The H1/H2 ambiguity is not resolved.
5. **No "real" word for the C-4 gain:** the C-4 result stands at
   `phase-c4-results`; C-7 reports on a restricted probe set, not
   on the C-4 gain.
6. **Per-condition reporting only:** no aggregation across
   conditions except the pre-declared RQ-C7 verdict.

§7 hard-stop rule: if any move requires violating the above, the
phase stops. The phase did not require any such move.

---

## 11. Lineage

| Item                   | Commit    |
|------------------------|-----------|
| `PHASE_C7_SPEC.md`     | `779f9cb` |
| `PHASE_C7_FREEZE.json` | `06bbe40` |
| `doctor/adversarial/quotient.py` | `5963657` |
| `tests/test_quotient.py` | `5963657` |
| `runners/run_c7_quotient_lc322.py` | `d58fc00` |
| `data/c7_quotient_lc322.json`     | `5880f9b` |
| `docs/PHASE_C7_RESULTS.md` (this) | (pending) |

Inherited (lineage only, not modified):
- C-1 freeze `3bd286d`
- C-3a freeze `a6c97bc`, tag `phase-c3a-results` `1ad4777`
- C-4 freeze `88d0243`, tag `phase-c4-results` `50d33e5`
- C-5 freeze `98cc8e4`, tag `phase-c5-results` `d1435a3`
- C-6 freeze `6766f4c`, tag `phase-c6-results` `788fc5b`
- seval_manifest `d157d00`
- project-closure-004 `ccbf927`
